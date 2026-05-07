from __future__ import annotations

from pathlib import Path

from core.models import SubtitleSegment


def format_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_time(seconds: float) -> str:
    millis = int(round(seconds * 100)) # ASS uses centiseconds
    hours, remainder = divmod(millis, 360000)
    minutes, remainder = divmod(remainder, 6000)
    secs, centis = divmod(remainder, 100)
    return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centis:02d}"


def write_ass(path: Path, subtitles: list[SubtitleSegment]) -> str:
    """Writes subtitles in Advanced Substation Alpha (.ass) format for rich styling."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,54,&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,2,2,100,100,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    events = []
    for segment in subtitles:
        start = format_ass_time(segment.start_seconds)
        end = format_ass_time(segment.end_seconds)
        # Add a subtle "pop" animation to the text
        text = f"{{\\fade(100,100)\\fscx105\\fscy105\\t(0,100,\\fscx100\\fscy100)}}{segment.text}"
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    
    content = header + "\n".join(events)
    path.write_text(content, encoding="utf-8")
    return str(path)
