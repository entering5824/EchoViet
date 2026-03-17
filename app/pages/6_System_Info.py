"""
System Info: thông tin FFmpeg, models, hệ thống.
"""
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer

apply_custom_css()
st.set_page_config(page_title="System Info - Vietnamese Speech to Text", page_icon="ℹ️", layout="wide")

render_page_header("System Info", "Thông tin hệ thống, FFmpeg và models", "ℹ️")

st.subheader("ASR Models")
st.caption("Whisper, Faster-Whisper, Distil-Whisper, Whisper Large v3 Turbo, Parakeet, Moonshine")

st.subheader("Translation Models")
st.caption("NLLB, SeamlessM4T, M2M100")

st.subheader("Pipeline")
st.caption("Upload / Record → Transcription → Transcript → Analytics → Export")

st.subheader("FFmpeg")
try:
    from services.audio_service import get_ffmpeg_info
    ok, msg = get_ffmpeg_info()
    st.write(msg)
except Exception:
    st.write("N/A")

st.subheader("Python")
import platform
st.code(f"Python {platform.python_version()} | {platform.system()} {platform.release()}")

render_footer()
