from __future__ import annotations

import gradio as gr

from config.settings import load_settings
from core.models import GenerationRequest
from core.pipeline import TechExplainerPipeline
from utils.logging_utils import configure_logging

settings = load_settings()
configure_logging(settings.logging.level, settings.logging.log_file)
pipeline = TechExplainerPipeline(settings)


def run_generation(topic: str, duration: str, language: str, audience: str, style: str, images: bool, diagrams: bool, tts: bool, video: bool) -> dict:
    request = GenerationRequest(
        topic=topic,
        duration=duration,
        language=language,
        audience=audience,
        style=style,
        generate_images=images,
        generate_diagrams=diagrams,
        generate_tts=tts,
        render_video=video,
    )
    result = pipeline.run(request)
    return result.model_dump()


def launch() -> gr.Blocks:
    with gr.Blocks(title="TechExplainerAI") as demo:
        gr.Markdown("# TechExplainerAI")
        topic = gr.Textbox(label="Technology Topic", placeholder="Kubernetes")
        duration = gr.Dropdown(["3min", "5min", "10min", "1h", "2h"], value="5min", label="Duration", allow_custom_value=True)
        language = gr.Textbox(value="en", label="Language")
        audience = gr.Dropdown(["beginner", "intermediate", "advanced"], value="beginner", label="Audience")
        style = gr.Dropdown(["educational", "cinematic", "corporate", "youtube"], value="educational", label="Style")
        images = gr.Checkbox(value=True, label="Generate Images")
        diagrams = gr.Checkbox(value=True, label="Generate Diagrams")
        tts = gr.Checkbox(value=True, label="Generate Narration")
        video = gr.Checkbox(value=True, label="Render Video")
        output = gr.JSON(label="Run Result")
        submit = gr.Button("Generate")
        submit.click(run_generation, [topic, duration, language, audience, style, images, diagrams, tts, video], output)
    return demo


if __name__ == "__main__":
    launch().launch()
