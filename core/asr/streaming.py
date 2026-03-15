"""
Streaming ASR: buffer audio chunks, VAD segments, transcribe with Whisper, emit partial/final text.
Used by WebSocket endpoint /ws/transcribe.
"""

import io
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional, Generator, Tuple

# Sample rate expected by Whisper / frontend
STREAM_SR = 16000


def buffer_to_float(chunk: bytes) -> np.ndarray:
    """Convert PCM 16-bit little-endian bytes to float32 [-1, 1]."""
    arr = np.frombuffer(chunk, dtype=np.int16)
    return arr.astype(np.float32) / 32768.0


def transcribe_segment(
    model,
    audio_float: np.ndarray,
    sr: int = STREAM_SR,
    language: str = "vi",
) -> str:
    """Transcribe a segment (float array). Returns text."""
    if model is None or len(audio_float) == 0:
        return ""
    try:
        # Whisper expects file path or array; for array we need to write temp wav
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        sf.write(tmp.name, audio_float, sr, subtype="PCM_16")
        result = model.transcribe(tmp.name, language=language, fp16=False, verbose=False)
        import os
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
        if result and "text" in result:
            return (result["text"] or "").strip()
        return ""
    except Exception:
        return ""


def stream_with_vad(
    model,
    audio_buffer: np.ndarray,
    sr: int = STREAM_SR,
    language: str = "vi",
    min_speech_dur: float = 0.5,
    min_silence_dur: float = 0.3,
) -> Generator[Tuple[str, bool], None, None]:
    """
    Run VAD on buffer, split into segments, transcribe each. Yield (text, is_final).
    is_final=True for last segment.
    """
    if len(audio_buffer) == 0:
        return
    try:
        from core.audio.vad import load_silero_vad, get_speech_timestamps_from_array, merge_close_timestamps
        vad_model, vad_utils = load_silero_vad(device="cpu")
        if vad_model is None or vad_utils is None:
            # No VAD: transcribe whole buffer as one segment
            text = transcribe_segment(model, audio_buffer, sr=sr, language=language)
            if text:
                yield text, True
            return
        timestamps = get_speech_timestamps_from_array(audio_buffer, sr, vad_model, vad_utils)
        if not timestamps:
            text = transcribe_segment(model, audio_buffer, sr=sr, language=language)
            if text:
                yield text, True
            return
        merged = merge_close_timestamps(timestamps, max_gap=min_silence_dur)
        for i, seg in enumerate(merged):
            start_s = int(seg["start"] * sr)
            end_s = int(seg["end"] * sr)
            start_s = max(0, start_s)
            end_s = min(len(audio_buffer), end_s)
            if end_s <= start_s:
                continue
            chunk = audio_buffer[start_s:end_s]
            if len(chunk) < sr * min_speech_dur:
                continue
            text = transcribe_segment(model, chunk, sr=sr, language=language)
            if text:
                yield text, (i == len(merged) - 1)
    except Exception:
        text = transcribe_segment(model, audio_buffer, sr=sr, language=language)
        if text:
            yield text, True
