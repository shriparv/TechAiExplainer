from __future__ import annotations

import argparse
import json
from pathlib import Path

from config.settings import AppSettings, load_settings
from core.models import GenerationRequest
from core.pipeline import TechExplainerPipeline
from utils.logging_utils import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate local AI explainer videos.")
    parser.add_argument("--topic", required=True, help="Technology topic to explain.")
    parser.add_argument("--duration", default="5min", help="Duration of the video (e.g., 3m, 10min, 1h).")
    parser.add_argument("--language", default="en", help="Narration language code.")
    parser.add_argument("--audience", default="beginner", choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--style", default="educational", choices=["educational", "cinematic", "corporate", "youtube"])
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config.")
    parser.add_argument("--output-dir", help="Override output directory.")
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument("--skip-diagrams", action="store_true")
    parser.add_argument("--skip-tts", action="store_true")
    parser.add_argument("--skip-video", action="store_true")
    parser.add_argument("--youtube", action="store_true", help="Enable optional upload stage.")
    return parser


def build_request(args: argparse.Namespace) -> GenerationRequest:
    duration = args.duration.lower().strip()
    # Normalize formats like 3m, 1h to 3min, 60min for consistent LLM understanding
    if "min" in duration or "minute" in duration:
        pass # Already standard
    elif "m" in duration:
        duration = duration.replace("m", "min")
    elif "h" in duration:
        duration = duration.replace("h", "hour")
    
    return GenerationRequest(
        topic=args.topic,
        duration=duration,
        language=args.language,
        audience=args.audience,
        style=args.style,
        generate_images=not args.skip_images,
        generate_diagrams=not args.skip_diagrams,
        generate_tts=not args.skip_tts,
        render_video=not args.skip_video,
        upload_youtube=args.youtube,
    )


def main() -> int:
    args = build_parser().parse_args()
    settings: AppSettings = load_settings(args.config, args.output_dir)
    configure_logging(settings.logging.level, settings.logging.log_file)

    pipeline = TechExplainerPipeline(settings)
    result = pipeline.run(build_request(args))
    Path(result.run_dir, "result.json").write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")
    print(json.dumps(result.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
