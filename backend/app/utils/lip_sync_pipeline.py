# backend/app/utils/lip_sync_pipeline.py

import os
import subprocess
import uuid
import tempfile
import ffmpeg
from typing import Dict, Any

class LipSyncPipeline:
    """
    A pipeline that:
    1) Runs forced alignment (using Montreal Forced Aligner or similar).
    2) Time-stretches or pitch-shifts the audio to match on-screen timing.
    """

    def __init__(self, mfa_command: str = "mfa", acoustic_model_path: str = None, dictionary_path: str = None):
        """
        mfa_command: the CLI command or path for Montreal Forced Aligner, e.g. 'mfa'
        acoustic_model_path: path to acoustic model (English, etc.)
        dictionary_path: path to the pronunciation dictionary
        """
        self.mfa_command = mfa_command
        self.acoustic_model_path = acoustic_model_path
        self.dictionary_path = dictionary_path

    def run_forced_alignment(self, wav_path: str, transcript: str, speaker_name: str = "default") -> Dict[str, Any]:
        """
        1) Write a temporary text file with the transcript.
        2) Call MFA to produce alignment data (CTM, TextGrid, etc.).
        3) Parse the alignment result to get phoneme start/end times.

        Returns a dictionary with alignment info, e.g.
        {
          "phonemes": [
            {"symbol": "HH", "start": 0.2, "end": 0.35},
            ...
          ],
          "words": [
            {"text": "Hello", "start": 0.2, "end": 0.5},
            ...
          ]
        }
        """
        # Step 1: create temp folder
        tmp_dir = tempfile.mkdtemp(prefix="mfa_")
        audio_dir = os.path.join(tmp_dir, "audio")
        text_dir = os.path.join(tmp_dir, "text")
        output_dir = os.path.join(tmp_dir, "output")

        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Copy audio to the folder
        base_name = f"{speaker_name}_{uuid.uuid4()}"
        audio_filename = f"{base_name}.wav"
        transcript_filename = f"{base_name}.txt"

        local_audio_path = os.path.join(audio_dir, audio_filename)
        with open(wav_path, "rb") as src, open(local_audio_path, "wb") as dst:
            dst.write(src.read())

        # Write transcript
        local_text_path = os.path.join(text_dir, transcript_filename)
        with open(local_text_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        # Step 2: call MFA
        # Example command:
        # mfa align /tmp/audio /tmp/text <dictionary> <acoustic_model> /tmp/output
        # Real usage: check the MFA version and arguments
        align_cmd = [
            self.mfa_command,
            "align",
            audio_dir,
            text_dir,
            self.dictionary_path,
            self.acoustic_model_path,
            output_dir,
            "--clean"
        ]

        try:
            subprocess.run(align_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print("MFA error output:", e.stderr.decode("utf-8"))
            raise RuntimeError("Montreal Forced Aligner failed.")

        # Step 3: parse alignment data
        # MFA typically produces TextGrid files in the output directory, e.g. "speaker.TextGrid"
        # We'll parse them to extract phoneme or word-level timings
        textgrid_path = os.path.join(output_dir, f"{speaker_name}_{base_name}.TextGrid")
        # Note: actual filename may differ depending on MFA version.
        # You may need to list the directory or parse known name patterns.

        if not os.path.isfile(textgrid_path):
            # fallback: try a different naming
            # or read the first .TextGrid found
            grids = [f for f in os.listdir(output_dir) if f.endswith(".TextGrid")]
            if grids:
                textgrid_path = os.path.join(output_dir, grids[0])
            else:
                raise FileNotFoundError("No TextGrid file found in MFA output.")

        alignment_data = self.parse_textgrid(textgrid_path)
        return alignment_data

    def parse_textgrid(self, textgrid_file: str) -> Dict[str, Any]:
        """
        Parse the TextGrid to extract phoneme and word alignments.
        This is a simplistic approach.
        For robust usage, see python packages like textgrid or Praat-parsing libraries.
        """
        # For brevity, let's illustrate a dummy parser or a library usage:
        try:
            import textgrid
        except ImportError:
            raise ImportError("Please install python-textgrid for parsing MFA outputs (pip install textgrid).")

        tg = textgrid.TextGrid.fromFile(textgrid_file)

        # MFA often stores intervals in tiers named "words" and "phones"
        words, phonemes = [], []
        for tier in tg.tiers:
            if tier.name.lower() in ["words", "word"]:
                for interval in tier.intervals:
                    if interval.mark.strip():
                        words.append({
                            "text": interval.mark.strip(),
                            "start": interval.minTime,
                            "end": interval.maxTime
                        })
            elif tier.name.lower() in ["phones", "phonemes"]:
                for interval in tier.intervals:
                    if interval.mark.strip():
                        phonemes.append({
                            "symbol": interval.mark.strip(),
                            "start": interval.minTime,
                            "end": interval.maxTime
                        })

        return {
            "words": words,
            "phonemes": phonemes
        }

    def time_stretch_audio(self, input_wav: str, output_wav: str, factor: float):
        """
        Time-stretch audio by a given factor using FFmpeg or RubberBand.
        factor < 1.0 => speed up
        factor > 1.0 => slow down
        """
        # FFmpeg approach (at the risk of pitch shifting):
        # If you use the atempo filter, you can only do up to 2x. For more complex, chain multiple atempos or use rubberband.
        # Another approach: sox, rubberband CLI, etc.
        # For demonstration, let's do a simple approach with ffmpeg:

        # If factor < 0.5 or > 2.0, you might chain multiple steps or use more advanced approach
        cmd = (
            ffmpeg
            .input(input_wav)
            .filter_("atempo", factor)
            .output(output_wav, format='wav')
            .overwrite_output()
        )
        cmd.run(quiet=True)

    def align_and_stretch(self, wav_path: str, transcript: str, desired_duration: float) -> str:
        """
        1) Force-align with MFA to get actual speech duration from phonemes.
        2) Compare the actual speech length to 'desired_duration' (from the video).
        3) If there's mismatch, time-stretch the audio slightly.
        4) Return the path to the new aligned WAV file.
        """
        alignment_data = self.run_forced_alignment(wav_path, transcript)
        # Determine actual speech length from phonemes or words
        if alignment_data["phonemes"]:
            actual_end = alignment_data["phonemes"][-1]["end"]
        elif alignment_data["words"]:
            actual_end = alignment_data["words"][-1]["end"]
        else:
            # No alignment data means we can't do much
            actual_end = 0.0

        if actual_end == 0.0:
            # fallback, no alignment
            return wav_path

        factor = desired_duration / actual_end

        # If factor is close to 1.0, no need to do anything
        if abs(factor - 1.0) < 0.05:
            return wav_path

        # Build new path
        aligned_wav = wav_path.replace(".wav", "_aligned.wav")
        self.time_stretch_audio(wav_path, aligned_wav, factor)
        return aligned_wav
