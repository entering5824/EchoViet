"""Audio player and visualization: waveform, spectrogram, playback."""
import streamlit as st
import numpy as np
from services.audio_service import plot_waveform, plot_spectrogram


def render_audio_player(audio_data: np.ndarray, sr: int):
    """Render waveform, spectrogram, and optional audio element for playback."""
    if audio_data is None or len(audio_data) == 0:
        st.warning("⚠️ Không có dữ liệu audio để hiển thị")
        return
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Waveform")
        fig_wave = plot_waveform(audio_data, sr, title="Audio Waveform")
        st.pyplot(fig_wave)
        try:
            import matplotlib.pyplot as plt
            plt.close(fig_wave)
        except Exception:
            pass
    with col2:
        st.subheader("🎵 Spectrogram")
        fig_spec = plot_spectrogram(audio_data, sr, title="Audio Spectrogram")
        st.pyplot(fig_spec)
        try:
            import matplotlib.pyplot as plt
            plt.close(fig_spec)
        except Exception:
            pass
    st.audio(audio_data, sample_rate=sr, format="audio/wav")
