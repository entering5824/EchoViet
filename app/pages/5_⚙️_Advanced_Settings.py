"""
Advanced Settings Page
Cấu hình nâng cao cho technical users - Model sizes, hyperparameters, pipeline config
"""
import streamlit as st
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from core.utils.settings_manager import load_settings, save_settings, load_settings_from_file
from core.asr.model_registry import get_all_models, get_model_info
from config import config

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="Advanced Settings - Vietnamese Speech to Text",
    page_icon="⚙️",
    layout="wide"
)

st.header("⚙️ Advanced Settings & Configuration")
st.caption("Trang này dành cho người dùng kỹ thuật. Thay đổi settings có thể ảnh hưởng đến hiệu suất và độ chính xác.")

# Warning for non-technical users
st.warning("⚠️ Trang này dành cho người dùng kỹ thuật. Thay đổi settings có thể ảnh hưởng đến hiệu suất và độ chính xác.")

# Load current settings
current_settings = load_settings()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🤖 Model Config", "⚡ Inference", "💾 Resource", 
    "🔧 Pipeline", "🚀 Deployment", "🐛 Debug"
])

with tab1:
    st.subheader("Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Model selection with size
        all_models = get_all_models()
        model_ids = list(all_models.keys())
        
        selected_model_id = st.selectbox(
            "ASR Model",
            model_ids,
            help="Chọn model ASR"
        )
        
        model_info = get_model_info(selected_model_id)
        
        # Model size selection (technical detail)
        if model_info.get("sizes"):
            model_size = st.selectbox(
                "Model Size",
                model_info["sizes"],
                index=model_info["sizes"].index(model_info.get("default_size", model_info["sizes"][0])),
                help="Kích thước model: tiny (nhanh, ít chính xác) → large (chậm, chính xác nhất)"
            )
            st.caption(f"💡 Model size được chọn: {model_size}")
        
        whisper_model_path = st.text_input(
            "Whisper Model Path",
            value=current_settings["model"]["whisper_model_path"],
            help="Đường dẫn đến Whisper model (để trống để dùng default)"
        )
        
        phowhisper_repo = st.text_input(
            "PhoWhisper Repository",
            value=current_settings["model"]["phowhisper_repo"],
            help="HuggingFace repo cho PhoWhisper"
        )
    
    with col2:
        device = st.selectbox(
            "Device",
            ["cpu", "cuda"],
            index=0 if current_settings["model"]["device"] == "cpu" else 1,
            disabled=config.is_cloud(),
            help="CPU hoặc CUDA (tự động CPU trên Cloud)"
        )
        
        precision = st.selectbox(
            "Precision",
            ["fp32", "fp16", "int8"],
            index=["fp32", "fp16", "int8"].index(current_settings["model"]["precision"]),
            help="Model precision (fp32 recommended)"
        )
        
        # Chunking settings (moved from Transcription page)
        st.markdown("#### Chunking Settings")
        enable_chunk = st.checkbox(
            "Enable Chunking",
            value=True,
            help="Chia audio thành chunks để xử lý"
        )
        
        chunk_seconds = st.selectbox(
            "Chunk Length (seconds)",
            [15, 30, 45, 60, 90],
            index=2,  # Default 45
            help="Độ dài mỗi chunk"
        )
    
    current_settings["model"]["whisper_model_path"] = whisper_model_path
    current_settings["model"]["phowhisper_repo"] = phowhisper_repo
    current_settings["model"]["device"] = device
    current_settings["model"]["precision"] = precision

with tab2:
    st.subheader("Inference Hyperparameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        beam_size = st.number_input(
            "Beam Size",
            min_value=1,
            max_value=20,
            value=current_settings["inference"]["beam_size"],
            help="Số lượng beams cho beam search"
        )
        
        batch_size = st.number_input(
            "Batch Size",
            min_value=1,
            max_value=128,
            value=current_settings["inference"]["batch_size"],
            help="Batch size cho inference"
        )
    
    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=current_settings["inference"]["temperature"],
            step=0.1,
            help="Temperature cho sampling (0.0 = greedy)"
        )
        
        best_of = st.number_input(
            "Best Of",
            min_value=1,
            max_value=20,
            value=current_settings["inference"]["best_of"],
            help="Số lượng candidates để chọn"
        )
    
    current_settings["inference"]["beam_size"] = beam_size
    current_settings["inference"]["batch_size"] = batch_size
    current_settings["inference"]["temperature"] = temperature
    current_settings["inference"]["best_of"] = best_of

