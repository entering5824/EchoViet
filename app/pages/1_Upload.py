"""
Upload: upload audio file, preview and prepare for transcription.
"""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.audio_player import render_audio_player
from services.audio_service import get_audio_info, ensure_ffmpeg, load_audio

ensure_ffmpeg(silent=True)
apply_custom_css()
st.set_page_config(page_title="Upload - Vietnamese Speech to Text", page_icon="📤", layout="wide")

def init_state():
    for k, v in {"audio_data": None, "audio_sr": None, "audio_info": None, "audio_ready": False}.items():
        st.session_state.setdefault(k, v)

init_state()
render_page_header("Upload Audio", "Upload file (WAV, MP3, FLAC, M4A, OGG) to transcribe", "📤")

uploaded_file = st.file_uploader(
    "Chọn file âm thanh",
    type=["wav", "mp3", "flac", "m4a", "ogg"],
    help="Định dạng hỗ trợ: WAV, MP3, FLAC, M4A, OGG",
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

if st.session_state.get("audio_ready") and st.session_state.get("audio_data") is not None:
    render_audio_player(st.session_state.audio_data, st.session_state.audio_sr)
    info = st.session_state.get("audio_info") or {}
    if info:
        st.caption(f"Duration: {info.get('duration', 0):.1f}s | Sample rate: {info.get('sample_rate')} | Samples: {info.get('samples')}")

render_footer()
