# Hướng dẫn Deploy lên Streamlit Cloud

## 📋 Yêu cầu

1. Tài khoản GitHub
2. Tài khoản Streamlit Cloud (miễn phí tại https://streamlit.io/cloud)
3. Repository GitHub chứa code

## 🚀 Các bước deploy

### 1. Push code lên GitHub

```bash
git init
git add .
git commit -m "Initial commit: Vietnamese Speech to Text System"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Deploy lên Streamlit Cloud

1. Đăng nhập vào https://share.streamlit.io/
2. Click "New app"
3. Chọn repository và branch
4. Đặt tên app (ví dụ: `vietnamese-speech-to-text`)
5. **Quan trọng**: Đảm bảo file `main.py` là file chính
6. Click "Deploy"

### 3. Cấu hình (Tự động)

Streamlit Cloud sẽ tự động:
- ✅ Cài đặt tất cả packages từ `requirements.txt`
- ✅ Tải static FFmpeg từ GitHub (qua `static-ffmpeg`)
- ✅ Tải Whisper models khi cần

## ⚙️ Static FFmpeg

Hệ thống tự động sử dụng **static FFmpeg** từ GitHub thông qua thư viện `static-ffmpeg`:
- Không cần cài đặt FFmpeg thủ công
- Hoạt động trên Streamlit Cloud
- Tự động tải binary phù hợp với hệ điều hành

## 📝 Lưu ý

1. **Lần đầu deploy**: Có thể mất 5-10 phút để:
   - Cài đặt packages
   - Tải static FFmpeg
   - Tải Whisper model (khi user sử dụng lần đầu)

2. **Memory limits**: Streamlit Cloud free tier có giới hạn memory
   - Khuyến nghị dùng model "tiny" hoặc "base"
   - Model "large" có thể vượt quá giới hạn

3. **Timeout**: 
   - Streamlit Cloud có timeout cho mỗi request
   - Audio dài có thể cần xử lý theo chunks

4. **File size**: 
   - Giới hạn upload file trên Streamlit Cloud
   - Khuyến nghị: < 100MB

## 🔧 Troubleshooting

### Lỗi "FFmpeg not found":
- Đảm bảo `static-ffmpeg>=2.1.0` có trong `requirements.txt`
- Kiểm tra logs trên Streamlit Cloud

### Lỗi "Out of memory":
- Sử dụng model nhỏ hơn (tiny/base)
- Xử lý audio ngắn hơn

### Lỗi "Timeout":
- Audio quá dài
- Thử chia nhỏ audio hoặc sử dụng model nhỏ hơn

## 📚 Tài liệu tham khảo

- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- static-ffmpeg: https://github.com/joshbernard/static-ffmpeg
- OpenAI Whisper: https://github.com/openai/whisper

