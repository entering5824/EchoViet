"""
Speaker & Text Enhancement Page
Combined page: Speaker Diarization + AI Text Enhancement
Make transcript "clean & usable"
"""
import streamlit as st
import os
import sys
import re
import traceback
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
from app.components.diarization_timeline import render_diarization_timeline
from app.components.footer import render_footer
from core.diarization.speaker_diarization import (
    simple_speaker_segmentation, format_with_speakers, format_time
)
from core.nlp.post_processing import format_text
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

# ===== Helper Functions =====

def count_words(text: str) -> int:
    """Đếm số từ trong text"""
    if not text:
        return 0
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def parse_transcript_segments(transcript_text: str) -> List[Dict]:
    """
    Parse transcript text thành segments với timestamps
    
    Args:
        transcript_text: Transcript text có thể có format [start - end] text hoặc chỉ text
    
    Returns:
        List[Dict]: List of segments với keys: start, end, text
    """
    transcript_lines = transcript_text.split('\n')
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
            # No timestamp, estimate from previous segment
            prev_end = segments[-1]['end'] if segments else 0
            estimated_dur = max(2.0, len(line.split()) * 0.5)
            segments.append({'start': prev_end, 'end': prev_end + estimated_dur, 'text': line})
    
    return segments


def render_diarization_settings(use_english: bool = True) -> Tuple[int, float]:
    """
    Render UI cho diarization settings
    
    Args:
        use_english: Use English labels if True, Vietnamese if False
    
    Returns:
        Tuple[int, float]: (max_speakers, min_silence)
    """
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if use_english:
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
        else:
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
        if use_english:
            st.info("""
            **💡 Guide:**
            - Adjust number of speakers according to reality
            - Shorter silence = detect more transitions
            - Can edit speaker labels after running
            """)
        else:
            st.info("""
            **💡 Hướng dẫn:**
            - Điều chỉnh số lượng người nói theo thực tế
            - Khoảng im lặng ngắn hơn = phát hiện nhiều chuyển đổi hơn
            - Có thể chỉnh sửa speaker labels sau khi chạy
            """)
    
    return max_speakers, min_silence


def run_diarization_workflow(
    audio_data: Any,
    audio_sr: int,
    transcript_text: str,
    max_speakers: int,
    min_silence: float,
    use_english: bool = True
) -> Optional[List[Dict]]:
    """
    Chạy diarization workflow
    
    Args:
        audio_data: Audio data array
        audio_sr: Sample rate
        transcript_text: Transcript text
        max_speakers: Maximum number of speakers
        min_silence: Minimum silence duration
        use_english: Use English messages if True
    
    Returns:
        List[Dict] or None: Speaker segments nếu thành công, None nếu lỗi
    """
    try:
        # Parse transcript segments
        segments = parse_transcript_segments(transcript_text)
        
        # Run diarization
        speaker_segments = simple_speaker_segmentation(
            audio_data,
            audio_sr,
            segments if segments else transcript_text.split('\n'),
            min_silence_duration=min_silence,
            max_speakers=max_speakers
        )
        
        if speaker_segments:
            num_speakers = len(set(seg.get('speaker') for seg in speaker_segments))
            if use_english:
                st.success(f"✅ Detected {num_speakers} speakers in {len(speaker_segments)} segments!")
            else:
                st.success(f"✅ Đã phát hiện {num_speakers} người nói trong {len(speaker_segments)} segments!")
            
            # Show preview
            st.markdown("#### 👁️ Preview Results")
            preview_text = format_with_speakers(speaker_segments[:5])
            st.text_area(
                "Preview (first 5 segments):" if use_english else "Preview (5 segments đầu tiên):",
                preview_text,
                height=150,
                disabled=True
            )
            st.caption(
                f"Showing {min(5, len(speaker_segments))} first segments. See full results below."
                if use_english
                else f"Hiển thị {min(5, len(speaker_segments))} segments đầu tiên. Xem kết quả đầy đủ bên dưới."
            )
            return speaker_segments
        else:
            if use_english:
                st.warning("⚠️ Cannot distinguish speakers. May be due to audio too short or only 1 speaker.")
                st.info("💡 **Suggestion**: \n- Ensure audio has at least 2 speakers\n- Check if audio is clear\n- Try adjusting 'Minimum silence duration' smaller")
            else:
                st.warning("⚠️ Không thể phân biệt speaker. Có thể do audio quá ngắn hoặc chỉ có 1 người nói.")
            return None
            
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Error running diarization: {error_msg}" if use_english else f"❌ Lỗi khi chạy diarization: {error_msg}")
        if use_english:
            st.info("💡 **Suggestion**: \n- Check if audio is valid\n- Ensure audio was uploaded at Audio Input page\n- Try reducing expected number of speakers")
        with st.expander("🔍 Chi tiết lỗi" if not use_english else "🔍 Error Details"):
            st.code(traceback.format_exc())
        return None


