"""
Model Registry
Quản lý ASR models: Whisper, Distil-Whisper, Whisper Large v3 Turbo, Parakeet, Moonshine
"""
from typing import Dict, List, Optional

MODELS: Dict[str, Dict] = {
    "whisper": {
        "name": "Whisper",
        "type": "Transformer seq2seq",
        "category": "Nhiều ngôn ngữ SOTA",
        "service": "transcription_service",
        "sizes": ["tiny", "base", "small", "medium", "large"],
        "default_size": "base",
        "description": "Mô hình đa ngôn ngữ từ OpenAI, benchmark chuẩn cho ASR",
        "recommended": True,
        "vietnamese_support": True,
        "dependencies": ["openai-whisper", "torch"]
    },
    "faster_whisper": {
        "name": "Faster-Whisper",
        "type": "CTranslate2 Whisper",
        "category": "Nhiều ngôn ngữ",
        "sizes": ["tiny", "base", "small", "medium", "large", "large-v2"],
        "default_size": "base",
        "description": "Whisper tối ưu với CTranslate2, nhanh hơn với độ chính xác tương đương",
        "vietnamese_support": True,
        "dependencies": ["faster-whisper", "torch"]
    },
    "distil_whisper": {
        "name": "Distil-Whisper",
        "type": "Knowledge distillation",
        "category": "Tối ưu tốc độ",
        "sizes": ["distil-large-v3", "distil-medium.en", "distil-small.en"],
        "default_size": "distil-large-v3",
        "description": "Whisper distilled 6x nhanh hơn large-v3, WER ~1%",
        "vietnamese_support": True,
        "dependencies": ["faster-whisper", "torch"]
    },
    "whisper_large_v3_turbo": {
        "name": "Whisper Large v3 Turbo",
        "type": "Whisper Turbo",
        "category": "Tối ưu tốc độ",
        "sizes": ["large-v3-turbo"],
        "default_size": "large-v3-turbo",
        "description": "Whisper Large v3 phiên bản turbo, nhanh với độ chính xác cao",
        "vietnamese_support": True,
        "dependencies": ["faster-whisper", "torch"]
    },
    "parakeet": {
        "name": "Parakeet",
        "type": "NVIDIA ASR CTC",
        "category": "NVIDIA",
        "sizes": ["parakeet-ctc-1.1b", "parakeet-rnnt-1.1b"],
        "default_size": "parakeet-ctc-1.1b",
        "description": "Mô hình ASR từ NVIDIA, hỗ trợ đa ngôn ngữ",
        "vietnamese_support": True,
        "dependencies": ["transformers", "torch"]
    },
    "moonshine": {
        "name": "Moonshine",
        "type": "Real-time ASR",
        "category": "Tối ưu thời gian thực",
        "sizes": ["moonshine-tiny", "moonshine-base"],
        "default_size": "moonshine-base",
        "description": "ASR tối ưu real-time, 5x ít compute hơn Whisper tiny",
        "vietnamese_support": True,
        "dependencies": ["transformers", "torch"]
    }
}

def get_model_info(model_id: str) -> Optional[Dict]:
    """Lấy thông tin model theo ID"""
    return MODELS.get(model_id)

def get_all_models() -> Dict[str, Dict]:
    """Lấy tất cả models"""
    return MODELS

def get_available_models() -> List[str]:
    """Lấy danh sách model IDs"""
    return list(MODELS.keys())

def get_recommended_models() -> List[str]:
    """Lấy danh sách models được khuyến nghị"""
    return [model_id for model_id, info in MODELS.items() if info.get("recommended", False)]

def get_models_by_category() -> Dict[str, List[str]]:
    """Nhóm models theo category"""
    categories = {}
    for model_id, info in MODELS.items():
        category = info.get("category", "Other")
        if category not in categories:
            categories[category] = []
        categories[category].append(model_id)
    return categories

def check_model_dependencies(model_id: str):
    """
    Kiểm tra dependencies của model
    
    Returns:
        (is_available, missing_dependencies)
    """
    model_info = get_model_info(model_id)
    if not model_info:
        return False, []
    
    dependencies = model_info.get("dependencies", [])
    missing = []
    
    for dep in dependencies:
        try:
            if dep == "openai-whisper":
                import whisper
            elif dep == "faster-whisper":
                import faster_whisper
            elif dep == "transformers":
                import transformers
            elif dep == "torch":
                import torch
        except (ImportError, SyntaxError, IndentationError, AttributeError, Exception) as e:
            # Bắt tất cả exception để tránh crash khi check dependencies
            missing.append(dep)
    
    return len(missing) == 0, missing

