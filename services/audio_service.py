"""Business logic for audio: normalize, VAD, chunk, format. Delegates to utils and core.audio where needed."""
import os
import tempfile
from typing import Tuple, List, Dict, Optional, Union, Any
import numpy as np
import librosa
import soundfile as sf

from utils import audio_utils

# FFmpeg and legacy load_audio still in core.audio for now
try:
    from core.audio.ffmpeg_setup import ensure_ffmpeg, get_ffmpeg_info
except Exception:
    def ensure_ffmpeg(silent: bool = True) -> None:
        pass
    def get_ffmpeg_info() -> Tuple[bool, str]:
        return False, "FFmpeg setup not available"


def normalize_audio_to_wav(audio_path: str, target_sr: int = 16000) -> Tuple[str, int, np.ndarray]:
    """Normalize audio file to mono 16kHz WAV. Returns (wav_path, sr, samples)."""
    return audio_utils.normalize_audio_to_wav(audio_path, target_sr=target_sr)


def validate_audio_format(file_extension: str) -> Tuple[bool, str]:
    """Validate supported audio format."""
    return audio_utils.validate_audio_format(file_extension)


def chunk_signal(y: np.ndarray, sr: int, chunk_seconds: int) -> List[Tuple[int, int]]:
    """Split signal into (start_sample, end_sample) chunks by duration."""
    return audio_utils.chunk_signal(y, sr, chunk_seconds)


def detect_speech_segments(
    y: np.ndarray,
    sr: int,
    vad_threshold: float = 0.5,
    min_gap: float = 0.5,
    min_dur: Optional[float] = None,
    max_dur: Optional[float] = None,
    intent: str = "asr",
) -> List[Dict]:
    """Detect speech windows using VAD."""
    return audio_utils.detect_speech_segments(
        y, sr, vad_threshold=vad_threshold, min_gap=min_gap,
        min_dur=min_dur, max_dur=max_dur, intent=intent,
    )


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    return audio_utils.format_timestamp(seconds)


def get_audio_info(y: Optional[np.ndarray], sr: int) -> dict:
    """Return duration, sample_rate, channels, samples."""
    return audio_utils.get_audio_info(y, sr)


def plot_waveform(y: np.ndarray, sr: int, title: str = "Waveform"):
    """Plot waveform; returns matplotlib figure."""
    return audio_utils.plot_waveform(y, sr, title=title)


def plot_spectrogram(y: np.ndarray, sr: int, title: str = "Spectrogram"):
    """Plot spectrogram; returns matplotlib figure."""
    return audio_utils.plot_spectrogram(y, sr, title=title)


def load_audio(file_or_bytes: Union[Any, bytes], sr: int = 16000) -> Tuple[Optional[np.ndarray], int]:
    """
    Load audio from file-like (with .read(), .name) or bytes. Returns (y, sr) or (None, sr) on error.
    """
    try:
        if isinstance(file_or_bytes, bytes):
            audio_bytes = file_or_bytes
            ext = "wav"
        else:
            audio_bytes = file_or_bytes.read()
            ext = (
                file_or_bytes.name.split(".")[-1].lower()
                if getattr(file_or_bytes, "name", None) else "wav"
            )
        if len(audio_bytes) == 0:
            return None, sr
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            y, sr_out = librosa.load(tmp_path, sr=sr, mono=True)
            if y is None or len(y) == 0:
                return None, sr
            return y, sr_out
        except Exception:
            try:
                y, sr_out = sf.read(tmp_path)
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)
                if sr_out != sr:
                    y = librosa.resample(y, orig_sr=sr_out, target_sr=sr)
                    sr_out = sr
                return y, sr_out
            except Exception:
                return None, sr
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
    except Exception:
        return None, sr
