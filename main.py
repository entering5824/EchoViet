"""
Hệ thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản
Vietnamese Speech to Text System for Automatic Meeting Transcription
Main Entry Point for Streamlit Cloud
"""
import streamlit as st
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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

# Import components
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

# Initialize session state
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'audio_sr' not in st.session_state:
    st.session_state.audio_sr = None
if 'transcript_result' not in st.session_state:
    st.session_state.transcript_result = None
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""
if 'audio_info' not in st.session_state:
    st.session_state.audio_info = None

# ========== HOME PAGE ==========
st.markdown('<div class="main-header">Designing and Developing a Vietnamese Speech to Text System for Automatic Meeting Transcription</div>', 
            unsafe_allow_html=True)

st.markdown("""
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
7. **🏠 Home**: Giới thiệu đề tài
8. **📊 Analysis**: Phân tích audio & Speech-to-Text với chunking
9. **📚 Training Info**: Thông tin về mô hình và training

### 🔧 Công nghệ sử dụng

- **Speech Recognition**: OpenAI Whisper, PhoWhisper (VinAI Research)
- **Audio Processing**: Librosa, PyDub, SoundFile
- **Visualization**: Matplotlib, Seaborn
- **Framework**: Streamlit
- **Transformers**: HuggingFace Transformers (cho PhoWhisper)

### 📝 Model Selection

- **Whisper**: Mô hình đa ngôn ngữ, hỗ trợ nhiều ngôn ngữ
- **PhoWhisper**: 🌟 Tối ưu đặc biệt cho tiếng Việt, độ chính xác cao hơn
""")

# Import footer component
from app.components.footer import render_footer

# ===== FOOTER =====
render_footer()
