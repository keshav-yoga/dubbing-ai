# SPDX-License-Identifier: MIT
"""Global configuration and registry."""
from pathlib import Path
import torch

MODELS = Path.home() / ".sarvabhasha_models"
MODELS.mkdir(exist_ok=True)

PYTORCH_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LANG_FALLBACK = "en"

# Registry of pipeline classes (import paths)
PIPELINES = {
    "langid": "sarvabhasha_tts.preprocess.langid:FastTextLangID",
    "tokenizer": "sarvabhasha_tts.preprocess.tokenize:NltkIndicTokenizer",
    "normalizer": "sarvabhasha_tts.preprocess.normalize:NumNormalizer",
    "transliterate": "sarvabhasha_tts.preprocess.transliterate:Transliterator",
    "g2p": "sarvabhasha_tts.phonemize.g2p_router:G2PRouter",
    "prosody": "sarvabhasha_tts.acoustic.styletts2_backend:StyleEncoder",
    "acoustic": "sarvabhasha_tts.acoustic.xtts_backend:XttsSynthesiser",
    "vocoder": "sarvabhasha_tts.vocoder.hifigan:HiFiGANVocoder",
    "speaker_embed": "sarvabhasha_tts.cloning.speaker_embed:SpeakerEncoder"
}
