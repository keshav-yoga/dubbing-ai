# SPDX-License-Identifier: Apache-2.0
"""XTTS v3 synthesiser."""
from xtts.api import TTS

class XttsSynthesiser:
    def __init__(self, model_path=None, device="cpu"):
        self.tts = TTS(model_path=model_path, gpu=device.startswith("cuda"))
    def __call__(self, phonemes, speaker_wav=None, lang="en", **kwargs):
        return self.tts.tts_from_phonemes(phonemes, speaker_wav, lang=lang, **kwargs)