def calculate_speaker_stats(speaker_segments: List[Dict], total_duration: float) -> Dict[str, Dict]:
    """
    Tính thống kê cho từng speaker
    
    Args:
        speaker_segments: List of speaker segments
        total_duration: Total audio duration
    
    Returns:
        Dict: Speaker statistics với keys: count, duration, percentage
    """
    speakers = set(seg.get('speaker') for seg in speaker_segments)
    speaker_stats = {}
    
    for speaker in speakers:
        speaker_segs = [s for s in speaker_segments if s.get('speaker') == speaker]
        total_dur = sum(s.get('end', 0) - s.get('start', 0) for s in speaker_segs)
        speaker_stats[speaker] = {
            'count': len(speaker_segs),
            'duration': total_dur,
            'percentage': (total_dur / (total_duration or 1)) * 100
        }
    
    return speaker_stats


def render_diarization_results(
    speaker_segments: List[Dict],
    duration: float,
    use_english: bool = True,
    key_suffix: str = ""
):
    """
    Hiển thị kết quả diarization (stats, timeline, transcript)
    
    Args:
        speaker_segments: List of speaker segments
        duration: Audio duration
        use_english: Use English labels if True
        key_suffix: Suffix for unique keys
    """
    st.markdown("---")
    st.subheader("📊 Diarization Results")
    
    # Statistics
    speaker_stats = calculate_speaker_stats(speaker_segments, duration)
    speakers = list(speaker_stats.keys())
    
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
    if duration > 0:
        render_diarization_timeline(speaker_segments, duration)
    
    # Transcript with speakers
    st.subheader("📝 Transcript with Speaker Labels" if use_english else "📝 Transcript với Speaker Labels")
    
    # Allow manual editing of speaker labels
    with st.expander("✏️ Edit Speaker Labels" if use_english else "✏️ Chỉnh sửa Speaker Labels", expanded=False):
        st.caption("Change speaker names or reassign segments to other speakers" if use_english else "Thay đổi tên speaker hoặc gán lại segments cho speakers khác")
        
        # Speaker renaming
        st.markdown("**Rename Speakers:**" if use_english else "**Đổi tên Speakers:**")
        rename_cols = st.columns(min(len(speakers), 4))
        speaker_rename_map = {}
        for idx, speaker in enumerate(sorted(speakers)):
            with rename_cols[idx % len(rename_cols)]:
                new_name = st.text_input(
                    f"Rename {speaker}",
                    value=speaker,
                    key=f"rename_{speaker}_{key_suffix}"
                )
                if new_name and new_name != speaker:
                    speaker_rename_map[speaker] = new_name
        
        if speaker_rename_map and st.button("💾 Apply Rename" if use_english else "💾 Áp dụng đổi tên"):
            for seg in speaker_segments:
                old_speaker = seg.get('speaker')
                if old_speaker in speaker_rename_map:
                    seg['speaker'] = speaker_rename_map[old_speaker]
            st.success("✅ Updated speaker names!" if use_english else "✅ Đã cập nhật tên speakers!")
            st.rerun()
    
    formatted_transcript = format_with_speakers(speaker_segments)
    st.text_area(
        "Transcript with speakers:" if use_english else "Transcript với speakers:",
        formatted_transcript,
        height=300,
        key=f"diarized_transcript_{key_suffix}"
    )
    
    # Update transcript text with speaker labels
    col1, col2 = st.columns(2)
    with col1:
        button_text = "💾 Apply Speaker Labels to Transcript" if use_english else "💾 Áp dụng Speaker Labels vào Transcript"
        if st.button(button_text, type="primary", use_container_width=True, key=f"apply_labels_{key_suffix}"):
            st.session_state.transcript_text = formatted_transcript
            st.success("✅ Updated transcript with speaker labels!" if use_english else "✅ Đã cập nhật transcript với speaker labels!")
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
                use_container_width=True,
                key=f"download_txt_{key_suffix}"
            )
        with export_col2:
            docx_data, docx_filename = export_docx(formatted_transcript, None, "transcript_with_speakers.docx")
            st.download_button(
                "📥 Download DOCX",
                data=docx_data,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key=f"download_docx_{key_suffix}"
            )


