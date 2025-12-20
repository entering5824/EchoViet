"""
Audio Input & Preparation Page
Upload / record audio, overview, visualization, basic preprocessing
"""
import streamlit as st
import os
import sys
import tempfile

# ================== PATH SETUP ==================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from app.components.audio_visualizer import render_audio_visualization
from core.audio.audio_processor import (
    load_audio,
    get_audio_info,
    preprocess_audio,
)
from core.audio.ffmpeg_setup import ensure_ffmpeg

# ================== ENV SETUP ==================
ensure_ffmpeg(silent=True)
apply_custom_css()

st.set_page_config(
    page_title="Audio Input - Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide",
)

# ================== SESSION STATE ==================
def init_state():
    defaults = {
        "audio_data": None,
        "audio_sr": None,
        "audio_info": None,
        "audio_ready": False,
        "audio_source": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()

# ================== HEADER ==================
st.header("🎤 Audio Input & Preparation")
st.caption("Upload hoặc ghi âm audio, kiểm tra và chuẩn bị cho ASR pipeline")

# ================== INPUT ==================
tab_upload, tab_record = st.tabs(["📤 Upload", "🎙️ Record"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Audio file (wav, mp3, flac, m4a, ogg)",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
    )

    if uploaded_file:
        with st.spinner("Loading audio..."):
            audio_data, sr = load_audio(uploaded_file)

        if audio_data is None:
            st.error("❌ Không thể load audio")
        else:
            st.session_state.audio_data = audio_data
            st.session_state.audio_sr = sr
            st.session_state.audio_info = get_audio_info(audio_data, sr)
            st.session_state.audio_ready = False
            st.session_state.audio_source = uploaded_file
            st.success("✅ Audio loaded")

with tab_record:
    st.info("Ghi âm trực tiếp từ trình duyệt (tùy chọn)")

    try:
        from audio_recorder_streamlit import audio_recorder

        audio_bytes = audio_recorder()

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                audio_data, sr = load_audio(tmp_path)
                if audio_data is not None:
                    st.session_state.audio_data = audio_data
                    st.session_state.audio_sr = sr
                    st.session_state.audio_info = get_audio_info(audio_data, sr)
                    st.session_state.audio_ready = False
                    st.session_state.audio_source = audio_bytes
                    st.success("✅ Audio recorded")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    except ImportError:
        st.warning("Cài đặt audio-recorder-streamlit để dùng chức năng ghi âm")

# ================== OVERVIEW ==================
if st.session_state.audio_data is not None:
    st.divider()
    st.subheader("📄 Audio Overview")

    info = st.session_state.audio_info
    c1, c2, c3 = st.columns(3)
    c1.metric("Duration", f"{info['duration']:.1f}s")
    c2.metric("Sample Rate", f"{st.session_state.audio_sr} Hz")
    c3.metric("Samples", f"{len(st.session_state.audio_data):,}")

    if isinstance(st.session_state.audio_source, bytes):
        st.audio(st.session_state.audio_source, format="audio/wav")
    else:
        st.audio(st.session_state.audio_source)

    # ================== VISUALIZATION ==================
    with st.expander("📊 Waveform & Visualization"):
        render_audio_visualization(
            st.session_state.audio_data,
            st.session_state.audio_sr,
        )

    # ================== PREPROCESSING ==================
    st.divider()
    st.subheader("🔧 Basic Preprocessing")

    col1, col2 = st.columns(2)

    with col1:
        normalize = st.checkbox("Normalize amplitude", value=True)
        trim_silence = st.checkbox("Trim silence", value=False)

    with col2:
        target_sr = st.selectbox("Target sample rate", [16000, 22050, 44100], index=0)

    if st.button("Apply preprocessing", type="primary"):
        with st.spinner("Processing audio..."):
            audio = preprocess_audio(
                st.session_state.audio_data,
                st.session_state.audio_sr,
                normalize=normalize,
                remove_noise=False,
            )

            if target_sr != st.session_state.audio_sr:
                import librosa
                audio = librosa.resample(audio, st.session_state.audio_sr, target_sr)
                st.session_state.audio_sr = target_sr

            if trim_silence:
                import librosa
                audio, _ = librosa.effects.trim(audio)

            st.session_state.audio_data = audio
            st.session_state.audio_info = get_audio_info(audio, st.session_state.audio_sr)
            st.session_state.audio_ready = True

        st.success("✅ Audio ready for transcription")

    # ================== NEXT STEP ==================
    st.divider()
    st.info("🎯 Audio đã sẵn sàng cho bước Transcription & Speaker Diarization")

    if st.button("➡️ Go to Transcription", type="primary", use_container_width=True):
        st.switch_page("pages/2_📝_Transcription.py")

else:
    st.info("👆 Upload hoặc ghi âm audio để bắt đầu")
