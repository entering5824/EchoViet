"""
Module setup FFmpeg sử dụng imageio-ffmpeg
Tự động tải và cấu hình portable FFmpeg cho Streamlit Cloud
Sử dụng imageio-ffmpeg: portable FFmpeg binary không cần system installation
Chỉ cần ffmpeg cho whisper, không cần ffprobe (pipeline không dùng pydub)
"""

import os
import sys
import subprocess
import shutil
from typing import Optional, Tuple

# Đường dẫn FFmpeg cố định cho local Windows
LOCAL_FFMPEG_PATH = r"C:\Users\phamt\Downloads\Vietnamese-Speech-to-Text-System-for-Automatic-Meeting-Transcription\core\audio\ffmpeg.exe"

def verify_ffmpeg(ffmpeg_path: str) -> Tuple[bool, str]:
    """
    Verify FFmpeg có hoạt động không
    """
    try:
        result = subprocess.run(
            [ffmpeg_path, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
            return True, f"FFmpeg hoạt động: {version_line}"
        else:
            return False, f"FFmpeg không hoạt động (return code: {result.returncode})"
    except subprocess.TimeoutExpired:
        return False, "FFmpeg timeout khi kiểm tra"
    except FileNotFoundError:
        return False, f"Không tìm thấy FFmpeg tại: {ffmpeg_path}"
    except Exception as e:
        return False, f"Lỗi khi kiểm tra FFmpeg: {str(e)}"

def check_ffmpeg_in_path() -> Tuple[bool, Optional[str]]:
    """
    Kiểm tra xem FFmpeg có trong PATH không
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, ffmpeg_path
        except:
            pass

    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            which_result = shutil.which("ffmpeg")
            if which_result:
                return True, which_result
            which_cmd = 'where' if sys.platform == 'win32' else 'which'
            which_result = subprocess.run([which_cmd, 'ffmpeg'], capture_output=True, text=True, timeout=5)
            if which_result.returncode == 0:
                return True, which_result.stdout.strip()
    except:
        pass
    return False, None

def get_ffmpeg_path() -> Optional[str]:
    """
    Lấy đường dẫn FFmpeg executable
    Ưu tiên: local path > system FFmpeg > imageio-ffmpeg
    """
    # 1. Kiểm tra local Windows path
    if os.path.isfile(LOCAL_FFMPEG_PATH):
        verified, _ = verify_ffmpeg(LOCAL_FFMPEG_PATH)
        if verified:
            return LOCAL_FFMPEG_PATH

    # 2. Kiểm tra system FFmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        verified, _ = verify_ffmpeg(system_ffmpeg)
        if verified:
            return system_ffmpeg

    # 3. Fallback imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        verified, _ = verify_ffmpeg(ffmpeg_path)
        if verified:
            return ffmpeg_path
    except ImportError:
        return None

    return None

def setup_ffmpeg(silent=False, verbose=False) -> Tuple[bool, dict]:
    """
    Setup FFmpeg: ưu tiên local path > system > imageio
    """
    info = {
        "ffmpeg_path": None,
        "ffmpeg_dir": None,
        "source": None,
        "in_path": False,
        "verified": False,
        "error": None,
        "env_vars_set": False
    }

    try:
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path is None:
            info["error"] = "Không tìm thấy FFmpeg"
            return False, info

        verified, verify_msg = verify_ffmpeg(ffmpeg_path)
        info["ffmpeg_path"] = ffmpeg_path
        info["ffmpeg_dir"] = os.path.dirname(ffmpeg_path)
        info["verified"] = verified
        info["error"] = None if verified else verify_msg

        # Xác định nguồn
        if ffmpeg_path == LOCAL_FFMPEG_PATH:
            info["source"] = "local"
        elif shutil.which("ffmpeg"):
            info["source"] = "system"
        else:
            info["source"] = "imageio-ffmpeg"

        # Set environment variables
        os.environ["FFMPEG_BINARY"] = ffmpeg_path
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
        os.environ["LIBROSA_FFMPEG_BINARY"] = ffmpeg_path
        info["env_vars_set"] = True

        # Thêm vào PATH
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = current_path + os.pathsep + ffmpeg_dir

        # Kiểm tra PATH
        in_path, path_location = check_ffmpeg_in_path()
        info["in_path"] = in_path
        if path_location:
            info["path_location"] = path_location

        if not silent:
            if verified:
                try:
                    import streamlit as st
                    st.success(f"✅ FFmpeg đã được cấu hình thành công! ({info['source']})")
                    if verbose:
                        st.info(f"📍 Path: {ffmpeg_path}")
                except:
                    print(f"✅ FFmpeg đã được cấu hình thành công! ({info['source']})")
            else:
                try:
                    import streamlit as st
                    st.warning(f"⚠️ FFmpeg setup nhưng không xác thực được: {verify_msg}")
                except:
                    print(f"⚠️ FFmpeg setup nhưng không xác thực được: {verify_msg}")

        return verified, info

    except ImportError:
        error_msg = "Không tìm thấy imageio-ffmpeg"
        info["error"] = error_msg
        if not silent:
            try:
                import streamlit as st
                st.error(f"❌ {error_msg}. Vui lòng cài đặt: pip install imageio-ffmpeg")
            except:
                print(f"❌ {error_msg}. Vui lòng cài đặt: pip install imageio-ffmpeg")
        return False, info
    except Exception as e:
        error_msg = f"Không thể setup FFmpeg: {str(e)}"
        info["error"] = error_msg
        if not silent:
            try:
                import streamlit as st
                st.warning(f"⚠️ {error_msg}")
            except:
                print(f"⚠️ {error_msg}")
        return False, info

# Tự động setup khi import
_ffmpeg_setup_done = False
_ffmpeg_info = None

def ensure_ffmpeg(silent=True, verbose=False) -> Tuple[bool, dict]:
    """
    Đảm bảo FFmpeg đã được setup
    """
    global _ffmpeg_setup_done, _ffmpeg_info
    if not _ffmpeg_setup_done:
        success, info = setup_ffmpeg(silent=silent, verbose=verbose)
        _ffmpeg_setup_done = True
        _ffmpeg_info = info
        return success, info
    else:
        return _ffmpeg_info.get("verified", False) if _ffmpeg_info else False, _ffmpeg_info or {}

def get_ffmpeg_info() -> dict:
    """Lấy thông tin FFmpeg hiện tại"""
    global _ffmpeg_info
    if _ffmpeg_info:
        return _ffmpeg_info.copy()
    ensure_ffmpeg(silent=True)
    return _ffmpeg_info or {}
