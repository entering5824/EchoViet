"""Audio processing utilities: load, normalize, chunk, VAD, visualization."""
import os
import tempfile
import warnings
from typing import Tuple, List, Dict, Optional

import librosa
import numpy as np
import soundfile as sf

# Optional matplotlib for plots (caller can check)
try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

# VAD cache
_cached_vad_model = None
_cached_vad_utils = None


def validate_audio_format(file_extension: str) -> Tuple[bool, str]:
    """Validate that the audio format is supported."""
    supported = ["wav", "mp3", "flac", "m4a", "ogg", "wma", "aac"]
    ext = file_extension.lower().lstrip(".")
    if ext in supported:
        return True, f"Format {ext.upper()} được hỗ trợ"
    return False, f"Format {ext.upper()} không được hỗ trợ. Các format: {', '.join(supported).upper()}"


def _make_safe_temp_copy(original_path: str) -> str:
    """Create a safe temp copy of file (avoids odd filenames). Caller must delete."""
    from utils.file_utils import make_safe_temp_copy
    return make_safe_temp_copy(original_path)


def normalize_audio_to_wav(
    audio_path: str,
    target_sr: int = 16000,
) -> Tuple[str, int, np.ndarray]:
    """Load audio, convert to mono 16kHz WAV PCM16, peak-normalize. Returns (wav_path, sr, samples)."""
    temp_copy = None
    try:
        if not os.path.exists(audio_path) or os.path.basename(audio_path).strip() != os.path.basename(audio_path):
            temp_copy = _make_safe_temp_copy(audio_path)
            load_path = temp_copy
        else:
            load_path = audio_path
        y, sr = librosa.load(load_path, sr=target_sr, mono=True)
        peak = float(np.max(np.abs(y))) if y.size else 0.0
        if peak > 0:
            y = y / peak
        out = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out.close()
        sf.write(out.name, y, target_sr, subtype="PCM_16")
        return out.name, target_sr, y
    finally:
        if temp_copy and os.path.exists(temp_copy):
            try:
                os.unlink(temp_copy)
            except Exception:
                pass


def load_audio_from_path(path: str, sr: int = 16000) -> Tuple[Optional[np.ndarray], int]:
    """Load audio from file path; return (y, sr) or (None, sr) on error."""
    try:
        y, sr_out = librosa.load(path, sr=sr, mono=True)
        if y is None or len(y) == 0:
            return None, sr
        return y, sr_out
    except Exception:
        return None, sr


def preprocess_audio(
    y: Optional[np.ndarray],
    sr: int,
    normalize: bool = False,
    remove_noise: bool = False,
) -> Optional[np.ndarray]:
    """Preprocess: optional normalize and high-pass filter."""
    if y is None:
        return None
    if normalize:
        y = librosa.util.normalize(y)
    if remove_noise:
        from scipy import signal
        sos = signal.butter(10, 80, "hp", fs=sr, output="sos")
        y = signal.sosfilt(sos, y)
    return y


def apply_noise_reduction(y: np.ndarray, sr: int, cutoff: int = 80) -> np.ndarray:
    """Simple high-pass filter to reduce low-frequency noise."""
    from scipy import signal
    sos = signal.butter(10, cutoff, "hp", fs=sr, output="sos")
    return signal.sosfilt(sos, y)


def chunk_signal(y: np.ndarray, sr: int, chunk_seconds: int) -> List[Tuple[int, int]]:
    """Split signal into (start_sample, end_sample) chunks by duration in seconds."""
    total = len(y)
    chunk_len = int(chunk_seconds * sr)
    if chunk_len <= 0 or total == 0:
        return [(0, total)]
    return [(s, min(s + chunk_len, total)) for s in range(0, total, chunk_len)]


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def get_audio_info(y: Optional[np.ndarray], sr: int) -> dict:
    """Return duration, sample_rate, channels, samples."""
    if y is None:
        return {}
    return {
        "duration": len(y) / sr,
        "sample_rate": sr,
        "channels": 1 if len(y.shape) == 1 else y.shape[1],
        "samples": len(y),
    }


