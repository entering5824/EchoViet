"""
Footer Component
Hiển thị thông tin students và instructor
"""
import streamlit as st

def render_footer():
    """Render footer với thông tin students và instructor"""
    st.write("---")
    
    # --- STUDENTS BOX ---
    st.markdown(
        """
        <div style="
            padding:18px;
            background:#0b0f1b;
            border-radius:12px;
            border:1px solid #f0e6b2;
            font-size:15px;
            line-height:1.55;
        ">
            <span style="font-weight:600; font-size:17px;">Students</span><br>
            • Phạm Nguyễn Minh Tú — phamtuofficial5824@gmail.com<br>
            • Trần Lê Hữu Nghĩa — nghíatlh22@uef.edu.vn<br>
            • Student 3 — email<br>
            • Student 4 — email<br>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # --- INSTRUCTOR BOX ---
    st.markdown(
        """
        <div style="
            padding:18px;
            background:#0b0f1b;
            border-radius:12px;
            border:1px solid #e0e0e0;
            margin-top:18px;
            display:flex;
            align-items:center;
            font-size:16px;
        ">
            <img src="https://upload.wikimedia.org/wikipedia/commons/0/06/ORCID_iD.svg"
                 width="26"
                 style="margin-right:10px;">
            <div>
                <b>Bùi Tiến Đức</b><br>
                <a href="https://orcid.org/0000-0001-5174-3558"
                   target="_blank"
                   style="color:#0066cc; text-decoration:none;">
                   ORCID: 0000-0001-5174-3558
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

