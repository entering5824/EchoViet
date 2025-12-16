"""
Module transcription sử dụng PhoWhisper (HuggingFace)
PhoWhisper là mô hình ASR tối ưu cho tiếng Việt từ VinAI Research
"""
import os
import sys
import traceback

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

# Setup FFmpeg trước khi import các thư viện khác
# PhoWhisper sử dụng transformers pipeline, có thể cần ffmpeg qua librosa
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.audio.ffmpeg_setup import ensure_ffmpeg, get_ffmpeg_info, verify_ffmpeg, get_ffmpeg_path

# Setup FFmpeg ngay từ đầu
ffmpeg_success, ffmpeg_info = ensure_ffmpeg(silent=True, verbose=True)

# Check Python version early
_python_version_valid, _python_version_warning = check_python_version()
if _python_version_warning:
    try:
        import streamlit as st
        st.warning(_python_version_warning)
    except:
        print(_python_version_warning)

import torch
import streamlit as st
from typing import Optional, Dict, List
import numpy as np
from transformers import pipeline
import librosa
import soundfile as sf
import tempfile
import subprocess
import time
import shutil
from core.audio.audio_processor import _make_safe_temp_copy

def check_ffmpeg_for_librosa():
    """
    Kiểm tra xem librosa có thể tìm thấy FFmpeg không
    
    Returns:
        Tuple (success: bool, error_message: str)
    """
    try:
        # Thử load một file audio test với librosa
        # Tạo một file WAV đơn giản để test
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second at 16kHz
        tmp_name = None
        try:
            # Tạo file tạm và ngay lập tức đóng nó để tránh file-lock trên Windows
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp_name = tmp.name
            # Ghi dữ liệu vào file đã đóng
            sf.write(tmp_name, test_audio, 16000)

            # Thử load với librosa - nếu cần ffmpeg, sẽ báo lỗi ở đây
            # Thêm cơ chế retry ngắn để xử lý các trường hợp lock tạm thời trên Windows
            import time
            last_exc = None
            for attempt in range(5):
                try:
                    y, sr = librosa.load(tmp_name, sr=16000)
                    last_exc = None
                    break
                except Exception as e:
                    last_exc = e
                    # Nếu là lỗi do file đang được dùng (WinError 32), thử lại sau chút delay
                    if (isinstance(e, OSError) and getattr(e, 'winerror', None) == 32) or 'The process cannot access the file' in str(e):
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    else:
                        # Nếu lỗi liên quan FFmpeg, cố gắng setup lại FFmpeg và thử một lần nữa
                        error_msg = str(e)
                        if 'ffmpeg' in error_msg.lower() or 'ffmpeg was not found' in error_msg.lower():
                            # Re-run ffmpeg setup (may set env vars or add to PATH)
                            ensure_ffmpeg(silent=False, verbose=True)
                            time.sleep(0.2)
                            try:
                                y, sr = librosa.load(tmp_name, sr=16000)
                                last_exc = None
                            except Exception as e2:
                                last_exc = e2
                            break
                        # Không phải lỗi tạm thời or ffmpeg -> dừng ngay
                        break

            # Nếu có exception sau các lần thử, xử lý nó
            if last_exc:
                error_msg = str(last_exc)
                # Nếu lỗi ám chỉ thiếu FFmpeg, trả về lỗi rõ ràng kèm thông tin FFmpeg hiện tại
                if "ffmpeg" in error_msg.lower() or 'ffmpeg was not found' in error_msg.lower():
                    ffmpeg_info = get_ffmpeg_info()
                    return False, f"Librosa không tìm thấy FFmpeg: {error_msg} | FFmpeg info: {ffmpeg_info}"
                # Nếu không phải lỗi FFmpeg, thử fallback qua soundfile
                try:
                    y, sr = sf.read(tmp_name)
                    if len(y.shape) > 1:
                        y = np.mean(y, axis=1)
                    if sr != 16000:
                        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                    return True, "Librosa test passed (fallback qua soundfile thành công)"
                except Exception as sf_err:
                    return True, f"Librosa test passed (error không liên quan FFmpeg: {error_msg}; soundfile fallback failed: {str(sf_err)})"

            return True, "Librosa có thể load audio (FFmpeg OK)"
        finally:
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except Exception:
                    pass
    except Exception as e:
        return False, f"Lỗi khi test librosa: {str(e)}"

