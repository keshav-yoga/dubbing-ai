# SPDX-License-Identifier: Apache-2.0
"""Route to best G2P for requested language."""
from functools import lru_cache
from typing import List
from g2p_en import G2p
from indic_phonemizer import phonemize as indic_g2p
import subprocess, tempfile, os

@lru_cache
def _espeak_ng(lang):
    def g2p(words: List[str]):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write("\n".join(words))
        cmd = ["espeak-ng", "-q", "-v", lang, "-f", tmp.name, "--ipa=3"]
        phonemes = subprocess.check_output(cmd, text=True)
        os.unlink(tmp.name)
        return phonemes.splitlines()
    return g2p

class G2PRouter:
    def __init__(self, lang):
        self.lang = lang
        if lang == "en":
            self.engine = G2p()
        elif lang in indic_g2p.SUPPORTED_LANGS:
            self.engine = lambda words: indic_g2p(words, lang=lang)
        else:
            self.engine = _espeak_ng(lang)
    def __call__(self, words):
        return self.engine(words)
