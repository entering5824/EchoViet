"""
Module xử lý audio: upload, preprocessing, visualization
Pipeline không cần ffprobe - sử dụng librosa/soundfile thay vì pydub
"""
import os
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import streamlit as st
import tempfile
from typing import Tuple, List, Dict

def validate_audio_format(file_extension: str) -> Tuple[bool, str]:
    """
    Validate audio format được hỗ trợ
    
    Args:
        file_extension: Extension của file (ví dụ: 'mp3', 'wav')
    
    Returns:
        Tuple (is_valid: bool, message: str)
    """
    supported_formats = ['wav', 'mp3', 'flac', 'm4a', 'ogg', 'wma', 'aac']
    file_ext_lower = file_extension.lower().lstrip('.')
    
    if file_ext_lower in supported_formats:
        return True, f"Format {file_ext_lower.upper()} được hỗ trợ"
    else:
        return False, f"Format {file_ext_lower.upper()} không được hỗ trợ. Các format được hỗ trợ: {', '.join(supported_formats).upper()}"

def load_audio(file, sr=16000):
    """
    Load audio file và convert về format chuẩn
    Sử dụng librosa/soundfile thay vì pydub để tránh phụ thuộc ffprobe
    
    Args:
        file: File object hoặc bytes
        sr: Target sample rate (default 16kHz)
    
    Returns:
        Tuple (audio_array: np.ndarray, sample_rate: int) hoặc (None, None) nếu lỗi
    """
    try:
        # Đọc audio file vào temporary file để librosa có thể xử lý
        if isinstance(file, bytes):
            audio_bytes = file
            file_extension = 'wav'  # Default
        else:
            audio_bytes = file.read()
            file_extension = file.name.split('.')[-1].lower() if hasattr(file, 'name') else 'wav'
        
        # Validate audio format
        is_valid_format, format_msg = validate_audio_format(file_extension)
        if not is_valid_format:
            try:
                st.warning(f"⚠️ {format_msg}")
                st.info("💡 Đang thử convert tự động...")
            except:
                pass
        
        # Kiểm tra file không rỗng
        if len(audio_bytes) == 0:
            try:
                st.error("❌ File audio rỗng! Vui lòng upload file hợp lệ.")
            except:
                pass
            return None, None
        
        # Tạo temporary file để librosa load
        # Librosa có thể load mp3, flac, ogg, m4a mà không cần pydub
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Sử dụng librosa để load - hỗ trợ nhiều format và tự động convert về mono
            y, sr_original = librosa.load(tmp_path, sr=sr, mono=True)
            
            # Validate audio data
            if y is None or len(y) == 0:
                try:
                    st.error("❌ Không thể đọc được dữ liệu audio từ file. File có thể bị hỏng.")
                except:
                    pass
                return None, None
            
            # Check sample rate
            if sr_original != sr:
                try:
                    st.info(f"ℹ️ Audio được resample từ {sr_original}Hz về {sr}Hz")
                except:
                    pass
            
        except Exception as librosa_error:
            error_msg = str(librosa_error)
            # Nếu librosa không load được, thử soundfile
            try:
                y, sr_original = sf.read(tmp_path)
                # Convert to mono nếu stereo
                if len(y.shape) > 1:
                    y = np.mean(y, axis=1)
                # Resample nếu cần
                if sr_original != sr:
                    y = librosa.resample(y, orig_sr=sr_original, target_sr=sr)
                
                # Validate audio data
                if y is None or len(y) == 0:
                    try:
                        st.error("❌ Không thể đọc được dữ liệu audio từ file. File có thể bị hỏng.")
                    except:
                        pass
                    return None, None
            except Exception as sf_error:
                try:
                    st.error(f"❌ Lỗi khi load audio với librosa: {error_msg}")
                    if "ffmpeg" in error_msg.lower():
                        st.warning("💡 Lỗi có thể do FFmpeg chưa được cấu hình đúng. Vui lòng kiểm tra FFmpeg setup.")
                    st.error(f"❌ Lỗi khi load audio với soundfile: {str(sf_error)}")
                    st.info("💡 Vui lòng thử với file WAV hoặc MP3 chuẩn.")
                except:
                    pass
                return None, None
        finally:
            # Xóa temporary file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        
        return y, sr
    except Exception as e:
        try:
            st.error(f"❌ Lỗi khi load audio: {str(e)}")
        except:
            pass
        return None, None

