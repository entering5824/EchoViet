"""
Component hiển thị statistics và metrics
"""
import streamlit as st
from typing import Dict, List, Optional

def calculate_statistics(transcript_text: str, duration: float, speaker_segments: Optional[List] = None) -> Dict:
    """
    Tính toán statistics từ transcript
    
    Args:
        transcript_text: Transcript text
        duration: Audio duration in seconds
        speaker_segments: Optional speaker segments
    
    Returns:
        Dict với statistics
    """
    stats = {
        "word_count": 0,
        "character_count": 0,
        "sentence_count": 0,
        "duration": duration,
        "words_per_minute": 0,
        "characters_per_minute": 0,
        "speakers": 0,
        "speaker_stats": {}
    }
    
    if transcript_text:
        words = transcript_text.split()
        stats["word_count"] = len(words)
        stats["character_count"] = len(transcript_text)
        
        # Count sentences
        import re
        sentences = re.split(r'[.!?]+', transcript_text)
        stats["sentence_count"] = len([s for s in sentences if s.strip()])
        
        # Calculate rates
        if duration > 0:
            stats["words_per_minute"] = (stats["word_count"] / duration) * 60
            stats["characters_per_minute"] = (stats["character_count"] / duration) * 60
    
    if speaker_segments:
        speakers = set(seg.get('speaker', 'Unknown') for seg in speaker_segments)
        stats["speakers"] = len(speakers)
        
        # Per-speaker stats
        for speaker in speakers:
            speaker_segs = [seg for seg in speaker_segments if seg.get('speaker') == speaker]
            speaker_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in speaker_segs)
            speaker_text = ' '.join(seg.get('text', '') for seg in speaker_segs)
            speaker_words = len(speaker_text.split())
            
            stats["speaker_stats"][speaker] = {
                "duration": speaker_duration,
                "word_count": speaker_words,
                "segments": len(speaker_segs),
                "words_per_minute": (speaker_words / speaker_duration * 60) if speaker_duration > 0 else 0
            }
    
    return stats

def render_statistics(stats: Dict):
    """
    Hiển thị statistics
    """
    st.subheader("📊 Statistics")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Số từ", f"{stats['word_count']:,}")
    
    with col2:
        st.metric("Số câu", f"{stats['sentence_count']:,}")
    
    with col3:
        st.metric("WPM", f"{stats['words_per_minute']:.1f}")
    
    with col4:
        st.metric("Thời lượng", f"{stats['duration']:.2f}s")
    
    # Speaker statistics
    if stats.get("speakers", 0) > 0:
        st.markdown("---")
        st.subheader("👥 Speaker Statistics")
        
        for speaker, speaker_stat in stats["speaker_stats"].items():
            with st.expander(f"{speaker} - {speaker_stat['word_count']} từ"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Thời gian nói", f"{speaker_stat['duration']:.2f}s")
                with col2:
                    st.metric("Số segments", speaker_stat['segments'])
                with col3:
                    st.metric("WPM", f"{speaker_stat['words_per_minute']:.1f}")

