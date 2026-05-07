import logging
from core.models import SlideScene, SubtitleSegment, TimelinePlan, TimelineScene


class TimelineBuilder:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def build(self, scenes: list[SlideScene], scene_subtitles: list[list[SubtitleSegment]]) -> TimelinePlan:
        self.logger.info("Building timeline for %d scenes", len(scenes))
        timeline_scenes: list[TimelineScene] = []
        subtitles: list[SubtitleSegment] = []
        current_time = 0.0
        subtitle_index = 0

        for scene, subtitle_group in zip(scenes, scene_subtitles):
            start = round(current_time, 2)
            end = round(start + scene.duration_seconds, 2)
            indices: list[int] = []
            for segment in subtitle_group:
                shifted = SubtitleSegment(
                    index=subtitle_index,
                    start_seconds=round(start + segment.start_seconds, 2),
                    end_seconds=round(min(end, start + segment.end_seconds), 2),
                    text=segment.text,
                )
                subtitles.append(shifted)
                indices.append(subtitle_index)
                subtitle_index += 1

            timeline_scenes.append(
                TimelineScene(
                    scene_index=scene.index,
                    start_seconds=start,
                    end_seconds=end,
                    narration_path=scene.audio_path,
                    slide_path=scene.slide_path,
                    subtitle_indices=indices,
                )
            )
            current_time = end

        return TimelinePlan(total_duration_seconds=round(current_time, 2), scenes=timeline_scenes, subtitles=subtitles)
