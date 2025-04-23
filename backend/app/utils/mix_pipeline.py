# backend/app/utils/mix_pipeline.py

import os
import uuid
from pydub import AudioSegment
import pyloudnorm as pyln

class MixPipeline:
    """
    A pipeline to combine the original background track and newly generated dialogue.
    Optionally apply volume normalization or other effects.
    """

    def __init__(self, target_lufs=-23.0):
        """
        target_lufs: The loudness level you want to aim for (EBU R128 recommends -23 LUFS).
        """
        self.target_lufs = target_lufs

    def load_audio(self, path: str) -> AudioSegment:
        return AudioSegment.from_file(path)

    def measure_loudness(self, audio_segment: AudioSegment) -> float:
        """
        Convert pydub's AudioSegment to a numpy array,
        measure loudness in LUFS using pyloudnorm.
        """
        samples = audio_segment.get_array_of_samples()
        audio_float = [sample / 32767.0 for sample in samples]  # 16-bit assumption
        meter = pyln.Meter(audio_segment.frame_rate)
        loudness = meter.integrated_loudness(audio_float)
        return loudness

    def normalize_lufs(self, audio_segment: AudioSegment, target_lufs: float) -> AudioSegment:
        """
        Adjust the audio segment to the target LUFS using pyloudnorm.
        """
        current_loudness = self.measure_loudness(audio_segment)
        loudness_diff = target_lufs - current_loudness
        return audio_segment.apply_gain(loudness_diff)

    def combine_tracks(
        self,
        background_path: str,
        dialogue_paths: list,
        dialogue_starts: list,
        output_path: str,
        apply_normalization: bool = True,
        background_volume_adj: float = 0.0,
        dialogue_volume_adj: float = 0.0
    ) -> str:
        """
        1) Load background track
        2) For each dialogue track, overlay it at the specified start time (in ms)
        3) Adjust volumes if needed
        4) (Optional) apply overall loudness normalization
        5) Export final wave or mp3

        background_path: the path to the original or background audio
        dialogue_paths: list of dialogue audio file paths
        dialogue_starts: list of start times in ms for each dialogue
        output_path: path for the final mix
        background_volume_adj: dB to raise/lower background track
        dialogue_volume_adj: dB to raise/lower all dialogue tracks
        """
        bg_audio = self.load_audio(background_path)
        bg_audio = bg_audio + background_volume_adj  # adjust background volume

        # Convert to a common frame rate, channels if needed
        # e.g., if your background is 2-channel (stereo) and dialogues are 1-channel
        # pydub auto-converts on overlay, but let's standardize:
        sample_rate = bg_audio.frame_rate
        channels = bg_audio.channels

        mixed_audio = bg_audio

        for dpath, start_ms in zip(dialogue_paths, dialogue_starts):
            dlg = self.load_audio(dpath).set_frame_rate(sample_rate).set_channels(channels)
            dlg = dlg + dialogue_volume_adj  # apply volume change

            # Overlay the dialogue on the background at the correct time
            mixed_audio = mixed_audio.overlay(dlg, position=start_ms)

        if apply_normalization:
            mixed_audio = self.normalize_lufs(mixed_audio, self.target_lufs)

        # Export final
        mixed_audio.export(output_path, format="wav")
        return output_path
