"""
Speaker & Text Enhancement Page
Combined page: Speaker Diarization + AI Text Enhancement
Làm transcript "đẹp & dùng được"
"""
import streamlit as st
import os
import sys
import json
import re

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
from app.components.diarization_timeline import render_diarization_timeline
from app.components.footer import render_footer
from core.diarization.speaker_diarization import (
    simple_speaker_segmentation, format_with_speakers, format_time
)
from core.nlp.post_processing import format_text, correct_punctuation, capitalize_sentences, normalize_vietnamese, improve_vietnamese_punctuation
from core.nlp.keyword_extraction import extract_keywords, simple_summarize
from core.utils.export import export_docx, export_txt
from core.audio.ffmpeg_setup import ensure_ffmpeg

# Setup FFmpeg
ensure_ffmpeg(silent=True)

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="Speaker & Enhancement - Vietnamese Speech to Text",
    page_icon="✨",
    layout="wide"
)

# Initialize session state
for key, default in (
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_text", ""),
    ("transcript_segments", []),
    ("speaker_segments", []),
    ("transcript_enhanced", ""),
    ("enhancement_mode", "recommended"),
):
    st.session_state.setdefault(key, default)

render_page_header("Speaker & Text Enhancement", "Phân biệt người nói và làm sạch văn bản với AI", "✨")