with tab3:
    st.subheader("Resource & Performance Tuning")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_threads = st.number_input(
            "Number of Threads",
            min_value=1,
            max_value=16,
            value=current_settings["resource"]["num_threads"],
            help="Số lượng threads cho CPU"
        )
        
        max_memory_mb = st.number_input(
            "Max Memory (MB)",
            min_value=512,
            max_value=16384,
            value=current_settings["resource"]["max_memory_mb"],
            step=512,
            help="Giới hạn memory usage"
        )
    
    with col2:
        quantization = st.selectbox(
            "Quantization",
            ["none", "int8", "int4"],
            index=["none", "int8", "int4"].index(current_settings["resource"]["quantization"]),
            help="Model quantization (giảm memory nhưng có thể giảm accuracy)"
        )
    
    current_settings["resource"]["num_threads"] = num_threads
    current_settings["resource"]["max_memory_mb"] = max_memory_mb
    current_settings["resource"]["quantization"] = quantization

with tab4:
    st.subheader("Pipeline Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vad_enabled = st.checkbox(
            "Voice Activity Detection (VAD)",
            value=current_settings["pipeline"]["vad_enabled"],
            help="Bật VAD để phát hiện speech segments"
        )
        
        vad_threshold = st.slider(
            "VAD Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Ngưỡng để phát hiện speech"
        )
        
        min_segment_duration = st.number_input(
            "Min Segment Duration (s)",
            min_value=0.1,
            max_value=5.0,
            value=0.5,
            step=0.1,
            help="Độ dài segment tối thiểu"
        )
        
        max_segment_duration = st.number_input(
            "Max Segment Duration (s)",
            min_value=1.0,
            max_value=60.0,
            value=30.0,
            step=1.0,
            help="Độ dài segment tối đa"
        )
        
        diarization_backend = st.selectbox(
            "Diarization Backend",
            ["simple", "pyannote"],
            index=0 if current_settings["pipeline"]["diarization_backend"] == "simple" else 1,
            help="Backend cho speaker diarization"
        )
    
    with col2:
        sample_rate = st.selectbox(
            "Sample Rate (Hz)",
            [8000, 16000, 22050, 44100],
            index=1,  # Default 16000
            help="Sample rate cho audio processing"
        )
        
        max_speakers = st.number_input(
            "Max Speakers",
            min_value=1,
            max_value=10,
            value=current_settings["pipeline"]["max_speakers"],
            help="Số lượng người nói tối đa"
        )
    
    current_settings["pipeline"]["vad_enabled"] = vad_enabled
    current_settings["pipeline"]["diarization_backend"] = diarization_backend
    current_settings["pipeline"]["max_speakers"] = max_speakers

with tab5:
    st.subheader("Deployment Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        docker_image = st.text_input(
            "Docker Image",
            value=current_settings["deployment"]["docker_image"],
            help="Docker image name"
        )
        
        api_port = st.number_input(
            "API Port",
            min_value=1024,
            max_value=65535,
            value=current_settings["deployment"]["api_port"],
            help="Port cho FastAPI server"
        )
    
    with col2:
        cloud_run_url = st.text_input(
            "Cloud Run URL",
            value=current_settings["deployment"]["cloud_run"],
            help="Google Cloud Run deployment URL"
        )
        
        hf_spaces_url = st.text_input(
            "HuggingFace Spaces URL",
            value=current_settings["deployment"]["hf_spaces"],
            help="HuggingFace Spaces deployment URL"
        )
    
    current_settings["deployment"]["docker_image"] = docker_image
    current_settings["deployment"]["api_port"] = api_port
    current_settings["deployment"]["cloud_run"] = cloud_run_url
    current_settings["deployment"]["hf_spaces"] = hf_spaces_url

with tab6:
    st.subheader("Debug & Logging")
    
    col1, col2 = st.columns(2)
    
    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(current_settings["debug"]["log_level"]),
            help="Logging level"
        )
        
        enable_evaluation = st.checkbox(
            "Enable Evaluation",
            value=current_settings["debug"]["enable_evaluation"],
            help="Bật evaluation mode"
        )
    
    with col2:
        wer_cer_enabled = st.checkbox(
            "Calculate WER/CER",
            value=current_settings["debug"]["wer_cer_enabled"],
            help="Tính Word Error Rate và Character Error Rate"
        )
    
    current_settings["debug"]["log_level"] = log_level
    current_settings["debug"]["enable_evaluation"] = enable_evaluation
    current_settings["debug"]["wer_cer_enabled"] = wer_cer_enabled

# Save/Load settings
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        format_type = st.radio("Format", ["JSON", "YAML"], horizontal=True, key="save_format")
        if save_settings(current_settings, format=format_type.lower()):
            st.success(f"✅ Đã lưu settings vào settings.{format_type.lower()}")

with col2:
    uploaded_file = st.file_uploader("📁 Load Settings", type=["json", "yaml", "yml"], key="load_settings")
    if uploaded_file:
        file_content = uploaded_file.read().decode('utf-8')
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=uploaded_file.name) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        
        loaded_settings = load_settings_from_file(tmp_path)
        if loaded_settings:
            st.success("✅ Đã load settings!")
            st.json(loaded_settings)
            os.unlink(tmp_path)

with col3:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        current_settings = load_settings()
        st.success("✅ Đã reset về defaults!")
        st.rerun()

# Display current settings
with st.expander("📋 Current Settings (JSON)"):
    st.json(current_settings)

