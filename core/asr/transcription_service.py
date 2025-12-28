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
        f"Python 3.11+ hoặc 3.8- có thể gây lỗi với Whisper."
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

def get_vietnamese_initial_prompt(include_english: bool = True) -> str:
    """
    Tạo initial prompt tối ưu cho tiếng Việt và mixed language
    
    Args:
        include_english: Có bao gồm từ tiếng Anh phổ biến không
    
    Returns:
        Initial prompt string
    """
    # Các từ khóa tiếng Việt phổ biến để giúp model nhận diện tốt hơn
    vietnamese_common_words = [
        "xin chào", "cảm ơn", "vâng", "không", "được", "không được",
        "hôm nay", "ngày mai", "hôm qua", "bây giờ", "sau đó",
        "công ty", "dự án", "cuộc họp", "khách hàng", "đối tác",
        "việc làm", "nhiệm vụ", "mục tiêu", "kết quả", "giải pháp",
        "tốt", "tuyệt vời", "xuất sắc", "chấp nhận được", "cần cải thiện",
        "đúng", "sai", "chính xác", "rõ ràng", "hiểu",
        "vấn đề", "thách thức", "cơ hội", "rủi ro", "nguy cơ"
    ]
    
    english_common_words = [
        "okay", "yes", "no", "thank you", "hello", "meeting",
        "project", "customer", "partner", "solution", "problem"
    ]
    
    # Tạo prompt với context về mixed language
    if include_english:
        prompt = "Đây là đoạn ghi âm tiếng Việt, có thể có một số từ tiếng Anh như: " + ", ".join(english_common_words[:5])
        prompt += ". Các từ tiếng Việt phổ biến: " + ", ".join(vietnamese_common_words[:10])
    else:
        prompt = "Đây là đoạn ghi âm tiếng Việt. " + ", ".join(vietnamese_common_words[:15])
    
    return prompt


