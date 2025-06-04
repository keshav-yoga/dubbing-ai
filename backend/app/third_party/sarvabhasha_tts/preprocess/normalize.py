# SPDX-License-Identifier: MIT
"""Number & unit verbalisation using num2words + indic‑numtowords."""
from num2words import num2words
from indic_numtowords import num_to_words

class NumNormalizer:
    def __init__(self, lang):
        self.lang = lang
    def _is_number(self, token):
        try:
            float(token)
            return True
        except ValueError:
            return False
    def __call__(self, tokens):
        out = []
        for tok in tokens:
            if self._is_number(tok):
                if self.lang in {"hi","ta","bn","te","ml","kn","gu","pa","or","mr"}:
                    out.append(num_to_words(tok, self.lang))
                else:
                    out.append(num2words(tok, lang=self.lang))
            else:
                out.append(tok)
        return out