def render_diarization_section(container, use_english: bool = True):
    """
    Render diarization section trong container (tab hoặc main)
    
    Args:
        container: Streamlit container (tab hoặc st.container())
        use_english: Use English labels if True
    """
    with container:
        st.subheader("👥 Speaker Diarization")
        st.caption("Identify and label speakers in the meeting" if use_english else "Phân biệt và gán nhãn người nói trong cuộc họp")
        
        if st.session_state.audio_data is None:
            warning_text = "⚠️ Audio data required to run diarization. Please upload audio first." if use_english else "⚠️ Cần audio data để chạy diarization. Vui lòng upload audio trước."
            st.warning(warning_text)
            if st.button("🎤 Go to Audio Input", type="primary", key=f"go_audio_{use_english}"):
                st.switch_page("pages/1_🎤_Audio_Input.py")
        else:
            # Render settings
            max_speakers, min_silence = render_diarization_settings(use_english)
            
            # Run diarization button
            button_text = "🚀 Run Speaker Diarization" if use_english else "🚀 Chạy Speaker Diarization"
            spinner_text = "Analyzing speakers..." if use_english else "Đang phân tích speaker..."
            
            if st.button(button_text, type="primary", use_container_width=True, key=f"run_diarization_{use_english}"):
                with st.spinner(spinner_text):
                    speaker_segments = run_diarization_workflow(
                        st.session_state.audio_data,
                        st.session_state.audio_sr,
                        st.session_state.transcript_text,
                        max_speakers,
                        min_silence,
                        use_english
                    )
                    
                    if speaker_segments:
                        st.session_state.speaker_segments = speaker_segments
                        st.rerun()
            
            # Display results
            if st.session_state.speaker_segments:
                duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
                render_diarization_results(
                    st.session_state.speaker_segments,
                    duration,
                    use_english,
                    key_suffix=f"{use_english}"
                )


