# SPDX-License-Identifier: MIT
"""Unicode normalisation + transliteration to native script."""
import unicodedata
from indicnlp.transliterate.unicode_transliterate import UnicodeIndicTransliterator

class Transliterator:
    def __init__(self, lang):
        self.lang = lang
    def __call__(self, text):
        text = unicodedata.normalize("NFKC", text)
        return UnicodeIndicTransliterator.transliterate(text, "hi", self.lang) if self.lang!="en" else text
