from core.models import SlideScene, SubtitleSegment
from render.timeline import TimelineBuilder


def test_timeline_builder_offsets_subtitles() -> None:
    scenes = [
        SlideScene(
            index=1,
            title="Intro",
            bullet_points=["a"],
            narration="hello world",
            image_prompt="intro",
            duration_seconds=10,
        ),
        SlideScene(
            index=2,
            title="Next",
            bullet_points=["b"],
            narration="next scene",
            image_prompt="next",
            duration_seconds=8,
        ),
    ]
    subtitles = [
        [SubtitleSegment(index=0, start_seconds=0, end_seconds=5, text="hello world")],
        [SubtitleSegment(index=0, start_seconds=0, end_seconds=4, text="next scene")],
    ]
    timeline = TimelineBuilder().build(scenes, subtitles)
    assert timeline.total_duration_seconds == 18
    assert timeline.subtitles[1].start_seconds == 10