@st.cache_resource
def load_phowhisper_model(model_size="small"):
    """
    Load PhoWhisper model từ HuggingFace với cache
    
    Args:
        model_size: "small", "medium", hoặc "base"
    
    Returns:
        pipeline: Transformers pipeline object hoặc None nếu lỗi
    """
    error_details = []
    
    try:
        # 1. Kiểm tra FFmpeg
        error_details.append("=== FFmpeg Setup Check ===")
        ffmpeg_success, ffmpeg_info = ensure_ffmpeg(silent=True, verbose=True)
        error_details.append(f"FFmpeg setup success: {ffmpeg_success}")
        error_details.append(f"FFmpeg path: {ffmpeg_info.get('ffmpeg_path', 'Not found')}")
        error_details.append(f"FFmpeg verified: {ffmpeg_info.get('verified', False)}")
        error_details.append(f"FFmpeg in PATH: {ffmpeg_info.get('in_path', False)}")
        
        if not ffmpeg_success:
            error_details.append(f"FFmpeg error: {ffmpeg_info.get('error', 'Unknown')}")
        
        # 2. Kiểm tra librosa có thể dùng FFmpeg
        error_details.append("\n=== Librosa FFmpeg Check ===")
        librosa_ok, librosa_msg = check_ffmpeg_for_librosa()
        error_details.append(f"Librosa check: {librosa_ok}")
        error_details.append(f"Librosa message: {librosa_msg}")
        
        if not librosa_ok:
            st.error(f"❌ Librosa không thể sử dụng FFmpeg: {librosa_msg}")
            with st.expander("🔍 Chi tiết lỗi FFmpeg"):
                st.code("\n".join(error_details))
            return None
        
        # 3. Kiểm tra và cài đặt tf-keras nếu cần
        error_details.append("\n=== Keras Check ===")
        try:
            import tf_keras
            error_details.append("tf-keras: OK")
        except ImportError:
            try:
                import subprocess
                import sys
                st.warning("⚠️ Đang cài đặt tf-keras để tương thích với Keras 3...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "tf-keras>=2.15.0", "-q"])
                import tf_keras
                error_details.append("tf-keras: Installed successfully")
            except Exception as install_error:
                error_msg = f"Không thể cài đặt tf-keras: {str(install_error)}"
                error_details.append(f"tf-keras: FAILED - {error_msg}")
                st.error(f"❌ {error_msg}")
                st.info("💡 Vui lòng cài đặt thủ công: pip install tf-keras")
                with st.expander("🔍 Chi tiết lỗi"):
                    st.code("\n".join(error_details))
                return None
        
        # 4. Check memory usage before loading model
        error_details.append("\n=== Memory Check ===")
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024 / 1024  # MB
            error_details.append(f"Memory before model load: {mem_before:.2f} MB")
            if mem_before > 500:
                st.warning(f"⚠️ Memory usage cao trước khi load model: {mem_before:.2f} MB. Có thể gây vấn đề trên Streamlit Cloud (limit ~1GB).")
        except ImportError:
            error_details.append("psutil not available for memory monitoring")
        except Exception as mem_err:
            error_details.append(f"Memory check failed: {str(mem_err)}")
        
        # 5. Load model
        error_details.append("\n=== Model Loading ===")
        # Ensure we don't force CUDA on Cloud (check if CUDA is actually available)
        device = 0 if torch.cuda.is_available() else -1
        # On Streamlit Cloud, force CPU even if CUDA is detected (to avoid issues)
        if os.getenv("STREAMLIT_SHARING", "").lower() == "true" or os.getenv("STREAMLIT_SERVER_BASE_URL", ""):
            device = -1  # Force CPU on Cloud
            error_details.append("Streamlit Cloud detected: forcing CPU device")
        
        model_name = f"vinai/PhoWhisper-{model_size}"
        error_details.append(f"Model: {model_name}")
        error_details.append(f"Device: {device} (0=GPU, -1=CPU)")
        
        try:
            transcriber = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device=device
            )
            
            # Check memory after loading
            try:
                import psutil
                process = psutil.Process(os.getpid())
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                mem_increase = mem_after - mem_before if 'mem_before' in locals() else 0
                error_details.append(f"Memory after model load: {mem_after:.2f} MB (increase: {mem_increase:.2f} MB)")
                if mem_after > 1000:
                    st.warning(f"⚠️ Memory usage cao sau khi load model: {mem_after:.2f} MB. Có thể gây crash trên Streamlit Cloud.")
            except:
                pass
            
            error_details.append("Model loaded: SUCCESS")
            return transcriber
        except KeyError as ke:
            # Handle "missing field" errors from model loading
            error_msg = f"Missing field error: {str(ke)}"
            error_details.append(f"KeyError (missing field): {error_msg}")
            st.error(f"❌ Lỗi 'missing field' khi load model. Đây thường do cache model bị lỗi.")
            st.warning("""
            **Khắc phục:**
            1. Xóa cache Whisper: `rm -rf ~/.cache/whisper` (Linux) hoặc xóa thư mục cache trên Windows
            2. Xóa cache Transformers: `rm -rf ~/.cache/huggingface`
            3. Restart ứng dụng và thử lại
            """)
            with st.expander("🔍 Chi tiết lỗi"):
                st.code("\n".join(error_details))
            return None
        except RuntimeError as re:
            # Handle CUDA unavailable errors
            error_msg = str(re)
            if "cuda" in error_msg.lower() or "CUDA" in error_msg:
                error_details.append(f"CUDA error: {error_msg}")
                st.error(f"❌ Lỗi CUDA: {error_msg}")
                st.info("💡 Đang tự động chuyển sang CPU mode...")
                # Retry with CPU
                try:
                    transcriber = pipeline(
                        "automatic-speech-recognition",
                        model=model_name,
                        device=-1  # Force CPU
                    )
                    error_details.append("Model loaded with CPU fallback: SUCCESS")
                    return transcriber
                except Exception as cpu_err:
                    error_details.append(f"CPU fallback also failed: {str(cpu_err)}")
                    st.error(f"❌ Không thể load model ngay cả với CPU: {str(cpu_err)}")
                    with st.expander("🔍 Chi tiết lỗi"):
                        st.code("\n".join(error_details))
                    return None
            else:
                raise  # Re-raise if not CUDA-related
        
    except Exception as e:
        error_msg = str(e)
        error_details.append(f"\n=== ERROR ===")
        error_details.append(f"Error type: {type(e).__name__}")
        error_details.append(f"Error message: {error_msg}")
        error_details.append(f"\nTraceback:\n{traceback.format_exc()}")
        
        # Hiển thị lỗi chi tiết
        st.error(f"❌ Lỗi khi load PhoWhisper model: {error_msg}")
        
        # Kiểm tra nếu là lỗi FFmpeg
        if "ffmpeg" in error_msg.lower() or "ffmpeg" in str(e).lower():
            st.error("🔴 LỖI FFMPEG PHÁT HIỆN!")
            st.warning("""
            **Các bước khắc phục:**
            1. Đảm bảo `imageio-ffmpeg` đã được cài đặt: `pip install imageio-ffmpeg`
            2. Kiểm tra FFmpeg có trong PATH
            3. Thử restart ứng dụng
            """)
        
        with st.expander("🔍 Chi tiết lỗi (Click để xem)"):
            st.code("\n".join(error_details))
            st.json(ffmpeg_info)
        
        return None

