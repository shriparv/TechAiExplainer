from __future__ import annotations

import logging
import wave
from pathlib import Path

from core.models import SubtitleSegment
from utils.command import CommandRunner


class PiperTTSEngine:
    def __init__(
        self,
        executable: str,
        model_path: str,
        config_path: str,
        voice_models: dict[str, dict[str, str]],
        runner: CommandRunner,
    ) -> None:
        self.executable = executable
        self.model_path = model_path
        self.config_path = config_path
        self.voice_models = voice_models
        self.runner = runner
        self.logger = logging.getLogger(self.__class__.__name__)

    def synthesize(self, text: str, output_path: Path, language: str = "en") -> tuple[str, float, list[SubtitleSegment]]:
        self.logger.info("Synthesizing audio (lang=%s): %s...", language, text[:50])
        self.runner.ensure_command(self.executable)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        model_path, config_path = self._resolve_voice(language)
        self.runner.run(
            [
                self.executable,
                "--model",
                model_path,
                "--config",
                config_path,
                "--output_file",
                str(output_path),
            ],
            input_text=text,
        )
        duration = self._wav_duration(output_path)
        subtitles = self._segments_from_text(text, duration)
        return str(output_path), duration, subtitles

    def _wav_duration(self, path: Path) -> float:
        with wave.open(str(path), "rb") as wav:
            return wav.getnframes() / float(wav.getframerate())

    def _segments_from_text(self, text: str, duration: float) -> list[SubtitleSegment]:
        words = text.split()
        if not words:
            return []
        chunk_size = 8
        chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        per_chunk = duration / len(chunks)
        return [
            SubtitleSegment(
                index=index,
                start_seconds=round(index * per_chunk, 2),
                end_seconds=round((index + 1) * per_chunk, 2),
                text=chunk,
            )
            for index, chunk in enumerate(chunks)
        ]

    def _resolve_voice(self, language: str) -> tuple[str, str]:
        entry = self.voice_models.get(language) or self.voice_models.get(language.split("-")[0])
        if entry:
            return entry["model_path"], entry["config_path"]
        return self.model_path, self.config_path
