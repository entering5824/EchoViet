"""Silero VAD helpers

Provides a simple wrapper around the Silero VAD to extract speech timestamps
and group them into windows suitable for ASR (e.g., 20-30s chunks).
"""
from typing import List, Dict, Tuple
import torch
import numpy as np
import tempfile
import warnings


# Module-level cache to avoid re-loading the Silero VAD repeatedly (useful for cloud/streaming)
_cached_vad_model = None
_cached_vad_utils = None


def load_silero_vad(force_reload: bool = False, device: str = "cpu"):
    """Load Silero VAD model and utils via torch.hub.

    This function will cache the loaded model and utils in-module to avoid
    repeated downloads / loads when running multiple transcriptions in the
    same process (helpful for Streamlit deployments).

    Returns (model, utils_tuple) where utils_tuple contains helper functions
    such as get_speech_timestamps.
    """
    global _cached_vad_model, _cached_vad_utils
    if not force_reload and _cached_vad_model is not None and _cached_vad_utils is not None:
        try:
            _cached_vad_model.to(device)
        except Exception:
            pass
        return _cached_vad_model, _cached_vad_utils

    try:
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


def get_speech_timestamps_from_array(y: np.ndarray, sr: int, model, utils, threshold: float = 0.5) -> List[Dict]:
    """Return speech timestamps in seconds as list of dicts {'start': float, 'end': float}.

    The Silero utils may return timestamps in samples; we convert to seconds.
    """
    if model is None or utils is None:
        return []

    get_speech_ts = utils[0]

    # Silero expects a 1-D numpy array of floats (int16 -> float32 in [-1,1])
    if y.dtype != np.float32:
        y_proc = y.astype(np.float32)
    else:
        y_proc = y

    try:
        raw_ts = get_speech_ts(y_proc, model, sampling_rate=sr, threshold=threshold)
    except TypeError:
        # Some versions expect the sampling_rate as a named parameter
        raw_ts = get_speech_ts(y_proc, model, sr, threshold=threshold)

    # Convert to seconds: detect if values look like samples (big ints)
    timestamps = []
    for seg in raw_ts:
        start = seg.get("start", 0)
        end = seg.get("end", 0)

        # If values are large (greater than sr*10), they're probably samples -> convert
        if start > 1000 or end > 1000:
            start_s = float(start) / float(sr)
            end_s = float(end) / float(sr)
        else:
            # Already in seconds or small sample counts; be conservative
            start_s = float(start)
            end_s = float(end)

        timestamps.append({"start": start_s, "end": end_s})

    return timestamps


def merge_close_timestamps(timestamps: List[Dict], max_gap: float = 0.5) -> List[Dict]:
    """Merge adjacent timestamps separated by less than max_gap seconds."""
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


def group_segments_into_windows(segments: List[Dict], min_dur: float = 20.0, max_dur: float = 30.0, audio_duration: float = None) -> List[Dict]:
    """Group speech segments into windows between min_dur and max_dur seconds.

    Returns list of windows {'start': float, 'end': float}.
    """
    if not segments:
        # If no VAD segments found, create a single window covering the whole audio
        if audio_duration:
            return [{"start": 0.0, "end": audio_duration}]
        return []

    windows = []
    current = {"start": segments[0]["start"], "end": segments[0]["end"]}

    for seg in segments[1:]:
        proposed_end = seg["end"]
        # If merging the segment keeps us under max_dur, merge
        if (proposed_end - current["start"]) <= max_dur:
            current["end"] = proposed_end
        else:
            # If current window is shorter than min_dur, we can try to extend by including this seg
            if (current["end"] - current["start"]) < min_dur:
                current["end"] = proposed_end
                # If still exceeded max_dur, cut
                if (current["end"] - current["start"]) > max_dur:
                    current["end"] = current["start"] + max_dur
            windows.append(current)
            current = {"start": seg["start"], "end": seg["end"]}

    windows.append(current)

    # Optionally clip by audio_duration
    if audio_duration is not None:
        for w in windows:
            w["start"] = max(0.0, w["start"])
            w["end"] = min(audio_duration, w["end"])

    return windows


def extract_window_audio(y: np.ndarray, sr: int, window: Dict) -> Tuple[str, float, float]:
    """Write a window to a temporary WAV file and return (path, start, end)."""
    import soundfile as sf

    start_sample = int(window["start"] * sr)
    end_sample = int(window["end"] * sr)
    start_sample = max(0, start_sample)
    end_sample = min(len(y), end_sample)

    chunk = y[start_sample:end_sample]

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.close()
    sf.write(tmp.name, chunk, sr, subtype="PCM_16")
    return tmp.name, window["start"], window["end"]
