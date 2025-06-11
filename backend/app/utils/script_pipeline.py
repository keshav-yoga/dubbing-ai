# backend/app/utils/script_pipeline.py␊
␊
import language_tool_python␊
from transformers import MarianMTModel, MarianTokenizer, pipeline␊
import re␊
␊
# Example mapping from 'en' -> "Helsinki-NLP/opus-mt-en-ROMANCE", etc.␊
# In reality, you'd handle all 15 languages you need (Telugu, English, etc.)␊
# or dynamically pick the correct model pair for "source_lang -> target_lang".␊
MODEL_MAPPING = {␊
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",␊
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",␊
    # etc...␊
    # For demonstration only␊
}␊
␊
def detect_and_load_model(src_lang: str, tgt_lang: str):␊
    """␊
    Returns a translation pipeline or model for a given source->target pair.␊
    In production, you might have multiple models or a fallback to an API.␊
    """␊
    key = (src_lang, tgt_lang)␊
    model_name = MODEL_MAPPING.get(key)␊
    if not model_name:␊
        # If not found, fallback to a generic or external translator␊
        raise ValueError(f"No local model found for {src_lang} -> {tgt_lang}. Use an external API or add a new mapping.")␊
    ␊
    tokenizer = MarianTokenizer.from_pretrained(model_name)␊
    model = MarianMTModel.from_pretrained(model_name)␊
    return pipeline("translation", model=model, tokenizer=tokenizer)␊
␊
class ScriptProcessor:␊
    def __init__(self):␊
        # LanguageTool for grammar/spell checks, default is for English␊
        # you can load for different languages or adapt dynamically␊
        self.grammar_tool = language_tool_python.LanguageTool('en-US')␊
␊
    def clean_grammar(self, text: str, lang: str = "en") -> str:␊
        """␊
        Basic grammar correction using LanguageTool for demonstration.␊
        If text is not in English, you'd need to configure LanguageTool for that language if available.␊
        """␊
        # For advanced usage, consider different tools for different languages␊
        if lang != "en":␊
            # For demonstration, skip grammar checks if not English␊
            return text␊
␊
        matches = self.grammar_tool.check(text)␊
        corrected_text = language_tool_python.utils.correct(text, matches)␊
        return corrected_text␊
␊
    def rewrite_slang_or_cultural(self, text: str, lang: str = "en") -> str:␊
        """␊
        Placeholder function to adapt culturally-specific references, slang, jokes, etc.␊
        In a real system, you'd have advanced rules or an LLM to do this.␊
        """␊
        # Example: Replace "dude" with "friend" in English (just as a silly example)␊
        if lang == "en":␊
            text = re.sub(r"\bdude\b", "friend", text, flags=re.IGNORECASE)␊
        return text␊
␊
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:␊
        """␊
        Translate text from source_lang to target_lang using a local or external model.␊
        """␊
        # For demonstration, assume the text is always from 'en' to 'xx' or vice versa␊
        # In real usage, you'd handle multiple source/target combos, fallback to APIs if missing.␊
        translator = detect_and_load_model(source_lang, target_lang)␊
        # The huggingface translation pipeline returns a list of dicts: [{"translation_text": "..."}]␊
        result = translator(text)␊
        translated = result[0]["translation_text"]␊
        return translated␊
␊
    def process_segment(self, segment_text: str, source_lang: str, target_lang: str) -> str:␊
        """␊
        1) Grammar check + cleanup in source_lang (if relevant)␊
        2) Translate to target_lang␊
        3) (Optional) Another grammar pass in target_lang if needed␊
        4) Cultural/slang rewrite for target_lang␊
        """␊
        cleaned_source_text = self.clean_grammar(segment_text, lang=source_lang)␊
        # For demonstration, let's assume we do grammar cleanup only if the source is in English.␊
        ␊
        # Then translation␊
        translated_text = self.translate_text(cleaned_source_text, source_lang, target_lang)␊
␊
        # (Optional) final pass in target_lang (if there's a grammar tool for that language).␊
        # We'll skip that here for brevity.␊
␊
        # Cultural rewrite in target_lang␊
        final_text = self.rewrite_slang_or_cultural(translated_text, lang=target_lang)␊
␊
        return final_text␊
