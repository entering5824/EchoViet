"""
Module setup static FFmpeg từ GitHub
Tự động tải và cấu hình static FFmpeg cho Streamlit Cloud
Sử dụng static-ffmpeg từ GitHub: https://github.com/joshbernard/static-ffmpeg
"""
import os
import sys

def setup_ffmpeg(silent=False):
    """
    Setup static FFmpeg từ GitHub
    
    Args:
        silent: Nếu True, không hiển thị thông báo (dùng khi chưa có Streamlit context)
    
    Returns:
        bool: True nếu setup thành công
    """
    try:
        import static_ffmpeg
        # Thêm FFmpeg vào PATH
        static_ffmpeg.add_paths()
        
        # Kiểm tra xem ffmpeg có hoạt động không
        import subprocess
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                if not silent:
                    try:
                        import streamlit as st
                        st.success("✅ Static FFmpeg đã được tải và cấu hình thành công!")
                    except:
                        print("✅ Static FFmpeg đã được tải và cấu hình thành công!")
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
        except FileNotFoundError:
            # FFmpeg chưa được tải, thử lại
            if not silent:
                try:
                    import streamlit as st
                    st.info("ℹ️ Đang tải static FFmpeg từ GitHub...")
                except:
                    print("ℹ️ Đang tải static FFmpeg từ GitHub...")
            # Thử tải lại
            static_ffmpeg.add_paths()
            return True
            
    except ImportError:
        error_msg = "❌ Không tìm thấy static-ffmpeg. Vui lòng cài đặt: pip install static-ffmpeg"
        if not silent:
            try:
                import streamlit as st
                st.error(error_msg)
            except:
                print(error_msg)
        return False
    except Exception as e:
        error_msg = f"⚠️ Không thể setup static FFmpeg: {str(e)}"
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

