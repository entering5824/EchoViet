"""
Transcription Page
Chạy ASR (Whisper / PhoWhisper), chunking nhẹ, tối ưu cho Streamlit Cloud
"""
import streamlit as st
import os
import sys
import tempfile
import re
import soundfile as sf

# ================== PATH ==================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from app.components.transcript_editor import render_transcript_editor

from core.asr.model_registry import (
    get_all_models,
    get_model_info,
    check_model_dependencies,
    get_recommended_models,
)
from core.asr.transcription_service import (
    load_whisper_model,
    transcribe_audio,
)
from core.asr.phowhisper_service import (
    load_phowhisper_model,
    transcribe_phowhisper,
)
from core.asr.quality_presets import (
    get_model_size_for_preset,
    get_preset_description,
    get_preset_tooltip,
    get_recommended_preset,
    get_all_presets,
    detect_gpu,
)
from core.audio.audio_processor import chunk_signal, format_timestamp
from core.audio.ffmpeg_setup import ensure_ffmpeg

# ================== ENV ==================
ensure_ffmpeg(silent=True)
apply_custom_css()

st.set_page_config(
    page_title="Transcription - Vietnamese Speech to Text",
    page_icon="📝",
    layout="wide",
)

# ================== STATE ==================
def init_state():
    defaults = {
        "audio_data": None,
        "audio_sr": None,
        "audio_info": None,
        "transcript_text": "",
        "transcript_segments": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()

# ================== HEADER ==================
st.header("📝 Transcription")
st.caption("Chạy ASR với Whisper / PhoWhisper, hỗ trợ audio dài")

# ================== GUARD ==================
if st.session_state.audio_data is None:
    st.warning("⚠️ Chưa có audio. Vui lòng upload ở trang Audio Input.")
    if st.button("🎤 Go to Audio Input", type="primary"):
        st.switch_page("pages/1_🎤_Audio_Input.py")
    st.stop()

st.info(
    f"📊 Duration: {st.session_state.audio_info['duration']:.1f}s | "
    f"SR: {st.session_state.audio_sr} Hz"
)

# ================== MODEL SELECTION ==================
st.subheader("🎯 Model Selection")

all_models = get_all_models()
recommended = set(get_recommended_models())

model_ids = list(all_models.keys())

selected_model_id = st.selectbox(
    "ASR Model",
    model_ids,
    format_func=lambda mid: (
        all_models[mid]["name"]
        + (" 🌟" if mid in recommended else "")
    ),
    help="Chọn mô hình ASR: Whisper (đa ngôn ngữ) hoặc PhoWhisper (tối ưu cho tiếng Việt)"
)

model_info = get_model_info(selected_model_id)

is_available, missing = check_model_dependencies(selected_model_id)

if not is_available:
    st.error(f"❌ Missing dependencies: {', '.join(missing)}")

# ================== QUALITY PRESET ==================
st.subheader("⚡ Quality Preset")

# Get recommended preset (auto-suggest Accurate if GPU available)
recommended_preset = get_recommended_preset(selected_model_id)
has_gpu = detect_gpu()

if has_gpu:
    st.info("🎮 GPU detected! Recommend using 'Accurate' for best results.")

preset_options = get_all_presets()
preset_labels = {
    "fast": "⚡ Fast - Nhanh, ít chính xác",
    "balanced": "⚖️ Balanced - Cân bằng",
    "accurate": "🎯 Accurate - Chậm, chính xác nhất"
}

selected_preset = st.radio(
    "Chọn chất lượng",
    preset_options,
    index=preset_options.index(recommended_preset) if recommended_preset in preset_options else 0,
    format_func=lambda p: preset_labels.get(p, p),
    help=get_preset_tooltip(selected_preset) if selected_preset in preset_options else ""
)

# Show description
st.caption(get_preset_description(selected_preset))

# Auto-map preset to model size (hidden from user)
model_size = get_model_size_for_preset(selected_preset, selected_model_id)

if model_size is None:
    st.error(f"❌ Invalid preset/model combination")
    st.stop()

# Show what model size will be used (optional, can be hidden)
with st.expander("ℹ️ Technical Details"):
    st.write(f"**Model size:** {model_size}")
    st.write(f"**Preset:** {selected_preset}")
    st.caption("💡 Technical details moved to Advanced Settings page")

# Default options (hidden from regular users, moved to Advanced Settings)
enable_chunk = True  # Always enabled for long audio
chunk_seconds = 45  # Default chunk length
show_timestamps = True  # Always show timestamps

# ================== TRANSCRIBE ==================
def run_chunked_transcription(run_fn):
    ranges = (
        chunk_signal(st.session_state.audio_data, st.session_state.audio_sr, chunk_seconds)
        if enable_chunk else [(0, len(st.session_state.audio_data))]
    )

    results = []
    progress = st.progress(0.0)

    for i, (s0, s1) in enumerate(ranges, 1):
        y = st.session_state.audio_data[s0:s1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_name = tmp.name
        sf.write(tmp_name, y, st.session_state.audio_sr)

        try:
            text = run_fn(tmp_name)
            if text:
                if show_timestamps:
                    ts = f"[{format_timestamp(s0 / st.session_state.audio_sr)} - {format_timestamp(s1 / st.session_state.audio_sr)}] "
                else:
                    ts = ""
                results.append(ts + text.strip())
        finally:
            try:
                os.unlink(tmp_name)
            except Exception:
                pass

        progress.progress(i / len(ranges))

    return "\n".join(results)


if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
    if not is_available:
        st.stop()

    with st.spinner("Running ASR..."):
        try:
            if selected_model_id == "whisper":
                model, device = load_whisper_model(model_size)
                text = run_chunked_transcription(
                    lambda p: transcribe_audio(model, p, language="vi").get("text", "")
                )

            elif selected_model_id == "phowhisper":
                model = load_phowhisper_model(model_size)
                text = run_chunked_transcription(
                    lambda p: transcribe_phowhisper(model, p, language="vi").get("text", "")
                )
            else:
                st.error("❌ Unsupported model")
                st.stop()

            st.session_state.transcript_text = text
            st.success("✅ Transcription complete")
            st.rerun()

        except Exception as e:
            st.error(f"❌ ASR failed: {e}")

# ================== OUTPUT ==================
if st.session_state.transcript_text:
    st.divider()
    st.subheader("📝 Transcript")

    st.text_area(
        "Result",
        st.session_state.transcript_text,
        height=300,
        disabled=True,
    )

    edited_text, _ = render_transcript_editor(
        st.session_state.transcript_text,
        key_prefix="transcript",
    )

    if st.button("💾 Save edits"):
        st.session_state.transcript_text = edited_text
        st.success("Saved")
        st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Speaker & Enhancement", use_container_width=True):
            st.switch_page("pages/3_✨_Speaker_Enhancement.py")
    with col2:
        if st.button("📊 Export & Report", use_container_width=True):
            st.switch_page("pages/4_📊_Export_Reporting.py")
