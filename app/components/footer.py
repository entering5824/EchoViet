"""
Footer Component
Display information about students and instructor
"""
import streamlit as st

def render_footer():
    """Render footer with information about students and instructor"""
    st.write("---")
    
    # --- GITHUB & STUDENTS BOX ---
    st.markdown(
        """
        <div style="
            padding:18px;
            background:#0b0f1b;
            border-radius:12px;
            border:1px solid #f0e6b2;
            font-size:15px;
            line-height:1.55;
            margin-bottom:18px;
        ">
            <div style="margin-bottom:12px;">
                <span style="font-weight:600; font-size:17px; color:#f0e6b2;">Github: </span>
                <a href="https://github.com/entering5824/EchoViet" 
                   target="_blank" 
                   style="color:#4a9eff; text-decoration:none;">
                   https://github.com/entering5824/EchoViet
                </a>
            </div>
            <div style="margin-top:12px;">
                <span style="font-weight:600; font-size:17px; color:#f0e6b2;">Students:</span><br>
                <span style="color:#e0e0e0;">
                    • Phạm Nguyễn Minh Tú — phamtuofficial5824@gmail.com<br>
                    • Trần Lê Hữu Nghĩa — nghíatlh22@uef.edu.vn<br>
                    • Cao Minh Phú — phucm22@uef.edu.vn
                </span>
            </div>
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

