# Hệ Thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản

Vietnamese Speech to Text System for Automatic Meeting Transcription

## 📋 Mô tả

Hệ thống chuyển đổi giọng nói tiếng Việt thành văn bản tự động, được xây dựng bằng Streamlit với hỗ trợ cả OpenAI Whisper và PhoWhisper (VinAI Research). Hệ thống hỗ trợ xử lý audio từ các cuộc họp, phỏng vấn, thuyết trình và chuyển đổi thành văn bản có cấu trúc.

## ✨ Tính năng

### Tính năng cơ bản:
- ✅ **Upload Audio**: Hỗ trợ các định dạng WAV, MP3, FLAC, M4A, OGG
- ✅ **Visualization**: Hiển thị waveform và spectrogram
- ✅ **Audio Preprocessing**: Normalize và loại bỏ noise
- ✅ **Speech Recognition**: Hỗ trợ cả Whisper và PhoWhisper (tối ưu cho tiếng Việt) để transcribe
- ✅ **Timestamps**: Hiển thị thời gian cho từng đoạn transcript
- ✅ **Transcript Editing**: Cho phép chỉnh sửa transcript
- ✅ **Export**: Xuất ra TXT, DOCX, PDF
- ✅ **Statistics**: Thống kê số từ, ký tự, tốc độ nói

### Tính năng nâng cao:
- ✅ **Speaker Diarization**: Phân biệt người nói (đơn giản)
- ✅ **Long Audio Support**: Xử lý audio dài (meetings, interviews)
- ✅ **Multiple Model Sizes**: Tùy chọn model từ tiny đến large (Whisper) hoặc small/medium/base (PhoWhisper)
- ✅ **Model Selection**: Chọn giữa Whisper (đa ngôn ngữ) và PhoWhisper (tối ưu tiếng Việt)

## 🚀 Cài đặt

### Yêu cầu:
- Python 3.8+
- FFmpeg (tự động tải qua imageio-ffmpeg)

### FFmpeg Setup:

**Tự động (Khuyến nghị):**
Hệ thống tự động tải và sử dụng portable FFmpeg thông qua thư viện `imageio-ffmpeg`. 
Không cần cài đặt thủ công - hoạt động trên Streamlit Cloud và môi trường local.
FFmpeg được tự động cấu hình cho `pydub`, `moviepy`, và `whisper`.

**Pages (Workflow Order)**

Ứng dụng được tổ chức theo luồng công việc rõ ràng để hỗ trợ transcription project:

1. **Home / Dashboard**
2. **Audio Input & Preprocessing**
3. **Transcription**
4. **Speaker Diarization** (tùy chọn, bật bằng biến môi trường `DIARIZATION_ENABLED`)
5. **Post-processing / AI Enhancement** (noise reduction, punctuation, grammar enhancement)
6. **Export & Reporting**
7. **Settings / Advanced** (chỉ hiển thị cho IT / Technical users: AI specialists, Admins)

**Cài đặt thủ công (Tùy chọn):**
Nếu muốn sử dụng system FFmpeg thay vì portable version:

**Windows:**
```bash
choco install ffmpeg
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

### Cài đặt Python packages:

1. Tạo virtual environment (khuyến nghị):
```bash
python -m venv venv
```

2. Kích hoạt virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

**Lưu ý:** 
- Lần đầu tiên chạy, Whisper sẽ tự động tải model về. Model "base" có kích thước khoảng 150MB.
- PhoWhisper models sẽ được tải từ HuggingFace lần đầu sử dụng (có thể mất vài phút tùy vào kích thước model).

## 🚀 Deployment

### Quick Start - Local Development

**Cách nhanh nhất (khuyến nghị):**

```bash
# Linux/Mac
chmod +x scripts/run_local.sh
./scripts/run_local.sh

# Windows
scripts\run_local.bat
```

**Hoặc manual:**

```bash
# 1. Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc venv\Scripts\activate  # Windows

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy app
streamlit run app/main.py
```

### Streamlit Cloud Deployment

1. Push code lên GitHub
2. Truy cập [share.streamlit.io](https://share.streamlit.io)
3. Deploy với **Main file path**: `main.py`
4. Xem chi tiết trong [DEPLOYMENT.md](DEPLOYMENT.md)

### Docker Deployment

```bash
# Build image
docker build -t vietnamese-stt:latest .

