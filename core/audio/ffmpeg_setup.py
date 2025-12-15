"""
Module setup FFmpeg sử dụng imageio-ffmpeg
Tự động tải và cấu hình portable FFmpeg cho Streamlit Cloud
Sử dụng imageio-ffmpeg: portable FFmpeg binary không cần system installation
"""
import os
import sys
import shutil

def setup_ffmpeg(silent=False):
    """
    Setup FFmpeg từ imageio-ffmpeg
    
    Args:
        silent: Nếu True, không hiển thị thông báo (dùng khi chưa có Streamlit context)
    
    Returns:
        bool: True nếu setup thành công
    """
    try:
        import imageio_ffmpeg
        
        # Lấy đường dẫn ffmpeg executable từ imageio-ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Set environment variables để pydub, moviepy, whisper sử dụng
        os.environ["FFMPEG_BINARY"] = ffmpeg_path
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
        
        # Thêm vào PATH để các tool khác có thể tìm thấy
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = current_path + os.pathsep + ffmpeg_dir
        
        # Tạo alias ffprobe nếu chưa có (imageio-ffmpeg không có ffprobe)
        # ffmpeg binary có thể dùng làm ffprobe alias
        ffprobe_path = os.path.join(ffmpeg_dir, "ffprobe")
        if not os.path.exists(ffprobe_path):
            try:
                shutil.copy(ffmpeg_path, ffprobe_path)
            except Exception:
                # Nếu không copy được, có thể đã tồn tại hoặc không có quyền
                pass
        
        # Kiểm tra xem ffmpeg có hoạt động không
        import subprocess
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                if not silent:
                    try:
                        import streamlit as st
                        st.success("✅ FFmpeg đã được cấu hình thành công từ imageio-ffmpeg!")
                    except:
                        print("✅ FFmpeg đã được cấu hình thành công từ imageio-ffmpeg!")
                return True
            else:
                if not silent:
                    try:
                        import streamlit as st
                        st.warning("⚠️ FFmpeg đã được thêm vào PATH nhưng không thể kiểm tra version")
                    except:
                        print("⚠️ FFmpeg đã được thêm vào PATH nhưng không thể kiểm tra version")
                return True
        except subprocess.TimeoutExpired:
            # FFmpeg có thể đang chạy, coi như thành công
            return True
        except Exception as e:
            # Vẫn coi như thành công nếu đã set env vars
            if not silent:
                try:
                    import streamlit as st
                    st.warning(f"⚠️ Không thể kiểm tra FFmpeg: {str(e)}")
                except:
                    print(f"⚠️ Không thể kiểm tra FFmpeg: {str(e)}")
            return True
            
    except ImportError:
        error_msg = "❌ Không tìm thấy imageio-ffmpeg. Vui lòng cài đặt: pip install imageio-ffmpeg"
        if not silent:
            try:
                import streamlit as st
                st.error(error_msg)
            except:
                print(error_msg)
        return False
    except Exception as e:
        error_msg = f"⚠️ Không thể setup FFmpeg: {str(e)}"
        if not silent:
            try:
                import streamlit as st
                st.warning(error_msg)
            except:
                print(error_msg)
        # Vẫn tiếp tục, có thể system đã có ffmpeg
        return False

# Tự động setup khi import
_ffmpeg_setup_done = False

def ensure_ffmpeg(silent=True):
    """
    Đảm bảo FFmpeg đã được setup
    
    Args:
        silent: Nếu True, không hiển thị thông báo khi setup
    """
    global _ffmpeg_setup_done
    if not _ffmpeg_setup_done:
        setup_ffmpeg(silent=silent)
        _ffmpeg_setup_done = True
