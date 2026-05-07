from __future__ import annotations

import logging
import random
from pathlib import Path

from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips, CompositeAudioClip
import moviepy.video.fx as vfx
from moviepy.audio.fx import volumex

from config.settings import VideoSettings
from core.models import TimelinePlan
from render.subtitles import write_ass
from utils.command import CommandRunner


class VideoRenderer:
    def __init__(self, settings: VideoSettings, runner: CommandRunner, bg_music_dir: str | None = None) -> None:
        self.settings = settings
        self.runner = runner
        self.bg_music_dir = Path(bg_music_dir) if bg_music_dir else None
        self.logger = logging.getLogger(self.__class__.__name__)

    def render(self, timeline: TimelinePlan, output_dir: Path, slug: str) -> tuple[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_video = output_dir / f"{slug}_timeline.mp4"
        final_video = output_dir / f"{slug}.mp4"
        subtitle_path = output_dir / f"{slug}.ass"
        write_ass(subtitle_path, timeline.subtitles)

        self.logger.info("Preparing %d video clips for concatenation...", len(timeline.scenes))
        clips = []
        for scene in timeline.scenes:
            if scene.slide_path is None or scene.narration_path is None:
                self.logger.warning("Skipping scene %d: missing slide or narration path", scene.scene_index)
                continue
            duration = scene.end_seconds - scene.start_seconds
            image_clip = ImageClip(scene.slide_path).with_duration(duration)
            
            # --- ANIMATION: Subtle Zoom (Ken Burns Effect) ---
            # Increase scale from 1.0 to 1.1 over the duration
            image_clip = image_clip.transform(lambda get_frame, t: vfx.resize(get_frame(t), 1.0 + 0.1 * (t / duration)))
            
            audio_clip = AudioFileClip(scene.narration_path)
            image_clip = image_clip.with_audio(audio_clip)
            clips.append(image_clip)

        if not clips:
            raise RuntimeError("No clips were available for video rendering.")

        self.logger.info("Concatenating clips and writing temporary video file: %s", temp_video)
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # --- BACKGROUND MUSIC ---
        if self.bg_music_dir and self.bg_music_dir.exists():
            music_files = list(self.bg_music_dir.glob("*.mp3")) + list(self.bg_music_dir.glob("*.wav"))
            if music_files:
                music_path = random.choice(music_files)
                self.logger.info("Adding background music: %s", music_path.name)
                bg_music = AudioFileClip(str(music_path))
                
                # Loop and trim to match video duration
                bg_music = bg_music.fx(vfx.loop, duration=final_clip.duration)
                bg_music = bg_music.fx(volumex, self.settings.bg_music_volume)
                
                # Mix with existing narration
                new_audio = CompositeAudioClip([final_clip.audio, bg_music])
                final_clip = final_clip.with_audio(new_audio)

        final_clip = CompositeVideoClip([final_clip], size=(self.settings.width, self.settings.height))
        final_clip.write_videofile(
            str(temp_video),
            fps=self.settings.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(output_dir / f"{slug}_audio.m4a"),
            remove_temp=True,
            logger="bar",
        )

        self.logger.info("Burning in subtitles using FFmpeg...")
        self.runner.ensure_command(self.settings.ffmpeg_path)
        subtitle_filter = self._subtitle_filter_path(subtitle_path)
        try:
            self.runner.run(
                [
                    self.settings.ffmpeg_path,
                    "-y",
                    "-i",
                    str(temp_video),
                    "-vf",
                    f"subtitles=filename={subtitle_filter}",
                    "-c:v",
                    self.settings.encoder,
                    "-preset",
                    self.settings.preset,
                    "-rc:v",
                    "vbr",
                    "-cq:v",
                    "22",
                    "-b:v",
                    "8M",
                    "-c:a",
                    "aac",
                    str(final_video),
                ]
            )
        finally:
            # Clean up clips to avoid ResourceWarnings
            final_clip.close()
            for clip in clips:
                clip.close()
                if clip.audio:
                    clip.audio.close()
                    
        return str(final_video), str(subtitle_path)

    def _subtitle_filter_path(self, path: Path) -> str:
        try:
            # Try to use relative path to avoid drive letter colon issues on Windows
            # FFmpeg's subtitles filter is notoriously difficult with Windows absolute paths
            value = path.resolve().relative_to(Path.cwd()).as_posix()
        except ValueError:
            # Fallback to absolute posix path if not under CWD
            value = path.resolve().as_posix()

        # FFmpeg filter escaping rules:
        # 1. The filter argument itself uses ':' as a separator
        # 2. Backslashes and single quotes need escaping
        # 3. Wrapping in single quotes helps with spaces and special characters
        
        # Escape colons for the filter parser (especially important for absolute paths)
        value = value.replace(":", "\\:")
        # Escape single quotes: ' -> '\'' (for FFmpeg filter parser)
        value = value.replace("'", "'\\''")
        
        return f"'{value}'"
