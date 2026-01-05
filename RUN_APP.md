# Hướng dẫn chạy App

## Cách 1: Chạy từ root directory (Khuyến nghị)

```bash
streamlit run main.py
```

## Cách 2: Chạy từ app directory

```bash
cd app
streamlit run main.py
```

## Cách 3: Chạy trực tiếp app/main.py

```bash
streamlit run app/main.py
```

## Lưu ý:

1. Đảm bảo đã cài đặt tất cả dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. App sẽ tự động:
   - Setup FFmpeg
   - Load logo từ `assets/logo.webp`
   - Initialize session state
   - Hiển thị Home page với logo và footer

3. Nếu gặp lỗi, kiểm tra:
   - Python version (khuyến nghị 3.9-3.10)
   - Đã cài đặt Streamlit: `pip install streamlit`
   - Đã cài đặt Whisper: `pip install openai-whisper`

## Troubleshooting:

- **App không hiển thị**: Đảm bảo chạy từ đúng directory và file `app/main.py` tồn tại
- **Lỗi import**: Kiểm tra `sys.path` đã được set đúng chưa
- **Lỗi logo**: Kiểm tra file `assets/logo.webp` có tồn tại không
