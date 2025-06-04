# SPDX-License-Identifier: MIT
"""Prosody & style encoder – StyleTTS2 inference wrapper."""
from styletts2.inference import load_encoder, generate_style

class StyleEncoder:
    def __init__(self, device="cpu"):
        self.device = device
        self.encoder = load_encoder(device=device)
    def __call__(self, wav_path):
        return generate_style(self.encoder, wav_path, device=self.device)