# Chạy container
docker run -d -p 8501:8501 --name vietnamese-stt vietnamese-stt:latest

# Hoặc dùng docker-compose
docker-compose up -d
```

Xem hướng dẫn chi tiết trong [DEPLOYMENT.md](DEPLOYMENT.md) cho:
- Streamlit Cloud setup
- Docker deployment
- FastAPI server deployment
- Troubleshooting

## 📖 Hướng dẫn sử dụng

### Chạy ứng dụng:

```bash
streamlit run app/main.py
```

Ứng dụng sẽ mở tại `http://localhost:8501`

**Lưu ý:** Với cấu trúc mới, Streamlit sẽ tự động phát hiện các pages trong `app/pages/` và hiển thị trong sidebar navigation.

### Chạy API (FastAPI):

```bash
uvicorn core.api.server:app --host 0.0.0.0 --port 8000
```

- Health check: `GET /health`
- Upload audio: `POST /transcribe` (form-data: `file`, optional `diarization` bool)
- Trả về JSON: `{ "text": "...", "language": "vi", "segments": [...] }`

### Sử dụng:

1. **Upload & Transcribe:**
   - Chọn tab "📤 Upload & Transcribe"
   - Upload file audio (WAV, MP3, FLAC, etc.)
   - Xem waveform/spectrogram (tùy chọn)
   - Áp dụng preprocessing nếu cần
   - **Chọn loại model**: Whisper hoặc PhoWhisper (🌟 khuyến nghị cho tiếng Việt)
   - Chọn kích thước model:
     - Whisper: tiny/base/small/medium/large
     - PhoWhisper: small/medium/base
   - Bấm "🚀 Bắt đầu Transcription"
   - Xem và chỉnh sửa transcript
   - Export nếu cần

2. **Ghi âm trực tiếp:**
   - Chọn tab "🎙️ Ghi âm trực tiếp"
   - Upload file audio đã ghi âm sẵn
   - Transcribe ngay lập tức

3. **Thống kê & Export:**
   - Chọn tab "📊 Thống kê & Export"
   - Xem thống kê chi tiết
   - Export ra TXT, DOCX, hoặc PDF
4. **Streaming (demo):**
   - Trang `Streaming` dùng `audio_recorder_streamlit` (optional)
   - Nếu chưa cài: `pip install audio-recorder-streamlit`
5. **API Docs:**
   - Trang `API Docs` mô tả endpoint FastAPI và ví dụ `curl`

## 🏗️ Cấu trúc dự án

```
.
├── app/                         # UI: Streamlit app
│   ├── main.py                 # Home page / entry point
│   ├── components/             # UI components
│   │   ├── sidebar.py         # Shared sidebar với logo
│   │   └── layout.py          # Layout utilities
│   └── pages/                  # Streamlit pages
│       ├── 1_📤_Upload_Record.py
│       ├── 2_🎧_Preprocessing.py
│       ├── 3_📝_Transcription.py
│       ├── 4_👥_Speaker_Diarization.py
│       ├── 5_📊_Export_Statistics.py
│       └── 6_🔬_ASR_Benchmark.py
├── core/                       # AI/ML logic
│   ├── audio/
│   │   ├── audio_processor.py
│   │   └── ffmpeg_setup.py
│   ├── asr/
│   │   ├── transcription_service.py
│   │   ├── phowhisper_service.py
│   │   └── evaluate_models.py
│   └── diarization/
│       └── speaker_diarization.py
├── export/
│   └── export_utils.py
├── assets/                      # logo, mẫu audio
│   └── logo.webp
├── docs/
│   ├── de_bai.md
│   ├── model_comparison.md
│   └── architecture.md
├── scripts/                     # công cụ hỗ trợ
├── tests/                       # tests (sau này)
├── requirements.txt
├── README.md
└── QUICKSTART.md
```

## 🔧 Công nghệ sử dụng

- **Streamlit**: Framework web app
- **ASR Models**:
  - OpenAI Whisper (Transformer seq2seq)
  - PhoWhisper (Whisper fine-tune) 🌟 - Tối ưu cho tiếng Việt
