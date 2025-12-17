"""
Quality Presets Module
Map quality presets (Fast/Balanced/Accurate) to model sizes
Ẩn technical details khỏi người dùng thường
"""
from typing import Dict, Optional
import torch

QUALITY_PRESETS: Dict[str, Dict[str, str]] = {
    "fast": {
        "whisper": "tiny",
        "phowhisper": "base",
        "description": "⚡ Nhanh, ít chính xác, ít tài nguyên",
        "tooltip": "Phù hợp cho demo, preview, hoặc Streamlit Cloud (RAM thấp)"
    },
    "balanced": {
        "whisper": "small",
        "phowhisper": "small",  # or medium if available
        "description": "⚖️ Cân bằng tốc độ và độ chính xác",
        "tooltip": "Tốt cho hầu hết cuộc họp - giữ độ chính xác chấp nhận được mà không quá chậm"
    },
    "accurate": {
        "whisper": "medium",
        "phowhisper": "medium",
        "description": "🎯 Chậm, chính xác nhất, nhiều tài nguyên",
        "tooltip": "Dùng cho transcript quan trọng (biên bản chính thức). Nếu có GPU, tự động khuyên dùng."
    }
}

def get_model_size_for_preset(preset: str, model_id: str) -> Optional[str]:
    """
    Map quality preset to model size
    
    Args:
        preset: Quality preset ("fast", "balanced", "accurate")
        model_id: Model ID ("whisper" or "phowhisper")
    
    Returns:
        Model size string (e.g., "tiny", "small", "medium") or None if invalid
    """
    if preset not in QUALITY_PRESETS:
        return None
    
    if model_id not in QUALITY_PRESETS[preset]:
        return None
    
    return QUALITY_PRESETS[preset][model_id]

def get_preset_description(preset: str) -> str:
    """Get description for a quality preset"""
    return QUALITY_PRESETS.get(preset, {}).get("description", "")

def get_preset_tooltip(preset: str) -> str:
    """Get tooltip text for a quality preset"""
    return QUALITY_PRESETS.get(preset, {}).get("tooltip", "")

def detect_gpu() -> bool:
    """
    Detect if GPU is available
    
    Returns:
        True if CUDA is available, False otherwise
    """
    try:
        return torch.cuda.is_available()
    except:
        return False

def get_recommended_preset(model_id: str = None) -> str:
    """
    Get recommended quality preset based on system resources
    
    Args:
        model_id: Optional model ID to consider
    
    Returns:
        Recommended preset ("fast", "balanced", or "accurate")
    """
    has_gpu = detect_gpu()
    
    # If GPU available, recommend Accurate
    if has_gpu:
        return "accurate"
    
    # Default to Balanced for CPU
    return "balanced"

def get_all_presets() -> list:
    """Get list of all available quality presets"""
    return list(QUALITY_PRESETS.keys())

