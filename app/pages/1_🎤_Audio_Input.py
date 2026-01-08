"""
Audio Input & Preparation Page
Upload / record audio, overview, visualization, basic preprocessing
"""
import streamlit as st
import os
import sys
import tempfile

# ================== PATH SETUP ==================
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.layout import apply_custom_css, render_page_header
from app.components.audio_visualizer import render_audio_visualization
from app.components.footer import render_footer
from core.audio.audio_processor import (
    load_audio,
    get_audio_info,
    preprocess_audio,
)
from core.audio.ffmpeg_setup import ensure_ffmpeg

# ================== ENV SETUP ==================
ensure_ffmpeg(silent=True)
apply_custom_css()

st.set_page_config(
    page_title="Audio Input - Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide",
)

# ================== SESSION STATE ==================
def init_state():
    defaults = {
        "audio_data": None,
        "audio_sr": None,
        "audio_info": None,
        "audio_ready": False,
        "audio_source": None,
        "preprocess_mode": "recommended",  # simple, recommended, advanced
        "preprocess_normalize": True,
        "preprocess_trim_silence": False,
        "preprocess_remove_noise": False,
        "preprocess_target_sr": 16000,
        "preprocess_noise_cutoff": 80,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_state()

# ================== HEADER ==================
render_page_header("Audio Input & Preparation", "Upload hoặc ghi âm audio, kiểm tra và chuẩn bị cho ASR pipeline", "🎤")

# ================== INPUT ==================
tab_upload, tab_record = st.tabs(["📤 Upload", "🎙️ Record"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Audio file (wav, mp3, flac, m4a, ogg)",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Tải lên file audio để bắt đầu. Hỗ trợ các định dạng: WAV, MP3, FLAC, M4A, OGG"
    )

    if uploaded_file:
        # Validation: Check file size (max 200MB)
        max_size_mb = 200
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            st.error(f"❌ File quá lớn ({file_size_mb:.1f}MB). Kích thước tối đa: {max_size_mb}MB")
            st.info("💡 **Gợi ý**: Hãy nén file hoặc chia nhỏ file audio")
        else:
            with st.spinner("⏳ Đang tải audio..."):
                try:
                    audio_data, sr = load_audio(uploaded_file)
                    
                    if audio_data is None:
                        st.error("❌ Không thể load audio. Vui lòng kiểm tra file có hợp lệ không.")
                        st.info("💡 **Gợi ý**: \n- Đảm bảo file không bị hỏng\n- Thử chuyển đổi sang định dạng WAV\n- Kiểm tra file có phải là audio không")
                    else:
                        # Additional validation: Check duration
                        duration = len(audio_data) / sr
                        if duration < 0.1:
                            st.warning("⚠️ File audio quá ngắn (< 0.1 giây). Có thể không phải file audio hợp lệ.")
                        elif duration > 3600:  # 1 hour
                            st.warning(f"⚠️ File audio rất dài ({duration/60:.1f} phút). Quá trình xử lý có thể mất nhiều thời gian.")
                        
                        st.session_state.audio_data = audio_data
                        st.session_state.audio_sr = sr
                        st.session_state.audio_info = get_audio_info(audio_data, sr)
                        st.session_state.audio_ready = False
                        st.session_state.audio_source = uploaded_file
                        st.success(f"✅ Đã tải audio thành công! ({file_size_mb:.1f}MB, {duration:.1f}s)")
                        
                except Exception as e:
                    st.error(f"❌ Lỗi khi tải audio: {str(e)}")
                    st.info("💡 **Gợi ý**: \n- Kiểm tra file có bị hỏng không\n- Thử file audio khác\n- Đảm bảo định dạng được hỗ trợ")

with tab_record:
    st.info("🎙️ Ghi âm trực tiếp từ trình duyệt. Nhấn nút để bắt đầu/dừng ghi âm.")
    
    # Initialize recorded audio in session state
    if "recorded_audio_bytes" not in st.session_state:
        st.session_state.recorded_audio_bytes = None
    if "recorded_audio_hash" not in st.session_state:
        st.session_state.recorded_audio_hash = None
    
    try:
        from audio_recorder_streamlit import audio_recorder
        import hashlib

        # Show recorder
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#6c757d",
            icon_name="microphone",
            icon_size="2x",
        )

        # Check if new audio was recorded (different from stored)
        if audio_bytes is not None:
            # Create hash to check if audio is new
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            
            # Check if this is new audio (different hash from what we have)
            if st.session_state.recorded_audio_hash != audio_hash:
                st.session_state.recorded_audio_bytes = audio_bytes
                st.session_state.recorded_audio_hash = audio_hash
                
                # Process the new audio
                with st.spinner("⏳ Đang xử lý audio đã ghi..."):
                    try:
                        # Create temp file for audio bytes
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                            tmp.write(audio_bytes)
                            tmp_path = tmp.name
                        
                        try:
                            # Load audio using load_audio function
                            audio_data, sr = load_audio(tmp_path)
                            
                            if audio_data is not None and len(audio_data) > 0:
                                # Calculate duration
                                duration = len(audio_data) / sr
                                
                                # Validate duration
                                if duration < 0.1:
                                    st.warning("⚠️ Audio quá ngắn (< 0.1 giây). Vui lòng ghi âm lại.")
                                else:
                                    # Save to session state
                                    st.session_state.audio_data = audio_data
                                    st.session_state.audio_sr = sr
                                    st.session_state.audio_info = get_audio_info(audio_data, sr)
                                    st.session_state.audio_ready = False
                                    st.session_state.audio_source = audio_bytes
                                    
                                    st.success(f"✅ Đã ghi âm thành công! ({duration:.1f}s)")
                                    
                                    # Show audio player
                                    st.audio(audio_bytes, format="audio/wav")
                            else:
                                st.error("❌ Không thể load audio đã ghi. Vui lòng thử lại.")
                        finally:
                            # Clean up temp file
                            try:
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                            except Exception:
                                pass
                    except Exception as e:
                        st.error(f"❌ Lỗi khi xử lý audio đã ghi: {str(e)}")
                        st.info("💡 **Gợi ý**: \n- Đảm bảo microphone hoạt động\n- Kiểm tra quyền truy cập microphone\n- Thử ghi âm lại")
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.exception(e)
        
        # Show previously recorded audio if available
        elif st.session_state.recorded_audio_bytes is not None:
            st.info("📼 Audio đã ghi trước đó:")
            st.audio(st.session_state.recorded_audio_bytes, format="audio/wav")
            
            # Option to clear recorded audio
            if st.button("🗑️ Xóa audio đã ghi", key="clear_recorded_audio"):
                st.session_state.recorded_audio_bytes = None
                st.session_state.audio_data = None
                st.session_state.audio_sr = None
                st.session_state.audio_info = None
                st.session_state.audio_source = None
                st.success("✅ Đã xóa audio đã ghi")
                st.rerun()
        
        # Show current audio status if loaded
        if st.session_state.audio_data is not None and st.session_state.recorded_audio_bytes is not None:
            duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
            st.info(f"✅ Audio đã sẵn sàng ({duration:.1f}s). Bạn có thể tiếp tục với tiền xử lý hoặc transcription.")
            
    except ImportError:
        st.warning("⚠️ Chưa cài đặt `audio-recorder-streamlit`. Cài đặt bằng lệnh: `pip install audio-recorder-streamlit`")
        st.info("💡 Sau khi cài đặt, làm mới trang để sử dụng tính năng ghi âm.")
    except Exception as e:
        st.error(f"❌ Lỗi khi khởi tạo audio recorder: {str(e)}")
        st.info("💡 **Gợi ý**: \n- Kiểm tra quyền truy cập microphone\n- Đảm bảo trình duyệt hỗ trợ Web Audio API\n- Thử trên trình duyệt khác (Chrome, Edge)")

# ================== OVERVIEW ==================
if st.session_state.audio_data is not None:
    st.divider()
    st.subheader("📄 Audio Overview")

    info = st.session_state.audio_info
    c1, c2, c3 = st.columns(3)
    c1.metric("Duration", f"{info['duration']:.1f}s")
    c2.metric("Sample Rate", f"{st.session_state.audio_sr} Hz")
    c3.metric("Samples", f"{len(st.session_state.audio_data):,}")

    if isinstance(st.session_state.audio_source, bytes):
        st.audio(st.session_state.audio_source, format="audio/wav")
    else:
        st.audio(st.session_state.audio_source)

    # ================== VISUALIZATION ==================
    with st.expander("📊 Waveform & Visualization"):
        render_audio_visualization(
            st.session_state.audio_data,
            st.session_state.audio_sr,
        )

    # ================== PREPROCESSING ==================
    st.divider()
    st.subheader("🔧 Tiền Xử Lý Âm Thanh")
    
    # Default to recommended mode
    if st.session_state.preprocess_mode not in ["simple", "recommended", "advanced"]:
        st.session_state.preprocess_mode = "recommended"
    
    # Simplified mode selection - default to recommended, hide advanced by default
    use_advanced = st.checkbox(
        "⚙️ Hiển thị tùy chọn nâng cao",
        value=False,
        help="Bật để xem và tùy chỉnh các thông số kỹ thuật chi tiết"
    )
    
    if use_advanced:
        # Show mode selection only if advanced is enabled
        mode_options = {
            "simple": "🎯 Đơn giản - Tự động xử lý với cài đặt mặc định",
            "recommended": "⭐ Đề xuất - Cài đặt tối ưu (Khuyến nghị)",
            "advanced": "⚙️ Nâng cao - Tùy chỉnh chi tiết"
        }
        
        selected_mode = st.radio(
            "Chọn chế độ xử lý:",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            index=list(mode_options.keys()).index(st.session_state.preprocess_mode),
            help="Chế độ 'Đề xuất' là lựa chọn tốt nhất cho hầu hết trường hợp"
        )
        st.session_state.preprocess_mode = selected_mode
    else:
        # Default to recommended mode
        st.session_state.preprocess_mode = "recommended"
        st.info("💡 **Chế độ Đề xuất**: Sử dụng cài đặt tối ưu cho chất lượng và tốc độ. Bật 'Tùy chọn nâng cao' để tùy chỉnh.")
    
    # Configuration based on preset mode
    st.markdown("### ⚙️ Cài Đặt")
    
    if st.session_state.preprocess_mode == "simple":
        # Simple mode: Show minimal, user-friendly options
        st.markdown("""
        **Chế độ Đơn giản** sẽ tự động:
        - ✅ Chuẩn hóa âm lượng để âm thanh rõ ràng hơn
        - ✅ Giữ nguyên sample rate 16kHz (tối ưu cho nhận diện giọng nói)
        - ❌ Không cắt im lặng (giữ nguyên thời lượng)
        - ❌ Không lọc nhiễu (giữ nguyên chất lượng gốc)
        """)
        
        # Use saved values
        normalize = True
        trim_silence = False
        remove_noise = False
        target_sr = 16000
        
    elif st.session_state.preprocess_mode == "recommended":
        # Recommended mode: Show recommended settings with explanations
        st.markdown("""
        **Chế độ Đề xuất** sử dụng các cài đặt đã được tối ưu:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            normalize = st.checkbox(
                "✅ Chuẩn hóa âm lượng",
                value=st.session_state.preprocess_normalize,
                help="Điều chỉnh âm lượng về mức chuẩn để cải thiện chất lượng nhận diện. Nên bật trong hầu hết trường hợp."
            )
            st.session_state.preprocess_normalize = normalize
            
            trim_silence = st.checkbox(
                "✂️ Cắt im lặng ở đầu/cuối",
                value=st.session_state.preprocess_trim_silence,
                help="Tự động loại bỏ khoảng im lặng ở đầu và cuối file. Tắt nếu bạn muốn giữ nguyên thời lượng gốc."
            )
            st.session_state.preprocess_trim_silence = trim_silence
        
        with col2:
            target_sr = st.selectbox(
                "🎵 Tần số lấy mẫu (Sample Rate)",
                [16000, 22050, 44100],
                index=[16000, 22050, 44100].index(st.session_state.preprocess_target_sr),
                help="16kHz là tối ưu cho nhận diện giọng nói. Chỉ đổi nếu có yêu cầu đặc biệt."
            )
            st.session_state.preprocess_target_sr = target_sr
            
            remove_noise = st.checkbox(
                "🔇 Giảm nhiễu tần số thấp",
                value=st.session_state.preprocess_remove_noise,
                help="Lọc bỏ tiếng ồn tần số thấp (như tiếng gió, rung động). Chỉ bật khi audio có nhiều nhiễu."
            )
            st.session_state.preprocess_remove_noise = remove_noise
    
    else:  # advanced mode
        # Advanced mode: Show all options with technical details
        st.markdown("""
        **Chế độ Nâng cao** cho phép tùy chỉnh chi tiết tất cả các thông số kỹ thuật.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            normalize = st.checkbox(
                "Chuẩn hóa âm lượng (Normalize Amplitude)",
                value=st.session_state.preprocess_normalize,
                help="Peak normalization: y = y / max(|y|). Đưa tín hiệu về biên độ tối đa ±1.0"
            )
            st.session_state.preprocess_normalize = normalize
            
            trim_silence = st.checkbox(
                "Cắt im lặng (Trim Silence)",
                value=st.session_state.preprocess_trim_silence,
                help="Sử dụng librosa.effects.trim() để loại bỏ silence ở đầu và cuối audio dựa trên energy threshold"
            )
            st.session_state.preprocess_trim_silence = trim_silence
        
        with col2:
            target_sr = st.selectbox(
                "Target Sample Rate (Hz)",
                [8000, 16000, 22050, 44100],
                index=[8000, 16000, 22050, 44100].index(st.session_state.preprocess_target_sr) if st.session_state.preprocess_target_sr in [8000, 16000, 22050, 44100] else 1,
                help="Tần số lấy mẫu mục tiêu. 16kHz là chuẩn cho ASR. Resample sử dụng librosa.resample()"
            )
            st.session_state.preprocess_target_sr = target_sr
            
            remove_noise = st.checkbox(
                "Lọc nhiễu tần số thấp (High-pass Filter)",
                value=st.session_state.preprocess_remove_noise,
                help="Áp dụng Butterworth high-pass filter để loại bỏ noise dưới cutoff frequency"
            )
            st.session_state.preprocess_remove_noise = remove_noise
        
        # Advanced noise reduction settings
        if remove_noise:
            with st.expander("🔧 Cài đặt chi tiết - Lọc nhiễu"):
                noise_cutoff = st.slider(
                    "Tần số cắt (Cutoff Frequency) - Hz",
                    min_value=40,
                    max_value=200,
                    value=st.session_state.preprocess_noise_cutoff,
                    step=10,
                    help="Tần số dưới mức này sẽ bị lọc bỏ. 80Hz là giá trị mặc định hợp lý cho hầu hết trường hợp."
                )
                st.session_state.preprocess_noise_cutoff = noise_cutoff
                st.caption("⚠️ Lưu ý: Lọc quá mạnh có thể làm giảm chất lượng giọng nói. Chỉ điều chỉnh khi cần thiết.")
    
    # Preview before processing
    st.markdown("---")
    st.markdown("### 👁️ Xem trước")
    
    preview_col1, preview_col2 = st.columns(2)
    with preview_col1:
        st.markdown("**Trước khi xử lý:**")
        if isinstance(st.session_state.audio_source, bytes):
            st.audio(st.session_state.audio_source, format="audio/wav")
        else:
            st.audio(st.session_state.audio_source)
    
    with preview_col2:
        st.markdown("**Sau khi xử lý:**")
        st.info("Audio đã xử lý sẽ hiển thị ở đây sau khi bạn nhấn 'Áp dụng'")
    
    # Apply preprocessing button
    st.divider()
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        if st.button("🚀 Áp Dụng Tiền Xử Lý", type="primary", use_container_width=True):
            with st.spinner("⏳ Đang xử lý âm thanh..."):
                try:
                    audio = st.session_state.audio_data.copy()
                    original_sr = st.session_state.audio_sr  # Store original sample rate
                    was_resampled = False
                    
                    # Apply preprocessing
                    # For advanced mode with noise reduction, we'll handle it separately with custom cutoff
                    use_standard_noise_reduction = remove_noise and st.session_state.preprocess_mode != "advanced"
                    
                    audio = preprocess_audio(
                        audio,
                        original_sr,
                        normalize=normalize,
                        remove_noise=use_standard_noise_reduction,
                    )
                    
                    # Advanced mode: apply noise reduction with custom cutoff
                    if st.session_state.preprocess_mode == "advanced" and remove_noise:
                        from scipy import signal
                        cutoff = st.session_state.preprocess_noise_cutoff
                        sos = signal.butter(10, cutoff, 'hp', fs=original_sr, output='sos')
                        audio = signal.sosfilt(sos, audio)
                    
                    # Resample if needed
                    if target_sr != original_sr:
                        import librosa
                        audio = librosa.resample(audio, orig_sr=original_sr, target_sr=target_sr)
                        st.session_state.audio_sr = target_sr
                        was_resampled = True
                    
                    # Trim silence if enabled
                    if trim_silence:
                        import librosa
                        audio, _ = librosa.effects.trim(audio)
                    
                    st.session_state.audio_data = audio
                    st.session_state.audio_info = get_audio_info(audio, st.session_state.audio_sr)
                    st.session_state.audio_ready = True
                    
                    st.success("✅ Tiền xử lý hoàn tất! Audio đã sẵn sàng cho bước nhận diện giọng nói.")
                    
                    # Show what was applied
                    applied_settings = []
                    if normalize:
                        applied_settings.append("✅ Chuẩn hóa âm lượng")
                    if trim_silence:
                        applied_settings.append("✅ Cắt im lặng")
                    if remove_noise:
                        cutoff_value = st.session_state.preprocess_noise_cutoff if st.session_state.preprocess_mode == 'advanced' else 80
                        applied_settings.append(f"✅ Lọc nhiễu ({cutoff_value}Hz)")
                    if was_resampled:
                        applied_settings.append(f"✅ Resample {original_sr}Hz → {target_sr}Hz")
                    
                    if applied_settings:
                        st.info("**Đã áp dụng:** " + " | ".join(applied_settings))
                    
                    # Show preview of processed audio
                    st.audio(audio, sample_rate=st.session_state.audio_sr)
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Lỗi khi xử lý audio: {error_msg}")
                    
                    # Provide helpful suggestions
                    if "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                        st.info("💡 **Gợi ý**: File audio quá lớn. Hãy thử:\n- Chia nhỏ file audio\n- Sử dụng chế độ 'Đơn giản'\n- Giảm sample rate")
                    elif "format" in error_msg.lower() or "codec" in error_msg.lower():
                        st.info("💡 **Gợi ý**: Định dạng file không được hỗ trợ. Hãy thử:\n- Chuyển đổi sang WAV hoặc MP3\n- Kiểm tra file có bị hỏng không")
                    else:
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.exception(e)

    # ================== NEXT STEP ==================
    st.divider()
    st.info("🎯 Audio đã sẵn sàng cho bước Transcription & Speaker Diarization")

    if st.button("➡️ Go to Transcription", type="primary", use_container_width=True):
        st.switch_page("pages/2_📝_Transcription.py")

else:
    st.info("👆 Upload hoặc ghi âm audio để bắt đầu")

# ===== Footer =====
render_footer()