def transcribe_audio(model, audio_path_or_array, sr=16000, language="vi", 
                     task="transcribe", verbose=False,
                     initial_prompt: Optional[str] = None,
                     beam_size: int = 5,
                     temperature: float = 0.0,
                     condition_on_previous_text: bool = True,
                     best_of: int = 5,
                     use_vietnamese_optimization: bool = True):
    """
    Transcribe audio với Whisper - CHUẨN cho tiếng Việt
    
    QUAN TRỌNG: Luôn dùng language="vi", fp16=False, verbose=False
    để tránh "1 tảng chữ" và đảm bảo chất lượng tốt nhất.
    """
    """
    Transcribe audio sử dụng Whisper với tối ưu cho tiếng Việt
    
    Args:
        model: Whisper model
        audio_path_or_array: Đường dẫn file hoặc numpy array
        sr: Sample rate
        language: Ngôn ngữ (vi cho tiếng Việt)
        task: "transcribe" hoặc "translate"
        verbose: Hiển thị thông tin chi tiết
        initial_prompt: Initial prompt để guide model (tự động tạo nếu None và use_vietnamese_optimization=True)
        beam_size: Beam size cho beam search (5 = tốt cho tiếng Việt)
        temperature: Temperature (0.0 = greedy, >0 = sampling)
        condition_on_previous_text: Sử dụng context từ segment trước
        best_of: Số lượng candidates để chọn best
        use_vietnamese_optimization: Tự động áp dụng tối ưu cho tiếng Việt
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

        # Tạo initial prompt nếu cần
        effective_prompt = initial_prompt
        if use_vietnamese_optimization and language == "vi" and initial_prompt is None:
            effective_prompt = get_vietnamese_initial_prompt(include_english=True)
        
        # Transcribe với các tham số tối ưu - CHUẨN cho tiếng Việt
        try:
            transcribe_kwargs = {
                "language": language,  # QUAN TRỌNG: Phải chỉ định language
                "task": task,
                "verbose": False,  # QUAN TRỌNG: verbose=False để tránh output lỗi
                "fp16": False,  # QUAN TRỌNG: fp16=False để tránh lỗi và đảm bảo độ chính xác
                "beam_size": beam_size,
                "temperature": temperature,
                "condition_on_previous_text": condition_on_previous_text,
                "best_of": best_of,
            }
            
            # Chỉ thêm initial_prompt nếu có
            if effective_prompt:
                transcribe_kwargs["initial_prompt"] = effective_prompt
            
            result = model.transcribe(
                audio_path_to_use,
                **transcribe_kwargs
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

def format_transcript(result: Dict, with_timestamps: bool = True, readable: bool = True) -> str:
    """
    Format transcript từ kết quả Whisper với segments dễ đọc
    
    Args:
        result: Whisper result dict
        with_timestamps: Có hiển thị timestamps không
        readable: Có chia thành segments dễ đọc không (7-15 từ, ≤6s)
    
    Returns:
        Formatted transcript string
    """
    if result is None:
        return ""
    
    text = result.get("text", "")
    segments = result.get("segments", [])
    
    if not with_timestamps or not segments:
        return text
    
    # Chia lại segments cho dễ đọc nếu cần
    if readable:
        segments = split_segments_readable(segments, max_words=15, max_duration=6.0)
    
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
    """
    Format thời gian từ seconds sang format dễ đọc [0.00 - 3.20]
    Chuẩn cho subtitle/transcript dễ đọc
    """
    return f"{seconds:.2f}"


def split_text_readable(text: str, max_words: int = 15, max_sentences: int = 2) -> List[str]:
    """
    Chia text thành các đoạn dễ đọc
    
    Tiêu chuẩn:
    - 7-15 từ mỗi đoạn (max_words)
    - Không quá 2 câu mỗi đoạn (max_sentences)
    - Mỗi đoạn ≤ 5-6 giây khi đọc
    
    Args:
        text: Text cần chia
        max_words: Số từ tối đa mỗi đoạn (default: 15)
        max_sentences: Số câu tối đa mỗi đoạn (default: 2)
    
    Returns:
        List các đoạn text đã chia
    """
    if not text or not text.strip():
        return []
    
    import re
    
    # Chia theo câu (giữ lại dấu câu)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        words = sentence.split()
        word_count = len(words)
        
        # Nếu câu hiện tại quá dài, chia nhỏ câu đó
        if word_count > max_words:
            # Chia câu thành các phần nhỏ hơn
            for i in range(0, word_count, max_words):
                part = " ".join(words[i:i + max_words])
                chunks.append(part.strip())
        else:
            # Kiểm tra xem có thể thêm câu này vào chunk hiện tại không
            if (len(current_chunk) < max_sentences and 
                current_word_count + word_count <= max_words):
                # Có thể thêm vào chunk hiện tại
                current_chunk.append(sentence)
                current_word_count += word_count
            else:
                # Lưu chunk hiện tại và bắt đầu chunk mới
                if current_chunk:
                    chunks.append(" ".join(current_chunk).strip())
                current_chunk = [sentence]
                current_word_count = word_count
    
    # Thêm chunk cuối cùng nếu còn
    if current_chunk:
        chunks.append(" ".join(current_chunk).strip())
    
    return [chunk for chunk in chunks if chunk]


def split_segments_readable(segments: List[Dict], max_words: int = 15, max_duration: float = 6.0) -> List[Dict]:
    """
    Chia lại Whisper segments thành các đoạn dễ đọc hơn
    
    Args:
        segments: List segments từ Whisper (có start, end, text)
        max_words: Số từ tối đa mỗi đoạn (default: 15)
        max_duration: Thời gian tối đa mỗi đoạn (giây, default: 6.0)
    
    Returns:
        List segments mới với text đã được chia nhỏ và timestamps mới
    """
    readable_segments = []
    
    for seg in segments:
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        text = seg.get("text", "").strip()
        
        if not text:
            continue
        
        # Chia text thành các đoạn nhỏ
        sub_texts = split_text_readable(text, max_words=max_words, max_sentences=2)
        
        if not sub_texts:
            continue
        
        # Tính thời gian cho mỗi đoạn
        duration = end - start
        num_parts = len(sub_texts)
        per_part = duration / num_parts if num_parts > 0 else duration
        
        # Tạo segments mới với timestamps được chia đều
        for i, sub_text in enumerate(sub_texts):
            seg_start = round(start + i * per_part, 2)
            seg_end = round(start + (i + 1) * per_part, 2)
            
            # Đảm bảo không vượt quá max_duration
            if seg_end - seg_start > max_duration:
                # Nếu một đoạn quá dài, chia đều lại
                words = sub_text.split()
                if len(words) > max_words:
                    words_per_part = max_words
                    num_sub_parts = (len(words) + words_per_part - 1) // words_per_part
                    sub_duration = (seg_end - seg_start) / num_sub_parts
                    
                    for j in range(0, len(words), words_per_part):
                        part_text = " ".join(words[j:j + words_per_part])
                        part_start = seg_start + (j // words_per_part) * sub_duration
                        part_end = min(seg_start + ((j // words_per_part) + 1) * sub_duration, seg_end)
                        
                        readable_segments.append({
                            "start": round(part_start, 2),
                            "end": round(part_end, 2),
                            "text": part_text.strip()
                        })
                else:
                    readable_segments.append({
                        "start": seg_start,
                        "end": seg_end,
                        "text": sub_text.strip()
                    })
    else:
                readable_segments.append({
                    "start": seg_start,
                    "end": seg_end,
                    "text": sub_text.strip()
                })
    
    return readable_segments

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

