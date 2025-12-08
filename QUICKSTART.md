# Hướng dẫn nhanh

## Cài đặt nhanh

1. **Cài FFmpeg** (nếu chưa có):
   - Windows: `choco install ffmpeg` hoặc tải từ https://ffmpeg.org
   - Linux: `sudo apt-get install ffmpeg`
   - Mac: `brew install ffmpeg`

2. **Cài đặt Python packages**:
```bash
pip install -r requirements.txt
```

3. **Chạy ứng dụng**:
```bash
streamlit run main.py
```

## Sử dụng

1. Mở trình duyệt tại `http://localhost:8501`
2. Chọn tab "📤 Upload & Transcribe"
3. Upload file audio (WAV, MP3, FLAC)
4. Chọn model Whisper (khuyến nghị: base)
5. Bấm "🚀 Bắt đầu Transcription"
6. Xem kết quả và export nếu cần

## Lưu ý

- Lần đầu chạy sẽ mất thời gian để tải Whisper model
- Model "base" cân bằng tốt giữa tốc độ và độ chính xác
- Audio dài sẽ mất nhiều thời gian để xử lý

