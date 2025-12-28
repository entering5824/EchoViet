"""
Module speaker diarization (phân biệt người nói)
Sử dụng pyannote.audio hoặc phương pháp đơn giản hơn
"""
import streamlit as st
import numpy as np
from typing import List, Dict, Tuple
# Ensure FFmpeg configured before importing librosa (best-effort)
try:
    from core.audio.ffmpeg_setup import ensure_ffmpeg
    ensure_ffmpeg(silent=True)
except Exception:
    pass
import librosa

def simple_speaker_segmentation(audio_array, sr, segments, min_silence_duration=0.5, max_speakers=4):
    """
    Phân đoạn đơn giản dựa trên energy và silence, gán speaker dựa trên transcript segments
    Cải thiện: Sử dụng max_speakers và logic phân loại tốt hơn
    
    Args:
        audio_array: Audio data (numpy array)
        sr: Sample rate
        segments: List of segments từ Whisper (có thể là dict với start/end/text hoặc text lines)
        min_silence_duration: Minimum silence duration để phân tách speaker
        max_speakers: Số lượng người nói tối đa
    
    Returns:
        List[Dict]: Speaker segments với keys: speaker, start, end, text
    """
    try:
        # Nếu segments là list of strings (từ transcript text), parse thành dicts
        if segments and isinstance(segments[0], str):
            # Parse transcript lines với format [start - end] text hoặc chỉ text
            parsed_segments = []
            for line in segments:
                line = line.strip()
                if not line:
                    continue
                # Try to parse timestamp
                import re
                ts_match = re.match(r'\[([\d.]+)\s*-\s*([\d.]+)\]\s*(.+)', line)
                if ts_match:
                    start, end, text = float(ts_match.group(1)), float(ts_match.group(2)), ts_match.group(3)
                    parsed_segments.append({'start': start, 'end': end, 'text': text.strip()})
                else:
                    # No timestamp, estimate from previous segment
                    prev_end = parsed_segments[-1]['end'] if parsed_segments else 0
                    estimated_dur = len(line.split()) * 0.5  # ~0.5s per word
                    parsed_segments.append({'start': prev_end, 'end': prev_end + estimated_dur, 'text': line})
            segments = parsed_segments
        
        # Kiểm tra nếu segments rỗng hoặc không hợp lệ
        if not segments or len(segments) == 0:
            return []
        
        # Kiểm tra format của segments
        if not isinstance(segments[0], dict) or 'start' not in segments[0]:
            return []
        
        # Tính energy để phát hiện silence
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = librosa.feature.rms(y=audio_array, frame_length=frame_length, hop_length=hop_length)[0]
        energy_threshold = np.percentile(energy, 25)  # Slightly higher threshold
        
        # Phân loại segments thành speakers dựa trên:
        # 1. Khoảng cách thời gian (silence gaps)
        # 2. Energy patterns
        # 3. Text length patterns
        
        speaker_segments = []
        current_speaker = 1
        last_seg_end = 0
        
        for i, seg in enumerate(segments):
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            seg_text = seg.get('text', '').strip()
            
            if not seg_text:
                continue
            
            # Tính gap từ segment trước
            gap = seg_start - last_seg_end if i > 0 else 0
            
            # Tính energy cho segment này
            start_frame = int(seg_start * sr / hop_length)
            end_frame = int(seg_end * sr / hop_length)
            seg_energy = np.mean(energy[start_frame:end_frame]) if start_frame < len(energy) and end_frame <= len(energy) else energy_threshold
            
            # Quyết định có đổi speaker không
            # Đổi speaker nếu:
            # - Gap lớn hơn min_silence_duration
            # - Hoặc energy pattern thay đổi đáng kể
            # - Hoặc đã đạt max_speakers và cần rotate
            should_switch = False
            
            if gap > min_silence_duration * 1.5:
                should_switch = True
            elif i > 0 and speaker_segments:
                # So sánh energy với segment trước
                prev_seg = speaker_segments[-1]
                prev_start = int(prev_seg['start'] * sr / hop_length)
                prev_end = int(prev_seg['end'] * sr / hop_length)
                if prev_start < len(energy) and prev_end <= len(energy):
                    prev_energy = np.mean(energy[prev_start:prev_end])
                    energy_diff = abs(seg_energy - prev_energy) / (prev_energy + 1e-6)
                    if energy_diff > 0.3:  # Energy thay đổi >30%
                        should_switch = True
            
            # Rotate speakers nếu đã đạt max
            if should_switch:
                current_speaker = (current_speaker % max_speakers) + 1
            
            speaker_segments.append({
                'speaker': f'Speaker {current_speaker}',
                'start': seg_start,
                'end': seg_end,
                'text': seg_text
            })
            
            last_seg_end = seg_end
        
        return speaker_segments
    except Exception as e:
        st.warning(f"Không thể thực hiện speaker diarization: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return []

def format_with_speakers(segments: List[Dict]) -> str:
    """Format transcript với thông tin speaker"""
    if not segments:
        return ""
    
    formatted_lines = []
    for seg in segments:
        speaker = seg.get('speaker', 'Unknown')
        start = seg.get('start', 0)
        end = seg.get('end', 0)
        text = seg.get('text', '').strip()
        
        if text:
            formatted_lines.append(
                f"[{format_time(start)} - {format_time(end)}] {speaker}: {text}"
            )
    
    return "\n".join(formatted_lines)

def format_time(seconds: float) -> str:
    """Format thời gian"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"

