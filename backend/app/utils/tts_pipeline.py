# backend/app/utils/tts_pipeline.py

import os
import uuid
import shutil
import tempfile
import torch
from TTS.api import TTS
from .sarvabhasha_processor import SarvabhashaProcessor

class TTSProcessor:
    """
    Manages local TTS synthesis using Coqui TTS or placeholders for other providers.
    """
    def __init__(self, model_path: str = None, vocoder_path: str = None, use_gpu: bool = True):
        """
        model_path: Path or name for the Coqui TTS model
        vocoder_path: If separate vocoder needed
        use_gpu: Use CUDA if available
        """
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        if model_path:
            self.tts = TTS(
                model_path=model_path,
                vocoder_path=vocoder_path,
                progress_bar=False,
                gpu=self.use_gpu
            )
        else:
            self.tts = None
            print("No local TTS model configured. You can use an external provider instead.")

        # Sarvabhasha processor is optional and initialised lazily
        self.sarva = SarvabhashaProcessor()

    def synthesize_local(self, text: str, output_path: str, speaker_idx: int = None, emotion: str = None):
        """
        Synthesize speech from text using a local Coqui TTS model,
        saving to output_path (WAV).
        speaker_idx: for multi-speaker models
        emotion: if supported
        """
        if not self.tts:
            raise ValueError("Local TTS model not loaded. Provide model_path to TTSProcessor.")

        # Example of controlling speaker, emotion, or other parameters if the model supports them
        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker=speaker_idx,
            emotion=emotion
        )

    def synthesize_external_google(self, text: str, output_path: str, voice_name: str):
        """
        Example placeholder for Google TTS or other cloud-based TTS.
        """
        # Here you'd call the google-cloud-texttospeech client,
        # then write the output to output_path.
        pass

    def synthesize_text(self, text: str, output_path: str, voice_name: str, speaker_label: str = "", emotion: str = None):
        """
        High-level interface. 
        If voice_name indicates a local Coqui voice, do local.
        If it indicates a cloud voice (like 'google_en-US-Wavenet-F'), do an external call.
        """
        # Example logic to distinguish
        if voice_name.startswith("local_coqui"):
            # parse out speaker index, etc.
            speaker_idx = 0
            self.synthesize_local(text, output_path, speaker_idx=speaker_idx, emotion=emotion)
        elif voice_name.startswith("google_"):
            self.synthesize_external_google(text, output_path, voice_name=voice_name)
        elif voice_name.startswith("sarva_"):
            lang = voice_name.replace("sarva_", "") or "en"
            self.sarva.synthesize(text, output_path, lang=lang)
        else:
            # default or error
            raise ValueError(f"Unknown voice_name pattern: {voice_name}")
        
        return output_path
