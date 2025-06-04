# SPDX-License-Identifier: MIT
"""FastText language identification."""
from pathlib import Path
import fasttext
from functools import lru_cache
from sarvabhasha_tts.config import MODELS

MODEL_PATH = MODELS / "lid.176.bin"

@lru_cache
def _model():
    if not MODEL_PATH.exists():
        # download once from fastText if absent
        import urllib.request, gzip, shutil, os
        url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        urllib.request.urlretrieve(url, MODEL_PATH)
    return fasttext.load_model(str(MODEL_PATH))

class FastTextLangID:
    def __call__(self, text: str) -> str:
        model = _model()
        return model.predict(text.replace("\n", " "), k=1)[0][0].replace("__label__", "")
