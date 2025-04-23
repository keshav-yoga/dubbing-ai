# backend/app/utils/asr_pipeline.py

import os
import uuid
import ffmpeg
import tempfile
import torch
import whisper
import langid

from pyannote.audio import Pipeline as PyannotePipeline
from pyannote.audio.utils.preview import AudioPreview

# For best performance with speaker diarization via pyannote, 
# you typically need a Hugging Face token and a pre-trained model checkpoint:
# e.g. "pyannote/speaker-diarization"
DIARIZATION_MODEL = "pyannote/speaker-diarization"
LANGUAGE_ID_THRESHOLD = 0.90  # Confidence threshold for language ID

class ASRPipeline:
    def __init__(self, use_gpu: bool = True):
        # Initialize Whisper (you can choose a bigger model like 'large-v2' for better accuracy)
        self.whisper_model = whisper.load_model("medium", device="cuda" if use_gpu else "cpu")
        
        # Initialize pyannote pipeline if you want local usage:
        # If you prefer a HF pipeline with an access token, do: 
        #   self.diarization_pipeline = PyannotePipeline.from_pretrained(DIARIZATION_MODEL, use_auth_token="YOUR_HF_TOKEN")
        # For brevity, we assume a local or previously downloaded model:
        try:
            self.diarization_pipeline = PyannotePipeline.from_pretrained(DIARIZATION_MODEL)
        except Exception:
            self.diarization_pipeline = None
            print("Warning: Pyannote diarization model not loaded. Please configure properly.")

    def preprocess_audio(self, input_audio_path: str, sample_rate: int = 16000):
        """
        Convert the audio to 16kHz, mono WAV for uniform ASR.
        Optionally apply noise reduction or other filters.
        """
        output_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        
        # Basic FFmpeg re-encoding
        (
            ffmpeg
            .input(input_audio_path)
            .output(
                output_path,
                format='wav',
                acodec='pcm_s16le',
                ac=1,
                ar=sample_rate
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # TODO: If you want noise reduction, you can do additional steps here
        # or use python libraries like noisereduce or sox

        return output_path

    def diarize_speakers(self, wav_path: str):
        """
        Run speaker diarization via pyannote.audio
        Returns a list of segments with (start, end, speaker_label).
        """
        if not self.diarization_pipeline:
            print("Diarization pipeline not available.")
            return []

        # pyannote requires a "file" dict with 'uri' and 'audio' keys
        diarization_result = self.diarization_pipeline({"audio": wav_path})
        segments = []
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            start = turn.start
            end = turn.end
            segments.append({
                "start": start,
                "end": end,
                "speaker": speaker
            })
        return segments

    def transcribe_segment(self, wav_path: str, segment):
        """
        Run Whisper on a portion of audio for more precise transcription
        (time-slicing to handle large files and diarized speakers).
        """
        # Extract segment from wav_path to a temp file:
        seg_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        (
            ffmpeg
            .input(wav_path, ss=segment["start"], to=segment["end"])
            .output(seg_wav, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )

        # Transcribe with Whisper
        # We use "multilingual" model if we suspect multiple languages
        result = self.whisper_model.transcribe(seg_wav, task="transcribe", language=None)
        text = result["text"]
        return text.strip()

    def language_id(self, text: str):
        """
        Identify language from text using langid or another approach.
        """
        lang, confidence = langid.classify(text)
        if confidence < LANGUAGE_ID_THRESHOLD:
            # Might be uncertain, default to e.g. "und" (undetermined)
            return "und"
        return lang

    def run_asr_pipeline(self, input_audio_path: str):
        """
        Full pipeline:
        1. Preprocess audio
        2. Diarize
        3. For each speaker segment, run Whisper
        4. Language ID
        5. Return combined results
        """
        # 1) Preprocess
        processed_wav = self.preprocess_audio(input_audio_path)

        # 2) Speaker Diarization
        speaker_segments = self.diarize_speakers(processed_wav)
        if not speaker_segments:
            # Fallback: single segment for entire audio
            audio_info = ffmpeg.probe(processed_wav)
            duration = float(audio_info["format"]["duration"])
            speaker_segments = [{"start": 0.0, "end": duration, "speaker": "Speaker1"}]

        # 3) For each segment, transcribe
        results = []
        for seg in speaker_segments:
            text = self.transcribe_segment(processed_wav, seg)
            # 4) Language ID
            lang_detected = self.language_id(text) if text else "und"
            # 5) Build result
            results.append({
                "start_time": seg["start"],
                "end_time": seg["end"],
                "speaker": seg["speaker"],
                "language_detected": lang_detected,
                "text": text
            })

        return results
