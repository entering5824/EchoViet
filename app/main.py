"""
Hệ thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản
Vietnamese Speech to Text System for Automatic Meeting Transcription
Home Page
"""
import streamlit as st
import os
import sys

# Add parent directory to path for imports
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, '..')))

# Setup static FFmpeg trước khi import các module khác
from core.audio.ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=True)

# Cấu hình trang
st.set_page_config(
    page_title="Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css
from app.components.footer import render_footer
import runpy

# Import internal pages for manual navigation
from app.pages import Home as HomePage
from app.pages import Analysis as AnalysisPage
from app.pages import Training_Info as TrainingInfoPage


def render_home():
    """Render the original home content."""
    st.markdown(
        '<div class="main-header">Designing and Developing a Vietnamese Speech to Text System for Automatic Meeting Transcription</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
### 📋 Giới thiệu

Hệ thống này cho phép bạn chuyển đổi giọng nói tiếng Việt thành văn bản một cách tự động và chính xác.
Hệ thống hỗ trợ:

- ✅ Upload file audio (WAV, MP3, FLAC)
- ✅ Ghi âm trực tiếp từ microphone
- ✅ Xử lý audio dài (meetings, interviews)
- ✅ Visualize waveform và spectrogram
- ✅ Tiền xử lý audio (normalize, noise reduction)
- ✅ Transcription với timestamps
- ✅ Speaker diarization (phân biệt người nói)
- ✅ Export ra TXT, DOCX, PDF
- ✅ Thống kê chi tiết
- ✅ So sánh mô hình ASR (Whisper vs PhoWhisper)

### 🚀 Bắt đầu

Sử dụng sidebar để điều hướng đến các chức năng:

1. **📤 Upload & Record**: Upload file audio hoặc ghi âm
2. **🎧 Preprocessing**: Tiền xử lý và visualization audio
3. **📝 Transcription**: Chọn model và transcribe audio
4. **👥 Speaker Diarization**: Phân biệt người nói
5. **📊 Export & Statistics**: Xem thống kê và export transcript
6. **🔬 ASR Benchmark**: So sánh chất lượng mô hình

### 🔧 Công nghệ sử dụng

- **Speech Recognition**: OpenAI Whisper, PhoWhisper (VinAI Research)
- **Audio Processing**: Librosa, PyDub, SoundFile
- **Visualization**: Matplotlib, Seaborn
- **Framework**: Streamlit
- **Transformers**: HuggingFace Transformers (cho PhoWhisper)

### 📝 Model Selection

- **Whisper**: Mô hình đa ngôn ngữ, hỗ trợ nhiều ngôn ngữ
- **PhoWhisper**: 🌟 Tối ưu đặc biệt cho tiếng Việt, độ chính xác cao hơn
"""
    )


def main():
    # Apply custom CSS
    apply_custom_css()

    # Render sidebar with logo and navigation (radio stored in session_state)
    render_sidebar()

    # Initialize session state
    for key, default in (
        ("audio_data", None),
        ("audio_sr", None),
        ("transcript_result", None),
        ("transcript_text", ""),
        ("audio_info", None),
    ):
        if key not in st.session_state:
            st.session_state[key] = default

    # Routing dựa trên lựa chọn trong sidebar
    choice = st.session_state.get("nav_selection", "🏠 Home")

    fallback_map = {
        "🏠 Home": None,
        "📤 Upload & Record": os.path.join(BASE_DIR, "pages", "1_📤_Upload_Record.py"),
        "🎧 Preprocessing": os.path.join(BASE_DIR, "pages", "2_🎧_Preprocessing.py"),
        "📝 Transcription": os.path.join(BASE_DIR, "pages", "3_📝_Transcription.py"),
        "👥 Speaker Diarization": os.path.join(BASE_DIR, "pages", "4_👥_Speaker_Diarization.py"),
        "📊 Export & Statistics": os.path.join(BASE_DIR, "pages", "5_📊_Export_Statistics.py"),
        "🔬 ASR Benchmark": os.path.join(BASE_DIR, "pages", "6_🔬_ASR_Benchmark.py"),
        "📊 Analysis (Single-file)": os.path.join(BASE_DIR, "pages", "Analysis.py"),
        "📚 Training Info": None,  # handled below
        "📡 Streaming": os.path.join(BASE_DIR, "pages", "Streaming.py"),
        "🧩 API Docs": os.path.join(BASE_DIR, "pages", "API_Docs.py"),
    }

    if choice == "🏠 Home":
        render_home()
    elif choice == "📊 Analysis":
        AnalysisPage.show()
    elif choice == "📚 Training Info":
        TrainingInfoPage.show()
    elif choice in fallback_map and fallback_map[choice]:
        runpy.run_path(fallback_map[choice])

    # Footer
    render_footer()


if __name__ == "__main__":
    main()

