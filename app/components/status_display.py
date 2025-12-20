"""
Component hiển thị trạng thái hệ thống
"""
import streamlit as st
import os
import sys
from typing import Dict, Optional

def get_system_status() -> Dict:
    """Lấy trạng thái hệ thống"""
    status = {
        "ffmpeg": False,
        "models": {},
        "api_key": None,
        "memory": None,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    # Check FFmpeg
    try:
        from core.audio.ffmpeg_setup import get_ffmpeg_info
        ffmpeg_info = get_ffmpeg_info()
        status["ffmpeg"] = ffmpeg_info.get("verified", False)
        status["ffmpeg_path"] = ffmpeg_info.get("ffmpeg_path", "Not found")
    except:
        pass
    
    # Check models availability
    try:
        from core.asr.model_registry import get_all_models, check_model_dependencies
        all_models = get_all_models()
        for model_id, info in all_models.items():
            is_available, _ = check_model_dependencies(model_id)
            status["models"][model_id] = {
                "available": is_available,
                "name": info.get("name", model_id)
            }
    except:
        pass
    
    # Check API key (if configured)
    status["api_key"] = os.getenv("HF_TOKEN") is not None or os.getenv("OPENAI_API_KEY") is not None
    
    # Check memory (if psutil available)
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        status["memory"] = {
            "rss_mb": mem_info.rss / 1024 / 1024,
            "vms_mb": mem_info.vms / 1024 / 1024
        }
    except:
        pass
    
    return status

def render_status_display():
    """Hiển thị trạng thái hệ thống"""
    status = get_system_status()
    
    st.subheader("📊 Trạng thái hệ thống")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # FFmpeg status
        if status["ffmpeg"]:
            st.success("✅ FFmpeg: Sẵn sàng")
        else:
            st.error("❌ FFmpeg: Chưa sẵn sàng")
    
    with col2:
        # Python version
        st.info(f"🐍 Python: {status['python_version']}")
    
    with col3:
        # API Key
        if status["api_key"]:
            st.success("🔑 API Key: Đã cấu hình")
        else:
            st.warning("⚠️ API Key: Chưa cấu hình")
    
    # Memory usage
    if status["memory"]:
        st.metric("💾 Memory Usage", f"{status['memory']['rss_mb']:.1f} MB")
    
    # Models status
    if status["models"]:
        with st.expander("🤖 Trạng thái Models"):
            for model_id, model_info in status["models"].items():
                if model_info["available"]:
                    st.success(f"✅ {model_info['name']}")
                else:
                    st.warning(f"⚠️ {model_info['name']} (chưa sẵn sàng)")

