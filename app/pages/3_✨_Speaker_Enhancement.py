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

st.success("✅ Transcript đã sẵn sàng cho enhancement")

# Simplified workflow: Show both options but make it clearer
st.markdown("### 🎯 Chọn tính năng cải thiện")

enhancement_option = st.radio(
    "Bạn muốn làm gì?",
    ["✨ Chỉ cải thiện văn bản (AI Text Enhancement)", "👥 Phân biệt người nói (Speaker Diarization)", "🔄 Cả hai (Text + Speaker)"],
    help="Chọn tính năng bạn muốn sử dụng. Có thể chạy cả hai nếu cần."
)

# Determine which tabs to show
show_diarization = enhancement_option in ["👥 Phân biệt người nói (Speaker Diarization)", "🔄 Cả hai (Text + Speaker)"]
show_text_enhancement = enhancement_option in ["✨ Chỉ cải thiện văn bản (AI Text Enhancement)", "🔄 Cả hai (Text + Speaker)"]

# Use tabs only if both are selected
if show_diarization and show_text_enhancement:
    tab1, tab2 = st.tabs(["👥 Speaker Diarization", "✨ AI Text Enhancement"])
else:
    # Create dummy tabs for consistent structure
    tab1 = st.container() if show_diarization else None
    tab2 = st.container() if show_text_enhancement else None

# ===== Speaker Diarization =====
if show_diarization:
    if show_diarization and show_text_enhancement:
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
                        
                        # Show preview
                        st.markdown("#### 👁️ Xem trước kết quả")
                        preview_text = format_with_speakers(speaker_segments[:5])  # Show first 5 segments
                        st.text_area("Preview (5 segments đầu):", preview_text, height=150, disabled=True)
                        st.caption(f"Hiển thị {min(5, len(speaker_segments))} segments đầu tiên. Xem đầy đủ ở phần kết quả bên dưới.")
                    else:
                        st.warning("⚠️ Không thể phân biệt speaker. Có thể do audio quá ngắn hoặc chỉ có 1 người nói.")
                        st.info("💡 **Gợi ý**: \n- Đảm bảo audio có ít nhất 2 người nói\n- Kiểm tra audio có rõ ràng không\n- Thử điều chỉnh 'Khoảng im lặng tối thiểu' nhỏ hơn")
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Lỗi khi chạy diarization: {error_msg}")
                    st.info("💡 **Gợi ý**: \n- Kiểm tra audio có hợp lệ không\n- Đảm bảo đã upload audio ở trang Audio Input\n- Thử giảm số lượng người nói dự kiến")
                    with st.expander("🔍 Chi tiết lỗi"):
                        import traceback
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

# ===== AI Text Enhancement =====
if show_text_enhancement:
    if show_diarization and show_text_enhancement:
        with tab2:
            st.subheader("✨ AI Text Enhancement")
            st.caption("Làm sạch và cải thiện văn bản với AI")
            
            # Simplified mode selection - default to recommended
            use_advanced_enhance = st.checkbox(
                "⚙️ Hiển thị tùy chọn nâng cao",
                value=False,
                help="Bật để tùy chỉnh chi tiết các thông số cải thiện văn bản"
            )
            
            if use_advanced_enhance:
                mode_options = {
                    "simple": "🎯 Đơn giản - Tự động cải thiện cơ bản",
                    "recommended": "⭐ Đề xuất - Cải thiện tối ưu (Khuyến nghị)",
                    "advanced": "⚙️ Nâng cao - Tùy chỉnh chi tiết"
                }
                
                selected_mode = st.radio(
                    "Chọn chế độ cải thiện:",
                    options=list(mode_options.keys()),
                    format_func=lambda x: mode_options[x],
                    index=list(mode_options.keys()).index(st.session_state.enhancement_mode) if st.session_state.enhancement_mode in mode_options else 1,
                    help="Chế độ 'Đề xuất' là lựa chọn tốt nhất cho hầu hết trường hợp"
                )
                st.session_state.enhancement_mode = selected_mode
            else:
                st.session_state.enhancement_mode = "recommended"
                st.info("💡 **Chế độ Đề xuất**: Sử dụng cài đặt tối ưu. Bật 'Tùy chọn nâng cao' để tùy chỉnh.")
            
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
            
            # Show preview before applying
            st.markdown("---")
            st.markdown("### 👁️ Xem trước")
            
            preview_col1, preview_col2 = st.columns(2)
            with preview_col1:
                st.markdown("**📝 Văn bản gốc:**")
                preview_original = st.session_state.transcript_text[:500] + "..." if len(st.session_state.transcript_text) > 500 else st.session_state.transcript_text
                st.text_area("Original (preview):", preview_original, height=200, disabled=True, key="preview_original_enhance")
                st.caption(f"Hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu. Tổng: {len(st.session_state.transcript_text)} ký tự")
            
            with preview_col2:
                st.markdown("**✨ Văn bản sau cải thiện:**")
                st.info("Kết quả sẽ hiển thị ở đây sau khi bạn nhấn 'Áp dụng'")
            
            # Apply enhancement button is already above
        with st.spinner("⏳ Đang xử lý với AI..."):
            try:
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
                
                # Show preview of enhanced text
                preview_enhanced = enhanced_text[:500] + "..." if len(enhanced_text) > 500 else enhanced_text
                with preview_col2:
                    st.text_area("Enhanced (preview):", preview_enhanced, height=200, disabled=True, key="preview_enhanced_result")
                    st.caption(f"Hiển thị {min(500, len(enhanced_text))} ký tự đầu. Tổng: {len(enhanced_text)} ký tự")
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ Lỗi khi cải thiện văn bản: {str(e)}")
                st.info("💡 **Gợi ý**: \n- Kiểm tra transcript có hợp lệ không\n- Thử lại với chế độ 'Đơn giản'")
                with st.expander("🔍 Chi tiết lỗi"):
                    import traceback
                    st.code(traceback.format_exc())
    
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
