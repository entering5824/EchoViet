"""
Hệ thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản
Vietnamese Speech to Text System for Automatic Meeting Transcription
"""
import streamlit as st
import numpy as np
import tempfile
import os
from datetime import datetime
import io
import soundfile as sf

# Setup static FFmpeg trước khi import các module khác
# Silent mode để tránh hiển thị thông báo khi chưa có Streamlit context
from ffmpeg_setup import ensure_ffmpeg
ensure_ffmpeg(silent=True)

# Import các module tự tạo
from audio_processor import (
    load_audio, preprocess_audio, plot_waveform, 
    plot_spectrogram, get_audio_info
)
from transcription_service import (
    load_whisper_model, transcribe_audio, format_transcript,
    format_time, get_transcript_statistics
)
from export_utils import export_txt, export_docx, export_pdf
from speaker_diarization import simple_speaker_segmentation, format_with_speakers

# Cấu hình trang
st.set_page_config(
    page_title="Vietnamese Speech to Text",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f4e79;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎤 Vietnamese Speech to Text")
st.sidebar.markdown("---")

# Menu điều hướng
page = st.sidebar.radio(
    "Chọn chức năng:",
    [
        "🏠 Trang chủ", 
        "📤 Upload & Transcribe", 
        "🎙️ Ghi âm trực tiếp", 
        "📊 Thống kê & Export",
        "🖼️ Image Encryption"
    ]
)

base = os.path.dirname(__file__)      # thư mục chứa file .py
img_path = os.path.join(base, "assets", "logo.webp")

if os.path.exists(img_path):
    st.sidebar.image(img_path, width=110)


# Initialize session state
if 'audio_data' not in st.session_state:
    st.session_state.audio_data = None
if 'audio_sr' not in st.session_state:
    st.session_state.audio_sr = None
if 'transcript_result' not in st.session_state:
    st.session_state.transcript_result = None
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""
if 'audio_info' not in st.session_state:
    st.session_state.audio_info = None

# ========== TRANG CHỦ ==========
if page == "🏠 Trang chủ":
    st.markdown('<div class="main-header">Topic 7. Designing and Developing a Vietnamese Speech to Text System for Automatic Meeting Transcription</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    ### 📋 Giới thiệu
    
    Hệ thống này cho phép bạn chuyển đổi giọng nói tiếng Việt thành văn bản một cách tự động và chính xác.
    Hệ thống hỗ trợ:
    
    - ✅ Upload file audio (WAV, MP3, FLAC)
    - ✅ Ghi âm trực tiếp từ microphone
    - ✅ Xử lý audio dài (meetings, interviews)
    - ✅ Visualize waveform và spectrogram
    - ✅ Tiền xử lý audio (normalize, noise reduction)
    - ✅ Transcription với timestamps
    - ✅ Speaker diarization (phân biệt người nói)
    - ✅ Export ra TXT, DOCX, PDF
    - ✅ Thống kê chi tiết
    
    ### 🚀 Bắt đầu
    
    1. Chọn **"Upload & Transcribe"** để upload file audio
    2. Hoặc chọn **"Ghi âm trực tiếp"** để ghi âm từ microphone
    3. Xem kết quả và export nếu cần
    
    ### 🔧 Công nghệ sử dụng
    
    - **Speech Recognition**: OpenAI Whisper
    - **Audio Processing**: Librosa, PyDub, SoundFile
    - **Visualization**: Matplotlib, Seaborn
    - **Framework**: Streamlit
    """)
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit and Whisper")

# ========== UPLOAD & TRANSCRIBE ==========
elif page == "📤 Upload & Transcribe":
    st.header("📤 Upload & Transcribe Audio")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Chọn file audio (WAV, MP3, FLAC)",
        type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
        help="Hỗ trợ các định dạng: WAV, MP3, FLAC, M4A, OGG"
    )
    
    if uploaded_file is not None:
        # Load audio
        with st.spinner("Đang tải audio..."):
            audio_data, sr = load_audio(uploaded_file)
            
            if audio_data is not None:
                st.session_state.audio_data = audio_data
                st.session_state.audio_sr = sr
                st.session_state.audio_info = get_audio_info(audio_data, sr)
                
                st.success(f"✅ Đã tải audio thành công!")
                
                # Hiển thị thông tin audio
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Độ dài", f"{st.session_state.audio_info['duration']:.2f} giây")
                with col2:
                    st.metric("Sample Rate", f"{sr} Hz")
                with col3:
                    st.metric("Số mẫu", f"{len(audio_data):,}")
        
        # Preprocessing options
        st.subheader("⚙️ Tiền xử lý Audio")
        col1, col2 = st.columns(2)
        with col1:
            normalize = st.checkbox("Normalize audio", value=True)
        with col2:
            remove_noise = st.checkbox("Loại bỏ noise", value=False)
        
        if st.button("Áp dụng tiền xử lý"):
            if st.session_state.audio_data is not None:
                with st.spinner("Đang xử lý..."):
                    st.session_state.audio_data = preprocess_audio(
                        st.session_state.audio_data, 
                        st.session_state.audio_sr,
                        normalize=normalize,
                        remove_noise=remove_noise
                    )
                st.success("✅ Đã áp dụng tiền xử lý!")
        
        # Visualization
        if st.session_state.audio_data is not None:
            st.subheader("📊 Visualization")
            viz_option = st.radio(
                "Chọn loại visualization:",
                ["Waveform", "Spectrogram", "Cả hai"],
                horizontal=True
            )
            
            if viz_option in ["Waveform", "Cả hai"]:
                fig_wave = plot_waveform(st.session_state.audio_data, st.session_state.audio_sr)
                st.pyplot(fig_wave)
            
            if viz_option in ["Spectrogram", "Cả hai"]:
                fig_spec = plot_spectrogram(st.session_state.audio_data, st.session_state.audio_sr)
                st.pyplot(fig_spec)
        
        # Transcription
        st.subheader("🎯 Transcription")
        
        col1, col2 = st.columns(2)
        with col1:
            model_size = st.selectbox(
                "Chọn model Whisper:",
                ["tiny", "base", "small", "medium", "large"],
                index=1,
                help="Model lớn hơn = chính xác hơn nhưng chậm hơn"
            )
        with col2:
            with_timestamps = st.checkbox("Hiển thị timestamps", value=True)
        
        speaker_diarization = st.checkbox("Speaker Diarization (phân biệt người nói)", value=False)
        
        if st.button("🚀 Bắt đầu Transcription", type="primary"):
            if st.session_state.audio_data is not None:
                with st.spinner(f"Đang transcribe với model {model_size}... (có thể mất vài phút)"):
                    # Load model
                    model, device = load_whisper_model(model_size)
                    
                    if model is not None:
                        # Lưu audio vào temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            sf.write(tmp_file.name, st.session_state.audio_data, st.session_state.audio_sr)
                            
                            # Transcribe
                            result = transcribe_audio(
                                model,
                                tmp_file.name,
                                sr=st.session_state.audio_sr,
                                language="vi",
                                task="transcribe"
                            )
                            
                            # Clean up
                            os.unlink(tmp_file.name)
                            
                            if result:
                                st.session_state.transcript_result = result
                                
                                # Format transcript
                                if speaker_diarization and 'segments' in result:
                                    # Simple speaker segmentation
                                    speaker_segments = simple_speaker_segmentation(
                                        st.session_state.audio_data,
                                        st.session_state.audio_sr,
                                        result['segments']
                                    )
                                    if speaker_segments:
                                        st.session_state.transcript_text = format_with_speakers(speaker_segments)
                                    else:
                                        st.session_state.transcript_text = format_transcript(
                                            result, with_timestamps=with_timestamps
                                        )
                                else:
                                    st.session_state.transcript_text = format_transcript(
                                        result, with_timestamps=with_timestamps
                                    )
                                
                                st.success("✅ Transcription hoàn tất!")
                            else:
                                st.error("❌ Lỗi khi transcribe!")
                    else:
                        st.error("❌ Không thể load model!")
            else:
                st.warning("⚠️ Vui lòng upload file audio trước!")
        
        # Hiển thị transcript
        if st.session_state.transcript_text:
            st.subheader("📝 Transcript")
            st.text_area(
                "Kết quả transcription:",
                st.session_state.transcript_text,
                height=400,
                key="transcript_display"
            )
            
            # Edit transcript
            st.subheader("✏️ Chỉnh sửa Transcript")
            edited_text = st.text_area(
                "Chỉnh sửa transcript:",
                st.session_state.transcript_text,
                height=300,
                key="transcript_edit"
            )
            
            if st.button("💾 Lưu thay đổi"):
                st.session_state.transcript_text = edited_text
                st.success("✅ Đã lưu thay đổi!")

# ========== GHI ÂM TRỰC TIẾP ==========
elif page == "🎙️ Ghi âm trực tiếp":
    st.header("🎙️ Ghi âm trực tiếp")
    
    st.info("💡 Tính năng này cho phép bạn upload file audio đã ghi âm sẵn để transcribe ngay lập tức.")
    st.warning("⚠️ Để ghi âm trực tiếp, vui lòng sử dụng ứng dụng ghi âm trên máy tính hoặc điện thoại, sau đó upload file tại đây.")
    
    # Audio upload cho recording
    audio_file = st.file_uploader(
        "Upload file audio đã ghi âm:",
        type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
        key="recording_upload"
    )
    
    if audio_file:
        st.success("✅ Đã tải file audio thành công!")
        
        # Play audio
        st.audio(audio_file, format='audio/wav')
        
        # Load audio từ file
        with st.spinner("Đang xử lý audio..."):
            audio_data, sr = load_audio(audio_file)
            
            if audio_data is not None:
                st.session_state.audio_data = audio_data
                st.session_state.audio_sr = sr
                st.session_state.audio_info = get_audio_info(audio_data, sr)
                
                # Hiển thị thông tin
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Độ dài", f"{st.session_state.audio_info['duration']:.2f} giây")
                with col2:
                    st.metric("Sample Rate", f"{sr} Hz")
        
        # Transcription
        model_size = st.selectbox(
            "Chọn model Whisper:",
            ["tiny", "base", "small", "medium"],
            index=1
        )
        
        if st.button("🚀 Transcribe", type="primary"):
            if st.session_state.audio_data is not None:
                with st.spinner("Đang transcribe..."):
                    model, device = load_whisper_model(model_size)
                    
                    if model is not None:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            sf.write(tmp_file.name, st.session_state.audio_data, st.session_state.audio_sr)
                            
                            result = transcribe_audio(
                                model,
                                tmp_file.name,
                                sr=st.session_state.audio_sr,
                                language="vi"
                            )
                            
                            os.unlink(tmp_file.name)
                            
                            if result:
                                st.session_state.transcript_result = result
                                st.session_state.transcript_text = format_transcript(result, with_timestamps=True)
                                st.success("✅ Transcription hoàn tất!")
                                
                                st.text_area(
                                    "Transcript:",
                                    st.session_state.transcript_text,
                                    height=300
                                )

# ========== THỐNG KÊ & EXPORT ==========
elif page == "📊 Thống kê & Export":
    st.header("📊 Thống kê & Export")
    
    if st.session_state.transcript_result and st.session_state.audio_info:
        # Statistics
        st.subheader("📈 Thống kê")
        
        stats = get_transcript_statistics(
            st.session_state.transcript_result,
            st.session_state.audio_info['duration']
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Số từ", f"{stats.get('word_count', 0):,}")
        with col2:
            st.metric("Số ký tự", f"{stats.get('character_count', 0):,}")
        with col3:
            st.metric("Độ dài", f"{stats.get('duration', 0):.2f} giây")
        with col4:
            st.metric("Từ/phút", f"{stats.get('words_per_minute', 0):.1f}")
        
        # Export options
        st.subheader("💾 Export Transcript")
        
        export_format = st.radio(
            "Chọn định dạng export:",
            ["TXT", "DOCX", "PDF"],
            horizontal=True
        )
        
        # Metadata
        metadata = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': stats.get('duration', 0),
            'word_count': stats.get('word_count', 0),
            'character_count': stats.get('character_count', 0)
        }
        
        if st.button(f"📥 Export {export_format}", type="primary"):
            if st.session_state.transcript_text:
                try:
                    if export_format == "TXT":
                        file_bytes, filename = export_txt(
                            st.session_state.transcript_text,
                            f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                        )
                        st.download_button(
                            label="⬇️ Tải xuống TXT",
                            data=file_bytes,
                            file_name=filename,
                            mime="text/plain"
                        )
                    
                    elif export_format == "DOCX":
                        file_bytes, filename = export_docx(
                            st.session_state.transcript_text,
                            metadata,
                            f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                        )
                        st.download_button(
                            label="⬇️ Tải xuống DOCX",
                            data=file_bytes,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    elif export_format == "PDF":
                        file_bytes, filename = export_pdf(
                            st.session_state.transcript_text,
                            metadata,
                            f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        )
                        st.download_button(
                            label="⬇️ Tải xuống PDF",
                            data=file_bytes,
                            file_name=filename,
                            mime="application/pdf"
                        )
                    
                    st.success("✅ File đã sẵn sàng để tải xuống!")
                except Exception as e:
                    st.error(f"❌ Lỗi khi export: {str(e)}")
            else:
                st.warning("⚠️ Không có transcript để export!")
    else:
        st.info("ℹ️ Vui lòng transcribe audio trước để xem thống kê và export.")

# ========== IMAGE ENCRYPTION PAGE ==========
elif page == "🖼️ Image Encryption":
    st.header("🖼️ Image Encryption (Password Protected)")

    st.write("Mã hóa / giải mã ảnh bằng password, chaotic logistic map và patch-level XOR.")

    import numpy as np
    from PIL import Image
    import hashlib
    import io

    # ===== KEY DERIVATION =====
    def derive_keys(password: str):
        h = hashlib.sha256(password.encode()).digest()
        seed = (int.from_bytes(h[:4], "big") % 1_000_000) / 1_000_000
        r = 3.8 + (h[4] / 255) * 0.19
        patch_size = [8, 16, 32][h[-1] % 3]
        xor_key = np.frombuffer(h, dtype=np.uint8)
        return seed, r, patch_size, xor_key

    # ===== CHAOTIC MAP =====
    def logistic_map(seed, r, size):
        x = seed
        arr = np.zeros(size)
        for i in range(size):
            x = r * x * (1 - x)
            arr[i] = x
        return arr

    # ===== PATCHIFY =====
    def patchify(img, patch):
        h, w, c = img.shape
        assert h % patch == 0 and w % patch == 0
        return (
            img.reshape(h//patch, patch, w//patch, patch, c)
               .swapaxes(1, 2)
               .reshape(-1, patch, patch, c)
        )

    def unpatchify(patches, img_shape, patch):
        h, w, c = img_shape
        H, W = h//patch, w//patch
        return (patches.reshape(H, W, patch, patch, c)
                      .swapaxes(1, 2)
                      .reshape(h, w, c))

    # ===== ENCRYPT =====
    def encrypt(img, password):
        seed, r, patch, xor_key = derive_keys(password)
        patches = patchify(img, patch)
        N = len(patches)

        chaos = logistic_map(seed, r, N)
        perm = np.argsort(chaos)
        chaos_vals = (chaos * 255).astype(np.uint8)

        enc = []
        for i in range(N):
            p = patches[i].astype(np.uint8)
            key = chaos_vals[i] ^ xor_key[i % len(xor_key)]
            enc.append(p ^ key)

        enc = np.stack(enc)[perm]
        return unpatchify(enc, img.shape, patch)

    # ===== DECRYPT =====
    def decrypt(img, password):
        seed, r, patch, xor_key = derive_keys(password)
        patches = patchify(img, patch)
        N = len(patches)

        chaos = logistic_map(seed, r, N)
        perm = np.argsort(chaos)
        inv_perm = np.argsort(perm)
        chaos_vals = (chaos * 255).astype(np.uint8)

        dec = np.zeros_like(patches)
        for i in range(N):
            p = patches[inv_perm[i]].astype(np.uint8)
            key = chaos_vals[i] ^ xor_key[i % len(xor_key)]
            dec[i] = p ^ key

        return unpatchify(dec, img.shape, patch)

    # ===== UI =====

    uploaded = st.file_uploader("Upload ảnh PNG/JPG", type=["png", "jpg", "jpeg"])
    password = st.text_input("Nhập mật khẩu", type="password")
    mode = st.selectbox("Chế độ:", ["Encrypt", "Decrypt"])

    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        img = img.resize((256, 256))
        arr = np.array(img)

        st.image(img, caption="Ảnh đầu vào", use_column_width=True)

        if st.button("▶️ Run Encryption/Decryption"):
            if not password:
                st.error("Vui lòng nhập mật khẩu!")
            else:
                if mode == "Encrypt":
                    out = encrypt(arr, password)
                else:
                    out = decrypt(arr, password)

                st.image(out, caption="Ảnh output", use_column_width=True)

                buffer = io.BytesIO()
                Image.fromarray(out).save(buffer, format="PNG")

                st.download_button(
                    "⬇ Tải ảnh",
                    buffer.getvalue(),
                    "output.png",
                    "image/png"
                )
# Footer
st.markdown("---")
st.caption("Vietnamese Speech to Text System | Made with Streamlit & Whisper")
