"""
Model Registry
Quản lý ASR models: Whisper
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
            elif dep == "transformers":
                import transformers
            elif dep == "torch":
                import torch
            # Chỉ hỗ trợ Whisper
        except (ImportError, SyntaxError, IndentationError, AttributeError, Exception) as e:
            # Bắt tất cả exception để tránh crash khi check dependencies
            missing.append(dep)
    
    return len(missing) == 0, missing

