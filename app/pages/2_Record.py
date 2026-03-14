"""
Record: record audio from browser for transcription.
"""
import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from app.components.audio_player import render_audio_player
from services.audio_service import get_audio_info, ensure_ffmpeg

ensure_ffmpeg(silent=True)
apply_custom_css()
st.set_page_config(page_title="Record - Vietnamese Speech to Text", page_icon="🎙️", layout="wide")

st.session_state.setdefault("recorded_audio_bytes", None)
st.session_state.setdefault("recorded_sr", 16000)
st.session_state.setdefault("recorded_audio_array", None)

render_page_header("Ghi âm", "Ghi âm trực tiếp từ trình duyệt", "🎙️")

st.info("🎙️ Nhấn nút để bắt đầu/dừng ghi âm. Cần cài thêm: pip install audio-recorder-streamlit")

try:
    from audio_recorder_streamlit import audio_recorder
    import numpy as np
    import soundfile as sf
    import io

    audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#6c757d", icon_name="microphone", icon_size="2x")
    if audio_bytes:
        st.session_state.recorded_audio_bytes = audio_bytes
        buf = io.BytesIO(audio_bytes)
        data, sr = sf.read(buf)
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        st.session_state.recorded_audio_array = data
        st.session_state.recorded_sr = sr
        st.success("Đã ghi xong. Bạn có thể phát và chuyển sang bước Transcription.")
except ImportError:
    st.warning("Cài đặt: pip install audio-recorder-streamlit để dùng tính năng ghi âm.")
    audio_bytes = None

if st.session_state.get("recorded_audio_array") is not None:
    render_audio_player(st.session_state.recorded_audio_array, st.session_state.recorded_sr)
    info = get_audio_info(st.session_state.recorded_audio_array, st.session_state.recorded_sr)
    st.caption(f"Duration: {info.get('duration', 0):.1f}s")

render_footer()