- **Frameworks**:
  - HuggingFace Transformers (PhoWhisper)
  - OpenAI Whisper API
- **Audio Processing**: Librosa, PyDub, SoundFile
- **Visualization**: Matplotlib, Seaborn
- **Export**: python-docx, ReportLab
- **Scientific Computing**: NumPy, SciPy
- **Evaluation**: jiwer (WER/CER)

## 📝 Chọn mô hình

Hệ thống hỗ trợ **2 mô hình ASR** chính:

### 🌟 PhoWhisper (VinAI Research) - **Khuyến nghị cho tiếng Việt**

Mô hình được tinh chỉnh đặc biệt cho tiếng Việt, đạt hiệu suất tốt nhất:

- **Type**: Whisper fine-tune
- **Sizes**: small, medium, base
- **Khuyến nghị**: medium (cân bằng tốt)
- **Ưu điểm**: Tối ưu cho tiếng Việt, độ chính xác cao nhất
- **Vietnamese support**: ✅ Có

### Whisper (OpenAI)

Mô hình ASR đa ngôn ngữ, benchmark chuẩn:

- **Type**: Transformer seq2seq
- **Sizes**: tiny, base, small, medium, large
- **Khuyến nghị**: base (cân bằng tốt)
- **Ưu điểm**: Hỗ trợ đa ngôn ngữ, dễ sử dụng
- **Vietnamese support**: ✅ Có

**Khuyến nghị chung**: Sử dụng **PhoWhisper-medium** cho audio tiếng Việt để đạt độ chính xác tốt nhất.

## ⚠️ Lưu ý

1. **Thời gian xử lý**: Transcription có thể mất vài phút tùy vào độ dài audio và model size
2. **Bộ nhớ**: Model lớn cần nhiều RAM (Whisper-large cần ~10GB RAM, PhoWhisper-medium cần ~4-6GB RAM)
3. **GPU**: Hỗ trợ GPU để tăng tốc (tự động phát hiện). PhoWhisper có thể chạy nhanh hơn trên GPU
4. **Internet**: Lần đầu cần internet để tải model từ HuggingFace (PhoWhisper) hoặc OpenAI (Whisper)
5. **PyTorch**: Nếu muốn sử dụng GPU, đảm bảo đã cài đặt PyTorch với CUDA support

## 🐛 Xử lý lỗi

### Lỗi "No module named 'whisper'":
```bash
pip install openai-whisper
```

### Lỗi FFmpeg:
Hệ thống tự động tải portable FFmpeg qua `imageio-ffmpeg`. Nếu gặp lỗi:
- Kiểm tra kết nối internet (lần đầu cần tải FFmpeg)
- Đảm bảo `imageio-ffmpeg` đã được cài đặt: `pip install imageio-ffmpeg`
- Hoặc cài đặt FFmpeg thủ công và đảm bảo có trong PATH

### Lỗi "CUDA out of memory":
Sử dụng model nhỏ hơn (tiny hoặc base cho Whisper, small cho PhoWhisper) hoặc xử lý audio ngắn hơn.

### Lỗi khi tải PhoWhisper từ HuggingFace:
- Kiểm tra kết nối internet
- Đảm bảo đã cài đặt `transformers` và `accelerate`
- Thử lại sau vài phút (có thể do HuggingFace server tạm thời quá tải)

## 📊 Đánh giá chất lượng mô hình

Để so sánh chất lượng giữa Whisper và PhoWhisper, sử dụng script đánh giá:

```bash
python evaluate_models.py --test_dir test_audio --whisper_model large --phowhisper_model medium
```

Script sẽ:
- Transcribe tất cả audio files trong thư mục `test_audio/`
- Tính WER (Word Error Rate) và CER (Character Error Rate)
- Tạo báo cáo chi tiết tại `docs/model_comparison.md`

**Yêu cầu**: Mỗi audio file cần có file `.txt` tương ứng chứa reference text (ground truth).

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

## 👥 Tác giả

Developed for Vietnamese Speech to Text System Project

## 🙏 Acknowledgments

- OpenAI Whisper team
- VinAI Research (PhoWhisper)
- Streamlit team
- Librosa developers
- HuggingFace team
- Cộng đồng open source

