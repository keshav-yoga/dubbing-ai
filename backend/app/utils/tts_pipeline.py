# backend/app/utils/tts_pipeline.py
"""Utility for synthesising speech using Sarvabhasha TTS."""

from importlib import import_module
from pathlib import Path
import soundfile as sf
import torch
from sarvabhasha_tts import config


class TTSProcessor:
    """Simple wrapper around Sarvabhasha TTS pipeline."""

    def __init__(self, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._instances: dict[str, object] = {}

    def _get(self, name: str, *args):
        if name not in self._instances:
            module_path, cls_name = config.PIPELINES[name].split(":")
            cls = getattr(import_module(module_path), cls_name)
            self._instances[name] = cls(*args)
        return self._instances[name]

    def synthesize(self, text: str, output_path: str, lang: str = "en", speaker_wav: str | None = None) -> str:
        """Synthesize ``text`` and save to ``output_path``."""
        lang = lang if lang != "auto" else self._get("langid")(text)
        toks = self._get("tokenizer", lang)(text)
        toks_norm = self._get("normalizer", lang)(toks)
        text_norm = self._get("transliterate", lang)(" ".join(toks_norm))
        phonemes = self._get("g2p", lang)(text_norm.split())

        style = None
        if speaker_wav:
            style = self._get("speaker_embed")(speaker_wav)

        wav = self._get("acoustic", model_path=None, device=self.device)(phonemes, style, lang)
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()

        sf.write(output_path, wav, 24000)
        return output_path

    # Backwards compatibility ----------------------------------------------
    def synthesize_text(self, text: str, output_path: str, voice_name: str = "sarvabhasha", speaker_label: str = "", emotion: str | None = None) -> str:
        return self.synthesize(text, output_path, lang="en")
