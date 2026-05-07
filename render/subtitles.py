from __future__ import annotations

from pathlib import Path

from core.models import SubtitleSegment


def format_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(path: Path, subtitles: list[SubtitleSegment]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[str] = []
    for segment in subtitles:
        parts.append(str(segment.index + 1))
        parts.append(f"{format_srt_time(segment.start_seconds)} --> {format_srt_time(segment.end_seconds)}")
        parts.append(segment.text)
        parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")
    return str(path)
