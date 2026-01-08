"""
Transcription Page
Chạy ASR với Whisper, chunking nhẹ, tối ưu cho Streamlit Cloud
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
render_page_header("Transcription", "Chạy ASR với Whisper, hỗ trợ audio dài", "📝")

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
st.subheader("🎯 Chọn Mô Hình")

all_models = get_all_models()
recommended = set(get_recommended_models())

# Simplify: Only show recommended models by default, hide others in expander
recommended_model_ids = [mid for mid in all_models.keys() if mid in recommended]
other_model_ids = [mid for mid in all_models.keys() if mid not in recommended]

if recommended_model_ids:
    # Default to first recommended model
    default_index = 0
    selected_model_id = st.selectbox(
        "Mô hình ASR (Khuyến nghị)",
        recommended_model_ids,
        index=default_index,
        format_func=lambda mid: all_models[mid]["name"] + " 🌟",
        help="Chọn mô hình ASR. Whisper là lựa chọn tốt nhất cho tiếng Việt."
    )
    
    # Show other models in expander
    if other_model_ids:
        with st.expander("🔧 Mô hình khác (Không khuyến nghị)"):
            other_selected = st.selectbox(
                "Mô hình khác",
                other_model_ids,
                format_func=lambda mid: all_models[mid]["name"],
                help="Các mô hình này có thể không tối ưu cho tiếng Việt"
            )
            if st.button("Sử dụng mô hình này", key="use_other_model"):
                selected_model_id = other_selected
                st.rerun()
else:
    # Fallback if no recommended models
    model_ids = list(all_models.keys())
    selected_model_id = st.selectbox(
        "ASR Model",
        model_ids,
        format_func=lambda mid: all_models[mid]["name"],
        help="Chọn mô hình ASR: Whisper (đa ngôn ngữ, hỗ trợ tiếng Việt)"
    )

model_info = get_model_info(selected_model_id)

is_available, missing = check_model_dependencies(selected_model_id)

if not is_available:
    st.error(f"❌ Thiếu dependencies: {', '.join(missing)}")
    st.info("💡 **Gợi ý**: Cài đặt dependencies bằng lệnh: `pip install {' '.join(missing)}`")

# ================== QUALITY PRESET ==================
st.subheader("⚡ Chọn Chất Lượng")

# Get recommended preset (auto-suggest Accurate if GPU available)
recommended_preset = get_recommended_preset(selected_model_id)
has_gpu = detect_gpu()

if has_gpu:
    st.success("🎮 Đã phát hiện GPU! Khuyến nghị sử dụng 'Chính xác' để có kết quả tốt nhất.")

preset_options = get_all_presets()
preset_labels = {
    "fast": "⚡ Nhanh - Xử lý nhanh, độ chính xác thấp hơn",
    "balanced": "⚖️ Cân bằng - Tốc độ và độ chính xác cân bằng (Khuyến nghị)",
    "accurate": "🎯 Chính xác - Xử lý chậm hơn, độ chính xác cao nhất"
}

selected_preset = st.radio(
    "Chọn chất lượng xử lý:",
    preset_options,
    index=preset_options.index(recommended_preset) if recommended_preset in preset_options else 1,  # Default to balanced
    format_func=lambda p: preset_labels.get(p, p),
    help="Chế độ 'Cân bằng' là lựa chọn tốt nhất cho hầu hết trường hợp"
)

# Show description
st.info(f"💡 {get_preset_description(selected_preset)}")

# Auto-map preset to model size (hidden from user)
model_size = get_model_size_for_preset(selected_preset, selected_model_id)

if model_size is None:
    st.error(f"❌ Kết hợp preset/model không hợp lệ")
    st.stop()

# Show technical details in expander (hidden by default)
with st.expander("ℹ️ Chi tiết kỹ thuật", expanded=False):
    st.write(f"**Kích thước model:** {model_size}")
    st.write(f"**Preset:** {selected_preset}")
    st.caption("💡 Thông tin kỹ thuật chi tiết có thể tìm thấy trong Advanced Settings")

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
                    for i, sub_text in enumerate(sub_texts):
                        # Timestamp tương đối trong segment gốc
                        sub_start = seg_start + i * per_part
                        sub_end = seg_start + (i + 1) * per_part
                        
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
        progress_percent = i / len(ranges)
        progress_bar.progress(progress_percent)
        status_text.text(f"Đang xử lý đoạn {i}/{len(ranges)} ({progress_percent*100:.0f}%)...")

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
        raise Exception(f"Tất cả {error_count} đoạn xử lý đều thất bại. Vui lòng kiểm tra file audio và model.")

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
                # Sử dụng tối ưu cho tiếng Việt (default: enabled)
                text = run_chunked_transcription(
                    lambda p: transcribe_audio(
                        model, 
                        p, 
                        language="vi",
                        use_vietnamese_optimization=True  # Tự động áp dụng initial prompt và tối ưu
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
            st.error(f"❌ Transcription thất bại: {error_msg}")
            
            # Provide helpful context for common errors with better formatting
            error_help = st.container()
            with error_help:
                if "NoneType" in error_msg or "None" in error_msg:
                    st.warning("""
                    **💡 Lỗi NoneType - Nguyên nhân thường gặp:**
                    - Audio file không thể load (kiểm tra format và path)
                    - Model không được load thành công
                    - FFmpeg không tìm thấy hoặc không hoạt động
                    
                    **🔧 Cách khắc phục:**
                    1. Quay lại trang Audio Input để kiểm tra audio file
                    2. Xem lỗi ở trên để biết model có load thành công không
                    3. Kiểm tra FFmpeg setup trong System Status
                    """)
                elif "Failed to load audio" in error_msg or "load audio" in error_msg.lower():
                    st.warning("""
                    **💡 Lỗi load audio - Nguyên nhân thường gặp:**
                    - File format không được hỗ trợ
                    - File bị hỏng hoặc không hợp lệ
                    - FFmpeg không tìm thấy hoặc không hoạt động
                    
                    **🔧 Cách khắc phục:**
                    1. Thử upload lại audio file ở trang Audio Input
                    2. Kiểm tra format file (WAV, MP3, FLAC, M4A, OGG)
                    3. Đảm bảo file không bị hỏng
                    4. Kiểm tra FFmpeg setup
                    """)
                elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                    st.warning("""
                    **💡 Lỗi bộ nhớ - File audio quá lớn:**
                    
                    **🔧 Cách khắc phục:**
                    1. Chia nhỏ file audio thành các đoạn ngắn hơn
                    2. Sử dụng preset 'Nhanh' thay vì 'Chính xác'
                    3. Giảm kích thước model (chọn 'tiny' hoặc 'base')
                    """)
                elif "cuda" in error_msg.lower() or "gpu" in error_msg.lower():
                    st.info("""
                    **💡 Lỗi GPU - Hệ thống sẽ tự động chuyển sang CPU:**
                    - Nếu có GPU, kiểm tra CUDA installation
                    - Nếu không có GPU, hệ thống sẽ sử dụng CPU (chậm hơn)
                    """)
                else:
                    with st.expander("🔍 Chi tiết lỗi"):
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

# ===== Footer =====
render_footer()
