"""
Module xử lý audio: upload, preprocessing, visualization
"""
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pydub import AudioSegment
import io
import streamlit as st

# Đảm bảo FFmpeg đã được setup (cho PyDub)
try:
    from ffmpeg_setup import ensure_ffmpeg
    ensure_ffmpeg()
except ImportError:
    # Nếu không có ffmpeg_setup, bỏ qua (có thể đã có FFmpeg trong system)
    pass

def load_audio(file, sr=16000):
    """Load audio file và convert về format chuẩn"""
    try:
        # Đọc audio file
        if isinstance(file, bytes):
            audio_bytes = file
        else:
            audio_bytes = file.read()
        
        # Xử lý theo định dạng
        file_extension = file.name.split('.')[-1].lower() if hasattr(file, 'name') else 'wav'
        
        if file_extension in ['mp3', 'm4a', 'flac', 'ogg']:
            # Sử dụng pydub để convert
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=file_extension)
            # Convert to WAV
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format="wav")
            wav_io.seek(0)
            y, sr_original = sf.read(wav_io)
        else:
            y, sr_original = sf.read(io.BytesIO(audio_bytes))
        
        # Resample nếu cần
        if sr_original != sr:
            y = librosa.resample(y, orig_sr=sr_original, target_sr=sr)
        
        return y, sr
    except Exception as e:
        st.error(f"Lỗi khi load audio: {str(e)}")
        return None, None

def preprocess_audio(y, sr, normalize=True, remove_noise=False):
    """Tiền xử lý audio"""
    if y is None:
        return None
    
    # Normalize
    if normalize:
        y = librosa.util.normalize(y)
    
    # Noise reduction (simple high-pass filter)
    if remove_noise:
        from scipy import signal
        # High-pass filter để loại bỏ noise tần số thấp
        sos = signal.butter(10, 80, 'hp', fs=sr, output='sos')
        y = signal.sosfilt(sos, y)
    
    return y

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

