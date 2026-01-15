"""
Speaker & Text Enhancement Page
Combined page: Speaker Diarization + AI Text Enhancement
Make transcript "clean & usable"
"""
import streamlit as st
import os
import sys
import json
import re
from collections import Counter

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
from core.nlp.gemini_enhancement import enhance_with_gemini, is_gemini_available
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

# Helper: đếm số từ trong text
def count_words(text: str) -> int:
    if not text:
        return 0
    # Đếm theo word boundary để ổn định hơn với tiếng Việt có dấu
    words = re.findall(r'\b\w+\b', text)
    return len(words)

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

render_page_header("Speaker & Text Enhancement", "Identify speakers and clean text with AI", "✨")

# Check prerequisites
if not st.session_state.transcript_text:
    st.warning("⚠️ Please run transcription first at 'Transcription' page")
    if st.button("📝 Go to Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
    st.stop()

st.success("✅ Transcript is ready for enhancement")

# Simplified workflow: Show both options but make it clearer
st.markdown("### 🎯 Select Enhancement Feature")

enhancement_option = st.radio(
    "What would you like to do?",
    ["✨ Text Enhancement Only (AI Text Enhancement)", "👥 Speaker Diarization Only", "🔄 Both (Text + Speaker)"],
    help="Select the feature you want to use. You can run both if needed."
)

# Determine which tabs to show
show_diarization = enhancement_option in ["👥 Speaker Diarization Only", "🔄 Both (Text + Speaker)"]
show_text_enhancement = enhancement_option in ["✨ Text Enhancement Only (AI Text Enhancement)", "🔄 Both (Text + Speaker)"]

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
            st.caption("Identify and label speakers in the meeting")
            
            if st.session_state.audio_data is None:
                st.warning("⚠️ Audio data required to run diarization. Please upload audio first.")
                if st.button("🎤 Go to Audio Input", type="primary"):
                    st.switch_page("pages/1_🎤_Audio_Input.py")
            else:
                # Settings
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    max_speakers = st.number_input(
                        "Expected number of speakers",
                        min_value=1,
                        max_value=10,
                        value=4,
                        help="Maximum number of speakers in audio. System will automatically classify and rotate between speakers."
                    )
                    
                    min_silence = st.slider(
                        "Minimum silence duration (seconds)",
                        min_value=0.1,
                        max_value=2.0,
                        value=0.5,
                        step=0.1,
                        help="Minimum silence duration to separate between speakers"
                    )
                
                with col2:
                    st.info("""
                    **💡 Guide:**
                    - Adjust number of speakers according to reality
                    - Shorter silence = detect more transitions
                    - Can edit speaker labels after running
                    """)
                
                # Run diarization
                if st.button("🚀 Run Speaker Diarization", type="primary", use_container_width=True):
                    with st.spinner("Analyzing speakers..."):
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
                                st.success(f"✅ Detected {num_speakers} speakers in {len(speaker_segments)} segments!")
                                
                                # Show preview
                                st.markdown("#### 👁️ Preview Results")
                                preview_text = format_with_speakers(speaker_segments[:5])  # Show first 5 segments
                                st.text_area("Preview (first 5 segments):", preview_text, height=150, disabled=True)
                                st.caption(f"Showing {min(5, len(speaker_segments))} first segments. See full results below.")
                            else:
                                st.warning("⚠️ Cannot distinguish speakers. May be due to audio too short or only 1 speaker.")
                                st.info("💡 **Suggestion**: \n- Ensure audio has at least 2 speakers\n- Check if audio is clear\n- Try adjusting 'Minimum silence duration' smaller")
                        except Exception as e:
                            error_msg = str(e)
                            st.error(f"❌ Error running diarization: {error_msg}")
                            st.info("💡 **Suggestion**: \n- Check if audio is valid\n- Ensure audio was uploaded at Audio Input page\n- Try reducing expected number of speakers")
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
                    st.subheader("📝 Transcript with Speaker Labels")
                    
                    # Allow manual editing of speaker labels
                    with st.expander("✏️ Edit Speaker Labels", expanded=False):
                        st.caption("Change speaker names or reassign segments to other speakers")
                        
                        # Speaker renaming
                        st.markdown("**Rename Speakers:**")
                        rename_cols = st.columns(min(len(speakers), 4))
                        speaker_rename_map = {}
                        for idx, speaker in enumerate(sorted(speakers)):
                            with rename_cols[idx % len(rename_cols)]:
                                new_name = st.text_input(
                                    f"Rename {speaker}",
                                    value=speaker,
                                    key=f"rename_{speaker}"
                                )
                                if new_name and new_name != speaker:
                                    speaker_rename_map[speaker] = new_name
                        
                        if speaker_rename_map and st.button("💾 Apply Rename"):
                            for seg in st.session_state.speaker_segments:
                                old_speaker = seg.get('speaker')
                                if old_speaker in speaker_rename_map:
                                    seg['speaker'] = speaker_rename_map[old_speaker]
                            st.success("✅ Updated speaker names!")
                            st.rerun()
                    
                    formatted_transcript = format_with_speakers(st.session_state.speaker_segments)
                    st.text_area(
                        "Transcript with speakers:",
                        formatted_transcript,
                        height=300,
                        key="diarized_transcript"
                    )
                    
                    # Update transcript text with speaker labels
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 Apply Speaker Labels to Transcript", type="primary", use_container_width=True):
                            st.session_state.transcript_text = formatted_transcript
                            st.success("✅ Updated transcript with speaker labels!")
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
    
    # Handle case when not using tabs (standalone diarization)
    elif not (show_diarization and show_text_enhancement) and show_diarization:
        st.subheader("👥 Speaker Diarization")
        st.caption("Phân biệt và gán nhãn người nói trong cuộc họp")
        
        if st.session_state.audio_data is None:
            st.warning("⚠️ Cần audio data để chạy diarization. Vui lòng upload audio trước.")
            if st.button("🎤 Go to Audio Input", type="primary"):
                st.switch_page("pages/1_🎤_Audio_Input.py")
        else:
            # Same code as above but without tab context
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
            
            # Run diarization (same logic as above)
            if st.button("🚀 Chạy Speaker Diarization", type="primary", use_container_width=True):
                with st.spinner("Đang phân tích speaker..."):
                    try:
                        transcript_lines = st.session_state.transcript_text.split('\n')
                        segments = []
                        
                        for line in transcript_lines:
                            line = line.strip()
                            if not line:
                                continue
                            ts_match = re.match(r'\[([\d.]+)\s*-\s*([\d.]+)\]\s*(.+)', line)
                            if ts_match:
                                start, end, text = float(ts_match.group(1)), float(ts_match.group(2)), ts_match.group(3)
                                segments.append({'start': start, 'end': end, 'text': text.strip()})
                            else:
                                prev_end = segments[-1]['end'] if segments else 0
                                estimated_dur = max(2.0, len(line.split()) * 0.5)
                                segments.append({'start': prev_end, 'end': prev_end + estimated_dur, 'text': line})
                        
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
                            st.rerun()
                        else:
                            st.warning("⚠️ Không thể phân biệt speaker. Có thể do audio quá ngắn hoặc chỉ có 1 người nói.")
                    except Exception as e:
                        st.error(f"❌ Lỗi khi chạy diarization: {str(e)}")
            
            # Display results (same as above)
            if st.session_state.speaker_segments:
                st.markdown("---")
                st.subheader("📊 Diarization Results")
                speakers = set(seg.get('speaker') for seg in st.session_state.speaker_segments)
                formatted_transcript = format_with_speakers(st.session_state.speaker_segments)
                st.text_area("Transcript với speakers:", formatted_transcript, height=300, key="diarized_transcript_standalone")
                
                if st.button("💾 Áp dụng Speaker Labels vào Transcript", type="primary", use_container_width=True):
                    st.session_state.transcript_text = formatted_transcript
                    st.success("✅ Đã cập nhật transcript với speaker labels!")
                    st.rerun()

# ===== AI Text Enhancement =====
if show_text_enhancement:
    if show_diarization and show_text_enhancement:
        with tab2:
            st.subheader("✨ AI Text Enhancement")
            st.caption("Clean and improve text with AI")
            
            # Simplified mode selection - default to recommended
            use_advanced_enhance = st.checkbox(
                "⚙️ Show advanced options",
                value=False,
                help="Enable to customize detailed text enhancement parameters"
            )
            
            if use_advanced_enhance:
                mode_options = {
                    "simple": "🎯 Simple - Automatic basic enhancement",
                    "recommended": "⭐ Recommended - Optimal enhancement (Recommended)",
                    "advanced": "⚙️ Advanced - Detailed customization"
                }
                
                selected_mode = st.radio(
                    "Select enhancement mode:",
                    options=list(mode_options.keys()),
                    format_func=lambda x: mode_options[x],
                    index=list(mode_options.keys()).index(st.session_state.enhancement_mode) if st.session_state.enhancement_mode in mode_options else 1,
                    help="'Recommended' mode is the best choice for most cases"
                )
                st.session_state.enhancement_mode = selected_mode
            else:
                st.session_state.enhancement_mode = "recommended"
                st.info("💡 **Recommended Mode**: Uses optimal settings. Enable 'Advanced options' to customize.")
            
            # Initialize variables to avoid NameError
            auto_punctuation = True
            capitalize_sent = True
            remove_spaces = True
            improve_vietnamese = True
            extract_keywords_enabled = False
            summarize_enabled = False
            num_keywords = 10
            num_sentences = 3
            use_gemini = False
            
            # Check if Gemini is available
            gemini_available = is_gemini_available()
            
            # Enhancement options based on mode
            if st.session_state.enhancement_mode == "simple":
                # Simple mode: Just apply recommended settings
                auto_punctuation = True
                capitalize_sent = True
                remove_spaces = True
                improve_vietnamese = True
                extract_keywords_enabled = False
                summarize_enabled = False
                use_gemini = False
                
                st.markdown("**Automatic settings:** Automatically fix punctuation, capitalize sentences, remove extra spaces, improve Vietnamese")
            
            elif st.session_state.enhancement_mode == "recommended":
                # Recommended mode: Show key options
                col1, col2 = st.columns(2)
                
                with col1:
                    auto_punctuation = st.checkbox("Auto fix punctuation", value=True, help="Fix and normalize Vietnamese punctuation")
                    capitalize_sent = st.checkbox("Capitalize sentences", value=True, help="Capitalize first letter of each sentence")
                    remove_spaces = st.checkbox("Remove extra spaces", value=True, help="Remove unnecessary spaces")
                    improve_vietnamese = st.checkbox("Improve Vietnamese", value=True, help="Apply special improvements for Vietnamese")
                    
                    # Gemini AI option
                    if gemini_available:
                        use_gemini = st.checkbox(
                            "🤖 Use Gemini AI (Recommended)",
                            value=True,
                            help="Use Google Gemini AI to improve text with higher accuracy"
                        )
                        if use_gemini:
                            st.info("💡 Gemini AI will improve text with AI, then apply other enhancements")
                    else:
                        st.info("💡 To use Gemini AI, configure GEMINI_API_KEY in environment variables")
                
                with col2:
                    extract_keywords_enabled = st.checkbox("Extract keywords", value=True, help="Extract important keywords")
                    summarize_enabled = st.checkbox("Create summary", value=True, help="Create content summary")
                    
                    if extract_keywords_enabled:
                        num_keywords = st.number_input(
                            "Number of keywords",
                            min_value=5,
                            max_value=50,
                            value=10,
                            help="Number of keywords to extract"
                        )
                    else:
                        num_keywords = 10
                    
                    if summarize_enabled:
                        num_sentences = st.number_input(
                            "Number of sentences in summary",
                            min_value=1,
                            max_value=10,
                            value=3,
                            help="Maximum number of sentences in summary"
                        )
                    else:
                        num_sentences = 3
            
            else:  # advanced
                # Advanced mode: All options exposed
                st.markdown("#### 🔧 Tùy chỉnh chi tiết")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Formatting Options:**")
                    auto_punctuation = st.checkbox("Auto fix punctuation", value=True)
                    capitalize_sent = st.checkbox("Capitalize sentences", value=True)
                    remove_spaces = st.checkbox("Remove extra spaces", value=True)
                    improve_vietnamese = st.checkbox("Improve Vietnamese", value=True)
                    
                    # Gemini AI option
                    if gemini_available:
                        use_gemini = st.checkbox(
                            "🤖 Use Gemini AI",
                            value=False,
                            help="Use Google Gemini AI to improve text"
                        )
                    else:
                        st.info("💡 To use Gemini AI, configure GEMINI_API_KEY in environment variables")
                        use_gemini = False
                
                with col2:
                    st.markdown("**Analysis Options:**")
                    extract_keywords_enabled = st.checkbox("Extract keywords", value=False)
                    summarize_enabled = st.checkbox("Create summary", value=False)
                    
                    num_keywords = st.number_input(
                        "Number of keywords",
                        min_value=5,
                        max_value=50,
                        value=10,
                        disabled=not extract_keywords_enabled
                    )
                    
                    num_sentences = st.number_input(
                        "Number of sentences in summary",
                        min_value=1,
                        max_value=10,
                        value=3,
                        disabled=not summarize_enabled
                    )
            
            # Thống kê + preview trước khi áp dụng
            st.markdown("---")
            st.markdown("### 👁️ Preview")
            
            preview_col1, preview_col2 = st.columns(2)
            with preview_col1:
                st.markdown("**📝 Original text:**")
                preview_original = (
                    st.session_state.transcript_text[:500] + "..."
                    if len(st.session_state.transcript_text) > 500
                    else st.session_state.transcript_text
                )
                st.text_area(
                    "Original (preview):",
                    preview_original,
                    height=200,
                    disabled=True,
                    key="preview_original_enhance",
                )

                original_word_count = count_words(st.session_state.transcript_text)
                st.caption(
                    f"Hiển thị {min(500, len(st.session_state.transcript_text))} ký tự đầu tiên. "
                    f"Tổng: {len(st.session_state.transcript_text)} ký tự · {original_word_count} từ (ước tính)"
                )
            
            with preview_col2:
                st.markdown("**✨ Enhanced text:**")
                st.info("Results will be displayed here after you click 'Apply'")
            
            # Apply enhancement button
            if st.button("✨ Apply Text Enhancement", type="primary", use_container_width=True, key="apply_enhance_tab"):
                with st.spinner("⏳ Đang xử lý với AI..."):
                    try:
                        text_to_enhance = st.session_state.transcript_text
                        
                        # Step 1: Use Gemini AI if enabled
                        if use_gemini and gemini_available:
                            with st.spinner("🤖 Improving with Gemini AI..."):
                                try:
                                    gemini_enhanced = enhance_with_gemini(text_to_enhance)
                                    if gemini_enhanced:
                                        text_to_enhance = gemini_enhanced
                                        st.success("✅ Gemini AI improved the text")
                                    else:
                                        st.warning("⚠️ Gemini AI did not return results, using basic method")
                                except Exception as gemini_error:
                                    st.warning(f"⚠️ Error using Gemini AI: {str(gemini_error)}. Using basic method.")
                        
                        # Step 2: Apply formatting options
                        formatting_options = {
                            "punctuation": auto_punctuation,
                            "capitalize": capitalize_sent,
                            "remove_extra_spaces": remove_spaces,
                            "improve_vietnamese": improve_vietnamese
                        }
                        
                        enhanced_text = format_text(text_to_enhance, formatting_options)
                        st.session_state.transcript_enhanced = enhanced_text
                        
                        # Save enhancement options to session state for later use
                        st.session_state.enhancement_extract_keywords = extract_keywords_enabled
                        st.session_state.enhancement_summarize = summarize_enabled
                        st.session_state.enhancement_num_keywords = num_keywords
                        st.session_state.enhancement_num_sentences = num_sentences
                        
                        st.success("✅ Processed successfully!")
                        
                        # Show preview of enhanced text
                        preview_enhanced = enhanced_text[:500] + "..." if len(enhanced_text) > 500 else enhanced_text
                        with preview_col2:
                            st.text_area("Enhanced (preview):", preview_enhanced, height=200, disabled=True, key="preview_enhanced_result")
                            st.caption(f"Showing {min(500, len(enhanced_text))} first characters. Total: {len(enhanced_text)} characters")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error improving text: {str(e)}")
                        st.info("💡 **Suggestion**: \n- Check if transcript is valid\n- Try again with 'Simple' mode\n- Check GEMINI_API_KEY if using Gemini AI")
                        with st.expander("🔍 Chi tiết lỗi"):
                            import traceback
                            st.code(traceback.format_exc())
    
    # Display enhanced transcript with side-by-side comparison
    if st.session_state.transcript_enhanced:
        st.markdown("---")
        st.subheader("✨ Enhanced Transcript")
        
        # Side-by-side comparison
        compare_mode = st.radio(
            "Display mode",
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
            if st.button("💾 Save Enhanced Transcript", type="primary", use_container_width=True):
                st.session_state.transcript_text = enhanced_text
                st.session_state.transcript_enhanced = ""
                st.success("✅ Saved enhanced transcript!")
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
        
        # Keywords - use session state values
        extract_keywords_enabled = st.session_state.get("enhancement_extract_keywords", False)
        if extract_keywords_enabled:
            st.markdown("---")
            st.subheader("🔑 Keywords")
            num_keywords = st.session_state.get("enhancement_num_keywords", 10)

            # Lấy keyword kèm tần suất
            keyword_counts = extract_keywords(
                enhanced_text,
                top_k=num_keywords,
                return_with_counts=True,
            )

            if keyword_counts:
                # Hiển thị tổng số từ sau cải thiện
                enhanced_word_count = count_words(enhanced_text)
                st.caption(f"Tổng số từ sau cải thiện (ước tính): **{enhanced_word_count}** từ")

                # Hiển thị keyword theo dạng chips + bảng tần suất
                tags_html = " ".join(
                    [
                        f'<span style="background-color: #e3f2fd; padding: 5px 10px; '
                        f'border-radius: 15px; margin: 5px; display: inline-block; '
                        f'font-weight: bold;">{kw}</span>'
                        for kw, _ in keyword_counts
                    ]
                )
                st.markdown(tags_html, unsafe_allow_html=True)

                # Bảng tần suất để thấy keyword nào xuất hiện nhiều
                st.markdown("**📊 Tần suất xuất hiện từ khóa:**")
                freq_data = {
                    "Keyword": [kw for kw, _ in keyword_counts],
                    "Số lần xuất hiện": [cnt for _, cnt in keyword_counts],
                }
                st.table(freq_data)
            else:
                st.info("No keywords found")
        
        # Summary - use session state values
        summarize_enabled = st.session_state.get("enhancement_summarize", False)
        if summarize_enabled:
            st.markdown("---")
            st.subheader("📄 Summary")
            num_sentences = st.session_state.get("enhancement_num_sentences", 3)
            summary = simple_summarize(enhanced_text, max_sentences=num_sentences)
            if summary:
                st.info(f"**Summary:** {summary}")
            else:
                st.info("Cannot create summary")

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
