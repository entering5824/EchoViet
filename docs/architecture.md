# Kiến trúc hệ thống

## Tổng quan

Hệ thống Vietnamese Speech to Text được xây dựng với kiến trúc modular, tách biệt rõ ràng giữa UI, business logic, và các services.

## Cấu trúc modules

### 1. App Layer (`app/`)

**Chức năng:** Giao diện người dùng với Streamlit

- **`main.py`**: Home page, entry point của ứng dụng
- **`components/`**: Shared UI components
  - `sidebar.py`: Sidebar với logo cho tất cả pages
  - `layout.py`: CSS styles và layout utilities
- **`pages/`**: Các trang chức năng riêng biệt
  - Upload & Record: Upload và quản lý audio files
  - Preprocessing: Tiền xử lý và visualization
  - Transcription: Chọn model và transcribe (hỗ trợ 7 models)
  - Speaker Diarization: Phân biệt người nói
  - Export & Statistics: Thống kê và export
  - ASR Benchmark: So sánh chất lượng mô hình

**Đặc điểm:**
- Streamlit pages tự động được phát hiện và hiển thị trong sidebar
- Session state được share giữa tất cả pages
- Shared sidebar component với logo hiển thị trên mọi page
- Mỗi page độc lập, dễ bảo trì và mở rộng

### 2. Core Layer (`core/`)

**Chức năng:** Business logic và AI/ML services

#### 2.1 Audio Processing (`core/audio/`)

- **`audio_processor.py`**: 
  - Load audio từ nhiều định dạng
  - Preprocessing (normalize, noise reduction)
  - Visualization (waveform, spectrogram)
  - Audio info extraction

- **`ffmpeg_setup.py`**:
  - Tự động setup portable FFmpeg từ `imageio-ffmpeg`
  - Cấu hình environment variables cho `pydub`, `moviepy`, và `whisper`
  - Hỗ trợ Streamlit Cloud và local environment

#### 2.2 ASR Services (`core/asr/`)

- **`model_registry.py`**: 
  - Registry quản lý tất cả ASR models
  - Metadata và dependencies cho mỗi model
  - Helper functions để check availability

- **`transcription_service.py`**:
  - Load và quản lý Whisper models
  - Transcribe audio với Whisper
  - Format transcript với timestamps
  - Tính toán statistics

- **`phowhisper_service.py`**:
  - Load PhoWhisper models từ HuggingFace
  - Transcribe audio với PhoWhisper
  - Format kết quả tương thích với Whisper

- **`wav2vec2_service.py`**:
  - Load Wav2Vec 2.0 models từ HuggingFace
  - Self-supervised learning model
  - CTC decoding

- **`deepspeech2_service.py`**:
  - Load DeepSpeech 2 models
  - CTC-based transcription
  - Yêu cầu model file (.pbmm)

- **`quartznet_service.py`**:
  - Load QuartzNet models từ NeMo
  - CNN-based architecture
  - Sử dụng NVIDIA NeMo framework

- **`wav2letter_service.py`**:
  - Placeholder cho Wav2Letter++
  - Cần build từ source hoặc Docker

- **`kaldi_service.py`**:
  - Placeholder cho Kaldi toolkit
  - Cần cài đặt Kaldi thủ công

- **`evaluate_models.py`**:
  - Script đánh giá chất lượng mô hình
  - Tính WER và CER
  - Tạo báo cáo so sánh

#### 2.3 Diarization (`core/diarization/`)

- **`speaker_diarization.py`**:
  - Simple speaker segmentation dựa trên energy
  - Format transcript với speaker labels
  - Xử lý fallback khi không có segments

### 3. Export Layer (`export/`)

- **`export_utils.py`**:
  - Export transcript ra TXT, DOCX, PDF
  - Format metadata
  - Generate download files

## Luồng dữ liệu

```
User Input (Audio File)
    ↓
app/pages/1_Upload_Record.py
    ↓
core/audio/audio_processor.py (load_audio)
    ↓
st.session_state.audio_data
    ↓
app/pages/2_Preprocessing.py (optional)
    ↓
core/audio/audio_processor.py (preprocess_audio)
    ↓
app/pages/3_Transcription.py
    ↓
core/asr/transcription_service.py hoặc phowhisper_service.py
    ↓
st.session_state.transcript_result
    ↓
app/pages/4_Speaker_Diarization.py (optional)
    ↓
core/diarization/speaker_diarization.py
    ↓
app/pages/5_Export_Statistics.py
    ↓
export/export_utils.py
    ↓
Download File
```

## Session State Management

Streamlit pages share session state, cho phép:
- Audio data được load một lần, sử dụng ở nhiều pages
- Transcript được tạo ở page Transcription, hiển thị ở các pages khác
- State được persist giữa các page navigation

**Key session state variables:**
- `audio_data`: Numpy array chứa audio samples
- `audio_sr`: Sample rate
- `audio_info`: Dict chứa thông tin audio (duration, channels, etc.)
- `transcript_result`: Dict kết quả từ ASR model
- `transcript_text`: String transcript đã format

## Model Management

### Whisper
- Load từ OpenAI repository
- Cache với `@st.cache_resource`
- Support multiple sizes: tiny, base, small, medium, large

### PhoWhisper
- Load từ HuggingFace (`vinai/PhoWhisper-{size}`)
- Cache với `@st.cache_resource`
- Support sizes: small, medium, base
- Auto-detect GPU/CPU

## Dependencies

### Core Dependencies
- `streamlit`: Web framework
- `torch`, `torchaudio`: PyTorch for models
- `transformers`: HuggingFace library (PhoWhisper, Wav2Vec 2.0)
- `librosa`: Audio processing
- `soundfile`: Audio I/O
- `pydub`: Audio format conversion

### Model-Specific Dependencies (Optional)
- `openai-whisper`: Whisper models
- `datasets`: For Wav2Vec 2.0
- `deepspeech`: DeepSpeech 2 (optional)
- `nemo-toolkit[asr]`: QuartzNet/NeMo (optional)

### Export Dependencies
- `python-docx`: DOCX export
- `reportlab`: PDF export

### Evaluation Dependencies
- `jiwer`: WER/CER calculation
- `pandas`: Data processing

**Lưu ý:** Một số models (Kaldi, Wav2Letter++) cần cài đặt thủ công hoặc Docker.

## Extension Points

### Thêm ASR Model mới
1. Tạo file mới trong `core/asr/` (e.g., `new_model_service.py`)
2. Implement `load_model()` và `transcribe()` functions
3. Format output tương thích với Whisper format: `{"text": str, "segments": List[Dict]}`
4. Thêm model vào `core/asr/model_registry.py` với metadata
5. Import và sử dụng trong `app/pages/3_Transcription.py`
6. Model sẽ tự động xuất hiện trong UI nhờ model registry

### Thêm Export Format mới
1. Thêm function mới trong `export/export_utils.py`
2. Thêm option trong `app/pages/5_Export_Statistics.py`

### Thêm Page mới
1. Tạo file trong `app/pages/` với format `N_Name.py`
2. Streamlit tự động phát hiện và thêm vào navigation

## Best Practices

1. **Imports**: Sử dụng relative imports trong core modules, absolute imports trong app
2. **Error Handling**: Luôn có try-except và hiển thị error messages rõ ràng
3. **Session State**: Kiểm tra state trước khi sử dụng
4. **File Paths**: Sử dụng `os.path.join()` để cross-platform compatibility
5. **Temporary Files**: Luôn clean up temp files sau khi sử dụng

