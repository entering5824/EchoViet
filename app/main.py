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
        "Designing and Developing a Vietnamese Speech to Text System for Automatic Meeting Transcription",
        None,
        None,
        show_logo=True
    )

    st.markdown(
        """
### 📋 Introduction

This system allows you to convert Vietnamese speech to text automatically and accurately.

### 🚀 Get Started
Use the sidebar to navigate functions or access **Home Dashboard** to see an overview.

### 🔧 Technology
- Whisper
- Librosa, PyDub
- Streamlit
"""
    )
    
    # Link to Dashboard
    if st.button("🏠 Go to Dashboard", type="primary"):
        try:
            st.switch_page("pages/0_🏠_Home_Dashboard.py")
        except:
            st.info("💡 Dashboard page: `pages/0_🏠_Home_Dashboard.py`")

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
