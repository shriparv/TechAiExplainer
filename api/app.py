from __future__ import annotations

from fastapi import FastAPI, HTTPException

from config.settings import load_settings
from core.models import GenerationRequest, GenerationResult
from core.pipeline import TechExplainerPipeline
from utils.logging_utils import configure_logging

settings = load_settings()
configure_logging(settings.logging.level, settings.logging.log_file)
pipeline = TechExplainerPipeline(settings)

app = FastAPI(title="TechExplainerAI", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate", response_model=GenerationResult)
def generate(request: GenerationRequest) -> GenerationResult:
    try:
        return pipeline.run(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
