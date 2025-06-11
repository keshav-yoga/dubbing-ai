# backend/app/utils/final_output_pipeline.py␊
␊
import os␊
import subprocess␊
import uuid␊
from typing import List, Optional␊
import srt␊
from datetime import timedelta␊
␊
class FinalOutputPipeline:␊
    """␊
    Handles:␊
    1) Replacing or adding the final audio track in the original video.␊
    2) Generating SRT or VTT files for subtitles if needed.␊
    """␊
␊
    def mux_audio_video(self, original_video_path: str, new_audio_path: str, output_path: str) -> str:␊
        """␊
        Use FFmpeg to mux the new audio track with the original video track. ␊
        We'll discard the old audio or you can keep it as a second audio track.␊
        """␊
        # Example: Discard original audio, replace with new␊
        cmd = [␊
            "ffmpeg",␊
            "-y",␊
            "-i", original_video_path,␊
            "-i", new_audio_path,␊
            "-c:v", "copy",  # copy the video without re-encoding␊
            "-map", "0:v:0",␊
            "-map", "1:a:0",␊
            output_path␊
        ]␊
        subprocess.run(cmd, check=True)␊
        return output_path␊
␊
    def create_subtitle_file(␊
        self,␊
        segments: List[dict],␊
        subtitle_path: str,␊
        fmt: str = "srt"␊
    ) -> str:␊
        """␊
        Creates a subtitle file (SRT/VTT) from a list of segments:␊
        segments = [␊
          {␊
            "start_time": 1.25,  # in seconds␊
            "end_time": 4.10,    ␊
            "text": "Hello world"␊
          },␊
          ...␊
        ]␊
        """␊
        # We can use 'srt' library for building srt subtitles easily␊
        subs = []␊
        for idx, seg in enumerate(segments, start=1):␊
            start_s = seg["start_time"]␊
            end_s = seg["end_time"]␊
            start_td = timedelta(seconds=start_s)␊
            end_td = timedelta(seconds=end_s)␊
            subs.append(␊
                srt.Subtitle(index=idx, start=start_td, end=end_td, content=seg["text"])␊
            )␊
␊
        subs_str = srt.compose(subs)␊
        with open(subtitle_path, "w", encoding="utf-8") as f:␊
            f.write(subs_str)␊
␊
        return subtitle_path␊
