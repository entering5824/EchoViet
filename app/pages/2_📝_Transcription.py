"""
Transcription Page
Run ASR with Whisper, light chunking, optimized for Streamlit Cloud
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

from app.components.layout import apply_custom_css, render_page_header
from app.components.transcript_editor import render_transcript_editor
from app.components.footer import render_footer

from core.asr.model_registry import (
    get_all_models,
    get_model_info,
    check_model_dependencies,
    get_recommended_models,
)
from core.asr.transcription_service import (
    load_whisper_model,
    transcribe_audio,
    split_text_readable,
    format_time,
)
from core.nlp.post_processing import normalize_vietnamese, format_text
from core.asr.quality_presets import (
    get_model_size_for_preset,
    get_preset_description,
    get_preset_tooltip,
    get_recommended_preset,
    get_all_presets,
    detect_gpu,
)
from core.audio.audio_processor import chunk_signal
from core.asr.transcription_service import format_time
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
render_page_header("Transcription", "Run ASR with Whisper, supports long audio", "📝")

# ================== GUARD ==================
if st.session_state.audio_data is None:
    st.warning("⚠️ No audio available. Please upload at Audio Input page.")
    if st.button("🎤 Go to Audio Input", type="primary"):
        st.switch_page("pages/1_🎤_Audio_Input.py")
    st.stop()

st.info(
    f"📊 Duration: {st.session_state.audio_info['duration']:.1f}s | "
    f"SR: {st.session_state.audio_sr} Hz"
)

# ================== MODEL SELECTION ==================
st.subheader("🎯 Select Model")

all_models = get_all_models()
recommended = set(get_recommended_models())

# Simplify: Only show recommended models by default, hide others in expander
recommended_model_ids = [mid for mid in all_models.keys() if mid in recommended]
other_model_ids = [mid for mid in all_models.keys() if mid not in recommended]

if recommended_model_ids:
    # Default to first recommended model
    default_index = 0
    selected_model_id = st.selectbox(
        "ASR Model (Recommended)",
        recommended_model_ids,
        index=default_index,
        format_func=lambda mid: all_models[mid]["name"] + " 🌟",
        help="Select ASR model. Whisper is the best choice for Vietnamese."
    )
    
    # Show other models in expander
    if other_model_ids:
        with st.expander("🔧 Other Models (Not Recommended)"):
            other_selected = st.selectbox(
                "Other models",
                other_model_ids,
                format_func=lambda mid: all_models[mid]["name"],
                help="These models may not be optimal for Vietnamese"
            )
            if st.button("Use this model", key="use_other_model"):
                selected_model_id = other_selected
                st.rerun()
else:
    # Fallback if no recommended models
    model_ids = list(all_models.keys())
    selected_model_id = st.selectbox(
        "ASR Model",
        model_ids,
        format_func=lambda mid: all_models[mid]["name"],
        help="Select ASR model: Whisper (multilingual, supports Vietnamese)"
    )

model_info = get_model_info(selected_model_id)

is_available, missing = check_model_dependencies(selected_model_id)

if not is_available:
    st.error(f"❌ Missing dependencies: {', '.join(missing)}")
    st.info("💡 **Suggestion**: Install dependencies with: `pip install {' '.join(missing)}`")

# ================== QUALITY PRESET ==================
st.subheader("⚡ Select Quality")

# Get recommended preset (auto-suggest Accurate if GPU available)
recommended_preset = get_recommended_preset(selected_model_id)
has_gpu = detect_gpu()

if has_gpu:
    st.success("🎮 GPU detected! Recommended to use 'Accurate' for best results.")

preset_options = get_all_presets()
preset_labels = {
    "fast": "⚡ Fast - Fast processing, lower accuracy",
    "balanced": "⚖️ Balanced - Balanced speed and accuracy (Recommended)",
    "accurate": "🎯 Accurate - Slower processing, highest accuracy"
}

selected_preset = st.radio(
    "Select processing quality:",
    preset_options,
    index=preset_options.index(recommended_preset) if recommended_preset in preset_options else 1,  # Default to balanced
    format_func=lambda p: preset_labels.get(p, p),
    help="'Balanced' mode is the best choice for most cases"
)

# Show description
st.info(f"💡 {get_preset_description(selected_preset)}")

# Auto-map preset to model size (hidden from user)
model_size = get_model_size_for_preset(selected_preset, selected_model_id)

if model_size is None:
    st.error(f"❌ Invalid preset/model combination")
    st.stop()

# Show technical details in expander (hidden by default)
with st.expander("ℹ️ Technical Details", expanded=False):
    st.write(f"**Model size:** {model_size}")
    st.write(f"**Preset:** {selected_preset}")
    st.caption("💡 Detailed technical information can be found in Advanced Settings")

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
    progress_bar = st.progress(0.0)
    status_text = st.empty()
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
            
            if result is None:
                error_count += 1
                continue
            
            # Lấy segments từ result và chia lại cho dễ đọc
            segments = result.get("segments", [])
            
            if segments:
                # Tính chunk start time (absolute) - offset từ đầu audio file
                chunk_start_time = s0 / st.session_state.audio_sr
                
                # Xử lý từng segment gốc từ Whisper và chia lại cho dễ đọc
                chunk_results = []
                for original_seg in segments:
                    seg_start = original_seg.get("start", 0)  # Timestamp tương đối trong chunk
                    seg_end = original_seg.get("end", 0)      # Timestamp tương đối trong chunk
                    seg_text = original_seg.get("text", "").strip()
                    
                    if not seg_text:
                        continue
                    
                    # Chia text của segment này thành các đoạn nhỏ dễ đọc (7-15 từ, ≤2 câu)
                    sub_texts = split_text_readable(seg_text, max_words=15, max_sentences=2)
                    
                    if not sub_texts:
                        continue
                    
                    # Tính thời gian cho mỗi đoạn con (chia đều thời gian)
                    seg_duration = seg_end - seg_start
                    num_parts = len(sub_texts)
                    per_part = seg_duration / num_parts if num_parts > 0 else seg_duration
                    
                    # Tạo readable segments với timestamps chính xác
                    for sub_idx, sub_text in enumerate(sub_texts):
                        # Timestamp tương đối trong segment gốc
                        sub_start = seg_start + sub_idx * per_part
                        sub_end = seg_start + (sub_idx + 1) * per_part
                        
                        # Áp dụng post-processing cho tiếng Việt
                        processed_text = normalize_vietnamese(sub_text)
                        processed_text = format_text(processed_text, {
                            "improve_vietnamese": True,
                            "punctuation": True,
                            "capitalize": True,
                            "remove_extra_spaces": True
                        })
                        
                        if processed_text.strip():
                            if show_timestamps:
                                # Timestamp absolute từ đầu audio file
                                abs_start = chunk_start_time + sub_start
                                abs_end = chunk_start_time + sub_end
                                ts = f"[{format_time(abs_start)} - {format_time(abs_end)}] "
                            else:
                                ts = ""
                            
                            chunk_results.append(ts + processed_text.strip())
                
                if chunk_results:
                    results.extend(chunk_results)
            else:
                # Fallback: dùng text nếu không có segments
                text = safe_get_text(result)
                if text:
                    # Áp dụng post-processing cho tiếng Việt
                    text = normalize_vietnamese(text)
                    text = format_text(text, {
                        "improve_vietnamese": True,
                        "punctuation": True,
                        "capitalize": True,
                        "remove_extra_spaces": True
                    })
                    
                    if show_timestamps:
                        ts = f"[{format_time(s0 / st.session_state.audio_sr)} - {format_time(s1 / st.session_state.audio_sr)}] "
                    else:
                        ts = ""
                    results.append(ts + text.strip())
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

        # Update progress with detailed status
        # Ensure progress is always in [0.0, 1.0] range
        if len(ranges) > 0:
            progress_percent = min(i / len(ranges), 1.0)
        else:
            progress_percent = 1.0
        progress_bar.progress(progress_percent)
        status_text.text(f"Processing chunk {i}/{len(ranges)} ({progress_percent*100:.0f}%)...")

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

    # Clear status text
    status_text.empty()
    
    if error_count > 0 and len(results) == 0:
        # All chunks failed
        raise Exception(f"All {error_count} chunks failed. Please check audio file and model.")

    return "\n".join(results) if results else ""


if st.button("🚀 Start Transcription", type="primary", use_container_width=True):
    if not is_available:
        st.stop()

    with st.spinner("Running ASR..."):
        try:
            if selected_model_id == "whisper":
                model, device = load_whisper_model(model_size)
                if model is None:
                    st.error("❌ Cannot load Whisper model. Please check errors above.")
                    st.stop()
                # Use optimization for Vietnamese (default: enabled)
                text = run_chunked_transcription(
                    lambda p: transcribe_audio(
                        model, 
                        p, 
                        language="vi",
                        use_vietnamese_optimization=True  # Automatically apply initial prompt and optimization
                    )
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
            st.error(f"❌ Transcription failed: {error_msg}")
            
            # Provide helpful context for common errors with better formatting
            error_help = st.container()
            with error_help:
                if "NoneType" in error_msg or "None" in error_msg:
                    st.warning("""
                    **💡 NoneType Error - Common causes:**
                    - Audio file cannot be loaded (check format and path)
                    - Model failed to load
                    - FFmpeg not found or not working
                    
                    **🔧 How to fix:**
                    1. Go back to Audio Input page to check audio file
                    2. Check errors above to see if model loaded successfully
                    3. Check FFmpeg setup in System Status
                    """)
                elif "Failed to load audio" in error_msg or "load audio" in error_msg.lower():
                    st.warning("""
                    **💡 Audio Load Error - Common causes:**
                    - File format not supported
                    - File corrupted or invalid
                    - FFmpeg not found or not working
                    
                    **🔧 How to fix:**
                    1. Try uploading audio file again at Audio Input page
                    2. Check file format (WAV, MP3, FLAC, M4A, OGG)
                    3. Ensure file is not corrupted
                    4. Check FFmpeg setup
                    """)
                elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                    st.warning("""
                    **💡 Memory Error - Audio file too large:**
                    
                    **🔧 How to fix:**
                    1. Split audio file into smaller segments
                    2. Use 'Fast' preset instead of 'Accurate'
                    3. Reduce model size (choose 'tiny' or 'base')
                    """)
                elif "cuda" in error_msg.lower() or "gpu" in error_msg.lower():
                    st.info("""
                    **💡 GPU Error - System will automatically switch to CPU:**
                    - If GPU available, check CUDA installation
                    - If no GPU, system will use CPU (slower)
                    """)
                else:
                    with st.expander("🔍 Error details"):
                        st.exception(e)

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

    if st.button("💾 Save Edits"):
        st.session_state.transcript_text = edited_text
        st.success("✅ Saved")
        st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✨ Speaker & Enhancement", use_container_width=True):
            st.switch_page("pages/3_✨_Speaker_Enhancement.py")
    with col2:
        if st.button("📊 Export & Report", use_container_width=True):
            st.switch_page("pages/4_📊_Export_Reporting.py")

# ===== Footer =====
render_footer()
