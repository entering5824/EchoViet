"""
ASR Benchmark Page
"""
import streamlit as st
import os
import sys
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.components.sidebar import render_sidebar
from app.components.layout import apply_custom_css

# Apply custom CSS
apply_custom_css()

# Render sidebar with logo
render_sidebar()

st.header("🔬 ASR Model Benchmark")
st.markdown("""
### So sánh Whisper và PhoWhisper

Trang này cho phép bạn chạy đánh giá chất lượng để so sánh giữa Whisper và PhoWhisper.

**Yêu cầu:**
- Tạo thư mục `test_audio/` trong project root
- Thêm các file audio test (.wav, .mp3, etc.)
- Mỗi file audio cần có file `.txt` tương ứng chứa reference text (ground truth)
- Ví dụ: `audio1.wav` cần có `audio1.txt`

**Metrics:**
- **WER (Word Error Rate)**: Tỷ lệ lỗi từ
- **CER (Character Error Rate)**: Tỷ lệ lỗi ký tự

Giá trị thấp hơn = tốt hơn.
""")

from core.asr.model_registry import get_all_models, get_model_info, check_model_dependencies

st.subheader("⚙️ Cấu hình đánh giá")

all_models = get_all_models()

# Model selection - allow multiple models
st.markdown("**Chọn các mô hình để so sánh:**")
selected_models = st.multiselect(
    "Models:",
    options=list(all_models.keys()),
    default=["whisper", "phowhisper"],
    format_func=lambda x: all_models[x]["name"]
)

# Model sizes for each selected model
model_configs = {}
for model_id in selected_models:
    model_info = get_model_info(model_id)
    if model_info and model_info.get("sizes"):
        if len(model_info["sizes"]) > 1:
            size = st.selectbox(
                f"{model_info['name']} size:",
                model_info["sizes"],
                key=f"size_{model_id}",
                index=model_info["sizes"].index(model_info.get("default_size", model_info["sizes"][0])) if model_info.get("default_size") in model_info["sizes"] else 0
            )
        else:
            size = model_info["sizes"][0]
        model_configs[model_id] = size
    else:
        model_configs[model_id] = "default"

test_dir = st.text_input("Thư mục test audio:", value="test_audio")

if st.button("🚀 Chạy đánh giá", type="primary"):
    if not selected_models:
        st.warning("⚠️ Vui lòng chọn ít nhất một mô hình để đánh giá!")
    else:
        # Check if test directory exists
        test_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), test_dir)
        
        if not os.path.exists(test_path):
            st.error(f"❌ Thư mục {test_dir} không tồn tại!")
        else:
            # Check dependencies for selected models
            unavailable_models = []
            for model_id in selected_models:
                is_available, missing = check_model_dependencies(model_id)
                if not is_available:
                    unavailable_models.append((model_id, missing))
            
            if unavailable_models:
                st.warning("⚠️ Một số mô hình chưa sẵn sàng:")
                for model_id, missing in unavailable_models:
                    model_name = get_model_info(model_id)["name"]
                    st.write(f"- {model_name}: Thiếu {', '.join(missing)}")
                st.info("💡 Bạn vẫn có thể chạy đánh giá với các mô hình đã sẵn sàng.")
            
            with st.spinner("Đang chạy đánh giá... (có thể mất vài phút)"):
                try:
                    # Run evaluation script (supports Whisper and PhoWhisper)
                    script_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "core", "asr", "evaluate_models.py"
                    )
                    
                    # Filter to supported models
                    supported = [m for m in selected_models if m in ["whisper", "phowhisper"]]
                    if not supported:
                        st.error("❌ Chỉ hỗ trợ Whisper và PhoWhisper.")
                    else:
                        whisper_size = model_configs.get("whisper", "large") if "whisper" in supported else "large"
                        phowhisper_size = model_configs.get("phowhisper", "medium") if "phowhisper" in supported else "medium"
                        
                        result = subprocess.run(
                            [
                                sys.executable,
                                script_path,
                                "--test_dir", test_dir,
                                "--whisper_model", whisper_size,
                                "--phowhisper_model", phowhisper_size,
                                "--output", "docs/model_comparison.md"
                            ],
                            capture_output=True,
                            text=True,
                            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                        )
                        
                        if result.returncode == 0:
                            st.success("✅ Đánh giá hoàn tất!")
                            st.code(result.stdout)
                            
                            # Show report
                            report_path = os.path.join(
                                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                "docs", "model_comparison.md"
                            )
                            if os.path.exists(report_path):
                                with open(report_path, 'r', encoding='utf-8') as f:
                                    st.markdown(f.read())
                        else:
                            st.error(f"❌ Lỗi khi chạy đánh giá:\n{result.stderr}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")

# Show existing report if available
report_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "docs", "model_comparison.md"
)
if os.path.exists(report_path):
    st.subheader("📄 Báo cáo hiện có")
    with open(report_path, 'r', encoding='utf-8') as f:
        st.markdown(f.read())

