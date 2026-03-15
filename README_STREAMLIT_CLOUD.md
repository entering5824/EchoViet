# Deploy EchoViet lên Streamlit Cloud

1. Đẩy repo lên GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → New app.
3. **Main file path**: `app/main.py`
4. **Root directory**: (trống nếu repo root là EchoViet)
5. **Python**: 3.10 (runtime.txt đã cấu hình).

Chạy local: `streamlit run app/main.py` (từ thư mục EchoViet). Cần FFmpeg (packages.yaml dùng cho Cloud).
