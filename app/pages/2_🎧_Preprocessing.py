"""
Preprocessing Page
"""
import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.audio.audio_processor import (
    preprocess_audio,
    plot_waveform,
    plot_spectrogram,
    get_audio_info,
    load_audio,
    apply_noise_reduction,
)
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

st.header("🎧 Audio Preprocessing & Visualization")

# Optional quick upload if user chưa vào Upload page
if st.session_state.audio_data is None:
    st.info("Bạn có thể upload nhanh tại đây hoặc vào trang 'Upload & Record'.")
    quick_file = st.file_uploader("📤 Upload audio (WAV/MP3/FLAC/M4A/OGG)", type=["wav", "mp3", "flac", "m4a", "ogg"])
    if quick_file:
        with st.spinner("Đang load audio..."):
            audio_data, sr = load_audio(quick_file)
            if audio_data is not None:
                st.session_state.audio_data = audio_data
                st.session_state.audio_sr = sr
                st.session_state.audio_info = get_audio_info(audio_data, sr)
                st.success("✅ Đã tải audio vào bộ nhớ!")

if st.session_state.audio_data is None:
    st.warning("⚠️ Vui lòng tải audio trước.")
    st.stop()

    # Display audio info
    if st.session_state.audio_info:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Độ dài", f"{st.session_state.audio_info['duration']:.2f} giây")
        with col2:
            st.metric("Sample Rate", f"{st.session_state.audio_sr} Hz")
        with col3:
            st.metric("Số mẫu", f"{len(st.session_state.audio_data):,}")
    
st.audio(st.session_state.audio_data, sample_rate=st.session_state.audio_sr)

    # Preprocessing options
    st.subheader("⚙️ Tiền xử lý Audio")
col1, col2, col3 = st.columns(3)
    with col1:
    normalize = st.checkbox("Normalize", value=True)
    with col2:
    remove_noise = st.checkbox("Noise reduction (HPF)", value=False)
with col3:
    noise_cutoff = st.slider("Cutoff (Hz)", min_value=40, max_value=200, value=80, step=10, help="Tần số cắt cho high-pass filter")
    
    if st.button("Áp dụng tiền xử lý", type="primary"):
        if st.session_state.audio_data is not None:
            with st.spinner("Đang xử lý..."):
            processed = st.session_state.audio_data
            if remove_noise:
                processed = apply_noise_reduction(processed, st.session_state.audio_sr, cutoff=noise_cutoff)
            processed = preprocess_audio(
                processed,
                    st.session_state.audio_sr,
                    normalize=normalize,
                remove_noise=False,  # đã xử lý noise ở trên nếu bật
                )
            st.session_state.audio_data = processed
            st.session_state.audio_info = get_audio_info(processed, st.session_state.audio_sr)
            st.success("✅ Đã áp dụng tiền xử lý!")
            st.rerun()
    
    # Visualization
    st.subheader("📊 Visualization")
    viz_option = st.radio(
        "Chọn loại visualization:",
        ["Waveform", "Spectrogram", "Cả hai"],
        horizontal=True
    )
    
    if st.session_state.audio_data is not None:
        if viz_option in ["Waveform", "Cả hai"]:
            fig_wave = plot_waveform(st.session_state.audio_data, st.session_state.audio_sr)
            st.pyplot(fig_wave)
        
        if viz_option in ["Spectrogram", "Cả hai"]:
            fig_spec = plot_spectrogram(st.session_state.audio_data, st.session_state.audio_sr)
            st.pyplot(fig_spec)

