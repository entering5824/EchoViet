"""
Centralized configuration management
Loads settings from environment variables with sensible defaults
"""
import os
from typing import Optional
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """Application configuration"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Vietnamese Speech-to-Text System")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Streamlit
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "0.0.0.0")
    STREAMLIT_BROWSER_GATHER_USAGE_STATS: bool = (
        os.getenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false").lower() == "true"
    )
    
    # FastAPI
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))
    
    # Model Configuration
    DEFAULT_WHISPER_MODEL: str = os.getenv("DEFAULT_WHISPER_MODEL", "base")
    DEFAULT_PHOWHISPER_MODEL: str = os.getenv("DEFAULT_PHOWHISPER_MODEL", "medium")
    
    # Cache directories
    TRANSFORMERS_CACHE: str = os.getenv(
        "TRANSFORMERS_CACHE",
        str(Path.home() / ".cache" / "huggingface")
    )
    HF_HOME: str = os.getenv(
        "HF_HOME",
        str(Path.home() / ".cache" / "huggingface")
    )
    WHISPER_CACHE: str = os.getenv(
        "WHISPER_CACHE",
        str(Path.home() / ".cache" / "whisper")
    )
    
    # Resource Limits
    MAX_AUDIO_DURATION: int = int(os.getenv("MAX_AUDIO_DURATION", "3600"))  # seconds
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "200"))  # MB
    MAX_MEMORY_USAGE: int = int(os.getenv("MAX_MEMORY_USAGE", "8192"))  # MB
    
    # GPU Configuration
    CUDA_VISIBLE_DEVICES: Optional[str] = os.getenv("CUDA_VISIBLE_DEVICES")
    USE_GPU: bool = os.getenv("USE_GPU", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    # Temporary Files
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "temp")))
    CLEANUP_TEMP_FILES: bool = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"

    # Features
    DIARIZATION_ENABLED: bool = os.getenv("DIARIZATION_ENABLED", "false").lower() == "true"  # Optional speaker diarization page
    
    # Export Settings
    EXPORT_DIR: Path = Path(os.getenv("EXPORT_DIR", str(BASE_DIR / "export")))
    MAX_EXPORT_FILES: int = int(os.getenv("MAX_EXPORT_FILES", "100"))
    
    # Security
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # HuggingFace
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")
    
    # Development
    DEVELOPMENT_MODE: bool = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    HOT_RELOAD: bool = os.getenv("HOT_RELOAD", "true").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        Path(cls.TRANSFORMERS_CACHE).mkdir(parents=True, exist_ok=True)
        Path(cls.WHISPER_CACHE).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.APP_ENV.lower() == "production"
    
    @classmethod
    def is_cloud(cls) -> bool:
        """Check if running on cloud (Streamlit Cloud, etc.)"""
        return os.getenv("STREAMLIT_SHARING", "").lower() == "true" or \
               os.getenv("STREAMLIT_SERVER_BASE_URL", "") != ""

# Create global config instance
config = Config()

# Ensure directories exist on import
config.ensure_directories()

