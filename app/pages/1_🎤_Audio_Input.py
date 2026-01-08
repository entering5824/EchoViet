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
render_page_header("Audio Input & Preparation", "Upload or record audio, check and prepare for ASR pipeline", "🎤")

# ================== INPUT ==================
tab_upload, tab_record = st.tabs(["📤 Upload", "🎙️ Record"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "Audio file (wav, mp3, flac, m4a, ogg)",
        type=["wav", "mp3", "flac", "m4a", "ogg"],
        help="Upload audio file to get started. Supported formats: WAV, MP3, FLAC, M4A, OGG"
    )

    if uploaded_file:
        # Validation: Check file size (max 200MB)
        max_size_mb = 200
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            st.error(f"❌ File too large ({file_size_mb:.1f}MB). Maximum size: {max_size_mb}MB")
            st.info("💡 **Suggestion**: Compress the file or split the audio file")
        else:
            with st.spinner("⏳ Loading audio..."):
                try:
                    audio_data, sr = load_audio(uploaded_file)
                    
                    if audio_data is None:
                        st.error("❌ Cannot load audio. Please check if the file is valid.")
                        st.info("💡 **Suggestion**: \n- Ensure the file is not corrupted\n- Try converting to WAV format\n- Check if the file is actually audio")
                    else:
                        # Additional validation: Check duration
                        duration = len(audio_data) / sr
                        if duration < 0.1:
                            st.warning("⚠️ Audio file too short (< 0.1 seconds). May not be a valid audio file.")
                        elif duration > 3600:  # 1 hour
                            st.warning(f"⚠️ Audio file very long ({duration/60:.1f} minutes). Processing may take a long time.")
                        
                        st.session_state.audio_data = audio_data
                        st.session_state.audio_sr = sr
                        st.session_state.audio_info = get_audio_info(audio_data, sr)
                        st.session_state.audio_ready = False
                        st.session_state.audio_source = uploaded_file
                        st.success(f"✅ Audio loaded successfully! ({file_size_mb:.1f}MB, {duration:.1f}s)")
                        
                except Exception as e:
                    st.error(f"❌ Error loading audio: {str(e)}")
                    st.info("💡 **Suggestion**: \n- Check if the file is corrupted\n- Try a different audio file\n- Ensure the format is supported")

with tab_record:
    st.info("🎙️ Record directly from browser. Press the button to start/stop recording.")
    
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
                with st.spinner("⏳ Processing recorded audio..."):
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
                                    st.warning("⚠️ Audio too short (< 0.1 seconds). Please record again.")
                                else:
                                    # Save to session state
                                    st.session_state.audio_data = audio_data
                                    st.session_state.audio_sr = sr
                                    st.session_state.audio_info = get_audio_info(audio_data, sr)
                                    st.session_state.audio_ready = False
                                    st.session_state.audio_source = audio_bytes
                                    
                                    st.success(f"✅ Recording successful! ({duration:.1f}s)")
                                    
                                    # Show audio player
                                    st.audio(audio_bytes, format="audio/wav")
                            else:
                                st.error("❌ Cannot load recorded audio. Please try again.")
                        finally:
                            # Clean up temp file
                            try:
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                            except Exception:
                                pass
                    except Exception as e:
                        st.error(f"❌ Error processing recorded audio: {str(e)}")
                        st.info("💡 **Suggestion**: \n- Ensure microphone is working\n- Check microphone access permissions\n- Try recording again")
                        with st.expander("🔍 Chi tiết lỗi"):
                            st.exception(e)
        
        # Show previously recorded audio if available
        elif st.session_state.recorded_audio_bytes is not None:
            st.info("📼 Previously recorded audio:")
            st.audio(st.session_state.recorded_audio_bytes, format="audio/wav")
            
            # Option to clear recorded audio
            if st.button("🗑️ Clear Recorded Audio", key="clear_recorded_audio"):
                st.session_state.recorded_audio_bytes = None
                st.session_state.audio_data = None
                st.session_state.audio_sr = None
                st.session_state.audio_info = None
                st.session_state.audio_source = None
                st.success("✅ Recorded audio cleared")
                st.rerun()
        
        # Show current audio status if loaded
        if st.session_state.audio_data is not None and st.session_state.recorded_audio_bytes is not None:
            duration = st.session_state.audio_info.get('duration', 0) if st.session_state.audio_info else 0
            st.info(f"✅ Audio ready ({duration:.1f}s). You can continue with preprocessing or transcription.")
            
    except ImportError:
        st.warning("⚠️ `audio-recorder-streamlit` not installed. Install with: `pip install audio-recorder-streamlit`")
        st.info("💡 After installation, refresh the page to use the recording feature.")
    except Exception as e:
        st.error(f"❌ Error initializing audio recorder: {str(e)}")
        st.info("💡 **Suggestion**: \n- Check microphone access permissions\n- Ensure browser supports Web Audio API\n- Try a different browser (Chrome, Edge)")

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
    st.subheader("🔧 Audio Preprocessing")
    
    # Default to recommended mode
    if st.session_state.preprocess_mode not in ["simple", "recommended", "advanced"]:
        st.session_state.preprocess_mode = "recommended"
    
    # Simplified mode selection - default to recommended, hide advanced by default
    use_advanced = st.checkbox(
        "⚙️ Show advanced options",
        value=False,
        help="Enable to view and customize detailed technical parameters"
    )
    
    if use_advanced:
        # Show mode selection only if advanced is enabled
        mode_options = {
            "simple": "🎯 Simple - Automatic processing with default settings",
            "recommended": "⭐ Recommended - Optimized settings (Recommended)",
            "advanced": "⚙️ Advanced - Detailed customization"
        }
        
        selected_mode = st.radio(
            "Select processing mode:",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            index=list(mode_options.keys()).index(st.session_state.preprocess_mode),
            help="'Recommended' mode is the best choice for most cases"
        )
        st.session_state.preprocess_mode = selected_mode
    else:
        # Default to recommended mode
        st.session_state.preprocess_mode = "recommended"
        st.info("💡 **Recommended Mode**: Uses optimal settings for quality and speed. Enable 'Advanced options' to customize.")
    
    # Configuration based on preset mode
    st.markdown("### ⚙️ Settings")
    
    if st.session_state.preprocess_mode == "simple":
        # Simple mode: Show minimal, user-friendly options
        st.markdown("""
        **Simple Mode** will automatically:
        - ✅ Normalize volume for clearer sound
        - ✅ Keep sample rate at 16kHz (optimal for speech recognition)
        - ❌ No silence trimming (preserve original duration)
        - ❌ No noise filtering (preserve original quality)
        """)
        
        # Use saved values
        normalize = True
        trim_silence = False
        remove_noise = False
        target_sr = 16000
        
    elif st.session_state.preprocess_mode == "recommended":
        # Recommended mode: Show recommended settings with explanations
        st.markdown("""
        **Recommended Mode** uses optimized settings:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            normalize = st.checkbox(
                "✅ Normalize volume",
                value=st.session_state.preprocess_normalize,
                help="Adjust volume to standard level to improve recognition quality. Should be enabled in most cases."
            )
            st.session_state.preprocess_normalize = normalize
            
            trim_silence = st.checkbox(
                "✂️ Trim silence at start/end",
                value=st.session_state.preprocess_trim_silence,
                help="Automatically remove silence at the beginning and end of file. Disable if you want to preserve original duration."
            )
            st.session_state.preprocess_trim_silence = trim_silence
        
        with col2:
            target_sr = st.selectbox(
                "🎵 Sample Rate",
                [16000, 22050, 44100],
                index=[16000, 22050, 44100].index(st.session_state.preprocess_target_sr),
                help="16kHz is optimal for speech recognition. Only change if there are special requirements."
            )
            st.session_state.preprocess_target_sr = target_sr
            
            remove_noise = st.checkbox(
                "🔇 Reduce low-frequency noise",
                value=st.session_state.preprocess_remove_noise,
                help="Filter out low-frequency noise (such as wind, vibration). Only enable when audio has significant noise."
            )
            st.session_state.preprocess_remove_noise = remove_noise
    
    else:  # advanced mode
        # Advanced mode: Show all options with technical details
        st.markdown("""
        **Advanced Mode** allows detailed customization of all technical parameters.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            normalize = st.checkbox(
                "Normalize Amplitude",
                value=st.session_state.preprocess_normalize,
                help="Peak normalization: y = y / max(|y|). Brings signal to maximum amplitude ±1.0"
            )
            st.session_state.preprocess_normalize = normalize
            
            trim_silence = st.checkbox(
                "Trim Silence",
                value=st.session_state.preprocess_trim_silence,
                help="Uses librosa.effects.trim() to remove silence at start and end of audio based on energy threshold"
            )
            st.session_state.preprocess_trim_silence = trim_silence
        
        with col2:
            target_sr = st.selectbox(
                "Target Sample Rate (Hz)",
                [8000, 16000, 22050, 44100],
                index=[8000, 16000, 22050, 44100].index(st.session_state.preprocess_target_sr) if st.session_state.preprocess_target_sr in [8000, 16000, 22050, 44100] else 1,
                help="Target sample rate. 16kHz is standard for ASR. Resample uses librosa.resample()"
            )
            st.session_state.preprocess_target_sr = target_sr
            
            remove_noise = st.checkbox(
                "High-pass Filter (Low-frequency noise removal)",
                value=st.session_state.preprocess_remove_noise,
                help="Apply Butterworth high-pass filter to remove noise below cutoff frequency"
            )
            st.session_state.preprocess_remove_noise = remove_noise
        
        # Advanced noise reduction settings
        if remove_noise:
            with st.expander("🔧 Detailed Settings - Noise Filtering"):
                noise_cutoff = st.slider(
                    "Cutoff Frequency (Hz)",
                    min_value=40,
                    max_value=200,
                    value=st.session_state.preprocess_noise_cutoff,
                    step=10,
                    help="Frequencies below this will be filtered out. 80Hz is a reasonable default for most cases."
                )
                st.session_state.preprocess_noise_cutoff = noise_cutoff
                st.caption("⚠️ Note: Filtering too aggressively may reduce voice quality. Only adjust when necessary.")
    
    # Preview before processing
    st.markdown("---")
    st.markdown("### 👁️ Preview")
    
    preview_col1, preview_col2 = st.columns(2)
    with preview_col1:
        st.markdown("**Before processing:**")
        if isinstance(st.session_state.audio_source, bytes):
            st.audio(st.session_state.audio_source, format="audio/wav")
        else:
            st.audio(st.session_state.audio_source)
    
    with preview_col2:
        st.markdown("**After processing:**")
        st.info("Processed audio will be displayed here after you click 'Apply'")
    
    # Apply preprocessing button
    st.divider()
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        if st.button("🚀 Apply Preprocessing", type="primary", use_container_width=True):
            with st.spinner("⏳ Processing audio..."):
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
                    
                    st.success("✅ Preprocessing complete! Audio is ready for speech recognition step.")
                    
                    # Show what was applied
                    applied_settings = []
                    if normalize:
                        applied_settings.append("✅ Normalize volume")
                    if trim_silence:
                        applied_settings.append("✅ Trim silence")
                    if remove_noise:
                        cutoff_value = st.session_state.preprocess_noise_cutoff if st.session_state.preprocess_mode == 'advanced' else 80
                        applied_settings.append(f"✅ Noise filtering ({cutoff_value}Hz)")
                    if was_resampled:
                        applied_settings.append(f"✅ Resample {original_sr}Hz → {target_sr}Hz")
                    
                    if applied_settings:
                        st.info("**Applied:** " + " | ".join(applied_settings))
                    
                    # Show preview of processed audio
                    st.audio(audio, sample_rate=st.session_state.audio_sr)
                    
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Error processing audio: {error_msg}")
                    
                    # Provide helpful suggestions
                    if "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                        st.info("💡 **Suggestion**: Audio file too large. Try:\n- Split the audio file\n- Use 'Simple' mode\n- Reduce sample rate")
                    elif "format" in error_msg.lower() or "codec" in error_msg.lower():
                        st.info("💡 **Suggestion**: File format not supported. Try:\n- Convert to WAV or MP3\n- Check if file is corrupted")
                    else:
                        with st.expander("🔍 Error details"):
                            st.exception(e)

    # ================== NEXT STEP ==================
    st.divider()
    st.info("🎯 Audio is ready for Transcription & Speaker Diarization step")

    if st.button("➡️ Go to Transcription", type="primary", use_container_width=True):
        st.switch_page("pages/2_📝_Transcription.py")

else:
    st.info("👆 Upload or record audio to get started")

# ===== Footer =====
render_footer()
