# SPDX-License-Identifier: MIT
"""FastAPI inference server."""
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import uvicorn, tempfile, wave, json, asyncio

from sarvabhasha_tts import config
from importlib import import_module

app = FastAPI(title="Sarvabhasha TTS")

# Dynamically load pipeline instances
_instances = {}
def _get(name, *args):
    if name not in _instances:
        module_path, cls_name = config.PIPELINES[name].split(":")
        cls = getattr(import_module(module_path), cls_name)
        _instances[name] = cls(*args)
    return _instances[name]

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

@app.post("/synth")
async def synthesise(req: TTSRequest, speaker: UploadFile = File(None)):
    # 1. Lang ID (if lang="auto")
    lang = req.lang if req.lang != "auto" else _get("langid")([req.text])

    # 2. Tokenise, normalise, transliterate
    toks = _get("tokenizer", lang)(req.text)
    toks_norm = _get("normalizer", lang)(toks)
    text_norm = _get("transliterate", lang)(" ".join(toks_norm))

    # 3. G2P
    phonemes = _get("g2p", lang)(text_norm.split())

    # 4. Prosody
    spk_emb = None
    if speaker is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await speaker.read())
            tmp.flush()
            spk_emb = _get("speaker_embed")(
                tmp.name
            )

    style = None
    if spk_emb is not None:
        style = spk_emb  # placeholder, could be prosody vector

    # 5. Acoustic
    wav = _get("acoustic", model_path=None, device=config.PYTORCH_DEVICE)(
        phonemes, style, lang
    )

    # 6. Return WAV bytes
    return wav

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