def render_enhancement_options(mode: str, gemini_available: bool) -> Dict[str, Any]:
    """
    Render UI cho enhancement options dựa trên mode
    
    Args:
        mode: Enhancement mode (simple, recommended, advanced)
        gemini_available: Whether Gemini AI is available
    
    Returns:
        Dict: Enhancement options
    """
    options = {
        'auto_punctuation': True,
        'capitalize_sent': True,
        'remove_spaces': True,
        'improve_vietnamese': True,
        'extract_keywords_enabled': False,
        'summarize_enabled': False,
        'num_keywords': 10,
        'num_sentences': 3,
        'use_gemini': False
    }
    
    if mode == "simple":
        st.markdown("**Automatic settings:** Automatically fix punctuation, capitalize sentences, remove extra spaces, improve Vietnamese")
        # Options already set to defaults
    
    elif mode == "recommended":
        col1, col2 = st.columns(2)
        
        with col1:
            options['auto_punctuation'] = st.checkbox("Auto fix punctuation", value=True, help="Fix and normalize Vietnamese punctuation")
            options['capitalize_sent'] = st.checkbox("Capitalize sentences", value=True, help="Capitalize first letter of each sentence")
            options['remove_spaces'] = st.checkbox("Remove extra spaces", value=True, help="Remove unnecessary spaces")
            options['improve_vietnamese'] = st.checkbox("Improve Vietnamese", value=True, help="Apply special improvements for Vietnamese")
            
            if gemini_available:
                options['use_gemini'] = st.checkbox(
                    "🤖 Use Gemini AI (Recommended)",
                    value=True,
                    help="Use Google Gemini AI to improve text with higher accuracy"
                )
                if options['use_gemini']:
                    st.info("💡 Gemini AI will improve text with AI, then apply other enhancements")
            else:
                st.info("💡 To use Gemini AI, configure GEMINI_API_KEY in environment variables")
        
        with col2:
            options['extract_keywords_enabled'] = st.checkbox("Extract keywords", value=True, help="Extract important keywords")
            options['summarize_enabled'] = st.checkbox("Create summary", value=True, help="Create content summary")
            
            if options['extract_keywords_enabled']:
                options['num_keywords'] = st.number_input(
                    "Number of keywords",
                    min_value=5,
                    max_value=50,
                    value=10,
                    help="Number of keywords to extract"
                )
            
            if options['summarize_enabled']:
                options['num_sentences'] = st.number_input(
                    "Number of sentences in summary",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="Maximum number of sentences in summary"
                )
    
    else:  # advanced
        st.markdown("#### 🔧 Tùy chỉnh chi tiết")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Formatting Options:**")
            options['auto_punctuation'] = st.checkbox("Auto fix punctuation", value=True)
            options['capitalize_sent'] = st.checkbox("Capitalize sentences", value=True)
            options['remove_spaces'] = st.checkbox("Remove extra spaces", value=True)
            options['improve_vietnamese'] = st.checkbox("Improve Vietnamese", value=True)
            
            if gemini_available:
                options['use_gemini'] = st.checkbox(
                    "🤖 Use Gemini AI",
                    value=False,
                    help="Use Google Gemini AI to improve text"
                )
            else:
                st.info("💡 To use Gemini AI, configure GEMINI_API_KEY in environment variables")
        
        with col2:
            st.markdown("**Analysis Options:**")
            options['extract_keywords_enabled'] = st.checkbox("Extract keywords", value=False)
            options['summarize_enabled'] = st.checkbox("Create summary", value=False)
            
            options['num_keywords'] = st.number_input(
                "Number of keywords",
                min_value=5,
                max_value=50,
                value=10,
                disabled=not options['extract_keywords_enabled']
            )
            
            options['num_sentences'] = st.number_input(
                "Number of sentences in summary",
                min_value=1,
                max_value=10,
                value=3,
                disabled=not options['summarize_enabled']
            )
    
    return options


