"""Auto language detection: from audio (Whisper) or from text (langdetect)."""
from typing import Optional
import os


def detect_language_from_audio(audio_path: str, whisper_model=None) -> Optional[str]:
    """
    Detect language from audio using Whisper (or faster-whisper).
    If whisper_model is None, loads default tiny model for detection only.
    Returns language code (e.g. 'vi', 'en') or None.
    """
    if not os.path.isfile(audio_path):
        return None
    try:
        import whisper
        model = whisper_model or whisper.load_model("tiny", device="cpu")
        result = model.transcribe(audio_path, language=None, task="transcribe", fp16=False)
        lang = result.get("language")
        return lang if isinstance(lang, str) else None
    except Exception:
        return None


def detect_language_from_audio_faster_whisper(audio_path: str, model=None) -> Optional[str]:
    """Detect language using faster-whisper (segment has 'language' or first segment)."""
    if not os.path.isfile(audio_path):
        return None
    try:
        import faster_whisper
        if model is None:
            model = faster_whisper.WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, language=None)
        lang = getattr(info, "language", None)
        if lang:
            return lang
        first = next(segments, None)
        if first and getattr(first, "language", None):
            return first.language
        return None
    except Exception:
        return None


def detect_language_from_text(text: str) -> Optional[str]:
    """
    Detect language from text (fallback when no audio).
    Uses langdetect; returns e.g. 'vi', 'en' or None.
    """
    if not (text and text.strip()):
        return None
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return None


def detect_language(audio_path: Optional[str] = None, text: Optional[str] = None, use_faster_whisper: bool = False) -> Optional[str]:
    """
    Auto-detect language: prefer audio (Whisper) if audio_path given, else text (langdetect).
    use_faster_whisper: use faster-whisper for audio detection if available.
    """
    if audio_path:
        if use_faster_whisper:
            return detect_language_from_audio_faster_whisper(audio_path)
        return detect_language_from_audio(audio_path)
    if text:
        return detect_language_from_text(text)
    return None
