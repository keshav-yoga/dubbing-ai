from gtts import gTTS
from pydub import AudioSegment
import os

class TTSProcessor:
    """Simple TTS processor using Google TTS service."""

    def __init__(self, lang: str = "en"):
        self.lang = lang

    def synthesize_text(
        self,
        text: str,
        output_path: str,
        voice_name: str | None = None,
        speaker_label: str | None = None,
    ) -> str:
        """Generate speech audio from ``text`` and save it as WAV."""
        tts = gTTS(text=text, lang=self.lang)
        mp3_path = output_path.rsplit(".", 1)[0] + ".mp3"
        tts.save(mp3_path)
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(output_path, format="wav")
        os.remove(mp3_path)
        return output_path
