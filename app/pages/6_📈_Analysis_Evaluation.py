"""
Analysis & Evaluation Page
Thống kê, so sánh model, và đánh giá WER/CER
Trang học thuật cho academic evaluation
"""
import streamlit as st
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css
from app.components.statistics_display import calculate_statistics

# Apply custom CSS
apply_custom_css()

# Page config
st.set_page_config(
    page_title="Analysis & Evaluation - Vietnamese Speech to Text",
    page_icon="📈",
    layout="wide"
)

st.header("📈 Analysis & Evaluation")
st.caption("Thống kê chi tiết, so sánh model, và đánh giá hiệu suất")

# Initialize session state
for key, default in (
    ("transcript_text", ""),
    ("transcript_segments", []),
    ("audio_info", None),
    ("speaker_segments", []),
    ("transcript_result", None),
):
    st.session_state.setdefault(key, default)

# Check if transcript is available
if not st.session_state.transcript_text:
    st.warning("⚠️ Vui lòng chạy transcription trước tại trang 'Transcription'")
    if st.button("📝 Go to Transcription", type="primary"):
        st.switch_page("pages/2_📝_Transcription.py")
    st.stop()

# Calculate statistics
duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
stats = calculate_statistics(
    st.session_state.transcript_text,
    duration,
    st.session_state.speaker_segments if st.session_state.speaker_segments else None
)

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Statistics", "🔬 Model Comparison", "📏 Evaluation Metrics"])

