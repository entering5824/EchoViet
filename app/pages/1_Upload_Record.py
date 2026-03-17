"""
Upload / Record: upload audio file hoặc ghi âm trực tiếp từ trình duyệt.
"""
import os
import sys
import io
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.audio_player import render_audio_player
from services.audio_service import get_audio_info, ensure_ffmpeg, load_audio

ensure_ffmpeg(silent=True)
apply_custom_css()
st.set_page_config(page_title="Upload / Record - Vietnamese Speech to Text", page_icon="📤", layout="wide")

def init_state():
    for k, v in {
        "audio_data": None,
        "audio_sr": None,
        "audio_info": None,
        "audio_ready": False,
        "recorded_audio_bytes": None,
        "recorded_sr": 16000,
        "recorded_audio_array": None,
    }.items():
        st.session_state.setdefault(k, v)

init_state()
render_page_header("Upload / Record", "Upload file audio hoặc ghi âm trực tiếp từ trình duyệt", "📤")

tab_upload, tab_record = st.tabs(["📤 Upload file", "🎙️ Ghi âm"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Chọn file âm thanh",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Định dạng hỗ trợ: WAV, MP3, FLAC, M4A, OGG",
        key="upload_file",
    )
    if uploaded_file:
        max_mb = 200
        size_mb = uploaded_file.size / (1024 * 1024)
        if size_mb > max_mb:
            st.error(f"File quá lớn ({size_mb:.1f}MB). Tối đa {max_mb}MB.")
        else:
            with st.spinner("Đang tải audio..."):
                audio_data, sr = load_audio(uploaded_file)
                if audio_data is None:
                    st.error("Không thể đọc file. Kiểm tra định dạng hoặc file có bị lỗi.")
                else:
                    st.session_state.audio_data = audio_data
                    st.session_state.audio_sr = sr
                    st.session_state.audio_info = get_audio_info(audio_data, sr)
                    st.session_state.audio_ready = True
                    dur = st.session_state.audio_info.get("duration", 0)
                    st.success(f"Đã tải xong. ({size_mb:.1f}MB, {dur:.1f}s)")

with tab_record:
    st.info("🎙️ Nhấn nút để bắt đầu/dừng ghi âm. Cần cài: pip install audio-recorder-streamlit")
    try:
        from audio_recorder_streamlit import audio_recorder
        import numpy as np
        import soundfile as sf

        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#6c757d",
            icon_name="microphone",
            icon_size="2x",
            key="recorder",
        )
        if audio_bytes:
            st.session_state.recorded_audio_bytes = audio_bytes
            buf = io.BytesIO(audio_bytes)
            data, sr = sf.read(buf)
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            st.session_state.recorded_audio_array = data
            st.session_state.recorded_sr = sr
            st.session_state.audio_data = data
            st.session_state.audio_sr = sr
            st.session_state.audio_info = get_audio_info(data, sr)
            st.session_state.audio_ready = True
            st.success("Đã ghi xong. Bạn có thể phát và chuyển sang bước Transcription.")
    except ImportError:
        st.warning("Cài đặt: pip install audio-recorder-streamlit để dùng tính năng ghi âm.")
        if st.session_state.get("recorded_audio_array") is not None:
            st.session_state.audio_data = st.session_state.recorded_audio_array
            st.session_state.audio_sr = st.session_state.recorded_sr
            st.session_state.audio_info = get_audio_info(
                st.session_state.recorded_audio_array, st.session_state.recorded_sr
            )
            st.session_state.audio_ready = True

if st.session_state.get("audio_ready") and st.session_state.get("audio_data") is not None:
    st.divider()
    st.subheader("Audio đã chọn")
    render_audio_player(st.session_state.audio_data, st.session_state.audio_sr)
    info = st.session_state.get("audio_info") or {}
    if info:
        st.caption(f"Duration: {info.get('duration', 0):.1f}s | Sample rate: {info.get('sample_rate')} | Samples: {info.get('samples')}")
    if st.button("Tiếp tục → Transcription", type="primary"):
        st.switch_page("pages/2_Transcription.py")

render_footer()
