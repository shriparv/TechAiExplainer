from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


DurationLiteral = str
AudienceLiteral = Literal["beginner", "intermediate", "advanced"]
StyleLiteral = Literal["educational", "cinematic", "corporate", "youtube"]


class DiagramSpec(BaseModel):
    title: str
    diagram_type: Literal["mermaid", "graphviz"]
    source: str
    output_path: str | None = None


class ChartSpec(BaseModel):
    title: str
    chart_type: Literal["line", "bar", "pie"]
    labels: list[str]
    values: list[float]
    x_label: str | None = None
    y_label: str | None = None
    output_path: str | None = None


class SlideScene(BaseModel):
    index: int
    title: str
    bullet_points: list[str]
    narration: str
    image_prompt: str
    duration_seconds: float
    diagram_required: bool = False
    diagram_caption: str | None = None
    image_path: str | None = None
    diagram_path: str | None = None
    chart_path: str | None = None
    slide_path: str | None = None
    audio_path: str | None = None


class TopicUnderstanding(BaseModel):
    introduction: str
    architecture: str
    workflow: str
    pros: list[str]
    cons: list[str]
    use_cases: list[str]
    related_technologies: list[str]
    learning_roadmap: list[str]


class TutorialPlan(BaseModel):
    topic: str
    language: str
    audience: AudienceLiteral
    style: StyleLiteral
    duration: DurationLiteral
    introduction_hook: str
    architecture_explanation: str
    workflow_explanation: str
    real_life_use_cases: list[str]
    pros_and_cons: dict[str, list[str]]
    related_technologies: list[str]
    learning_roadmap: list[str]
    scenes: list[SlideScene]
    diagrams: list[DiagramSpec]
    charts: list[ChartSpec] = Field(default_factory=list)
    intro_cta: str
    outro_cta: str


class SubtitleSegment(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    text: str


class TimelineScene(BaseModel):
    scene_index: int
    start_seconds: float
    end_seconds: float
    narration_path: str | None = None
    slide_path: str | None = None
    subtitle_indices: list[int] = Field(default_factory=list)


class TimelinePlan(BaseModel):
    total_duration_seconds: float
    scenes: list[TimelineScene]
    subtitles: list[SubtitleSegment]


class GenerationRequest(BaseModel):
    topic: str
    duration: DurationLiteral = "5min"
    language: str = "en"
    audience: AudienceLiteral = "beginner"
    style: StyleLiteral = "educational"
    generate_images: bool = True
    generate_diagrams: bool = True
    generate_tts: bool = True
    render_video: bool = True
    upload_youtube: bool = False

    @model_validator(mode="after")
    def validate_topic(self) -> "GenerationRequest":
        if not self.topic.strip():
            raise ValueError("Topic must not be empty.")
        return self


class GenerationResult(BaseModel):
    topic: str
    run_dir: str
    tutorial_json: str
    timeline_json: str
    final_video: str | None = None
    subtitle_file: str | None = None
    uploaded: bool = False

    @property
    def run_path(self) -> Path:
        return Path(self.run_dir)
