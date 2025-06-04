"""Wrapper around the Sarvabhasha TTS pipeline."""
from importlib import import_module
from typing import Optional

from app.third_party import sarvabhasha_tts as st
import sys

# Expose the third-party package under its original name for absolute imports
sys.modules.setdefault("sarvabhasha_tts", st)
from app.third_party.sarvabhasha_tts import config


class SarvabhashaProcessor:
    """Provide a simple interface to the Sarvabhasha pipelines."""

    def __init__(self):
        self._instances = {}

    def _get(self, name, *args):
        if name not in self._instances:
            module_path, cls_name = config.PIPELINES[name].split(":")
            cls = getattr(import_module(module_path), cls_name)
            self._instances[name] = cls(*args)
        return self._instances[name]

    def synthesize(self, text: str, output_path: str, lang: str = "en", speaker_wav: Optional[str] = None):
        """Synthesize ``text`` to ``output_path`` using Sarvabhasha."""
        lang = lang if lang != "auto" else self._get("langid")([text])

        toks = self._get("tokenizer", lang)(text)
        toks_norm = self._get("normalizer", lang)(toks)
        text_norm = self._get("transliterate", lang)(" ".join(toks_norm))

        phonemes = self._get("g2p", lang)(text_norm.split())

        spk_emb = None
        if speaker_wav is not None:
            spk_emb = self._get("speaker_embed")(speaker_wav)
        style = spk_emb if spk_emb is not None else None

        wav = self._get("acoustic", model_path=None, device=config.PYTORCH_DEVICE)(phonemes, style, lang)

        import soundfile as sf
        sf.write(output_path, wav, 24000)
        return output_path