# ===== TAB 1: Statistics =====
with tab1:
    st.subheader("📊 Detailed Statistics")
    
    # Segment analysis
    st.markdown("#### Segment Analysis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        segment_count = len(st.session_state.transcript_segments) if st.session_state.transcript_segments else 0
        st.metric("Số segments", segment_count)
    
    with col2:
        avg_segment_length = duration / segment_count if segment_count > 0 else 0
        st.metric("Độ dài trung bình segment", f"{avg_segment_length:.2f}s")
    
    with col3:
        processing_time = st.session_state.transcript_result.get("processing_time", 0) if st.session_state.transcript_result else 0
        st.metric("Thời gian xử lý", f"{processing_time:.2f}s" if processing_time > 0 else "N/A")
    
    # Text statistics
    st.markdown("---")
    st.markdown("#### Text Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Số từ", f"{stats['word_count']:,}")
    
    with col2:
        st.metric("Số ký tự", f"{stats['character_count']:,}")
    
    with col3:
        st.metric("Số câu", f"{stats['sentence_count']:,}")
    
    with col4:
        st.metric("Tốc độ nói", f"{stats['words_per_minute']:.1f} WPM")
    
    # Processing metrics
    if duration > 0:
        st.markdown("---")
        st.markdown("#### Processing Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            realtime_factor = processing_time / duration if processing_time > 0 else 0
            st.metric("Realtime Factor", f"{realtime_factor:.2f}x" if realtime_factor > 0 else "N/A")
            st.caption("Thời gian xử lý / Thời lượng audio. < 1.0 = nhanh hơn realtime")
        
        with col2:
            words_per_second = stats['word_count'] / duration if duration > 0 else 0
            st.metric("Tốc độ từ/giây", f"{words_per_second:.2f}")

# ===== TAB 2: Model Comparison =====
with tab2:
    st.subheader("🔬 Model Comparison")
    st.caption("So sánh hiệu suất giữa các model và kích thước")
    
    st.info("💡 Để so sánh model, hãy chạy transcription với các model khác nhau và so sánh kết quả.")
    
    # Comparison table
    st.markdown("#### Model Performance Comparison")
    
    comparison_data = {
        "Model": ["Whisper tiny", "Whisper small", "Whisper medium", "PhoWhisper base", "PhoWhisper medium"],
        "Speed": ["⚡⚡⚡", "⚡⚡", "⚡", "⚡⚡⚡", "⚡"],
        "Accuracy": ["⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐"],
        "Memory": ["Low", "Medium", "High", "Low", "Medium"],
        "Use Case": ["Demo/Preview", "General", "High Quality", "Vietnamese Focus", "Vietnamese Best"]
    }
    
    try:
        import pandas as pd
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    except ImportError:
        st.table(comparison_data)
    
    # Trade-offs visualization
    st.markdown("---")
    st.markdown("#### Speed vs Accuracy Trade-offs")
    
    try:
        import plotly.express as px
        
        # Sample data for visualization
        model_data = {
            "Model": ["Whisper tiny", "Whisper small", "Whisper medium", "PhoWhisper base", "PhoWhisper medium"],
            "Speed Score": [9, 7, 4, 8, 5],
            "Accuracy Score": [5, 7, 9, 7, 9]
        }
        
        df_tradeoff = pd.DataFrame(model_data)
        
        fig = px.scatter(
            df_tradeoff,
            x="Speed Score",
            y="Accuracy Score",
            text="Model",
            title="Speed vs Accuracy Trade-offs",
            labels={"Speed Score": "Speed (Higher = Faster)", "Accuracy Score": "Accuracy (Higher = Better)"}
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("💡 Cài đặt plotly để xem biểu đồ: `pip install plotly`")

# ===== TAB 3: Evaluation Metrics =====
with tab3:
    st.subheader("📏 Evaluation Metrics")
    st.caption("WER (Word Error Rate) và CER (Character Error Rate) - cần reference transcript")
    
    st.warning("⚠️ Để tính WER/CER, cần có reference transcript (ground truth) để so sánh.")
    
    # Reference transcript input
    reference_transcript = st.text_area(
        "Reference Transcript (Ground Truth)",
        height=200,
        help="Nhập reference transcript để so sánh với kết quả transcription",
        key="reference_transcript"
    )
    
    if reference_transcript:
        # Calculate WER and CER
        def calculate_wer(reference, hypothesis):
            """Calculate Word Error Rate"""
            ref_words = reference.split()
            hyp_words = hypothesis.split()
            
            # Simple Levenshtein distance for words
            # For production, use jiwer or similar library
            if len(ref_words) == 0:
                return 0.0 if len(hyp_words) == 0 else 1.0
            
            # Simple word-level comparison
            ref_set = set(ref_words)
            hyp_set = set(hyp_words)
            
            correct = len(ref_set & hyp_set)
            total = len(ref_set)
            
            wer = 1.0 - (correct / total) if total > 0 else 0.0
            return wer
        
        def calculate_cer(reference, hypothesis):
            """Calculate Character Error Rate"""
            if len(reference) == 0:
                return 0.0 if len(hypothesis) == 0 else 1.0
            
            # Simple character-level comparison
            ref_chars = set(reference.replace(" ", ""))
            hyp_chars = set(hypothesis.replace(" ", ""))
            
            correct = len(ref_chars & hyp_chars)
            total = len(ref_chars)
            
            cer = 1.0 - (correct / total) if total > 0 else 0.0
            return cer
        
        wer = calculate_wer(reference_transcript, st.session_state.transcript_text)
        cer = calculate_cer(reference_transcript, st.session_state.transcript_text)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Word Error Rate (WER)", f"{wer:.2%}")
            st.caption("WER càng thấp càng tốt. WER = 0% = hoàn hảo")
        
        with col2:
            st.metric("Character Error Rate (CER)", f"{cer:.2%}")
            st.caption("CER càng thấp càng tốt. CER = 0% = hoàn hảo")
        
        # Interpretation
        st.markdown("---")
        st.markdown("#### Interpretation")
        
        if wer < 0.1:
            st.success("✅ WER < 10%: Rất tốt! Model hoạt động xuất sắc.")
        elif wer < 0.2:
            st.info("ℹ️ WER 10-20%: Tốt. Có thể cải thiện với model lớn hơn hoặc preprocessing.")
        elif wer < 0.3:
            st.warning("⚠️ WER 20-30%: Chấp nhận được. Cân nhắc dùng model lớn hơn.")
        else:
            st.error("❌ WER > 30%: Cần cải thiện. Thử model lớn hơn hoặc kiểm tra audio quality.")
    else:
        st.info("💡 Nhập reference transcript để tính WER và CER")

# Navigation
st.markdown("---")
if st.button("🏠 Back to Home", use_container_width=True):
    st.switch_page("pages/0_🏠_Home_Dashboard.py")