def preprocess_audio(y, sr, normalize: bool = False, remove_noise: bool = False):
    """Tiền xử lý audio

    Notes:
    - Default `normalize=False` because ASR pipelines typically perform a
      single, canonical normalization step at the top-level (see
      `normalize_audio_to_wav`). Enabling `normalize` here is useful for
      visualization or other non-ASR use-cases but may be redundant for ASR.
    - `remove_noise` applies a simple high-pass filter; aggressive filtering can
      harm ASR quality and is **not recommended** by default. Keep `remove_noise`
      False unless you have noisy recordings and have validated the effect.
    """
    if y is None:
        return None
    
    # Normalize (off by default)
    if normalize:
        y = librosa.util.normalize(y)
    
    # Noise reduction (simple high-pass filter)
    if remove_noise:
        from scipy import signal
        # High-pass filter để loại bỏ noise tần số thấp
        sos = signal.butter(10, 80, 'hp', fs=sr, output='sos')
        y = signal.sosfilt(sos, y)
    
    return y


# === Convenience helpers ===
def _make_safe_temp_copy(original_path: str) -> str:
    """Create a temporary copy of a file's bytes to avoid problems with odd filenames.

    This is used to avoid passing potentially problematic paths (e.g., trailing spaces)
    to libraries that may invoke external tools.
    Returns the path to the temp copy (must be deleted by caller).
    """
    with open(original_path, "rb") as src:
        data = src.read()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_path)[1])
    tmp_name = tmp.name
    tmp.close()
    with open(tmp_name, "wb") as f:
        f.write(data)
    return tmp_name


def normalize_audio_to_wav(audio_path: str, target_sr: int = 16000) -> Tuple[str, int, np.ndarray]:
    """
    Load audio -> mono 16kHz WAV PCM16, peak-normalized.
    Returns (normalized_wav_path, sr, samples)

    To avoid Windows "No such file" / WinError 2 issues when the original filename
    is odd (e.g., trailing spaces) or when external tools have trouble with the
    original path, create a safe temp copy and load from that copy.
    """
    temp_copy = None
    try:
        # If the path looks suspicious (e.g., ends with whitespace) or does not exist
        # create a safe temp copy to read from.
        if not os.path.exists(audio_path) or os.path.basename(audio_path).strip() != os.path.basename(audio_path):
            temp_copy = _make_safe_temp_copy(audio_path)
            load_path = temp_copy
        else:
            load_path = audio_path

        y, sr = librosa.load(load_path, sr=target_sr, mono=True)
        peak = float(np.max(np.abs(y))) if y.size else 0.0
        if peak > 0:
            y = y / peak

        out_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        out_wav.close()
        sf.write(out_wav.name, y, target_sr, subtype="PCM_16")
        return out_wav.name, target_sr, y
    finally:
        if temp_copy and os.path.exists(temp_copy):
            try:
                os.unlink(temp_copy)
            except Exception:
                pass


def apply_noise_reduction(y: np.ndarray, sr: int, cutoff: int = 80):
    """
    Simple high-pass filter to reduce low-frequency noise.
    """
    from scipy import signal
    if y is None:
        return None
    sos = signal.butter(10, cutoff, "hp", fs=sr, output="sos")
    return signal.sosfilt(sos, y)


def chunk_signal(y: np.ndarray, sr: int, chunk_seconds: int) -> List[Tuple[int, int]]:
    """
    Split signal into chunks by duration (seconds).

    NOTE: This simple time-based chunking is useful for some use-cases but is
    not recommended as the primary method for ASR segmentation — prefer
    VAD-based segmentation (see `detect_speech_segments`).
    """
    total_samples = len(y)
    chunk_len = int(chunk_seconds * sr)
    if chunk_len <= 0 or total_samples == 0:
        return [(0, total_samples)]
    ranges = []
    for start in range(0, total_samples, chunk_len):
        end = min(start + chunk_len, total_samples)
        ranges.append((start, end))
    return ranges


