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

def simple_speaker_segmentation(audio_array, sr, segments, min_silence_duration=0.5):
    """
    Phân đoạn đơn giản dựa trên energy và silence
    Đây là phương pháp đơn giản, không phải diarization thực sự
    
    Args:
        audio_array: Audio data (numpy array)
        sr: Sample rate
        segments: List of segments từ Whisper hoặc PhoWhisper
        min_silence_duration: Minimum silence duration để phân tách speaker
    
    Returns:
        List[Dict]: Speaker segments hoặc [] nếu không có segments hợp lệ
    """
    try:
        # Kiểm tra nếu segments rỗng hoặc không hợp lệ
        if not segments or len(segments) == 0:
            return []
        
        # Kiểm tra format của segments
        if not isinstance(segments[0], dict) or 'start' not in segments[0]:
            return []
        # Tính energy
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        energy = librosa.feature.rms(y=audio_array, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Threshold để phát hiện speech
        energy_threshold = np.percentile(energy, 20)
        
        # Phân đoạn dựa trên energy
        speaker_segments = []
        current_speaker = 1
        in_speech = False
        speech_start = 0
        
        for i, seg in enumerate(segments):
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            
            # Tính energy trung bình cho segment này
            start_frame = int(seg_start * sr / hop_length)
            end_frame = int(seg_end * sr / hop_length)
            seg_energy = np.mean(energy[start_frame:end_frame]) if start_frame < len(energy) else 0
            
            if seg_energy > energy_threshold:
                if not in_speech:
                    speech_start = seg_start
                    in_speech = True
            else:
                if in_speech:
                    # Kết thúc speech segment
                    speaker_segments.append({
                        'speaker': f'Speaker {current_speaker}',
                        'start': speech_start,
                        'end': seg_start,
                        'text': ' '.join([s.get('text', '') for s in segments 
                                         if speech_start <= s.get('start', 0) <= seg_start])
                    })
                    in_speech = False
                    current_speaker += 1
        
        # Xử lý segment cuối
        if in_speech:
            speaker_segments.append({
                'speaker': f'Speaker {current_speaker}',
                'start': speech_start,
                'end': segments[-1].get('end', 0) if segments else 0,
                'text': ' '.join([s.get('text', '') for s in segments 
                                 if s.get('start', 0) >= speech_start])
            })
        
        return speaker_segments
    except Exception as e:
        st.warning(f"Không thể thực hiện speaker diarization: {str(e)}")
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