def apply_text_enhancement(text: str, options: Dict[str, Any], gemini_available: bool, show_messages: bool = True) -> Tuple[str, Optional[str]]:
    """
    Apply text enhancement với options
    
    Args:
        text: Text to enhance
        options: Enhancement options dict
        gemini_available: Whether Gemini AI is available
        show_messages: Whether to show success/warning messages (default: True)
    
    Returns:
        Tuple[str, Optional[str]]: (enhanced_text, error_message)
    """
    try:
        if not text or not text.strip():
            return "", "Text is empty or invalid"
        
        text_to_enhance = text
        
        # Step 1: Use Gemini AI if enabled
        if options.get('use_gemini') and gemini_available:
            try:
                gemini_enhanced = enhance_with_gemini(text_to_enhance)
                if gemini_enhanced:
                    text_to_enhance = gemini_enhanced
                    if show_messages:
                        st.success("✅ Gemini AI improved the text")
                else:
                    if show_messages:
                        st.warning("⚠️ Gemini AI did not return results, using basic method")
            except Exception as gemini_error:
                if show_messages:
                    st.warning(f"⚠️ Error using Gemini AI: {str(gemini_error)}. Using basic method.")
        
        # Step 2: Apply formatting options
        formatting_options = {
            "punctuation": options.get('auto_punctuation', True),
            "capitalize": options.get('capitalize_sent', True),
            "remove_extra_spaces": options.get('remove_spaces', True),
            "improve_vietnamese": options.get('improve_vietnamese', True)
        }
        
        enhanced_text = format_text(text_to_enhance, formatting_options)
        
        return enhanced_text, None
        
    except Exception as e:
        error_msg = f"Error enhancing text: {str(e)}"
        return "", error_msg


# ===== Main Page Logic =====