# Check prerequisites
if not st.session_state.transcript_text:
    st.warning("⚠️ Vui lòng chạy transcription trước tại trang 'Transcription'")
    if st.button("📝 Go to Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
    st.stop()

st.info("✅ Transcript đã sẵn sàng cho enhancement")

# Tabs for Speaker Diarization and Text Enhancement
tab1, tab2 = st.tabs(["👥 Speaker Diarization", "✨ AI Text Enhancement"])

# ===== TAB 1: Speaker Diarization =====
with tab1:
    st.subheader("👥 Speaker Diarization")
    st.caption("Phân biệt và gán nhãn người nói trong cuộc họp")
    
    if st.session_state.audio_data is None:
        st.warning("⚠️ Cần audio data để chạy diarization. Vui lòng upload audio trước.")
        if st.button("🎤 Go to Audio Input", type="primary"):
            st.switch_page("pages/1_🎤_Audio_Input.py")
    else:
        # Settings
        col1, col2 = st.columns([2, 1])
        
        with col1:
            max_speakers = st.number_input(
                "Số lượng người nói dự kiến",
                min_value=1,
                max_value=10,
                value=4,
                help="Số lượng người nói tối đa trong audio. Hệ thống sẽ tự động phân loại và rotate giữa các speakers."
            )
            
            min_silence = st.slider(
                "Độ dài khoảng im lặng tối thiểu (giây)",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                help="Khoảng im lặng tối thiểu để phân tách giữa các speakers"
            )
        
        with col2:
            st.info("""
            **💡 Hướng dẫn:**
            - Điều chỉnh số lượng người nói theo thực tế
            - Khoảng im lặng ngắn hơn = phát hiện nhiều chuyển đổi hơn
            - Có thể chỉnh sửa speaker labels sau khi chạy
            """)
        
        # Run diarization
        if st.button("🚀 Chạy Speaker Diarization", type="primary", use_container_width=True):
            with st.spinner("Đang phân tích speaker..."):
                try:
                    # Parse transcript text thành segments nếu chưa có
                    transcript_lines = st.session_state.transcript_text.split('\n')
                    segments = []
                    
                    for line in transcript_lines:
                        line = line.strip()
                        if not line:
                            continue
                        # Parse timestamp format [start - end] text
                        ts_match = re.match(r'\[([\d.]+)\s*-\s*([\d.]+)\]\s*(.+)', line)
                        if ts_match:
                            start, end, text = float(ts_match.group(1)), float(ts_match.group(2)), ts_match.group(3)
                            segments.append({'start': start, 'end': end, 'text': text.strip()})
                        else:
                            # No timestamp, estimate
                            prev_end = segments[-1]['end'] if segments else 0
                            estimated_dur = max(2.0, len(line.split()) * 0.5)
                            segments.append({'start': prev_end, 'end': prev_end + estimated_dur, 'text': line})
                    
                    # Use improved segmentation with max_speakers
                    speaker_segments = simple_speaker_segmentation(
                        st.session_state.audio_data,
                        st.session_state.audio_sr,
                        segments if segments else transcript_lines,
                        min_silence_duration=min_silence,
                        max_speakers=max_speakers
                    )
                    
                    if speaker_segments:
                        st.session_state.speaker_segments = speaker_segments
                        num_speakers = len(set(seg.get('speaker') for seg in speaker_segments))
                        st.success(f"✅ Đã phát hiện {num_speakers} người nói trong {len(speaker_segments)} segments!")
                    else:
                        st.warning("⚠️ Không thể phân biệt speaker. Có thể do audio quá ngắn hoặc chỉ có 1 người nói.")
                except Exception as e:
                    st.error(f"❌ Lỗi khi chạy diarization: {str(e)}")
                    import traceback
                    with st.expander("🔍 Chi tiết lỗi"):
                        st.code(traceback.format_exc())
        
        # Display results
        if st.session_state.speaker_segments:
            st.markdown("---")
            st.subheader("📊 Diarization Results")
            
            # Statistics
            speakers = set(seg.get('speaker') for seg in st.session_state.speaker_segments)
            speaker_stats = {}
            for speaker in speakers:
                speaker_segs = [s for s in st.session_state.speaker_segments if s.get('speaker') == speaker]
                total_duration = sum(s.get('end', 0) - s.get('start', 0) for s in speaker_segs)
                speaker_stats[speaker] = {
                    'count': len(speaker_segs),
                    'duration': total_duration,
                    'percentage': (total_duration / (st.session_state.audio_info.get('duration', 1) or 1)) * 100
                }
            
            # Display stats
            cols = st.columns(min(len(speakers), 4))
            for idx, speaker in enumerate(sorted(speakers)):
                with cols[idx % len(cols)]:
                    stats = speaker_stats[speaker]
                    st.metric(
                        speaker,
                        f"{stats['count']} segments",
                        f"{stats['duration']:.1f}s ({stats['percentage']:.1f}%)"
                    )
            
            # Timeline visualization
            duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
            if duration > 0:
                render_diarization_timeline(st.session_state.speaker_segments, duration)
            
            # Transcript with speakers
            st.subheader("📝 Transcript với Speaker Labels")
            
            # Allow manual editing of speaker labels
            with st.expander("✏️ Chỉnh sửa Speaker Labels", expanded=False):
                st.caption("Thay đổi tên speaker hoặc gán lại segments cho speakers khác")
                
                # Speaker renaming
                st.markdown("**Đổi tên Speakers:**")
                rename_cols = st.columns(min(len(speakers), 4))
                speaker_rename_map = {}
                for idx, speaker in enumerate(sorted(speakers)):
                    with rename_cols[idx % len(rename_cols)]:
                        new_name = st.text_input(
                            f"Đổi tên {speaker}",
                            value=speaker,
                            key=f"rename_{speaker}"
                        )
                        if new_name and new_name != speaker:
                            speaker_rename_map[speaker] = new_name
                
                if speaker_rename_map and st.button("💾 Áp dụng đổi tên"):
                    for seg in st.session_state.speaker_segments:
                        old_speaker = seg.get('speaker')
                        if old_speaker in speaker_rename_map:
                            seg['speaker'] = speaker_rename_map[old_speaker]
                    st.success("✅ Đã cập nhật tên speakers!")
                    st.rerun()
            
            formatted_transcript = format_with_speakers(st.session_state.speaker_segments)
            st.text_area(
                "Transcript với speakers:",
                formatted_transcript,
                height=300,
                key="diarized_transcript"
            )
            
            # Update transcript text with speaker labels
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Áp dụng Speaker Labels vào Transcript", type="primary", use_container_width=True):
                    st.session_state.transcript_text = formatted_transcript
                    st.success("✅ Đã cập nhật transcript với speaker labels!")
                    st.rerun()
            
            with col2:
                # Export options
                export_col1, export_col2 = st.columns(2)
                with export_col1:
                    txt_data, txt_filename = export_txt(formatted_transcript, "transcript_with_speakers.txt")
                    st.download_button(
                        "📥 Download TXT",
                        data=txt_data,
                        file_name=txt_filename,
                        mime="text/plain",
                        use_container_width=True
                    )
                with export_col2:
                    docx_data, docx_filename = export_docx(formatted_transcript, None, "transcript_with_speakers.docx")
                    st.download_button(
                        "📥 Download DOCX",
                        data=docx_data,
                        file_name=docx_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

# ===== TAB 2: AI Text Enhancement =====
with tab2:
    st.subheader("✨ AI Text Enhancement")
    st.caption("Làm sạch và cải thiện văn bản với AI")
    
    # Preset Mode Selection (similar to audio preprocessing)
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
        <strong>💡 Hướng dẫn:</strong> Chọn chế độ phù hợp với nhu cầu của bạn.
        <strong>Đề xuất</strong> là lựa chọn tốt nhất cho hầu hết trường hợp.
    </div>
    """, unsafe_allow_html=True)
    
    mode_options = {
        "simple": {
            "name": "🎯 Đơn giản",
            "description": "Tự động cải thiện cơ bản - Phù hợp cho người dùng không chuyên",
            "icon": "🎯"
        },
        "recommended": {
            "name": "⭐ Đề xuất (Khuyến nghị)",
            "description": "Cải thiện tối ưu cho chất lượng và tốc độ - Phù hợp cho hầu hết người dùng",
            "icon": "⭐"
        },
        "advanced": {
            "name": "⚙️ Nâng cao",
            "description": "Tùy chỉnh chi tiết các thông số - Dành cho người dùng có kinh nghiệm",
            "icon": "⚙️"
        }
    }
    
    preset_cols = st.columns(3)
    selected_mode = st.session_state.enhancement_mode
    
    with preset_cols[0]:
        if st.button(
            mode_options["simple"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "simple" else "secondary",
            key="preset_simple_enhance"
        ):
            st.session_state.enhancement_mode = "simple"
            st.rerun()
    
    with preset_cols[1]:
        if st.button(
            mode_options["recommended"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "recommended" else "secondary",
            key="preset_recommended_enhance"
        ):
            st.session_state.enhancement_mode = "recommended"
            st.rerun()
    
    with preset_cols[2]:
        if st.button(
            mode_options["advanced"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "advanced" else "secondary",
            key="preset_advanced_enhance"
        ):
            st.session_state.enhancement_mode = "advanced"
            st.rerun()
    
    # Display current mode description
    current_mode = mode_options[st.session_state.enhancement_mode]
    st.info(f"**{current_mode['name']}**: {current_mode['description']}")
    
    # Enhancement options based on mode
    if st.session_state.enhancement_mode == "simple":
        # Simple mode: Just apply recommended settings
        auto_punctuation = True
        capitalize_sent = True
        remove_spaces = True
        improve_vietnamese = True
        extract_keywords_enabled = False
        summarize_enabled = False
        
        st.markdown("**Cài đặt tự động:** Tự động sửa dấu câu, viết hoa đầu câu, loại bỏ khoảng trắng thừa, cải thiện tiếng Việt")
    
    elif st.session_state.enhancement_mode == "recommended":
        # Recommended mode: Show key options
        col1, col2 = st.columns(2)
        
        with col1:
            auto_punctuation = st.checkbox("Tự động sửa dấu câu", value=True, help="Sửa và chuẩn hóa dấu câu tiếng Việt")
            capitalize_sent = st.checkbox("Viết hoa đầu câu", value=True, help="Viết hoa chữ cái đầu mỗi câu")
            remove_spaces = st.checkbox("Loại bỏ khoảng trắng thừa", value=True, help="Xóa các khoảng trắng không cần thiết")
            improve_vietnamese = st.checkbox("Cải thiện tiếng Việt", value=True, help="Áp dụng các cải thiện đặc biệt cho tiếng Việt")
        
        with col2:
            extract_keywords_enabled = st.checkbox("Extract keywords", value=True, help="Trích xuất từ khóa quan trọng")
            summarize_enabled = st.checkbox("Tạo summary", value=True, help="Tạo tóm tắt nội dung")
            
            if extract_keywords_enabled:
                num_keywords = st.number_input(
                    "Số keywords",
                    min_value=5,
                    max_value=50,
                    value=10,
                    help="Số lượng từ khóa cần trích xuất"
                )
            else:
                num_keywords = 10
            
            if summarize_enabled:
                num_sentences = st.number_input(
                    "Số câu trong summary",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Số câu tối đa trong tóm tắt"
                )
            else:
                num_sentences = 3
    
    else:  # advanced
        # Advanced mode: All options exposed
        st.markdown("#### 🔧 Tùy chỉnh chi tiết")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Formatting Options:**")
            auto_punctuation = st.checkbox("Tự động sửa dấu câu", value=True)
            capitalize_sent = st.checkbox("Viết hoa đầu câu", value=True)
            remove_spaces = st.checkbox("Loại bỏ khoảng trắng thừa", value=True)
            improve_vietnamese = st.checkbox("Cải thiện tiếng Việt", value=True)
        
        with col2:
            st.markdown("**Analysis Options:**")
            extract_keywords_enabled = st.checkbox("Extract keywords", value=False)
            summarize_enabled = st.checkbox("Tạo summary", value=False)
            
            num_keywords = st.number_input(
                "Số keywords",
                min_value=5,
                max_value=50,
                value=10,
                disabled=not extract_keywords_enabled
            )
            
            num_sentences = st.number_input(
                "Số câu trong summary",
                min_value=1,
                max_value=10,
                value=3,
                disabled=not summarize_enabled
            )
    
    # Display original transcript
    st.markdown("---")
    st.markdown("#### 📝 Original Transcript")
    st.text_area(
        "Original:",
        st.session_state.transcript_text,
        height=200,
        key="original_transcript_enhance",
        disabled=True
    )
    
    # Apply enhancement
    if st.button("✨ Apply AI Enhancement", type="primary", use_container_width=True):
        with st.spinner("Đang xử lý với AI..."):
            # Format text
            formatting_options = {
                "punctuation": auto_punctuation,
                "capitalize": capitalize_sent,
                "remove_extra_spaces": remove_spaces,
                "improve_vietnamese": improve_vietnamese
            }
            
            enhanced_text = format_text(st.session_state.transcript_text, formatting_options)
            st.session_state.transcript_enhanced = enhanced_text
            
            st.success("✅ Đã xử lý thành công!")
            st.rerun()
    
    # Display enhanced transcript with side-by-side comparison
    if st.session_state.transcript_enhanced:
        st.markdown("---")
        st.subheader("✨ Enhanced Transcript")
        
        # Side-by-side comparison
        compare_mode = st.radio(
            "Chế độ hiển thị",
            ["Enhanced only", "Side-by-side comparison"],
            horizontal=True,
            key="compare_mode"
        )
        
        if compare_mode == "Side-by-side comparison":
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📝 Original**")
                st.text_area(
                    "Original transcript:",
                    st.session_state.transcript_text,
                    height=300,
                    key="original_compare",
                    disabled=True
                )
            
            with col2:
                st.markdown("**✨ Enhanced**")
                enhanced_text = st.text_area(
                    "Enhanced transcript:",
                    st.session_state.transcript_enhanced,
                    height=300,
                    key="enhanced_compare"
                )
        else:
            enhanced_text = st.text_area(
                "Enhanced:",
                st.session_state.transcript_enhanced,
                height=300,
                key="enhanced_transcript_display"
            )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Lưu Enhanced Transcript", type="primary", use_container_width=True):
                st.session_state.transcript_text = enhanced_text
                st.session_state.transcript_enhanced = ""
                st.success("✅ Đã lưu enhanced transcript!")
                st.rerun()
        
        with col2:
            txt_data, txt_filename = export_txt(enhanced_text, "enhanced_transcript.txt")
            st.download_button(
                "📥 Download TXT",
                data=txt_data,
                file_name=txt_filename,
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            docx_data, docx_filename = export_docx(enhanced_text, None, "enhanced_transcript.docx")
            st.download_button(
                "📥 Download DOCX",
                data=docx_data,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        # Keywords
        if extract_keywords_enabled:
            st.markdown("---")
            st.subheader("🔑 Keywords")
            keywords = extract_keywords(enhanced_text, top_k=num_keywords)
            if keywords:
                # Display as tags/chips
                keyword_html = " ".join([f'<span style="background-color: #e3f2fd; padding: 5px 10px; border-radius: 15px; margin: 5px; display: inline-block; font-weight: bold;">{kw}</span>' for kw in keywords])
                st.markdown(keyword_html, unsafe_allow_html=True)
            else:
                st.info("Không tìm thấy keywords")
        
        # Summary
        if summarize_enabled:
            st.markdown("---")
            st.subheader("📄 Summary")
            summary = simple_summarize(enhanced_text, max_sentences=num_sentences)
            if summary:
                st.info(f"**Tóm tắt:** {summary}")
            else:
                st.info("Không thể tạo summary")

# ===== Navigation =====
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Go to Export & Report", use_container_width=True):
        st.switch_page("pages/4_📊_Export_Reporting.py")

with col2:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("pages/0_🏠_Home_Dashboard.py")

# ===== Footer =====
render_footer()