def transcribe_phowhisper(model, audio_path_or_array, sr=16000, language="vi"):
    """
    Transcribe audio sử dụng PhoWhisper
    
    Args:
        model: PhoWhisper pipeline model
        audio_path_or_array: Đường dẫn file hoặc numpy array
        sr: Sample rate (PhoWhisper yêu cầu 16kHz)
        language: Ngôn ngữ (vi cho tiếng Việt)
    
    Returns:
        Dict: Kết quả transcription với format tương thích Whisper
        {
            "text": str,
            "segments": List[Dict] (có thể rỗng nếu không có timestamps)
        }
    """
    error_details = []
    audio_path = None
    is_temp = False
    
    try:
        error_details.append("=== Transcription Start ===")
        
        if model is None:
            error_details.append("ERROR: Model is None")
            st.error("❌ Model không được load. Vui lòng kiểm tra lỗi ở bước load model.")
            return None
        
        # Xử lý input: có thể là file path hoặc numpy array
        error_details.append(f"Input type: {type(audio_path_or_array)}")
        
        if isinstance(audio_path_or_array, str):
            # Đã là file path
            audio_path = audio_path_or_array
            error_details.append(f"Using file path: {audio_path}")
            if not os.path.exists(audio_path):
                error_details.append(f"ERROR: File không tồn tại: {audio_path}")
                st.error(f"❌ File không tồn tại: {audio_path}")
                return None
        else:
            # Là numpy array, cần lưu vào temp file
            error_details.append(f"Input is numpy array, shape: {audio_path_or_array.shape if hasattr(audio_path_or_array, 'shape') else 'unknown'}")
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    sf.write(tmp_file.name, audio_path_or_array, sr)
                    audio_path = tmp_file.name
                    is_temp = True
                error_details.append(f"Created temp file: {audio_path}")
            except Exception as e:
                error_details.append(f"ERROR creating temp file: {str(e)}")
                st.error(f"❌ Không thể tạo file tạm: {str(e)}")
                return None
        
        # Kiểm tra FFmpeg trước khi transcribe
        error_details.append("\n=== Pre-transcribe FFmpeg Check ===")
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            verified, verify_msg = verify_ffmpeg(ffmpeg_path)
            error_details.append(f"FFmpeg path: {ffmpeg_path}")
            error_details.append(f"FFmpeg verified: {verified}")
            error_details.append(f"Verify message: {verify_msg}")
            
            if not verified:
                st.warning(f"⚠️ FFmpeg có thể không hoạt động: {verify_msg}")
        else:
            error_details.append("WARNING: FFmpeg path not found")
            st.warning("⚠️ Không tìm thấy FFmpeg path")
        
        # Transcribe với PhoWhisper
        error_details.append("\n=== Calling Pipeline ===")
        error_details.append(f"Audio path: {audio_path}")
        error_details.append(f"Return timestamps: True")
        
        # Preflight: ensure audio file exists and is readable (help diagnose WinError 2)
        preflight_attempts = 3
        for attempt in range(preflight_attempts):
            file_ok = audio_path and os.path.exists(audio_path) and os.path.isfile(audio_path)
            if file_ok:
                try:
                    # On Windows, ensure the path is accessible for reading
                    with open(audio_path, 'rb'):
                        pass
                    break
                except Exception as e:
                    # transient I/O error (file lock?) - retry
                    time.sleep(0.1 * (attempt + 1))
                    continue
            else:
                # If file not found, attempt to make a safe temp copy if original path looks readable
                try:
                    if os.path.exists(audio_path):
                        # path exists but not a file? continue to allow model to fail with clear message
                        pass
                    else:
                        # Original path missing; try to create temp copy from path if possible
                        # (This handles weird cases with trailing spaces in filenames)
                        base = os.path.basename(audio_path) if audio_path else None
                        if base and base.strip() != base:
                            # make a safe copy by reading bytes from the problematic path and creating a new temp file
                            try:
                                tmp_copy = _make_safe_temp_copy(audio_path)
                                audio_path = tmp_copy
                                is_temp = True
                                continue
                            except Exception:
                                pass
                except Exception:
                    pass
                time.sleep(0.1 * (attempt + 1))

        try:
            result = model(audio_path, return_timestamps=True)
            error_details.append("Pipeline call: SUCCESS")
            error_details.append(f"Result type: {type(result)}")
            error_details.append(f"Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        except KeyError as ke:
            # Handle "missing field" errors during transcription
            error_msg = f"Missing field error during transcription: {str(ke)}"
            error_details.append(f"KeyError (missing field): {error_msg}")
            st.error(f"❌ Lỗi 'missing field' khi transcribe. Đây thường do model cache bị lỗi.")
            st.warning("""
            **Khắc phục:**
            1. Xóa cache Transformers: `rm -rf ~/.cache/huggingface`
            2. Restart ứng dụng và thử lại
            3. Nếu vẫn lỗi, thử model size nhỏ hơn (small thay vì medium)
            """)
            # Clean up temp file
            if is_temp and audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass
            with st.expander("🔍 Chi tiết lỗi"):
                st.code("\n".join(error_details))
            return None
        except Exception as pipeline_error:
            error_msg = str(pipeline_error)
            error_details.append(f"Pipeline call: FAILED")
            error_details.append(f"Error type: {type(pipeline_error).__name__}")
            error_details.append(f"Error message: {error_msg}")
            error_details.append(f"\nTraceback:\n{traceback.format_exc()}")

            # Clean up temp file
            if is_temp and audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

            # Detect common "file not found" / WinError 2 cases
            if isinstance(pipeline_error, OSError) and getattr(pipeline_error, 'errno', None) == 2 or 'No such file' in error_msg or 'ffmpeg was not found' in error_msg.lower():
                st.error("🔴 FILE NOT FOUND / PATH ERROR DURING TRANSCRIBE!")
                st.error(f"❌ {error_msg}")
                with st.expander("🔍 Chi tiết lỗi"): 
                    st.code("\n".join(error_details))
                    st.json(get_ffmpeg_info())
                st.warning("""
                **Khắc phục nhanh:**
                1. Kiểm tra tên file có ký tự lạ (ví dụ dấu cách cuối tên) hoặc đường dẫn dài.
                2. Thử upload lại file hoặc rename để loại bỏ khoảng trắng cuối.
                3. Restart ứng dụng nếu vẫn gặp lỗi.
                """)
                return None

            # Kiểm tra nếu là lỗi FFmpeg
            if "ffmpeg" in error_msg.lower():
                st.error("🔴 LỖI FFMPEG KHI TRANSCRIBE!")
                st.error(f"❌ {error_msg}")

                # Hiển thị thông tin debug
                with st.expander("🔍 Chi tiết lỗi FFmpeg"):
                    st.code("\n".join(error_details))
                    st.json(get_ffmpeg_info())

                    # Thử test librosa
                    librosa_ok, librosa_msg = check_ffmpeg_for_librosa()
                    st.write(f"**Librosa test:** {librosa_ok}")
                    st.write(f"**Message:** {librosa_msg}")

                st.warning("""
                **Khắc phục:**
                1. Đảm bảo `imageio-ffmpeg` đã được cài: `pip install imageio-ffmpeg`
                2. Restart ứng dụng
                3. Kiểm tra file audio có hợp lệ không
                """)
            else:
                st.error(f"❌ Lỗi khi transcribe: {error_msg}")
                with st.expander("🔍 Chi tiết lỗi"):
                    st.code("\n".join(error_details))

            return None
        
        # Clean up temp file nếu có
        if is_temp and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
                error_details.append("Temp file cleaned up")
            except Exception as e:
                error_details.append(f"Warning: Could not delete temp file: {str(e)}")
        
        # Format kết quả
        error_details.append("\n=== Formatting Result ===")
        output = {
            "text": result.get("text", ""),
            "segments": []
        }
        
        # PhoWhisper có thể trả về chunks với timestamps
        if "chunks" in result:
            error_details.append(f"Found {len(result['chunks'])} chunks")
            for chunk in result["chunks"]:
                if "timestamp" in chunk:
                    timestamp = chunk["timestamp"]
                    output["segments"].append({
                        "start": timestamp[0] if isinstance(timestamp, (list, tuple)) else timestamp,
                        "end": timestamp[1] if isinstance(timestamp, (list, tuple)) and len(timestamp) > 1 else timestamp,
                        "text": chunk.get("text", "").strip()
                    })
        
        # Nếu không có chunks, tạo một segment duy nhất
        if not output["segments"] and output["text"]:
            try:
                if isinstance(audio_path_or_array, str):
                    duration = librosa.get_duration(path=audio_path_or_array)
                else:
                    duration = len(audio_path_or_array) / sr
            except:
                duration = 0
            
            output["segments"] = [{
                "start": 0.0,
                "end": duration,
                "text": output["text"]
            }]
            error_details.append(f"Created single segment, duration: {duration}")
        
        error_details.append("Transcription: SUCCESS")
        return output
        
    except Exception as e:
        error_msg = str(e)
        error_details.append(f"\n=== UNEXPECTED ERROR ===")
        error_details.append(f"Error type: {type(e).__name__}")
        error_details.append(f"Error message: {error_msg}")
        error_details.append(f"\nTraceback:\n{traceback.format_exc()}")
        
        st.error(f"❌ Lỗi không mong đợi khi transcribe: {error_msg}")
        
        # Clean up temp file nếu có
        if is_temp and audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except:
                pass
        
        with st.expander("🔍 Chi tiết lỗi (Click để xem)"):
            st.code("\n".join(error_details))
        
        return None

# Tái sử dụng các hàm format từ transcription_service
from .transcription_service import format_transcript, format_time, get_transcript_statistics
