from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from config.settings import AppSettings
from core.models import GenerationRequest, GenerationResult, SlideScene, TutorialPlan
from diagrams.engines import DiagramEngine
from diagrams.chart_engine import ChartEngine
from llm.ollama_client import OllamaTutorialGenerator
from render.timeline import TimelineBuilder
from render.video_renderer import VideoRenderer
from slides.scene_builder import ScenePlanner
from tts.piper_engine import PiperTTSEngine
from uploads.youtube import YouTubeUploader
from utils.cache import DiskCache
from utils.command import CommandRunner
from visuals.comfyui_client import ComfyUIClient
from visuals.slide_renderer import SlideComposer
from utils.search_client import SearchClient


class TechExplainerPipeline:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cache = DiskCache(settings.app.cache_dir)
        self.runner = CommandRunner()
        self.ollama = OllamaTutorialGenerator(
            settings.ollama.base_url,
            settings.ollama.model,
            settings.ollama.timeout_seconds,
            self.cache,
        )
        self.comfyui = ComfyUIClient(
            settings.comfyui.base_url,
            settings.comfyui.workflow_path,
            settings.comfyui.poll_interval_seconds,
            self.cache,
        )
        self.diagram_engine = DiagramEngine(settings.diagram.mermaid_cli, settings.diagram.graphviz_dot, self.runner)
        self.chart_engine = ChartEngine()
        self.tts = PiperTTSEngine(
            settings.tts.piper_executable,
            settings.tts.model_path,
            settings.tts.config_path,
            settings.tts.voice_models,
            self.runner,
        )
        self.timeline_builder = TimelineBuilder()
        self.video_renderer = VideoRenderer(settings.video, self.runner)
        self.slide_composer = SlideComposer(settings.video.width, settings.video.height)
        self.scene_planner = ScenePlanner()
        self.search_client = SearchClient()
        self.youtube = YouTubeUploader()

    def run(self, request: GenerationRequest) -> GenerationResult:
        self.logger.info("Starting pipeline for topic: %s", request.topic)
        run_dir = self._create_run_directory(request.topic)
        self.logger.info("Run directory created: %s", run_dir)
        
        self.logger.info("Generating tutorial plan via LLM...")
        search_context = self.search_client.search_topic(request.topic)
        self.logger.info("Web search context gathered (%d chars)", len(search_context))
        print(f"\n--- WEB SEARCH RESULTS FOR: {request.topic} ---\n{search_context}\n-----------------------------------\n")
        
        tutorial = self.scene_planner.normalize(request, self.ollama.generate(request, search_context))
        tutorial_path = run_dir / "tutorial.json"
        tutorial_path.write_text(json.dumps(tutorial.model_dump(), indent=2), encoding="utf-8")
        self.logger.info("Tutorial plan saved to %s", tutorial_path)

        if request.generate_diagrams and tutorial.diagrams:
            self.logger.info("Rendering %d diagrams...", len(tutorial.diagrams))
            tutorial.diagrams = self.diagram_engine.render_all(tutorial.diagrams, run_dir / "diagrams")
            self._attach_diagrams(tutorial)

        if tutorial.charts:
            self.logger.info("Rendering %d data charts...", len(tutorial.charts))
            tutorial.charts = self.chart_engine.render_all(tutorial.charts, run_dir / "charts")
            self._attach_charts(tutorial)

        if request.generate_images:
            self.logger.info("Generating AI images for scenes...")
            self._generate_images(tutorial, run_dir / "images")

        self.logger.info("Rendering presentation slides...")
        self._render_slides(tutorial, run_dir / "slides")
        
        self.logger.info("Synthesizing narration and building timeline...")
        timeline = self._build_audio_and_timeline(tutorial, run_dir, request.generate_tts)
        timeline_path = run_dir / "timeline.json"
        timeline_path.write_text(json.dumps(timeline.model_dump(), indent=2), encoding="utf-8")

        final_video = None
        subtitle_file = None
        if request.render_video and not request.generate_tts:
            raise RuntimeError("Video rendering requires narration audio. Re-run without --skip-tts or disable video rendering.")
        
        if request.render_video:
            self.logger.info("Starting video rendering...")
            final_video, subtitle_file = self.video_renderer.render(timeline, run_dir / "final", self._slugify(request.topic))
            self.logger.info("Video rendering complete: %s", final_video)

        uploaded = False
        if request.upload_youtube and final_video:
            uploaded = self.youtube.upload(
                final_video,
                title=f"{request.topic} Explained",
                description=tutorial.architecture_explanation,
                tags=tutorial.related_technologies[:10],
            )

        return GenerationResult(
            topic=request.topic,
            run_dir=str(run_dir),
            tutorial_json=str(tutorial_path),
            timeline_json=str(timeline_path),
            final_video=final_video,
            subtitle_file=subtitle_file,
            uploaded=uploaded,
        )

    def _create_run_directory(self, topic: str) -> Path:
        slug = self._slugify(topic)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(self.settings.app.output_dir) / f"{stamp}_{slug}"
        for folder in ["images", "diagrams", "slides", "audio", "subtitles", "final"]:
            (run_dir / folder).mkdir(parents=True, exist_ok=True)
        return run_dir

    def _generate_images(self, tutorial: TutorialPlan, output_dir: Path) -> None:
        for scene in tutorial.scenes:
            scene.image_path = self.comfyui.generate_image(scene.image_prompt, output_dir, f"scene_{scene.index:02d}")

    def _attach_diagrams(self, tutorial: TutorialPlan) -> None:
        diagram_iter = iter([diagram.output_path for diagram in tutorial.diagrams if diagram.output_path])
        for scene in tutorial.scenes:
            if scene.diagram_required:
                scene.diagram_path = next(diagram_iter, None)

    def _attach_charts(self, tutorial: TutorialPlan) -> None:
        chart_iter = iter([chart.output_path for chart in tutorial.charts if chart.output_path])
        for scene in tutorial.scenes:
            # If the scene title or content suggests a comparison/trend, we might attach a chart
            # For simplicity, we just attach them in order for now or if we add a flag later
            # Let's check if there are charts left
            if "comparison" in scene.title.lower() or "trend" in scene.title.lower() or "stats" in scene.title.lower():
                scene.chart_path = next(chart_iter, None)
        
        # If any charts left, distribute them to scenes that don't have diagrams
        for scene in tutorial.scenes:
            if scene.chart_path is None and scene.diagram_path is None:
                scene.chart_path = next(chart_iter, None)

    def _render_slides(self, tutorial: TutorialPlan, output_dir: Path) -> None:
        for scene in tutorial.scenes:
            scene.slide_path = self.slide_composer.render(scene, output_dir / f"slide_{scene.index:02d}.png")

    def _build_audio_and_timeline(self, tutorial: TutorialPlan, run_dir: Path, generate_tts: bool):
        scene_subtitles = []
        for scene in tutorial.scenes:
            if generate_tts and scene.audio_path is None:
                audio_path, actual_duration, subtitles = self.tts.synthesize(
                    scene.narration,
                    run_dir / "audio" / f"narration_{scene.index:02d}.wav",
                    tutorial.language,
                )
                scene.audio_path = audio_path
                scene.duration_seconds = max(scene.duration_seconds, round(actual_duration, 2))
                scene_subtitles.append(subtitles)
            else:
                scene_subtitles.append([])
        return self.timeline_builder.build(tutorial.scenes, scene_subtitles)

    def _slugify(self, value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return cleaned or "topic"
