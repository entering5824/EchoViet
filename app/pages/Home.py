"""
Home Page - Giới thiệu đề tài
"""
import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css
from app.components.footer import render_footer

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

st.markdown('<div class="main-header">Designing and Developing a Vietnamese Speech to Text System for Automatic Meeting Transcription</div>', 
            unsafe_allow_html=True)

st.markdown("---")

# Section 1: Bối cảnh và Lý do chọn đề tài
st.markdown("### 1. Bối cảnh và Lý do chọn đề tài")

st.markdown("""
<div class="card">
<p style="font-size: 16px; line-height: 1.7;">
Trong các cuộc họp, thảo luận, phỏng vấn hoặc thuyết trình,
việc ghi biên bản thủ công thường tốn thời gian và dễ sai sót.
</p>
<p style="font-size: 16px; line-height: 1.7; margin-top: 10px;">
Đề tài này xây dựng hệ thống <strong>Vietnamese Speech-to-Text</strong>
giúp tự động chuyển giọng nói tiếng Việt thành văn bản,
phục vụ cho hành chính, giáo dục và doanh nghiệp.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Section 2: Mục tiêu Đề tài
st.markdown("### 2. Mục tiêu Đề tài")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li>Xây dựng hệ thống Speech-to-Text tiếng Việt bằng mô hình mã nguồn mở.</li>
    <li>Cho phép tải lên audio cuộc họp (WAV/MP3/FLAC).</li>
    <li>Hiển thị waveform và spectrogram.</li>
    <li>Tạo transcript tự động và cho phép chỉnh sửa.</li>
    <li>Hỗ trợ 2 mô hình ASR chính: Whisper và PhoWhisper (tối ưu cho tiếng Việt).</li>
    <li>Xử lý audio dài với chunking và speaker diarization.</li>
    <li>Export transcript ra nhiều định dạng (TXT, DOCX, PDF).</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Section 3: Phạm vi thực hiện
st.markdown("### 3. Phạm vi thực hiện")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li><strong>Tiền xử lý audio:</strong> Normalize, noise reduction, format conversion.</li>
    <li><strong>Nhận dạng tiếng nói:</strong> Sử dụng Whisper và PhoWhisper (tối ưu cho tiếng Việt).</li>
    <li><strong>Xử lý audio dài:</strong> Chunking và xử lý từng đoạn.</li>
    <li><strong>Speaker Diarization:</strong> Phân biệt người nói trong cuộc họp.</li>
    <li><strong>Triển khai web app:</strong> Sử dụng Streamlit framework.</li>
    <li><strong>Export và thống kê:</strong> Xuất transcript và hiển thị thống kê chi tiết.</li>
    <li><strong>So sánh mô hình:</strong> Benchmark và đánh giá chất lượng các mô hình ASR.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Section 4: Ý nghĩa khoa học và thực tiễn
st.markdown("### 4. Ý nghĩa khoa học và thực tiễn")

st.markdown("""
<div class="card">
<ul style="font-size: 16px; line-height: 1.8;">
    <li><strong>Ứng dụng AI vào xử lý tiếng nói tiếng Việt:</strong> Nghiên cứu và triển khai các mô hình ASR hiện đại cho tiếng Việt.</li>
    <li><strong>Hỗ trợ tự động hóa ghi biên bản cuộc họp:</strong> Giảm thiểu công việc thủ công, tăng hiệu quả làm việc.</li>
    <li><strong>Khả năng mở rộng:</strong> Có thể mở rộng sang tóm tắt và phân tích cuộc họp, sentiment analysis.</li>
    <li><strong>Giáo dục và nghiên cứu:</strong> Cung cấp nền tảng để nghiên cứu và học tập về ASR và NLP.</li>
    <li><strong>Ứng dụng thực tế:</strong> Phục vụ cho các doanh nghiệp, tổ chức cần ghi chép và lưu trữ thông tin từ cuộc họp.</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Footer
render_footer()
