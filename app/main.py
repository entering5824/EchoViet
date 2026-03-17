"""
Vietnamese Speech to Text System for Automatic Meeting Transcription
Home Page
"""

import os
import sys
import streamlit as st

# =========================
# 1️⃣ CONFIG FFmpeg (REQUIRED BEFORE WHISPER)
# =========================
# Add parent directory to path to import core modules
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, '..')))

# Setup FFmpeg automatically from imageio-ffmpeg
from core.audio.ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=False)  # Show message if there's an error

# =========================
# 2️⃣ STREAMLIT CONFIG (PHẢI ĐỨNG SỚM)
# =========================
st.set_page_config(
    page_title="Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# 3️⃣ PROJECT IMPORTS
# =========================
# BASE_DIR đã được set ở trên

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from core.auth.session import init_session

# =========================
# 4️⃣ HOME PAGE (Legacy - redirect to Dashboard)
# =========================
def render_home():
    # Redirect to new Dashboard if available
    render_page_header(
        "Vietnamese Speech-to-Text for Meeting Transcription",
        None,
    )

    st.markdown(
        """
### 📋 Introduction

Vietnamese Speech-to-Text for Meeting Transcription is a system that converts Vietnamese meeting audio into accurate text transcripts automatically, enabling searchable meeting records and reducing manual note-taking.
"""
    )
    
    # Link to Upload (main flow)
    if st.button("📤 Bắt đầu — Upload / Record", type="primary"):
        try:
            st.switch_page("pages/1_Upload_Record.py")
        except Exception:
            st.info("💡 Trang: `pages/1_Upload_Record.py`")

# =========================
# 5️⃣ MAIN
# =========================
def main():
    # Initialize session and auth
    init_session()
    
    apply_custom_css()

    # Initialize session state (legacy - now handled by init_session)
    for key, default in (
        ("audio_data", None),
        ("audio_sr", None),
        ("transcript_result", None),
        ("transcript_text", ""),
        ("audio_info", None),
    ):
        st.session_state.setdefault(key, default)

    render_home()
    render_footer()

# Run main function
main()