def plot_waveform(y: np.ndarray, sr: int, title: str = "Waveform"):
    """Plot waveform; returns matplotlib figure."""
    if not _HAS_MPL:
        raise RuntimeError("matplotlib not available")
    fig, ax = plt.subplots(figsize=(12, 4))
    time = np.linspace(0, len(y) / sr, len(y))
    ax.plot(time, y, linewidth=0.5)
    ax.set_xlabel("Thời gian (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig


def plot_spectrogram(y: np.ndarray, sr: int, title: str = "Spectrogram"):
    """Plot spectrogram; returns matplotlib figure."""
    if not _HAS_MPL:
        raise RuntimeError("matplotlib not available")
    D = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    fig, ax = plt.subplots(figsize=(12, 6))
    img = librosa.display.specshow(S_db, x_axis="time", y_axis="hz", sr=sr, ax=ax, cmap="viridis")
    ax.set_title(title)
    ax.set_xlabel("Thời gian (s)")
    ax.set_ylabel("Tần số (Hz)")
    plt.colorbar(img, ax=ax, format="%+2.0f dB")
    plt.tight_layout()
    return fig


# --- Silero VAD ---
def load_silero_vad(force_reload: bool = False, device: str = "cpu"):
    """Load Silero VAD model and utils. Returns (model, utils)."""
    global _cached_vad_model, _cached_vad_utils
    if not force_reload and _cached_vad_model is not None and _cached_vad_utils is not None:
        try:
            _cached_vad_model.to(device)
        except Exception:
            pass
        return _cached_vad_model, _cached_vad_utils
    try:
        import torch
        model, utils = torch.hub.load(
            "snakers4/silero-vad",
            "silero_vad",
            force_reload=force_reload,
            verbose=False,
        )
        model.to(device)
        _cached_vad_model = model
        _cached_vad_utils = utils
        return model, utils
    except Exception as e:
        warnings.warn(f"Could not load Silero VAD: {e}")
        return None, None


def get_speech_timestamps_from_array(
    y: np.ndarray,
    sr: int,
    model,
    utils,
    threshold: float = 0.5,
) -> List[Dict]:
    """Return speech timestamps in seconds: [{'start': float, 'end': float}, ...]."""
    if model is None or utils is None:
        return []
    get_speech_ts = utils[0]
    y_proc = y.astype(np.float32) if y.dtype != np.float32 else y
    try:
        raw_ts = get_speech_ts(y_proc, model, sampling_rate=sr, threshold=threshold)
    except TypeError:
        raw_ts = get_speech_ts(y_proc, model, sr, threshold=threshold)
    timestamps = []
    for seg in raw_ts:
        start, end = seg.get("start", 0), seg.get("end", 0)
        if start > 1000 or end > 1000:
            start = float(start) / float(sr)
            end = float(end) / float(sr)
        else:
            start, end = float(start), float(end)
        timestamps.append({"start": start, "end": end})
    return timestamps


def merge_close_timestamps(timestamps: List[Dict], max_gap: float = 0.5) -> List[Dict]:
    """Merge adjacent segments separated by less than max_gap seconds."""
    if not timestamps:
        return []
    timestamps = sorted(timestamps, key=lambda x: x["start"])
    merged = [timestamps[0].copy()]
    for seg in timestamps[1:]:
        prev = merged[-1]
        if seg["start"] - prev["end"] <= max_gap:
            prev["end"] = max(prev["end"], seg["end"])
        else:
            merged.append(seg.copy())
    return merged


def group_segments_into_windows(
    segments: List[Dict],
    min_dur: float = 20.0,
    max_dur: float = 30.0,
    audio_duration: Optional[float] = None,
) -> List[Dict]:
    """Group speech segments into windows (start/end in seconds)."""
    if not segments:
        if audio_duration is not None:
            return [{"start": 0.0, "end": audio_duration}]
        return []
    windows = []
    current = {"start": segments[0]["start"], "end": segments[0]["end"]}
    for seg in segments[1:]:
        if (seg["end"] - current["start"]) <= max_dur:
            current["end"] = seg["end"]
        else:
            if (current["end"] - current["start"]) < min_dur:
                current["end"] = seg["end"]
                if (current["end"] - current["start"]) > max_dur:
                    current["end"] = current["start"] + max_dur
            windows.append(current)
            current = {"start": seg["start"], "end": seg["end"]}
    windows.append(current)
    if audio_duration is not None:
        for w in windows:
            w["start"] = max(0.0, w["start"])
            w["end"] = min(audio_duration, w["end"])
    return windows


def extract_window_audio(y: np.ndarray, sr: int, window: Dict) -> Tuple[str, float, float]:
    """Write a window to a temporary WAV file; return (path, start_sec, end_sec). Caller must delete path."""
    start_sample = int(window["start"] * sr)
    end_sample = int(window["end"] * sr)
    start_sample = max(0, start_sample)
    end_sample = min(len(y), end_sample)
    chunk = y[start_sample:end_sample]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    sf.write(tmp.name, chunk, sr, subtype="PCM_16")
    return tmp.name, window["start"], window["end"]


def detect_speech_segments(
    y: np.ndarray,
    sr: int,
    vad_threshold: float = 0.5,
    min_gap: float = 0.5,
    min_dur: Optional[float] = None,
    max_dur: Optional[float] = None,
    intent: str = "asr",
) -> List[Dict]:
    """Detect speech regions using Silero VAD; return list of {'start', 'end'} windows."""
    if min_dur is None or max_dur is None:
        if intent == "asr":
            min_dur = 20.0
            max_dur = 30.0
        elif intent == "diarization":
            min_dur = 2.0
            max_dur = 8.0
        else:
            min_dur = 10.0
            max_dur = 30.0
    try:
        model, utils = load_silero_vad(device="cpu")
        if model is None or utils is None:
            return [{"start": 0.0, "end": len(y) / sr}]
        timestamps = get_speech_timestamps_from_array(y, sr, model, utils, threshold=vad_threshold)
        timestamps = merge_close_timestamps(timestamps, max_gap=min_gap)
        windows = group_segments_into_windows(
            timestamps, min_dur=min_dur, max_dur=max_dur, audio_duration=len(y) / sr
        )
        if not windows:
            return [{"start": 0.0, "end": len(y) / sr}]
        return windows
    except Exception:
        return [{"start": 0.0, "end": len(y) / sr}]
