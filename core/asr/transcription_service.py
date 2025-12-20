"""
Module transcription sử dụng Whisper
"""
import os
import sys
import whisper
import torch
import streamlit as st
from typing import Optional, Dict, List
import numpy as np
import time
from core.audio.audio_processor import _make_safe_temp_copy

def check_python_version():
    """
    Kiểm tra Python version và cảnh báo nếu không phù hợp với Streamlit Cloud
    
    Returns:
        Tuple (is_valid: bool, warning_message: Optional[str])
    """
    version = sys.version_info
    if version.major == 3 and 9 <= version.minor <= 10:
        return True, None
    
    warning_msg = (
        f"⚠️ Python {version.major}.{version.minor} được phát hiện. "
        f"Streamlit Cloud khuyến nghị Python 3.9-3.10. "
        f"Python 3.11+ hoặc 3.8- có thể gây lỗi với Whisper/PhoWhisper."
    )
    return False, warning_msg

# Check Python version early
_python_version_valid, _python_version_warning = check_python_version()
if _python_version_warning:
    try:
        import streamlit as st
        st.warning(_python_version_warning)
    except:
        print(_python_version_warning)

@st.cache_resource
def load_whisper_model(model_size="base"):
    """Load Whisper model với cache"""
    try:
        # On Streamlit Cloud, force CPU even if CUDA is detected
        if os.getenv("STREAMLIT_SHARING", "").lower() == "true" or os.getenv("STREAMLIT_SERVER_BASE_URL", ""):
            device = "cpu"  # Force CPU on Cloud
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        model = whisper.load_model(model_size, device=device)
        return model, device
    except KeyError as ke:
        # Handle "missing field" errors
        error_msg = f"Missing field error: {str(ke)}"
        st.error(f"❌ Lỗi 'missing field' khi load Whisper model. Đây thường do cache model bị lỗi.")
        st.warning("""
        **Khắc phục:**
        1. Xóa cache Whisper: `rm -rf ~/.cache/whisper` (Linux) hoặc xóa thư mục cache trên Windows
        2. Restart ứng dụng và thử lại
        """)
        return None, None
    except RuntimeError as re:
        # Handle CUDA unavailable errors
        error_msg = str(re)
        if "cuda" in error_msg.lower() or "CUDA" in error_msg:
            st.error(f"❌ Lỗi CUDA: {error_msg}")
            st.info("💡 Đang tự động chuyển sang CPU mode...")
            # Retry with CPU
            try:
                model = whisper.load_model(model_size, device="cpu")
                return model, "cpu"
            except Exception as cpu_err:
                st.error(f"❌ Không thể load model ngay cả với CPU: {str(cpu_err)}")
                return None, None
        else:
            raise  # Re-raise if not CUDA-related
    except Exception as e:
        error_msg = str(e)
        # Kiểm tra lỗi network
        if "getaddrinfo failed" in error_msg or "urlopen error" in error_msg.lower():
            st.error(f"❌ Lỗi kết nối mạng khi tải Whisper model. Vui lòng kiểm tra kết nối internet hoặc thử lại sau.")
            st.info("💡 Whisper cần tải model từ internet lần đầu tiên. Model sẽ được cache sau khi tải thành công.")
        else:
            st.error(f"Lỗi khi load Whisper model: {error_msg}")
        return None, None

