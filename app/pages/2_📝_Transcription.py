"""
Transcription Page
Chạy ASR (Whisper / PhoWhisper), chunking nhẹ, tối ưu cho Streamlit Cloud
"""
import streamlit as st
import os
import sys
import tempfile
import re
import time
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
    # Do not reference `selected_preset` here (NameError when evaluated). Show tooltip after selection.
    help=get_preset_tooltip(recommended_preset) if recommended_preset in preset_options else ""
)

# Show description and tooltip (tooltip depends on the actual selection)
st.caption(get_preset_description(selected_preset))
st.caption(get_preset_tooltip(selected_preset))

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
def safe_get_text(result, default=""):
    """
    Safely extract text from transcription result.
    Handles None result (common on local when audio loading fails).
    
    Args:
        result: Transcription result dict or None
        default: Default text if result is None or missing 'text' key
    
    Returns:
        str: Extracted text or default
    """
    if result is None:
        return default
    if isinstance(result, dict):
        return result.get("text", default)
    # If result is already a string (shouldn't happen, but handle gracefully)
    if isinstance(result, str):
        return result
    return default

def run_chunked_transcription(run_fn):
    ranges = (
        chunk_signal(st.session_state.audio_data, st.session_state.audio_sr, chunk_seconds)
        if enable_chunk else [(0, len(st.session_state.audio_data))]
    )

    results = []
    progress = st.progress(0.0)
    error_count = 0
    temp_files_to_cleanup = []  # Track files to cleanup after transcription

    for i, (s0, s1) in enumerate(ranges, 1):
        y = st.session_state.audio_data[s0:s1]
        tmp_name = None

        try:
            # Create temp file and ensure it's closed before writing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp_name = tmp.name
            
            # Write audio data to file
            sf.write(tmp_name, y, st.session_state.audio_sr)
            
            # CRITICAL: Ensure file is flushed and closed before passing to transcription
            # On Windows, file must be fully written and closed before other processes can access it
            time.sleep(0.05)  # Small delay to ensure file system sync on Windows
            
            # Verify file exists and is readable before transcription
            if not os.path.exists(tmp_name):
                error_count += 1
                st.warning(f"⚠️ Chunk {i}/{len(ranges)}: Temp file không tồn tại sau khi tạo: {tmp_name}")
                continue
            
            # Normalize path for Windows (resolve any path issues)
            tmp_name_normalized = os.path.normpath(os.path.abspath(tmp_name))
            
            # Verify normalized path exists
            if not os.path.exists(tmp_name_normalized):
                error_count += 1
                st.warning(f"⚠️ Chunk {i}/{len(ranges)}: Normalized path không tồn tại: {tmp_name_normalized}")
                # Try original path
                tmp_name_normalized = tmp_name
            
            # Run transcription
            result = run_fn(tmp_name_normalized)
            text = safe_get_text(result)
            
            if text:
                if show_timestamps:
                    ts = f"[{format_timestamp(s0 / st.session_state.audio_sr)} - {format_timestamp(s1 / st.session_state.audio_sr)}] "
                else:
                    ts = ""
                results.append(ts + text.strip())
            else:
                # Transcription returned None or empty - log but continue
                error_count += 1
                if error_count == 1:  # Only show warning once
                    st.warning(f"⚠️ Chunk {i}/{len(ranges)}: Transcription failed or returned empty. Check error messages above.")
        except Exception as chunk_err:
            error_count += 1
            error_msg = str(chunk_err)
            if "WinError 2" in error_msg or "cannot find the file" in error_msg.lower():
                st.warning(f"⚠️ Chunk {i}/{len(ranges)}: File không tìm thấy. Có thể file đã bị xóa hoặc path có vấn đề.")
            else:
                st.warning(f"⚠️ Chunk {i}/{len(ranges)} failed: {error_msg}")
        finally:
            # Add to cleanup list instead of deleting immediately
            # This ensures file exists during entire transcription process
            if tmp_name and os.path.exists(tmp_name):
                temp_files_to_cleanup.append(tmp_name)

        progress.progress(i / len(ranges))

    # Cleanup all temp files after all transcriptions are complete
    for tmp_file in temp_files_to_cleanup:
        try:
            if os.path.exists(tmp_file):
                # Small delay to ensure file is not in use
                time.sleep(0.1)
                os.unlink(tmp_file)
        except Exception as cleanup_err:
            # Ignore cleanup errors - file may already be deleted
            pass

    if error_count > 0 and len(results) == 0:
        # All chunks failed
        raise Exception(f"All {error_count} chunks failed. Check audio file and model loading.")

    return "\n".join(results) if results else ""


if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
    if not is_available:
        st.stop()

    with st.spinner("Running ASR..."):
        try:
            if selected_model_id == "whisper":
                model, device = load_whisper_model(model_size)
                if model is None:
                    st.error("❌ Không thể load Whisper model. Vui lòng kiểm tra lỗi ở trên.")
                    st.stop()
                text = run_chunked_transcription(
                    lambda p: transcribe_audio(model, p, language="vi")
                )

            elif selected_model_id == "phowhisper":
                model = load_phowhisper_model(model_size)
                if model is None:
                    st.error("❌ Không thể load PhoWhisper model. Vui lòng kiểm tra lỗi ở trên.")
                    st.stop()
                text = run_chunked_transcription(
                    lambda p: transcribe_phowhisper(model, p, language="vi")
                )
            else:
                st.error("❌ Unsupported model")
                st.stop()

            if not text or text.strip() == "":
                st.warning("⚠️ Transcription completed but result is empty. Check audio file and try again.")
            else:
                st.session_state.transcript_text = text
                st.success("✅ Transcription complete")
                st.rerun()

        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ ASR failed: {error_msg}")
            # Provide helpful context for common errors
            if "NoneType" in error_msg or "None" in error_msg:
                st.info("""
                💡 **Lỗi NoneType thường do:**
                - Audio file không thể load (kiểm tra format và path)
                - Model không được load thành công
                - FFmpeg không tìm thấy hoặc không hoạt động
                
                **Khắc phục:**
                1. Kiểm tra audio file ở trang Audio Input
                2. Xem lỗi ở trên để biết model có load thành công không
                3. Kiểm tra FFmpeg setup
                """)
            elif "Failed to load audio" in error_msg or "load audio" in error_msg.lower():
                st.info("""
                💡 **Lỗi load audio thường do:**
                - File format không được hỗ trợ
                - File bị hỏng
                - FFmpeg không tìm thấy
                
                **Khắc phục:**
                1. Thử upload lại audio file
                2. Kiểm tra format file (WAV, MP3, FLAC, M4A, OGG)
                3. Kiểm tra FFmpeg setup
                """)

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
