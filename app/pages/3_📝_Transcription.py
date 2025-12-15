"""
Transcription Page
Hỗ trợ tất cả ASR models
"""
import streamlit as st
import os
import sys
import tempfile
import soundfile as sf
import torch
import numpy as np
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.asr.model_registry import (
    get_all_models, get_model_info, check_model_dependencies, get_recommended_models
)
from core.asr.transcription_service import (
    load_whisper_model, transcribe_audio, format_transcript
)
from core.asr.phowhisper_service import (
    load_phowhisper_model, transcribe_phowhisper
)
from core.asr.wav2vec2_service import (
    load_wav2vec2_model, transcribe_wav2vec2
)
from core.asr.deepspeech2_service import (
    load_deepspeech2_model, transcribe_deepspeech2, check_deepspeech_available
)
from core.asr.quartznet_service import (
    load_quartznet_model, transcribe_quartznet, check_nemo_available
)
from core.asr.wav2letter_service import (
    load_wav2letter_model, transcribe_wav2letter, check_wav2letter_available
)
from core.asr.kaldi_service import (
    load_kaldi_model, transcribe_kaldi, check_kaldi_available
)
from core.audio.audio_processor import chunk_signal, format_timestamp
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Ensure session_state keys exist when page is opened directly
for key, default in (
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_result", None),
    ("transcript_text", ""),
):
    if key not in st.session_state:
        st.session_state[key] = default

# Render sidebar with logo
render_sidebar()

st.header("📝 Transcription")

if st.session_state.audio_data is None:
    st.warning("⚠️ Vui lòng upload audio file trước tại trang 'Upload & Record'")
