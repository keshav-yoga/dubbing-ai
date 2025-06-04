# SPDX-License-Identifier: Apache-2.0
"""Sentence tokenisation for Indic + non‑Indic."""
import nltk
from indicnlp.tokenize import sentence_tokenize

class NltkIndicTokenizer:
    def __init__(self, lang):
        self.lang = lang
        nltk.download("punkt", quiet=True)
    def __call__(self, text: str):
        if self.lang in {"hi","ta","bn","te","ml","kn","gu","pa","or","mr"}:
            return sentence_tokenize.sentence_split(text, lang=self.lang)
        return nltk.sent_tokenize(text)
