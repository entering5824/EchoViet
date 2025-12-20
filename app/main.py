"""
Hệ thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản
Vietnamese Speech to Text System for Automatic Meeting Transcription
Home Page
"""

import os
import sys
import streamlit as st

# =========================
# 1️⃣ CONFIG FFmpeg (BẮT BUỘC TRƯỚC WHISPER)
# =========================
# Thêm parent directory vào path để import core modules
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, '..')))

# Setup FFmpeg tự động từ imageio-ffmpeg
from core.audio.ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=False)  # Hiển thị thông báo nếu có lỗi

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

from app.components.layout import apply_custom_css
from app.components.footer import render_footer
from core.auth.session import init_session

# =========================
# 4️⃣ HOME PAGE (Legacy - redirect to Dashboard)
# =========================
def render_home():
    # Redirect to new Dashboard if available
    st.markdown(
        '<div class="main-header">'
        'Designing and Developing a Vietnamese Speech to Text System '
        'for Automatic Meeting Transcription'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
### 📋 Giới thiệu

Hệ thống này cho phép bạn chuyển đổi giọng nói tiếng Việt thành văn bản một cách tự động và chính xác.

### 🚀 Bắt đầu
Sử dụng sidebar để điều hướng các chức năng hoặc truy cập **Home Dashboard** để xem tổng quan.

### 🔧 Công nghệ
- Whisper / PhoWhisper
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


if __name__ == "__main__":
    main()
