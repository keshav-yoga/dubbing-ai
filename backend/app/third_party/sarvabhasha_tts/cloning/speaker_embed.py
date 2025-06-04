# SPDX-License-Identifier: Apache-2.0
"""ECAPA‑TDNN speaker encoder via SpeechBrain."""
import speechbrain as sb
import torch

class SpeakerEncoder:
    def __init__(self, device="cpu"):
        self.device = device
        self.model = sb.pretrained.interfaces.SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="/tmp/ectdnn",
            run_opts={"device": device}
        )
    def __call__(self, wav_path):
        signal, fs = sb.dataio.dataio.read_audio(wav_path)
        emb = self.model.encode_batch(signal.unsqueeze(0))
        return emb.squeeze(0).cpu()