def transcribe_audio(model, audio_path_or_array, sr=16000, language="vi", 
                     task="transcribe", verbose=False):
    """
    Transcribe audio sử dụng Whisper
    
    Args:
        model: Whisper model
        audio_path_or_array: Đường dẫn file hoặc numpy array
        sr: Sample rate
        language: Ngôn ngữ (vi cho tiếng Việt)
        task: "transcribe" hoặc "translate"
        verbose: Hiển thị thông tin chi tiết
    """
    try:
        if model is None:
            return None
        
        # If audio_path_or_array is a filepath, preflight-check and create safe copy if needed
        audio_path_to_use = audio_path_or_array
        if isinstance(audio_path_or_array, str):
            # Normalize path for Windows (resolve any path issues with absolute paths)
            audio_path_to_use = os.path.normpath(os.path.abspath(audio_path_or_array))
            
            # CRITICAL: Verify file exists before transcribe (prevents WinError 2)
            if not os.path.exists(audio_path_to_use):
                error_msg = f"File không tồn tại: {audio_path_to_use}"
                st.error(f"❌ {error_msg}")
                st.warning("💡 File có thể đã bị xóa hoặc path không đúng. Vui lòng kiểm tra lại.")
                return None
            
            if not os.path.isfile(audio_path_to_use):
                error_msg = f"Path không phải là file: {audio_path_to_use}"
                st.error(f"❌ {error_msg}")
                return None
            
            # Retry a few times for transient file access issues (Windows file lock)
            file_accessible = False
            for attempt in range(3):
                try:
                    # Test if file is readable
                    with open(audio_path_to_use, 'rb') as test_file:
                        test_file.read(1)  # Read 1 byte to test
                    file_accessible = True
                    break
                except PermissionError:
                    st.warning(f"⚠️ File đang được sử dụng bởi process khác. Retry {attempt + 1}/3...")
                    time.sleep(0.2 * (attempt + 1))
                    continue
                except Exception as file_err:
                    # Try to create a safe temp copy if original filename could be problematic
                    try:
                        tmp_copy = _make_safe_temp_copy(audio_path_to_use)
                        audio_path_to_use = tmp_copy
                        file_accessible = True
                        break
                    except Exception:
                        time.sleep(0.1 * (attempt + 1))
                        continue
            
            if not file_accessible:
                st.error(f"❌ Không thể truy cập file: {audio_path_to_use}")
                st.warning("💡 File có thể đang bị khóa bởi process khác hoặc không có quyền truy cập.")
                return None

        # Final check before transcribe
        if isinstance(audio_path_to_use, str):
            if not os.path.exists(audio_path_to_use):
                st.error(f"❌ File không tồn tại trước khi transcribe: {audio_path_to_use}")
                return None

        # Transcribe
        try:
            result = model.transcribe(
                audio_path_to_use,
                language=language,
                task=task,
                verbose=verbose,
                fp16=False  # Sử dụng fp32 để tránh lỗi trên CPU
            )
            return result
        except FileNotFoundError as fnf_err:
            error_msg = str(fnf_err)
            st.error(f"❌ FileNotFoundError: {error_msg}")
            st.error(f"❌ File path: {audio_path_to_use}")
            st.warning("""
            **WinError 2 - File không tìm thấy:**
            1. File có thể đã bị xóa
            2. Path không đúng
            3. FFmpeg không tìm thấy (nếu lỗi xảy ra trong quá trình load audio)
            
            **Khắc phục:**
            - Kiểm tra file có tồn tại không
            - Kiểm tra FFmpeg setup
            - Thử lại với file audio khác
            """)
            return None
        except OSError as os_err:
            # WinError 2 on Windows
            if getattr(os_err, 'winerror', None) == 2 or os_err.errno == 2:
                error_msg = str(os_err)
                st.error(f"❌ WinError 2: {error_msg}")
                st.error(f"❌ File path: {audio_path_to_use}")
                st.warning("""
                **WinError 2 - File không tìm thấy (Windows):**
                - File có thể đã bị xóa hoặc không tồn tại
                - FFmpeg không tìm thấy
                - Path có vấn đề
                
                **Đã kiểm tra:**
                - File existence: ✅
                - File readable: ✅
                - Có thể là lỗi FFmpeg hoặc Whisper internal
                """)
            return None
    except KeyError as ke:
        # Handle "missing field" errors during transcription
        error_msg = f"Missing field error during transcription: {str(ke)}"
        st.error(f"❌ Lỗi 'missing field' khi transcribe. Đây thường do model cache bị lỗi.")
        st.warning("""
        **Khắc phục:**
        1. Xóa cache Whisper: `rm -rf ~/.cache/whisper`
        2. Restart ứng dụng và thử lại
        3. Nếu vẫn lỗi, thử model size nhỏ hơn
        """)
        return None
    except OSError as os_err:
        # Handle WinError 2 specifically
        error_msg = str(os_err)
        if getattr(os_err, 'winerror', None) == 2 or os_err.errno == 2:
            st.error(f"❌ WinError 2: File không tìm thấy")
            st.error(f"❌ Chi tiết: {error_msg}")
            st.warning("""
            **WinError 2 trên Windows:**
            - File không tồn tại hoặc đã bị xóa
            - FFmpeg không tìm thấy
            - Path có vấn đề
            
            **Đã thử:**
            - Kiểm tra file existence
            - Tạo safe temp copy
            - Retry mechanism
            """)
        else:
            st.error(f"❌ Lỗi OS: {error_msg}")
        return None
    except Exception as e:
        error_msg = str(e)
        # Check for FFmpeg errors
        if "ffmpeg" in error_msg.lower() or "ffmpeg was not found" in error_msg.lower():
            st.error(f"❌ Lỗi FFmpeg khi transcribe: {error_msg}")
            st.warning("💡 Đảm bảo FFmpeg đã được cài đặt và cấu hình đúng.")
        elif "failed to load audio" in error_msg.lower() or "cannot load audio" in error_msg.lower():
            st.error(f"❌ Lỗi khi load audio: {error_msg}")
            st.warning("""
            💡 **Nguyên nhân có thể:**
            - File format không được hỗ trợ hoặc bị hỏng
            - FFmpeg không tìm thấy hoặc không hoạt động
            - File path có vấn đề (khoảng trắng, ký tự đặc biệt)
            - File đang bị khóa bởi process khác
            
            **Khắc phục:**
            - Thử upload lại file audio
            - Kiểm tra format file (WAV, MP3, FLAC, M4A, OGG)
            - Kiểm tra FFmpeg setup
            """)
        elif "cannot find the file" in error_msg.lower() or "No such file" in error_msg:
            st.error(f"❌ File không tìm thấy: {error_msg}")
            st.warning("💡 File có thể đã bị xóa hoặc path không đúng.")
        else:
            st.error(f"Lỗi khi transcribe: {error_msg}")
        return None

def format_transcript(result: Dict, with_timestamps: bool = True) -> str:
    """Format transcript từ kết quả Whisper"""
    if result is None:
        return ""
    
    text = result.get("text", "")
    segments = result.get("segments", [])
    
    if not with_timestamps or not segments:
        return text
    
    # Format với timestamps
    formatted_lines = []
    for segment in segments:
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        segment_text = segment.get("text", "").strip()
        
        if segment_text:
            formatted_lines.append(f"[{format_time(start)} - {format_time(end)}] {segment_text}")
    
    return "\n".join(formatted_lines)

def format_time(seconds: float) -> str:
    """Format thời gian từ seconds sang HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    else:
        return f"{minutes:02d}:{secs:02d}.{millis:03d}"

def get_transcript_statistics(result: Dict, duration: float) -> Dict:
    """Tính toán thống kê transcript"""
    if result is None:
        return {}
    
    text = result.get("text", "")
    words = text.split()
    
    return {
        'word_count': len(words),
        'character_count': len(text),
        'duration': duration,
        'words_per_minute': (len(words) / duration * 60) if duration > 0 else 0,
        'segments_count': len(result.get("segments", []))
    }

