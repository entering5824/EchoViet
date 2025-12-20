"""
Component visualization audio: waveform và spectrogram
"""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import librosa
from core.audio.audio_processor import plot_waveform, plot_spectrogram

def render_audio_visualization(audio_data, sr):
    """
    Hiển thị waveform và spectrogram của audio
    
    Args:
        audio_data: Numpy array chứa audio samples
        sr: Sample rate
    """
    if audio_data is None or len(audio_data) == 0:
        st.warning("⚠️ Không có dữ liệu audio để hiển thị")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Waveform")
        fig_wave = plot_waveform(audio_data, sr, title="Audio Waveform")
        st.pyplot(fig_wave)
        plt.close(fig_wave)
    
    with col2:
        st.subheader("🎵 Spectrogram")
        fig_spec = plot_spectrogram(audio_data, sr, title="Audio Spectrogram")
        st.pyplot(fig_spec)
        plt.close(fig_spec)

