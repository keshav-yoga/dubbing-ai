# backend/app/utils/tts_pipeline.py␊
␊
"""TTS processing pipeline using the Sarvabhasha TTS engine."""␊
␊
from importlib import import_module␊
from typing import Optional␊
␊
import soundfile as sf␊
␊
from app.sarvabhasha_tts import config␊
␊
␊
class TTSProcessor:␊
    """Generate speech audio using the Sarvabhasha TTS pipeline."""␊
␊
    def __init__(self, device: Optional[str] = None):␊
        self.device = device or config.PYTORCH_DEVICE␊
        self._instances = {}␊
␊
    def _get(self, name: str, *args):␊
        if name not in self._instances:␊
            module_path, cls_name = config.PIPELINES[name].split(":")␊
            cls = getattr(import_module(module_path), cls_name)␊
            if name in {"acoustic", "speaker_embed", "prosody", "vocoder"}:␊
                self._instances[name] = cls(device=self.device, *args)␊
            else:␊
                self._instances[name] = cls(*args)␊
        return self._instances[name]␊
␊
    def synthesize_text(␊
        self,␊
        text: str,␊
        output_path: str,␊
        lang: str = "en",␊
        speaker_wav: Optional[str] = None,␊
    ) -> str:␊
        """Synthesize ``text`` into ``output_path`` using XTTS."""␊
␊
        if lang == "auto":␊
            lang = self._get("langid")(text)␊
␊
        tokens = self._get("tokenizer", lang)(text)␊
        tokens = self._get("normalizer", lang)(tokens)␊
        text_norm = self._get("transliterate", lang)(" ".join(tokens))␊
        phonemes = self._get("g2p", lang)(text_norm.split())␊
␊
        style = None␊
        if speaker_wav:␊
            style = self._get("speaker_embed")(speaker_wav)␊
␊
        wav = self._get("acoustic", model_path=None, device=self.device)(␊
            phonemes, style, lang␊
        )␊
␊
        sf.write(output_path, wav, 24000)␊
        return output_path␊
