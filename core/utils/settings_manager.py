"""
Settings Manager
Quản lý settings và config cho advanced users
"""
import os
import json
from typing import Dict, Optional
from pathlib import Path

def load_settings() -> Dict:
    """Load settings từ config hoặc environment"""
    from config import config
    
    settings = {
        "model": {
            "whisper_model_path": os.getenv("WHISPER_MODEL_PATH", ""),
            "phowhisper_repo": os.getenv("PHOWHISPER_REPO", "vinai/PhoWhisper"),
            "device": "cpu" if config.is_cloud() else ("cuda" if os.getenv("USE_GPU", "true").lower() == "true" else "cpu"),
            "precision": os.getenv("MODEL_PRECISION", "fp32"),
        },
        "inference": {
            "beam_size": int(os.getenv("BEAM_SIZE", "5")),
            "batch_size": int(os.getenv("BATCH_SIZE", "16")),
            "temperature": float(os.getenv("TEMPERATURE", "0.0")),
            "best_of": int(os.getenv("BEST_OF", "5")),
            "patience": float(os.getenv("PATIENCE", "1.0")),
        },
        "resource": {
            "num_threads": int(os.getenv("NUM_THREADS", "4")),
            "quantization": os.getenv("QUANTIZATION", "none"),
            "max_memory_mb": int(os.getenv("MAX_MEMORY_MB", "4096")),
        },
        "pipeline": {
            "vad_enabled": os.getenv("VAD_ENABLED", "false").lower() == "true",
            "diarization_backend": os.getenv("DIARIZATION_BACKEND", "simple"),
            "max_speakers": int(os.getenv("MAX_SPEAKERS", "4")),
        },
        "deployment": {
            "docker_image": os.getenv("DOCKER_IMAGE", ""),
            "api_port": int(os.getenv("API_PORT", "8000")),
            "cloud_run": os.getenv("CLOUD_RUN_URL", ""),
            "hf_spaces": os.getenv("HF_SPACES_URL", ""),
        },
        "debug": {
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "enable_evaluation": os.getenv("ENABLE_EVALUATION", "false").lower() == "true",
            "wer_cer_enabled": os.getenv("WER_CER_ENABLED", "false").lower() == "true",
        }
    }
    
    return settings

def save_settings(settings: Dict, format: str = "json") -> bool:
    """
    Save settings to file
    
    Args:
        settings: Settings dict
        format: "json" or "yaml"
    
    Returns:
        True if successful
    """
    try:
        settings_file = Path("settings.json") if format == "json" else Path("settings.yaml")
        
        if format == "json":
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        else:
            try:
                import yaml
                with open(settings_file, 'w', encoding='utf-8') as f:
                    yaml.dump(settings, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                try:
                    import streamlit as st
                    st.warning("⚠️ PyYAML chưa được cài đặt. Sử dụng JSON format.")
                except:
                    pass
                return save_settings(settings, format="json")
        
        return True
    except Exception as e:
        try:
            import streamlit as st
            st.error(f"❌ Lỗi khi lưu settings: {str(e)}")
        except:
            pass
        return False

def load_settings_from_file(file_path: str) -> Optional[Dict]:
    """Load settings từ file"""
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        if path.suffix == ".json":
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except ImportError:
                try:
                    import streamlit as st
                    st.warning("⚠️ PyYAML chưa được cài đặt.")
                except:
                    pass
                return None
    except Exception as e:
        try:
            import streamlit as st
            st.error(f"❌ Lỗi khi load settings: {str(e)}")
        except:
            pass
        return None

