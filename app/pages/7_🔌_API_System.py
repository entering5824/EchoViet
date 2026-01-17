"""
API / System Info Page
API endpoints demo, system information, and integration examples
Demonstrates scalability and deployment readiness
"""
import streamlit as st
import os
import sys
import platform
import json
import requests
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple

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

# Initialize session state
for key, default in (
    ("api_base_url", "http://localhost:8000"),
    ("api_key", ""),
    ("api_request_history", []),
    ("api_health_status", None),
):
    st.session_state.setdefault(key, default)

# Helper functions
def check_api_health(base_url: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """Check API health status"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json(), None
        else:
            return False, None, f"HTTP {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, None, "Không thể kết nối đến API server. Đảm bảo server đang chạy."
    except requests.exceptions.Timeout:
        return False, None, "Timeout khi kết nối đến API server."
    except Exception as e:
        return False, None, f"Lỗi: {str(e)}"

def test_transcribe_api(base_url: str, file_data: bytes, filename: str, api_key: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """Test transcribe API endpoint"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        files = {"file": (filename, file_data)}
        data = {
            "language": "vi",
            "diarization": False
        }
        
        response = requests.post(
            f"{base_url}/transcribe",
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return True, response.json(), None
        else:
            return False, None, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, None, f"Lỗi: {str(e)}"

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔌 API Endpoints", "🧪 API Testing", "💻 System Info", "📚 Integration Examples"])

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
    
    # API Configuration
    st.markdown("---")
    st.markdown("#### ⚙️ API Configuration")
    api_base_url = st.text_input(
        "API Base URL:",
        value=st.session_state.api_base_url,
        help="Base URL của API server (ví dụ: http://localhost:8000)"
    )
    st.session_state.api_base_url = api_base_url
    
    api_key_input = st.text_input(
        "API Key (optional):",
        value=st.session_state.api_key,
        type="password",
        help="API key để xác thực (nếu có)"
    )
    st.session_state.api_key = api_key_input

# ===== TAB 2: API Testing =====
with tab2:
    st.subheader("🧪 API Testing")
    st.caption("Test API endpoints trực tiếp từ giao diện")
    
    # Health Check
    st.markdown("### 🏥 Health Check")
    col_health1, col_health2 = st.columns([3, 1])
    
    with col_health1:
        if st.button("🔍 Kiểm tra trạng thái API", type="primary", use_container_width=True):
            with st.spinner("Đang kiểm tra..."):
                is_healthy, health_data, error = check_api_health(st.session_state.api_base_url)
                st.session_state.api_health_status = {
                    "is_healthy": is_healthy,
                    "data": health_data,
                    "error": error,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.rerun()
    
    with col_health2:
        if st.button("🔄 Auto-refresh", use_container_width=True):
            st.session_state.auto_refresh_health = True
    
    # Display health status
    if st.session_state.api_health_status:
        health_status = st.session_state.api_health_status
        if health_status["is_healthy"]:
            st.success("✅ API đang hoạt động bình thường")
            if health_status["data"]:
                st.json(health_status["data"])
        else:
            st.error(f"❌ API không khả dụng: {health_status['error']}")
    
    # Transcribe API Test
    st.markdown("---")
    st.markdown("### 🎤 Test Transcribe API")
    
    uploaded_file = st.file_uploader(
        "Chọn file audio để test:",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Upload file audio để test API transcribe"
    )
    
    if uploaded_file:
        col_test1, col_test2 = st.columns([1, 1])
        
        with col_test1:
            st.info(f"📁 File: {uploaded_file.name}\n📊 Size: {len(uploaded_file.getvalue()) / 1024:.2f} KB")
        
        with col_test2:
            if st.button("🚀 Test Transcribe", type="primary", use_container_width=True):
                with st.spinner("Đang gửi request đến API..."):
                    file_data = uploaded_file.getvalue()
                    success, result, error = test_transcribe_api(
                        st.session_state.api_base_url,
                        file_data,
                        uploaded_file.name,
                        st.session_state.api_key if st.session_state.api_key else None
                    )
                    
                    # Save to history
                    request_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "endpoint": "/transcribe",
                        "success": success,
                        "result": result if success else None,
                        "error": error if not success else None
                    }
                    if "api_request_history" not in st.session_state:
                        st.session_state.api_request_history = []
                    st.session_state.api_request_history.insert(0, request_entry)
                    
                    if success:
                        st.success("✅ Transcribe thành công!")
                        st.json(result)
                        
                        if result and "text" in result:
                            st.markdown("#### 📝 Transcript Result:")
                            st.text_area("Transcript:", result["text"], height=200, disabled=True)
                    else:
                        st.error(f"❌ Lỗi: {error}")
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.code(error)
    
    # Request History
    if st.session_state.api_request_history:
        st.markdown("---")
        st.markdown("### 📜 Lịch sử Requests")
        
        with st.expander("Xem lịch sử", expanded=False):
            for idx, entry in enumerate(st.session_state.api_request_history[:10]):  # Show last 10
                status_icon = "✅" if entry["success"] else "❌"
                st.markdown(f"**{status_icon} {entry['timestamp']}** - {entry['endpoint']}")
                if not entry["success"] and entry["error"]:
                    st.caption(f"Lỗi: {entry['error']}")
                st.markdown("---")

# ===== TAB 3: System Info =====
with tab3:
    st.subheader("💻 System Information")
    
    # System info cards
    st.markdown("#### 🐍 Python Environment")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{sys.version.split()[0]}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Python Version</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{platform.system()}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Platform</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h3 style="margin:0; color: #1f4e79;">{platform.machine()}</h3>
            <p style="margin:0.5rem 0 0 0; color: #666;">Architecture</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption(f"Python Executable: {sys.executable}")
    
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
    st.markdown("#### 🖥️ Device Information")
    
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        device_name = "CUDA" if has_cuda else "CPU"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="margin:0; color: #1f4e79;">{device_name}</h3>
                <p style="margin:0.5rem 0 0 0; color: #666;">Device</p>
            </div>
            """, unsafe_allow_html=True)
            
            if has_cuda:
                st.markdown(f"""
                <div class="stat-box">
                    <h3 style="margin:0; color: #1f4e79;">{torch.version.cuda}</h3>
                    <p style="margin:0.5rem 0 0 0; color: #666;">CUDA Version</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="stat-box">
                    <h3 style="margin:0; color: #1f4e79;">{torch.cuda.device_count()}</h3>
                    <p style="margin:0.5rem 0 0 0; color: #666;">GPU Count</p>
                </div>
                """, unsafe_allow_html=True)
                if torch.cuda.device_count() > 0:
                    st.markdown(f"""
                    <div class="stat-box">
                        <h3 style="margin:0; color: #1f4e79; font-size: 1rem;">{torch.cuda.get_device_name(0)}</h3>
                        <p style="margin:0.5rem 0 0 0; color: #666;">GPU Name</p>
                    </div>
                    """, unsafe_allow_html=True)
        with col2:
            if has_cuda:
                cudnn_version = torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else "N/A"
                st.markdown(f"""
                <div class="stat-box">
                    <h3 style="margin:0; color: #1f4e79;">{cudnn_version}</h3>
                    <p style="margin:0.5rem 0 0 0; color: #666;">cuDNN Version</p>
                </div>
                """, unsafe_allow_html=True)
    except ImportError:
        st.info("💡 PyTorch không có sẵn")
    
    # Memory info
    st.markdown("---")
    st.markdown("#### 💾 Memory Information")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="margin:0; color: #1f4e79;">{memory.total / (1024**3):.2f} GB</h3>
                <p style="margin:0.5rem 0 0 0; color: #666;">Total Memory</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="margin:0; color: #1f4e79;">{memory.available / (1024**3):.2f} GB</h3>
                <p style="margin:0.5rem 0 0 0; color: #666;">Available Memory</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-box">
                <h3 style="margin:0; color: #1f4e79;">{memory.percent}%</h3>
                <p style="margin:0.5rem 0 0 0; color: #666;">Memory Usage</p>
            </div>
            """, unsafe_allow_html=True)
    except ImportError:
        st.info("💡 psutil không có sẵn")
    
    # FFmpeg info
    st.markdown("---")
    st.markdown("#### 🎬 FFmpeg Status")
    ffmpeg_info = get_ffmpeg_info()
    
    if ffmpeg_info.get("available", False):
        st.success("✅ FFmpeg đã được cài đặt")
        st.json(ffmpeg_info)
    else:
        st.warning("⚠️ FFmpeg chưa được cài đặt hoặc không tìm thấy")
        st.json(ffmpeg_info)

# ===== TAB 4: Integration Examples =====
with tab4:
    st.subheader("📚 Integration Examples")
    st.caption("Code examples để tích hợp API vào các ứng dụng")
    
    # Code generator
    st.markdown("### 🔧 Code Generator")
    code_language = st.selectbox(
        "Chọn ngôn ngữ:",
        ["Python", "JavaScript/Node.js", "cURL", "PHP", "Java"],
        help="Chọn ngôn ngữ để generate code example"
    )
    
    # Generate code based on selection
    base_url = st.session_state.api_base_url
    api_key = st.session_state.api_key if st.session_state.api_key else "YOUR_API_KEY"
    
    if code_language == "Python":
        python_code = f"""
import requests

# Transcribe audio
url = "{base_url}/transcribe"
headers = {{"Authorization": "Bearer {api_key}"}}

with open("audio.wav", "rb") as f:
    files = {{"file": f}}
    data = {{
        "language": "vi",
        "diarization": False
    }}
    response = requests.post(url, headers=headers, files=files, data=data)
    
if response.status_code == 200:
    result = response.json()
    print(f"Transcript: {{result.get('text', '')}}")
else:
    print(f"Error: {{response.status_code}} - {{response.text}}")
"""
        st.code(python_code, language="python")
    
    elif code_language == "JavaScript/Node.js":
        js_code = f"""
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('audio.wav'));
form.append('language', 'vi');
form.append('diarization', 'false');

axios.post('{base_url}/transcribe', form, {{
    headers: {{
        ...form.getHeaders(),
        'Authorization': 'Bearer {api_key}'
    }}
}})
.then(response => {{
    console.log('Transcript:', response.data.text);
}})
.catch(error => {{
    console.error('Error:', error.response?.data || error.message);
}});
"""
        st.code(js_code, language="javascript")
    
    elif code_language == "cURL":
        curl_code = f"""
curl -X POST "{base_url}/transcribe" \\
  -H "Authorization: Bearer {api_key}" \\
  -F "file=@audio.wav" \\
  -F "language=vi" \\
  -F "diarization=false"
"""
        st.code(curl_code, language="bash")
    
    elif code_language == "PHP":
        php_code = f"""
<?php
$url = "{base_url}/transcribe";
$file_path = "audio.wav";

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Authorization: Bearer {api_key}"
]);

$file = new CURLFile($file_path);
$data = [
    "file" => $file,
    "language" => "vi",
    "diarization" => "false"
];
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code == 200) {{
    $result = json_decode($response, true);
    echo "Transcript: " . $result['text'];
}} else {{
    echo "Error: " . $response;
}}
?>
"""
        st.code(php_code, language="php")
    
    elif code_language == "Java":
        java_code = f"""
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.Files;

public class TranscribeAPI {{
    public static void main(String[] args) throws Exception {{
        String url = "{base_url}/transcribe";
        String apiKey = "{api_key}";
        File audioFile = new File("audio.wav");
        
        String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Authorization", "Bearer " + apiKey);
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        conn.setDoOutput(true);
        
        try (OutputStream os = conn.getOutputStream();
             PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, "UTF-8"), true)) {{
            
            writer.append("--").append(boundary).append("\\r\\n");
            writer.append("Content-Disposition: form-data; name=\\"file\\"; filename=\\"").append(audioFile.getName()).append("\\"\\r\\n");
            writer.append("Content-Type: audio/wav\\r\\n\\r\\n").flush();
            Files.copy(audioFile.toPath(), os);
            os.flush();
            writer.append("\\r\\n").flush();
            
            writer.append("--").append(boundary).append("\\r\\n");
            writer.append("Content-Disposition: form-data; name=\\"language\\"\\r\\n\\r\\n");
            writer.append("vi\\r\\n").flush();
            
            writer.append("--").append(boundary).append("--\\r\\n").flush();
        }}
        
        int responseCode = conn.getResponseCode();
        if (responseCode == 200) {{
            BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
            String response = in.readLine();
            System.out.println("Transcript: " + response);
        }} else {{
            System.out.println("Error: " + responseCode);
        }}
    }}
}}
"""
        st.code(java_code, language="java")
    
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

