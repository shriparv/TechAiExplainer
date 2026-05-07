from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppPaths(BaseModel):
    name: str = "TechExplainerAI"
    output_dir: str = "output"
    cache_dir: str = "output/cache"
    temp_dir: str = "output/tmp"
    assets_dir: str = "output/assets"
    bg_music_dir: str = "bgmusics"


class OllamaSettings(BaseModel):
    base_url: str = "http://127.0.0.1:11434"
    model: str = "llama3.2"
    timeout_seconds: int = 300


class ComfyUISettings(BaseModel):
    base_url: str = "http://127.0.0.1:8188"
    workflow_path: str = "config/comfyui_sdxl_workflow.json"
    poll_interval_seconds: int = 2


class DiagramSettings(BaseModel):
    mermaid_cli: str = "mmdc"
    graphviz_dot: str = "dot"


class TTSSettings(BaseModel):
    piper_executable: str = "piper"
    model_path: str = "models/piper/en_US-lessac-medium.onnx"
    config_path: str = "models/piper/en_US-lessac-medium.onnx.json"
    voice_models: dict[str, dict[str, str]] = Field(default_factory=dict)


class VideoSettings(BaseModel):
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    fps: int = 30
    width: int = 1920
    height: int = 1080
    audio_sample_rate: int = 22050
    encoder: str = "h264_nvenc"
    preset: str = "p4"
    bg_music_volume: float = 0.1


class ApiSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000


class LoggingSettings(BaseModel):
    level: str = "INFO"
    log_file: str = "output/techexplainer.log"


class YouTubeSettings(BaseModel):
    enabled: bool = False


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TECHEXPLAINER_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppPaths = Field(default_factory=AppPaths)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    comfyui: ComfyUISettings = Field(default_factory=ComfyUISettings)
    diagram: DiagramSettings = Field(default_factory=DiagramSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)


def _read_yaml(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    return yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}


def load_settings(config_path: str = "config/default.yaml", output_dir: str | None = None) -> AppSettings:
    payload = _read_yaml(config_path)
    settings = AppSettings(**payload)
    if output_dir:
        settings.app.output_dir = output_dir
    for directory in [
        settings.app.output_dir,
        settings.app.cache_dir,
        settings.app.temp_dir,
        settings.app.assets_dir,
    ]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    Path(settings.logging.log_file).parent.mkdir(parents=True, exist_ok=True)
    return settings