# Initialize session state
for key, default in (
    ("audio_data", None),
    ("audio_sr", None),
    ("audio_info", None),
    ("transcript_text", ""),
    ("transcript_segments", []),
    ("speaker_segments", []),
    ("transcript_enhanced", ""),
    ("preview_enhanced", ""),
    ("enhancement_mode", "recommended"),
    ("enhancement_history", []),
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

# Feature selection
st.markdown("### 🎯 Select Enhancement Feature")

enhancement_option = st.radio(
    "What would you like to do?",
    ["✨ Text Enhancement Only (AI Text Enhancement)", "👥 Speaker Diarization Only", "🔄 Both (Text + Speaker)"],
    help="Select the feature you want to use. You can run both if needed."
)

# Determine which features to show
show_diarization = enhancement_option in ["👥 Speaker Diarization Only", "🔄 Both (Text + Speaker)"]
show_text_enhancement = enhancement_option in ["✨ Text Enhancement Only (AI Text Enhancement)", "🔄 Both (Text + Speaker)"]

# Use tabs only if both are selected
if show_diarization and show_text_enhancement:
    tab1, tab2 = st.tabs(["👥 Speaker Diarization", "✨ AI Text Enhancement"])
    tab1_container = tab1
    tab2_container = tab2
    use_english = True
else:
    tab1_container = st.container() if show_diarization else None
    tab2_container = st.container() if show_text_enhancement else None
    use_english = not show_diarization  # Use Vietnamese if standalone diarization

# ===== Speaker Diarization Section =====
if show_diarization:
    render_diarization_section(tab1_container, use_english=use_english)

# ===== AI Text Enhancement Section =====
if show_text_enhancement:
    container = tab2_container if show_diarization and show_text_enhancement else st.container()
    
    with container:
        st.subheader("✨ AI Text Enhancement")
        st.caption("Clean and improve text with AI")
        
        # Mode selection
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
        
        # Check if Gemini is available
        gemini_available = is_gemini_available()
        
        # Render enhancement options
        options = render_enhancement_options(st.session_state.enhancement_mode, gemini_available)
        
        # Preview section
        st.markdown("---")
        st.markdown("### 👁️ Preview & Apply")
        
        preview_col1, preview_col2 = st.columns(2)
        with preview_col1:
            st.markdown("**📝 Văn bản gốc:**")
            preview_original = (
                st.session_state.transcript_text[:500] + "..."
                if len(st.session_state.transcript_text) > 500
                else st.session_state.transcript_text
            )
            st.text_area(
                "Văn bản gốc (xem trước):",
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
            st.markdown("**✨ Văn bản đã cải thiện:**")
            
            # Preview enhancement button
            if st.button("🔍 Xem trước cải thiện", use_container_width=True, key="preview_enhance"):
                with st.spinner("⏳ Đang xử lý với AI..."):
                    preview_text, preview_error = apply_text_enhancement(
                        st.session_state.transcript_text[:1000],  # Preview first 1000 chars
                        options,
                        gemini_available,
                        show_messages=False
                    )
                    
                    if preview_error:
                        st.error(f"❌ Lỗi: {preview_error}")
                    else:
                        st.session_state.preview_enhanced = preview_text
                        st.success("✅ Xem trước thành công!")
                        st.rerun()
            
            # Show preview result
            if st.session_state.get("preview_enhanced"):
                preview_enhanced = st.session_state.preview_enhanced
                st.text_area(
                    "Kết quả xem trước:",
                    preview_enhanced[:500] + ("..." if len(preview_enhanced) > 500 else ""),
                    height=200,
                    disabled=True,
                    key="preview_enhanced_display"
                )
                st.caption("💡 Đây là kết quả xem trước. Nhấn 'Áp dụng' để xử lý toàn bộ văn bản.")
            else:
                st.info("💡 Nhấn 'Xem trước cải thiện' để xem kết quả trước khi áp dụng")
        
        # Apply enhancement button
        col_apply1, col_apply2 = st.columns([1, 1])
        with col_apply1:
            if st.button("✨ Áp dụng cải thiện văn bản", type="primary", use_container_width=True, key="apply_enhance"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("⏳ Đang xử lý với AI...")
                    progress_bar.progress(10)
                    
                    enhanced_text, error = apply_text_enhancement(
                        st.session_state.transcript_text,
                        options,
                        gemini_available,
                        show_messages=True
                    )
                    
                    progress_bar.progress(80)
                    
                    if error:
                        progress_bar.progress(100)
                        status_text.text("❌ Lỗi!")
                        st.error(f"❌ Lỗi khi cải thiện văn bản: {error}")
                        st.info("💡 **Gợi ý**: \n- Kiểm tra xem transcript có hợp lệ không\n- Thử lại với chế độ 'Simple'\n- Kiểm tra GEMINI_API_KEY nếu sử dụng Gemini AI")
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.code(traceback.format_exc())
                    else:
                        progress_bar.progress(100)
                        status_text.text("✅ Hoàn thành!")
                        st.session_state.transcript_enhanced = enhanced_text
                        
                        # Save enhancement options to session state
                        st.session_state.enhancement_extract_keywords = options.get('extract_keywords_enabled', False)
                        st.session_state.enhancement_summarize = options.get('summarize_enabled', False)
                        st.session_state.enhancement_num_keywords = options.get('num_keywords', 10)
                        st.session_state.enhancement_num_sentences = options.get('num_sentences', 3)
                        
                        st.success("✅ Xử lý thành công!")
                        progress_bar.empty()
                        status_text.empty()
                        st.rerun()
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text("❌ Lỗi!")
                    st.error(f"❌ Lỗi không mong đợi: {str(e)}")
                    with st.expander("🔍 Chi tiết lỗi"):
                        st.code(traceback.format_exc())
        
        with col_apply2:
            if st.button("🔄 Đặt lại", use_container_width=True, key="reset_enhance"):
                st.session_state.transcript_enhanced = ""
                st.session_state.preview_enhanced = ""
                st.success("✅ Đã đặt lại!")
                st.rerun()

# ===== Display Enhanced Transcript =====
if st.session_state.transcript_enhanced:
    st.markdown("---")
    st.subheader("✨ Enhanced Transcript")
    
    # Side-by-side comparison
    compare_mode = st.radio(
        "Chế độ hiển thị:",
        ["Chỉ văn bản đã cải thiện", "So sánh cạnh nhau"],
        horizontal=True,
        key="compare_mode"
    )
    
    if compare_mode == "So sánh cạnh nhau":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📝 Văn bản gốc**")
            original_word_count = count_words(st.session_state.transcript_text)
            st.text_area(
                "Văn bản gốc:",
                st.session_state.transcript_text,
                height=300,
                key="original_compare",
                disabled=True
            )
            st.caption(f"📊 {original_word_count} từ · {len(st.session_state.transcript_text)} ký tự")
        
        with col2:
            st.markdown("**✨ Văn bản đã cải thiện**")
            enhanced_word_count = count_words(st.session_state.transcript_enhanced)
            enhanced_text = st.text_area(
                "Văn bản đã cải thiện:",
                st.session_state.transcript_enhanced,
                height=300,
                key="enhanced_compare"
            )
            st.caption(f"📊 {enhanced_word_count} từ · {len(st.session_state.transcript_enhanced)} ký tự")
            
            # Show difference
            if original_word_count > 0:
                word_diff = enhanced_word_count - original_word_count
                if word_diff != 0:
                    diff_text = f"({word_diff:+d} từ)" if word_diff != 0 else ""
                    st.caption(f"💡 Thay đổi: {diff_text}")
    else:
        enhanced_text = st.text_area(
            "Văn bản đã cải thiện:",
            st.session_state.transcript_enhanced,
            height=300,
            key="enhanced_transcript_display"
        )
        enhanced_word_count = count_words(st.session_state.transcript_enhanced)
        st.caption(f"📊 {enhanced_word_count} từ · {len(st.session_state.transcript_enhanced)} ký tự")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Lưu văn bản đã cải thiện", type="primary", use_container_width=True):
            st.session_state.transcript_text = enhanced_text
            # Save to history
            if "enhancement_history" not in st.session_state:
                st.session_state.enhancement_history = []
            st.session_state.enhancement_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": enhanced_text,
                "mode": st.session_state.enhancement_mode
            })
            st.session_state.transcript_enhanced = ""
            st.session_state.preview_enhanced = ""
            st.success("✅ Đã lưu văn bản đã cải thiện!")
            st.rerun()
    
    with col2:
        try:
            txt_data, txt_filename = export_txt(enhanced_text, "enhanced_transcript.txt")
            st.download_button(
                "📥 Tải TXT",
                data=txt_data,
                file_name=txt_filename,
                mime="text/plain",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Lỗi export TXT: {str(e)}")
    
    with col3:
        try:
            metadata = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "word_count": count_words(enhanced_text),
                "enhancement_mode": st.session_state.enhancement_mode
            }
            docx_data, docx_filename = export_docx(enhanced_text, metadata, "enhanced_transcript.docx")
            st.download_button(
                "📥 Tải DOCX",
                data=docx_data,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Lỗi export DOCX: {str(e)}")
    
    with col4:
        if st.button("📊 Chuyển đến Export", use_container_width=True):
            st.switch_page("pages/4_📊_Export_Reporting.py")
    
    # Keywords
    extract_keywords_enabled = st.session_state.get("enhancement_extract_keywords", False)
    if extract_keywords_enabled:
        st.markdown("---")
        st.subheader("🔑 Keywords")
        num_keywords = st.session_state.get("enhancement_num_keywords", 10)
        
        keyword_counts = extract_keywords(
            enhanced_text,
            top_k=num_keywords,
            return_with_counts=True,
        )
        
        if keyword_counts:
            enhanced_word_count = count_words(enhanced_text)
            st.caption(f"Tổng số từ sau cải thiện (ước tính): **{enhanced_word_count}** từ")
            
            # Display keywords as chips
            tags_html = " ".join(
                [
                    f'<span style="background-color: #e3f2fd; padding: 5px 10px; '
                    f'border-radius: 15px; margin: 5px; display: inline-block; '
                    f'font-weight: bold;">{kw}</span>'
                    for kw, _ in keyword_counts
                ]
            )
            st.markdown(tags_html, unsafe_allow_html=True)
            
            # Frequency table
            st.markdown("**📊 Tần suất xuất hiện từ khóa:**")
            freq_data = {
                "Keyword": [kw for kw, _ in keyword_counts],
                "Số lần xuất hiện": [cnt for _, cnt in keyword_counts],
            }
            st.table(freq_data)
        else:
            st.info("No keywords found")
    
    # Summary
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
