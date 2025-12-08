# Hệ Thống Chuyển Giọng Nói Tiếng Việt Sang Văn Bản

Vietnamese Speech to Text System for Automatic Meeting Transcription

## 📋 Mô tả

Hệ thống chuyển đổi giọng nói tiếng Việt thành văn bản tự động, được xây dựng bằng Streamlit và OpenAI Whisper. Hệ thống hỗ trợ xử lý audio từ các cuộc họp, phỏng vấn, thuyết trình và chuyển đổi thành văn bản có cấu trúc.

## ✨ Tính năng

### Tính năng cơ bản:
- ✅ **Upload Audio**: Hỗ trợ các định dạng WAV, MP3, FLAC, M4A, OGG
- ✅ **Visualization**: Hiển thị waveform và spectrogram
- ✅ **Audio Preprocessing**: Normalize và loại bỏ noise
- ✅ **Speech Recognition**: Sử dụng Whisper model để transcribe tiếng Việt
- ✅ **Timestamps**: Hiển thị thời gian cho từng đoạn transcript
- ✅ **Transcript Editing**: Cho phép chỉnh sửa transcript
- ✅ **Export**: Xuất ra TXT, DOCX, PDF
- ✅ **Statistics**: Thống kê số từ, ký tự, tốc độ nói

### Tính năng nâng cao:
- ✅ **Speaker Diarization**: Phân biệt người nói (đơn giản)
- ✅ **Long Audio Support**: Xử lý audio dài (meetings, interviews)
- ✅ **Multiple Model Sizes**: Tùy chọn model từ tiny đến large

## 🚀 Cài đặt

### Yêu cầu:
- Python 3.8+
- FFmpeg (tự động tải qua static-ffmpeg)

### FFmpeg Setup:

**Tự động (Khuyến nghị):**
Hệ thống tự động tải và sử dụng static FFmpeg từ GitHub thông qua thư viện `static-ffmpeg`. 
Không cần cài đặt thủ công - hoạt động trên Streamlit Cloud và môi trường local.

**Cài đặt thủ công (Tùy chọn):**
Nếu muốn sử dụng system FFmpeg thay vì static version:

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

**Lưu ý:** Lần đầu tiên chạy, Whisper sẽ tự động tải model về. Model "base" có kích thước khoảng 150MB.

## 📖 Hướng dẫn sử dụng

### Chạy ứng dụng:

```bash
streamlit run main.py
```

Ứng dụng sẽ mở tại `http://localhost:8501`

### Sử dụng:

1. **Upload & Transcribe:**
   - Chọn tab "📤 Upload & Transcribe"
   - Upload file audio (WAV, MP3, FLAC, etc.)
   - Xem waveform/spectrogram (tùy chọn)
   - Áp dụng preprocessing nếu cần
   - Chọn model Whisper (tiny/base/small/medium/large)
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

## 🏗️ Cấu trúc dự án

```
.
├── main.py                      # Ứng dụng Streamlit chính
├── audio_processor.py           # Module xử lý audio
├── transcription_service.py     # Module transcription với Whisper
├── export_utils.py              # Module export (TXT, DOCX, PDF)
├── speaker_diarization.py       # Module phân biệt người nói
├── requirements.txt             # Dependencies
└── README.md                    # File này
```

## 🔧 Công nghệ sử dụng

- **Streamlit**: Framework web app
- **OpenAI Whisper**: Speech recognition model
- **Librosa**: Audio processing và analysis
- **PyDub**: Audio format conversion
- **SoundFile**: Audio I/O
- **Matplotlib/Seaborn**: Visualization
- **python-docx**: Export DOCX
- **ReportLab**: Export PDF
- **NumPy/SciPy**: Scientific computing

## 📝 Model Whisper

Whisper có nhiều kích thước model:

- **tiny**: ~39M parameters, nhanh nhất, độ chính xác thấp
- **base**: ~74M parameters, cân bằng tốt (khuyến nghị)
- **small**: ~244M parameters, chính xác hơn
- **medium**: ~769M parameters, rất chính xác
- **large**: ~1550M parameters, chính xác nhất, chậm nhất

Khuyến nghị sử dụng **base** hoặc **small** cho tiếng Việt.

## ⚠️ Lưu ý

1. **Thời gian xử lý**: Transcription có thể mất vài phút tùy vào độ dài audio và model size
2. **Bộ nhớ**: Model lớn cần nhiều RAM (large model cần ~10GB RAM)
3. **GPU**: Hỗ trợ GPU để tăng tốc (tự động phát hiện)
4. **Internet**: Lần đầu cần internet để tải model

## 🐛 Xử lý lỗi

### Lỗi "No module named 'whisper'":
```bash
pip install openai-whisper
```

### Lỗi FFmpeg:
Hệ thống tự động tải static FFmpeg. Nếu gặp lỗi:
- Kiểm tra kết nối internet (lần đầu cần tải FFmpeg)
- Hoặc cài đặt FFmpeg thủ công và đảm bảo có trong PATH

### Lỗi "CUDA out of memory":
Sử dụng model nhỏ hơn (tiny hoặc base) hoặc xử lý audio ngắn hơn.

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

## 👥 Tác giả

Developed for Vietnamese Speech to Text System Project

## 🙏 Acknowledgments

- OpenAI Whisper team
- Streamlit team
- Librosa developers
- Cộng đồng open source