def detect_speech_segments(y: np.ndarray, sr: int, vad_threshold: float = 0.5, min_gap: float = 0.5, min_dur: float = None, max_dur: float = None, intent: str = "asr") -> List[Dict]:
    """Detect speech regions using Silero VAD and return windows suitable for the given intent.

    Args:
        y, sr: audio samples and sample rate
        vad_threshold: Silero VAD threshold (higher -> fewer speech regions)
        min_gap: maximum gap (s) to merge adjacent speech segments
        min_dur / max_dur: window sizing; if None defaults depend on `intent`
        intent: 'asr' (default) or 'diarization' to pick sensible window sizes

    Returns a list of dicts: [{'start': float, 'end': float}, ...]. If Silero VAD
    cannot be loaded or finds no speech, this function falls back to returning
    a single window that spans the whole audio.
    """
    # Pick sensible window sizes based on intent if not provided
    if min_dur is None or max_dur is None:
        if intent == "asr":
            min_dur = 20.0 if min_dur is None else min_dur
            max_dur = 30.0 if max_dur is None else max_dur
        elif intent == "diarization":
            # diarization benefits from short segments
            min_dur = 2.0 if min_dur is None else min_dur
            max_dur = 8.0 if max_dur is None else max_dur
        else:
            min_dur = 10.0 if min_dur is None else min_dur
            max_dur = 30.0 if max_dur is None else max_dur

    try:
        from core.audio.vad import (
            load_silero_vad,
            get_speech_timestamps_from_array,
            merge_close_timestamps,
            group_segments_into_windows,
        )
    except Exception:
        # VAD module not available
        return [{"start": 0.0, "end": len(y) / sr}]

    model, utils = load_silero_vad(device="cpu")
    if model is None or utils is None:
        return [{"start": 0.0, "end": len(y) / sr}]

    timestamps = get_speech_timestamps_from_array(y, sr, model, utils, threshold=vad_threshold)
    timestamps = merge_close_timestamps(timestamps, max_gap=min_gap)
    windows = group_segments_into_windows(timestamps, min_dur=min_dur, max_dur=max_dur, audio_duration=len(y) / sr)

    if not windows:
        return [{"start": 0.0, "end": len(y) / sr}]

    return windows


def format_timestamp(seconds: float) -> str:
    """
    Format seconds -> MM:SS
    """
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def plot_waveform(y, sr, title="Waveform"):
    """Vẽ waveform"""
    fig, ax = plt.subplots(figsize=(12, 4))
    time = np.linspace(0, len(y) / sr, len(y))
    ax.plot(time, y, linewidth=0.5)
    ax.set_xlabel('Thời gian (s)', fontsize=10)
    ax.set_ylabel('Amplitude', fontsize=10)
    ax.set_title(title, fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig

def plot_spectrogram(y, sr, title="Spectrogram"):
    """Vẽ spectrogram"""
    # Tính spectrogram
    D = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    img = librosa.display.specshow(S_db, x_axis='time', y_axis='hz', 
                                    sr=sr, ax=ax, cmap='viridis')
    ax.set_title(title, fontsize=12)
    ax.set_xlabel('Thời gian (s)', fontsize=10)
    ax.set_ylabel('Tần số (Hz)', fontsize=10)
    plt.colorbar(img, ax=ax, format='%+2.0f dB')
    plt.tight_layout()
    return fig

def get_audio_info(y, sr):
    """Lấy thông tin audio"""
    if y is None:
        return {}
    
    duration = len(y) / sr
    return {
        'duration': duration,
        'sample_rate': sr,
        'channels': 1 if len(y.shape) == 1 else y.shape[1],
        'samples': len(y)
    }

