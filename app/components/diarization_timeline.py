"""
Component hiển thị timeline với speaker colors
"""
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from typing import List, Dict

def render_diarization_timeline(speaker_segments: List[Dict], duration: float):
    """
    Hiển thị timeline với speaker colors
    
    Args:
        speaker_segments: List of dicts với keys: speaker, start, end, text
        duration: Total duration của audio
    """
    if not speaker_segments:
        st.warning("⚠️ Không có dữ liệu speaker diarization")
        return
    
    # Get unique speakers
    speakers = list(set(seg.get('speaker', 'Unknown') for seg in speaker_segments))
    colors = plt.cm.Set3(np.linspace(0, 1, len(speakers)))
    speaker_colors = {speaker: colors[i] for i, speaker in enumerate(speakers)}
    
    # Create timeline
    fig, ax = plt.subplots(figsize=(14, 6))
    
    y_pos = 0.5
    for seg in speaker_segments:
        speaker = seg.get('speaker', 'Unknown')
        start = seg.get('start', 0)
        end = seg.get('end', duration)
        color = speaker_colors.get(speaker, 'gray')
        
        # Draw segment
        width = end - start
        ax.barh(y_pos, width, left=start, height=0.4, color=color, alpha=0.7, edgecolor='black')
        
        # Add speaker label
        mid_point = start + width / 2
        ax.text(mid_point, y_pos, speaker, ha='center', va='center', fontsize=9, fontweight='bold')
    
    ax.set_xlim(0, duration)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Thời gian (giây)', fontsize=12)
    ax.set_yticks([])
    ax.set_title('Speaker Diarization Timeline', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Legend
    patches = [mpatches.Patch(color=color, label=speaker) for speaker, color in speaker_colors.items()]
    ax.legend(handles=patches, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