else:
    # Get all models from registry
    all_models = get_all_models()
    recommended = get_recommended_models()
    
    # Model selection
    st.subheader("🎯 Model Selection")
    
    # Group models by category for better UX
    model_options = []
    model_descriptions = {}
    
    for model_id, info in all_models.items():
        name = info["name"]
        category = info.get("category", "Other")
        is_recommended = info.get("recommended", False)
        vietnamese_support = info.get("vietnamese_support", False)
        
        # Check availability
        is_available, missing_deps = check_model_dependencies(model_id)
        
        # Format display name
        display_name = name
        if is_recommended:
            display_name += " 🌟"
        if not vietnamese_support:
            display_name += " (EN)"
        if not is_available:
            display_name += " ⚠️"
        
        model_options.append((model_id, display_name))
        model_descriptions[model_id] = {
            "description": info.get("description", ""),
            "type": info.get("type", ""),
            "category": category,
            "is_available": is_available,
            "missing_deps": missing_deps,
            "vietnamese_support": vietnamese_support
        }
    
    # Model selection dropdown
    selected_model_id = st.selectbox(
        "Chọn mô hình ASR:",
        options=[opt[0] for opt in model_options],
        format_func=lambda x: next(opt[1] for opt in model_options if opt[0] == x),
        help="Chọn mô hình để transcribe audio"
    )
    
    # Display model info
    model_info = get_model_info(selected_model_id)
    if model_info:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Loại:** {model_info['type']}")
            st.markdown(f"**Category:** {model_info['category']}")
        with col2:
            if model_info.get("recommended"):
                st.success("🌟 Khuyến nghị cho tiếng Việt")
            if not model_info.get("vietnamese_support"):
                st.warning("⚠️ Chủ yếu cho tiếng Anh")
        
        st.info(f"💡 {model_info.get('description', '')}")
        
        # Check dependencies
        is_available, missing_deps = check_model_dependencies(selected_model_id)
        if not is_available:
            st.error(f"❌ Model chưa sẵn sàng. Thiếu dependencies: {', '.join(missing_deps)}")
            st.info(f"💡 Cài đặt: pip install {' '.join(missing_deps)}")
    
    # Model size selection (if applicable)
    model_size = None
    if model_info and model_info.get("sizes") and len(model_info["sizes"]) > 1:
        default_idx = 0
        if model_info.get("default_size"):
            try:
                default_idx = model_info["sizes"].index(model_info["default_size"])
            except:
                pass
        
        model_size = st.selectbox(
            f"Chọn kích thước {model_info['name']}:",
            model_info["sizes"],
            index=default_idx,
            help="Model lớn hơn thường chính xác hơn nhưng chậm hơn"
        )
    elif model_info and model_info.get("sizes"):
        model_size = model_info["sizes"][0]  # Use default/only size
    
    with_timestamps = st.checkbox("Hiển thị timestamps", value=True)
    enable_chunk = st.checkbox("Xử lý audio dài bằng chunking", value=True)
    chunk_seconds = st.selectbox(
        "Độ dài mỗi chunk (giây)",
        [15, 30, 45, 60, 90, 120],
        index=2,
        help="Chia audio dài thành các đoạn nhỏ để tránh hết bộ nhớ",
    )
    auto_punct = st.checkbox("Tự động chèn dấu câu (đơn giản)", value=False)
    
    # Special handling for models that need additional config
    deepspeech_model_path = None
    if selected_model_id == "deepspeech2" and check_deepspeech_available():
        st.info("💡 DeepSpeech cần model file (.pbmm). Tải từ: https://github.com/mozilla/DeepSpeech/releases")
        deepspeech_model_path = st.text_input("DeepSpeech model path (.pbmm):", key="deepspeech_model_path", value="")
        if deepspeech_model_path and not os.path.exists(deepspeech_model_path):
            st.error(f"❌ Không tìm thấy file: {deepspeech_model_path}")
    
    if st.button("🚀 Bắt đầu Transcription", type="primary"):
        if st.session_state.audio_data is not None:
            if not is_available:
                st.error("❌ Model chưa sẵn sàng. Vui lòng cài đặt dependencies trước.")
            else:
                with st.spinner(f"Đang transcribe với {model_info['name']}... (có thể mất vài phút)"):
                    result = None
                    model_obj = None
                    transcripts = []
                    
                    # Load và transcribe theo từng backend (có hỗ trợ chunk cho Whisper/PhoWhisper)
                    try:
                        def transcribe_chunked_with_whisper(model_obj, language):
                            ranges = chunk_signal(
                                st.session_state.audio_data, st.session_state.audio_sr, int(chunk_seconds)
                            ) if enable_chunk else [(0, len(st.session_state.audio_data))]
                            progress = st.progress(0.0)
                            for idx, (s0, s1) in enumerate(ranges, start=1):
                                chunk_y = st.session_state.audio_data[s0:s1]
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                                    sf.write(tmp_file.name, chunk_y, st.session_state.audio_sr)
                                    chunk_res = transcribe_audio(
                                        model_obj, tmp_file.name, sr=st.session_state.audio_sr,
                                        language=language, task="transcribe"
                                    )
                                try:
                                    os.unlink(tmp_file.name)
                                except:
                                    pass
                                if chunk_res and chunk_res.get("text"):
                                    start_ts = format_timestamp(s0 / st.session_state.audio_sr)
                                    end_ts = format_timestamp(s1 / st.session_state.audio_sr)
                                    transcripts.append(f"[{start_ts} - {end_ts}] {chunk_res.get('text','').strip()}")
                                progress.progress(idx / len(ranges))
                            return {"text": "\n".join(transcripts), "segments": []}

                        def transcribe_chunked_with_phowhisper(model_obj):
                            ranges = chunk_signal(
                                st.session_state.audio_data, st.session_state.audio_sr, int(chunk_seconds)
                            ) if enable_chunk else [(0, len(st.session_state.audio_data))]
                            progress = st.progress(0.0)
                            for idx, (s0, s1) in enumerate(ranges, start=1):
                                chunk_y = st.session_state.audio_data[s0:s1]
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                                    sf.write(tmp_file.name, chunk_y, st.session_state.audio_sr)
                                    chunk_res = transcribe_phowhisper(
                                        model_obj, tmp_file.name, sr=st.session_state.audio_sr, language="vi"
                                    )
                                try:
                                    os.unlink(tmp_file.name)
                                except:
                                    pass
                                if chunk_res and chunk_res.get("text"):
                                    start_ts = format_timestamp(s0 / st.session_state.audio_sr)
                                    end_ts = format_timestamp(s1 / st.session_state.audio_sr)
                                    transcripts.append(f"[{start_ts} - {end_ts}] {chunk_res.get('text','').strip()}")
                                progress.progress(idx / len(ranges))
                            return {"text": "\n".join(transcripts), "segments": []}

                        if selected_model_id == "whisper":
                            model_obj, device = load_whisper_model(model_size)
                            if model_obj:
                                result = transcribe_chunked_with_whisper(model_obj, language="vi")
                        
                        elif selected_model_id == "phowhisper":
                            model_obj = load_phowhisper_model(model_size)
                            if model_obj:
                                result = transcribe_chunked_with_phowhisper(model_obj)
                        
                        elif selected_model_id == "wav2vec2":
                            processor, model_obj = load_wav2vec2_model()
                            if processor and model_obj:
                                result = transcribe_wav2vec2(
                                    processor, model_obj, st.session_state.audio_data, sr=st.session_state.audio_sr
                                )
                        
                        elif selected_model_id == "deepspeech2":
                            if check_deepspeech_available():
                                if deepspeech_model_path and os.path.exists(deepspeech_model_path):
                                    model_obj = load_deepspeech2_model(deepspeech_model_path)
                                    if model_obj:
                                        result = transcribe_deepspeech2(
                                            model_obj, st.session_state.audio_data, sr=st.session_state.audio_sr
                                        )
                                    else:
                                        st.error("❌ Không thể load DeepSpeech model!")
                                else:
                                    st.error("❌ Vui lòng cung cấp đường dẫn đến DeepSpeech model file (.pbmm)")
                            else:
                                st.error("❌ DeepSpeech chưa được cài đặt. Cài: pip install deepspeech")
                        
                        elif selected_model_id == "quartznet":
                            if check_nemo_available():
                                model_obj = load_quartznet_model()
                                if model_obj:
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                                        sf.write(tmp_file.name, st.session_state.audio_data, st.session_state.audio_sr)
                                        result = transcribe_quartznet(
                                            model_obj, tmp_file.name, sr=st.session_state.audio_sr
                                        )
                                        os.unlink(tmp_file.name)
                            else:
                                st.error("❌ NeMo toolkit chưa được cài đặt.")
                        
                        elif selected_model_id == "wav2letter":
                            st.warning("⚠️ Wav2Letter++ chưa được tích hợp đầy đủ.")
                        
                        elif selected_model_id == "kaldi":
                            st.warning("⚠️ Kaldi chưa được tích hợp đầy đủ.")
                        
                        if result:
                            st.session_state.transcript_result = result
                            text_out = result.get("text", "") if isinstance(result, dict) else ""
                            if not text_out and hasattr(result, "text"):
                                text_out = result.text
                            if auto_punct:
                                # Cải thiện punctuation: thêm dấu câu cơ bản
                                text_out = text_out.replace(" ,", ",").replace(" .", ".")
                                # Thêm dấu chấm cuối câu nếu thiếu
                                if text_out and text_out[-1] not in ".!?":
                                    text_out += "."
                                # Fix spacing around punctuation
                                text_out = re.sub(r'\s+([,.!?;:])', r'\1', text_out)
                                text_out = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1\2', text_out)
                            if with_timestamps:
                                st.session_state.transcript_text = text_out or format_transcript(
                                    result, with_timestamps=True
                                )
                            else:
                                st.session_state.transcript_text = text_out or format_transcript(
                                    result, with_timestamps=False
                            )
                            st.success("✅ Transcription hoàn tất!")
                            st.rerun()
                        elif model_obj is None:
                            st.error("❌ Không thể load model!")
                    
                    except Exception as e:
                        st.error(f"❌ Lỗi khi transcribe: {str(e)}")
        else:
            st.warning("⚠️ Vui lòng upload file audio trước!")
    
    # Hiển thị transcript
    if st.session_state.transcript_text:
        st.subheader("📝 Transcript")
        st.text_area(
            "Kết quả transcription:",
            st.session_state.transcript_text,
            height=400,
            key="transcript_display"
        )
        
        # Edit transcript
        st.subheader("✏️ Chỉnh sửa Transcript")
        edited_text = st.text_area(
            "Chỉnh sửa transcript:",
            st.session_state.transcript_text,
            height=300,
            key="transcript_edit"
        )
        
        if st.button("💾 Lưu thay đổi"):
            st.session_state.transcript_text = edited_text
            st.success("✅ Đã lưu thay đổi!")
            st.rerun()

        st.subheader("📊 Thống kê & Export")
        words = st.session_state.transcript_text.split()
        word_count = len(words)
        duration = st.session_state.audio_info.get("duration") if st.session_state.audio_info else 0
        wpm = (word_count / duration * 60) if duration else 0
        col_stats = st.columns(3)
        col_stats[0].metric("Số từ", f"{word_count}")
        col_stats[1].metric("Thời lượng (s)", f"{duration:.2f}" if duration else "-")
        col_stats[2].metric("WPM", f"{wpm:.1f}")

        st.download_button(
            "⬇️ Tải TXT",
            data=st.session_state.transcript_text,
            file_name="transcript.txt",
            mime="text/plain",
        )
