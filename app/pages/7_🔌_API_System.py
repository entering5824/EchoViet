"""
API / System Info Page
API endpoints demo, system information, and integration examples
Demonstrates scalability and deployment readiness
"""
import streamlit as st
import os
import sys
import platform

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from core.audio.ffmpeg_setup import get_ffmpeg_info

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="API / System Info - Vietnamese Speech to Text",
    page_icon="🔌",
    layout="wide"
)

render_page_header("API / System Information", "API endpoints, system info, and integration examples", "🔌")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔌 API Endpoints", "💻 System Info", "📚 Integration Examples"])

# ===== TAB 1: API Endpoints =====
with tab1:
    st.subheader("🔌 API Endpoints (Demo)")
    st.caption("API endpoints for integration and deployment")
    
    # API Overview
    st.markdown("""
    ### API Overview
    
    The system supports RESTful API to integrate into other applications.
    API endpoints use FastAPI framework.
    """)
    
    # Endpoint: Transcribe
    st.markdown("---")
    st.markdown("#### POST `/api/transcribe`")
    st.caption("Transcribe audio file")
    
    with st.expander("Request Example"):
        st.code("""
POST /api/transcribe
Content-Type: multipart/form-data

{
    "file": <audio_file>,
    "model": "whisper",
    "quality": "fast" | "balanced" | "accurate",
    "language": "vi"
}
        """, language="json")
    
    with st.expander("Response Example"):
        st.code("""
{
    "status": "success",
    "transcript": "Đây là nội dung transcript...",
    "segments": [
        {
            "start": 0.0,
            "end": 5.2,
            "text": "Đây là nội dung transcript..."
        }
    ],
    "metadata": {
        "duration": 120.5,
        "word_count": 250,
        "processing_time": 15.3
    }
}
        """, language="json")
    
    # Endpoint: Health Check
    st.markdown("---")
    st.markdown("#### GET `/api/health`")
    st.caption("Health check endpoint")
    
    with st.expander("Response Example"):
        st.code("""
{
    "status": "healthy",
    "version": "1.0.0",
    "models_loaded": ["whisper"]
}
        """, language="json")
    
    # Authentication
    st.markdown("---")
    st.markdown("#### Authentication")
    st.info("""
    **API Key Authentication:**
    - Include API key in header: `Authorization: Bearer <your_api_key>`
    - Get API key from settings page
    - Rate limiting: 100 requests/hour (default)
    """)

# ===== TAB 2: System Info =====
with tab2:
    st.subheader("💻 System Information")
    
    # Python version
    st.markdown("#### Python Environment")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Python Version", sys.version.split()[0])
        st.metric("Platform", platform.system())
        st.metric("Architecture", platform.machine())
    
    with col2:
        st.metric("Python Executable", sys.executable)
    
    # Library versions
    st.markdown("---")
    st.markdown("#### Library Versions")
    
    libraries = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "whisper": "OpenAI Whisper",
        "streamlit": "Streamlit",
        "librosa": "Librosa",
        "soundfile": "SoundFile"
    }
    
    library_versions = {}
    for lib, name in libraries.items():
        try:
            module = __import__(lib)
            version = getattr(module, "__version__", "Unknown")
            library_versions[name] = version
        except ImportError:
            library_versions[name] = "Not installed"
    
    import pandas as pd
    try:
        df_libs = pd.DataFrame({
            "Library": list(library_versions.keys()),
            "Version": list(library_versions.values())
        })
        st.dataframe(df_libs, use_container_width=True, hide_index=True)
    except ImportError:
        for lib, version in library_versions.items():
            st.write(f"**{lib}**: {version}")
    
    # Device info
    st.markdown("---")
    st.markdown("#### Device Information")
    
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        device_name = "CUDA" if has_cuda else "CPU"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Device", device_name)
            if has_cuda:
                st.metric("CUDA Version", torch.version.cuda)
                st.metric("GPU Count", torch.cuda.device_count())
                if torch.cuda.device_count() > 0:
                    st.metric("GPU Name", torch.cuda.get_device_name(0))
        with col2:
            if has_cuda:
                st.metric("cuDNN Version", torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else "N/A")
    except ImportError:
        st.info("💡 PyTorch not available")
    
    # Memory info
    st.markdown("---")
    st.markdown("#### Memory Information")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Memory", f"{memory.total / (1024**3):.2f} GB")
        
        with col2:
            st.metric("Available Memory", f"{memory.available / (1024**3):.2f} GB")
        
        with col3:
            st.metric("Memory Usage", f"{memory.percent}%")
    except ImportError:
        st.info("💡 psutil not available")
    
    # FFmpeg info
    st.markdown("---")
    st.markdown("#### FFmpeg Status")
    ffmpeg_info = get_ffmpeg_info()
    st.json(ffmpeg_info)

# ===== TAB 3: Integration Examples =====
with tab3:
    st.subheader("📚 Integration Examples")
    st.caption("Code examples để tích hợp API vào các ứng dụng")
    
    # cURL example
    st.markdown("#### cURL Example")
    st.code("""
curl -X POST "http://localhost:8000/api/transcribe" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "file=@audio.wav" \\
  -F "model=whisper" \\
  -F "quality=balanced" \\
  -F "language=vi"
    """, language="bash")
    
    # Python example
    st.markdown("---")
    st.markdown("#### Python Client Example")
    st.code("""
import requests

# Transcribe audio
url = "http://localhost:8000/api/transcribe"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

with open("audio.wav", "rb") as f:
    files = {"file": f}
    data = {
        "model": "whisper",
        "quality": "balanced",
        "language": "vi"
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    
result = response.json()
print(f"Transcript: {result['transcript']}")
print(f"Word count: {result['metadata']['word_count']}")
    """, language="python")
    
    # JavaScript example
    st.markdown("---")
    st.markdown("#### JavaScript/Node.js Example")
    st.code("""
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('audio.wav'));
form.append('model', 'whisper');
form.append('quality', 'balanced');
form.append('language', 'vi');

axios.post('http://localhost:8000/api/transcribe', form, {
    headers: {
        ...form.getHeaders(),
        'Authorization': 'Bearer YOUR_API_KEY'
    }
})
.then(response => {
    console.log('Transcript:', response.data.transcript);
})
.catch(error => {
    console.error('Error:', error);
});
    """, language="javascript")
    
    # Webhook example
    st.markdown("---")
    st.markdown("#### Webhook Integration")
    st.info("""
    **Webhook Support:**
    - Configure webhook URL in settings
    - Receive transcription results via POST request
    - Useful for async processing and integrations
    """)

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("pages/0_🏠_Home_Dashboard.py")

# ===== Footer =====
render_footer()

