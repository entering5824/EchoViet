"""Sidebar configuration: model, VAD, language, pipeline options."""
import streamlit as st
from core.asr.model_registry import get_all_models, get_model_info


def render_sidebar_config(key_prefix: str = "sidebar"):
    """
    Render sidebar widgets for ASR/model config. Returns dict with model_size, language, vad_threshold, etc.
    """
    with st.sidebar:
        st.subheader("⚙️ Cấu hình")
        all_models = get_all_models()
        model_ids = list(all_models.keys())
        selected_id = st.selectbox("ASR Model", model_ids, key=f"{key_prefix}_model_id")
        model_info = get_model_info(selected_id) or {}
        sizes = model_info.get("sizes", ["tiny", "base", "small"])
        default_size = model_info.get("default_size", "base")
        idx = sizes.index(default_size) if default_size in sizes else 0
        model_size = st.selectbox("Model size", sizes, index=idx, key=f"{key_prefix}_size")
        language = st.selectbox("Ngôn ngữ", ["vi", "en"], key=f"{key_prefix}_lang")
        vad_threshold = st.slider("VAD threshold", 0.1, 0.9, 0.5, 0.05, key=f"{key_prefix}_vad")
    return {
        "model_id": selected_id,
        "model_size": model_size,
        "language": language,
        "vad_threshold": vad_threshold,
    }
