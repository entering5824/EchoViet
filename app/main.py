"""
Hệ thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản
Vietnamese Speech to Text System for Automatic Meeting Transcription
Home Page
"""
import streamlit as st
import os
import sys
import shutil

# Setup FFmpeg và ffprobe alias NGAY ĐẦU FILE (trước mọi import audio)
try:
    import imageio_ffmpeg
    
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    
    # Add PATH
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
    # Tạo alias ffprobe nếu chưa có (imageio-ffmpeg không có ffprobe)
    # ffmpeg binary có thể dùng làm ffprobe alias
    ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe")
    if not os.path.exists(ffprobe_path):
        # Copy ffmpeg để tạo ffprobe alias
        try:
            shutil.copy(ffmpeg_path, ffprobe_path)
        except Exception:
            # Nếu không copy được, có thể đã tồn tại hoặc không có quyền
            pass
except ImportError:
    # Nếu không có imageio-ffmpeg, bỏ qua (có thể đã có system ffmpeg)
    pass

# Add parent directory to path for imports
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, '..')))

# Setup FFmpeg từ imageio-ffmpeg TRƯỚC KHI import các module khác
# Điều này đảm bảo pydub, moviepy, whisper sử dụng đúng ffmpeg path
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

    # Render sidebar with logo
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

    # Navigation radio (main-level to avoid page_link errors)
    pages = [
        "🏠 Home",
        "📤 Upload & Record",
        "🎧 Preprocessing",
        "📝 Transcription",
        "👥 Speaker Diarization",
        "📊 Export & Statistics",
        "🔬 ASR Benchmark",
        "📊 Analysis (Single-file)",
        "📚 Training Info",
        "📡 Streaming",
        "🧩 API Docs",
    ]
    choice = st.radio("🚀 Điều hướng", pages, index=0)

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
    elif choice in fallback_map and fallback_map[choice]:
        runpy.run_path(fallback_map[choice])

    # Footer
    render_footer()


if __name__ == "__main__":
    main()

