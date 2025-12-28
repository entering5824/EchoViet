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
    )

    if uploaded_file:
        with st.spinner("Loading audio..."):
            audio_data, sr = load_audio(uploaded_file)

        if audio_data is None:
            st.error("❌ Không thể load audio")
        else:
            st.session_state.audio_data = audio_data
            st.session_state.audio_sr = sr
            st.session_state.audio_info = get_audio_info(audio_data, sr)
            st.session_state.audio_ready = False
            st.session_state.audio_source = uploaded_file
            st.success("✅ Audio loaded")

with tab_record:
    st.info("Ghi âm trực tiếp từ trình duyệt (tùy chọn)")

    try:
        from audio_recorder_streamlit import audio_recorder

        audio_bytes = audio_recorder()

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                audio_data, sr = load_audio(tmp_path)
                if audio_data is not None:
                    st.session_state.audio_data = audio_data
                    st.session_state.audio_sr = sr
                    st.session_state.audio_info = get_audio_info(audio_data, sr)
                    st.session_state.audio_ready = False
                    st.session_state.audio_source = audio_bytes
                    st.success("✅ Audio recorded")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    except ImportError:
        st.warning("Cài đặt audio-recorder-streamlit để dùng chức năng ghi âm")

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
    
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
        <strong>💡 Hướng dẫn:</strong> Chọn chế độ phù hợp với nhu cầu của bạn. 
        <strong>Đề xuất</strong> là lựa chọn tốt nhất cho hầu hết trường hợp.
    </div>
    """, unsafe_allow_html=True)
    
    # Preset Mode Selection
    mode_options = {
        "simple": {
            "name": "🎯 Đơn giản",
            "description": "Tự động xử lý với cài đặt mặc định - Phù hợp cho người dùng không chuyên",
            "icon": "🎯"
        },
        "recommended": {
            "name": "⭐ Đề xuất (Khuyến nghị)",
            "description": "Cài đặt tối ưu cho chất lượng và tốc độ - Phù hợp cho hầu hết người dùng",
            "icon": "⭐"
        },
        "advanced": {
            "name": "⚙️ Nâng cao",
            "description": "Tùy chỉnh chi tiết các thông số - Dành cho người dùng có kinh nghiệm",
            "icon": "⚙️"
        }
    }
    
    # Display preset selection with better UI
    preset_cols = st.columns(3)
    selected_mode = st.session_state.preprocess_mode
    
    with preset_cols[0]:
        if st.button(
            mode_options["simple"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "simple" else "secondary",
            key="preset_simple"
        ):
            selected_mode = "simple"
            st.session_state.preprocess_mode = "simple"
            st.session_state.preprocess_normalize = True
            st.session_state.preprocess_trim_silence = False
            st.session_state.preprocess_remove_noise = False
            st.session_state.preprocess_target_sr = 16000
            st.rerun()
    
    with preset_cols[1]:
        if st.button(
            mode_options["recommended"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "recommended" else "secondary",
            key="preset_recommended"
        ):
            selected_mode = "recommended"
            st.session_state.preprocess_mode = "recommended"
            st.session_state.preprocess_normalize = True
            st.session_state.preprocess_trim_silence = False
            st.session_state.preprocess_remove_noise = False
            st.session_state.preprocess_target_sr = 16000
            st.rerun()
    
    with preset_cols[2]:
        if st.button(
            mode_options["advanced"]["name"],
            use_container_width=True,
            type="primary" if selected_mode == "advanced" else "secondary",
            key="preset_advanced"
        ):
            selected_mode = "advanced"
            st.session_state.preprocess_mode = "advanced"
            st.rerun()
    
    # Show description of selected preset
    current_preset = mode_options[st.session_state.preprocess_mode]
    st.info(f"**{current_preset['name']}**: {current_preset['description']}")
    
    # Configuration based on preset mode
    st.markdown("### ⚙️ Cài Đặt")
    
    if st.session_state.preprocess_mode == "simple":
        # Simple mode: Show minimal, user-friendly options
        st.markdown("""
        **Chế độ Đơn giản** sẽ tự động:
        - ✅ Chuẩn hóa âm lượng (normalize) để âm thanh rõ ràng hơn
        - ✅ Giữ nguyên sample rate 16kHz (tối ưu cho nhận diện giọng nói)
        - ❌ Không cắt im lặng (giữ nguyên thời lượng)
        - ❌ Không lọc nhiễu (giữ nguyên chất lượng gốc)
        """)
        
        # Just show what will be applied
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Chuẩn hóa âm lượng:** ✅ Bật")
        with col2:
            st.markdown("**Sample Rate:** 16kHz")
        with col3:
            st.markdown("**Cắt im lặng:** ❌ Tắt")
        
        # Use saved values
        normalize = st.session_state.preprocess_normalize
        trim_silence = st.session_state.preprocess_trim_silence
        remove_noise = st.session_state.preprocess_remove_noise
        target_sr = st.session_state.preprocess_target_sr
        
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
                    
                except Exception as e:
                    st.error(f"❌ Lỗi khi xử lý audio: {str(e)}")
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
