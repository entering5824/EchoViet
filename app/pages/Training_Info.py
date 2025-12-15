"""
Training Info Page - Thông tin mô hình Speech-to-Text
"""
import streamlit as st
import os
import sys
import pickle
import torch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.asr.model_registry import get_all_models, get_model_info
from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css
from app.components.footer import render_footer

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

st.header("📚 Training Info – Thông tin mô hình Speech-to-Text")

st.markdown("""
<div class="card">
<p style="font-size: 16px; line-height: 1.7;">
Trang này trình bày <strong>quy trình xử lý – mô hình – kết quả – so sánh</strong>
của hệ thống Vietnamese Speech-to-Text.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================
# Helper function to load model info from .pkl files
# ==========================
def load_model_info_from_pkl():
    """Đọc thông tin model từ .pkl files trong models/ folder"""
    models_info = []
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
    
    if not os.path.exists(model_dir):
        return models_info
    
    for fname in os.listdir(model_dir):
        if not fname.endswith(".pkl"):
            continue
        
        fpath = os.path.join(model_dir, fname)
        
        try:
            with open(fpath, "rb") as f:
                model = pickle.load(f)
            
            # Count parameters
            if hasattr(model, 'parameters'):
                param_count = sum(p.numel() for p in model.parameters())
                trainable_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
            else:
                param_count = 0
                trainable_count = 0
            
            models_info.append({
                "name": fname.replace(".pkl", ""),
                "file": fname,
                "size_mb": round(os.path.getsize(fpath) / (1024 * 1024), 2),
                "total_params": param_count,
                "trainable_params": trainable_count,
                "device": "CPU"
            })
        
        except Exception as e:
            models_info.append({
                "name": fname.replace(".pkl", ""),
                "file": fname,
                "error": str(e)
            })
    
    return models_info

# ==========================================================
# 1️⃣ DỮ LIỆU THÔ
# ==========================================================
st.markdown("### 1. Dữ liệu thô (Raw Audio Data)")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li>Dữ liệu đầu vào là các file audio cuộc họp, thảo luận, phỏng vấn.</li>
    <li>Định dạng phổ biến: <strong>MP3, WAV, FLAC, M4A, OGG</strong>.</li>
    <li>Audio có thể có nhiễu nền, nhiều người nói.</li>
    <li>Độ dài audio có thể từ vài giây đến hàng giờ.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# 2️⃣ TIỀN XỬ LÝ
# ==========================================================
st.markdown("### 2. Tiền xử lý dữ liệu")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li>Chuẩn hóa audio về <strong>WAV – PCM16 – mono – 16kHz</strong>.</li>
    <li>Chia audio dài thành các đoạn nhỏ (chunking: 15/30/45/60 giây).</li>
    <li>Normalize amplitude để tránh clipping.</li>
    <li>Loại bỏ noise (high-pass filter) nếu cần.</li>
    <li>Visualization: Waveform và Spectrogram để kiểm tra chất lượng audio.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# 3️⃣ KIẾN TRÚC MÔ HÌNH
# ==========================================================
st.markdown("### 3. Kiến trúc mô hình")

st.markdown("""
<div class="card">
<h4 style="color: #1f4e79; margin-top: 0;">Hệ thống hỗ trợ 2 mô hình ASR chính:</h4>
<ul style="font-size: 16px; line-height: 1.8;">
    <li><strong>Whisper</strong> (OpenAI): Transformer Encoder–Decoder, huấn luyện đa ngôn ngữ</li>
    <li><strong>PhoWhisper</strong> (VinAI Research): Whisper fine-tune đặc biệt cho tiếng Việt 🌟</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# 4️⃣ THÔNG TIN MODEL ĐÃ LƯU (OBJECT)
# ==========================================================
st.markdown("### 4. Thông tin Model Object đã lưu")

models_info = load_model_info_from_pkl()

if not models_info:
    st.warning("⚠️ Chưa tìm thấy model .pkl trong thư mục models/")
    st.info("💡 Bạn có thể lưu model objects vào thư mục `models/` để hiển thị thông tin chi tiết ở đây.")
else:
    for m in models_info:
        if "error" in m:
            st.error(f"❌ {m['file']}: {m['error']}")
            continue
        
        st.markdown(f"""
        <div class="card">
        <h4 style="color: #1f4e79; margin-top: 0;">{m['name']}</h4>
        <ul style="font-size: 16px; line-height: 1.8;">
            <li><strong>File:</strong> {m['file']}</li>
            <li><strong>Dung lượng:</strong> {m['size_mb']} MB</li>
            <li><strong>Tổng số tham số:</strong> {m['total_params']:,}</li>
            <li><strong>Tham số trainable:</strong> {m['trainable_params']:,}</li>
            <li><strong>Thiết bị inference:</strong> {m['device']}</li>
            <li><strong>Định dạng lưu:</strong> Pickle (.pkl)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# 5️⃣ ĐÁNH GIÁ
# ==========================================================
st.markdown("### 5. Đánh giá & độ tin cậy")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li><strong>Whisper base</strong>: Độ chính xác tốt với tiếng Việt phổ thông, phù hợp cho đa ngôn ngữ.</li>
    <li><strong>PhoWhisper</strong>: 🌟 Độ chính xác cao nhất cho tiếng Việt, được khuyến nghị sử dụng.</li>
    <li>Model được cache và load từ object giúp tăng tốc độ hệ thống.</li>
    <li>Phù hợp triển khai trên CPU (Streamlit Cloud) và GPU (local development).</li>
    <li>Hỗ trợ xử lý audio dài với chunking để tránh out-of-memory.</li>
    <li>Timestamps chính xác cho từng đoạn transcript.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================================
# 6️⃣ SO SÁNH
# ==========================================================
st.markdown("### 6. So sánh các mô hình")

# Get model info from registry
all_models = get_all_models()

# Create comparison table
st.markdown("""
<div class="card">
<table style="width:100%; border-collapse:collapse; font-size: 14px;" border="1">
    <tr style="background:#f0f2f6;">
        <th style="padding: 8px; text-align: left;">Mô hình</th>
        <th style="padding: 8px; text-align: left;">Loại</th>
        <th style="padding: 8px; text-align: left;">Kích thước</th>
        <th style="padding: 8px; text-align: left;">Tiếng Việt</th>
        <th style="padding: 8px; text-align: left;">Khuyến nghị</th>
    </tr>
""", unsafe_allow_html=True)

for model_id, model_info in all_models.items():
    vietnamese_support = "✅" if model_info.get("vietnamese_support") else "⚠️"
    recommended = "🌟" if model_info.get("recommended") else ""
    sizes = ", ".join(model_info.get("sizes", []))
    
    st.markdown(f"""
    <tr>
        <td style="padding: 8px;"><strong>{model_info['name']}</strong> {recommended}</td>
        <td style="padding: 8px;">{model_info['type']}</td>
        <td style="padding: 8px;">{sizes}</td>
        <td style="padding: 8px;">{vietnamese_support}</td>
        <td style="padding: 8px;">{recommended if recommended else "-"}</td>
    </tr>
    """, unsafe_allow_html=True)

st.markdown("</table></div>", unsafe_allow_html=True)

# Detailed Whisper comparison
st.markdown("---")
st.markdown("#### So sánh chi tiết các kích thước Whisper")

st.markdown("""
<div class="card">
<table style="width:100%; border-collapse:collapse; font-size: 14px;" border="1">
    <tr style="background:#f0f2f6;">
        <th style="padding: 8px; text-align: left;">Kích thước</th>
        <th style="padding: 8px; text-align: left;">Tham số (ước tính)</th>
        <th style="padding: 8px; text-align: left;">Tốc độ</th>
        <th style="padding: 8px; text-align: left;">Độ chính xác</th>
        <th style="padding: 8px; text-align: left;">Phù hợp</th>
    </tr>
    <tr>
        <td style="padding: 8px;"><strong>tiny</strong></td>
        <td style="padding: 8px;">~39M</td>
        <td style="padding: 8px;">Rất nhanh</td>
        <td style="padding: 8px;">Thấp</td>
        <td style="padding: 8px;">Demo, testing</td>
    </tr>
    <tr>
        <td style="padding: 8px;"><strong>base</strong></td>
        <td style="padding: 8px;">~74M</td>
        <td style="padding: 8px;">Nhanh</td>
        <td style="padding: 8px;">Tốt</td>
        <td style="padding: 8px;">Khuyến nghị (cân bằng)</td>
    </tr>
    <tr>
        <td style="padding: 8px;"><strong>small</strong></td>
        <td style="padding: 8px;">~244M</td>
        <td style="padding: 8px;">Trung bình</td>
        <td style="padding: 8px;">Rất tốt</td>
        <td style="padding: 8px;">Audio ngắn, chất lượng cao</td>
    </tr>
    <tr>
        <td style="padding: 8px;"><strong>medium</strong></td>
        <td style="padding: 8px;">~769M</td>
        <td style="padding: 8px;">Chậm</td>
        <td style="padding: 8px;">Xuất sắc</td>
        <td style="padding: 8px;">Audio quan trọng, có GPU</td>
    </tr>
    <tr>
        <td style="padding: 8px;"><strong>large</strong></td>
        <td style="padding: 8px;">~1550M</td>
        <td style="padding: 8px;">Rất chậm</td>
        <td style="padding: 8px;">Tốt nhất</td>
        <td style="padding: 8px;">Production, có GPU mạnh</td>
    </tr>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Footer
render_footer()
