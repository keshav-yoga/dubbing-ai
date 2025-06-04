# SPDX-License-Identifier: MIT
"""HiFi‑GAN universal vocoder wrapper."""
import torch
from hifi_gan import Generator
from pathlib import Path
import requests

_URL = "https://github.com/jik876/hifi-gan/releases/download/v1/universal_hifigan_24k.pth"
CHECKPOINT = Path.home()/".sarvabhasha_models"/"hifigan_24k.pth"

if not CHECKPOINT.exists():
    CHECKPOINT.parent.mkdir(exist_ok=True)
    with requests.get(_URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(CHECKPOINT, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

class HiFiGANVocoder:
    def __init__(self, device="cpu"):
        self.device = device
        self.model = Generator().to(device)
        state = torch.load(CHECKPOINT, map_location=device)
        self.model.load_state_dict(state)
        self.model.remove_weight_norm()
        self.model.eval()
    @torch.no_grad()
    def __call__(self, mel):
        return self.model(mel).cpu().numpy()
