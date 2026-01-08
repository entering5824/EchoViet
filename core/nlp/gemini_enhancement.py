"""
Gemini AI Enhancement for Vietnamese Text
Sử dụng Google Gemini API để cải thiện transcript
"""
import os
from typing import Optional

def enhance_with_gemini(text: str, api_key: Optional[str] = None, model: Optional[str] = None) -> Optional[str]:
    """
    Cải thiện văn bản tiếng Việt sử dụng Gemini AI
    
    Args:
        text: Văn bản cần cải thiện
        api_key: Gemini API key (nếu None, lấy từ env GEMINI_API_KEY)
        model: Gemini model name (nếu None, lấy từ env GEMINI_MODEL hoặc dùng default)
    
    Returns:
        Enhanced text hoặc None nếu lỗi
    """
    try:
        # Get API key from env if not provided (support both GEMINI_API_KEY and GEMINI_API)
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY hoặc GEMINI_API không được tìm thấy trong environment variables")
        
        # Get model from env if not provided
        if model is None:
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Import google.generativeai
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Chưa cài đặt google-generativeai. Cài đặt bằng: pip install google-generativeai")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create model instance
        gemini_model = genai.GenerativeModel(model)
        
        # Create enhanced prompt for Vietnamese text enhancement with ASR error correction
        prompt = f"""Bạn là chuyên gia cải thiện văn bản tiếng Việt từ transcript ASR (speech-to-text). 
Văn bản này có nhiều lỗi do nhận diện giọng nói. Bạn PHẢI sửa chữa TẤT CẢ các lỗi sau:

**1. LỖI CHÍNH TẢ DO PHÁT ÂM SAI/ĐỊA PHƯƠNG (QUAN TRỌNG NHẤT):**
- "chứng cấp 3" → "trường cấp 3"
- "nối tiếng" → "nổi tiếng"  
- "dạy với một trường" → "học ở một trường" hoặc "dạy ở một trường" (tùy ngữ cảnh)
- "chia. Sẻ" → "chia sẻ"
- Tìm và sửa TẤT CẢ các từ sai do phát âm/địa phương thành từ đúng tiếng Việt chuẩn
- Phân biệt và sửa các từ đồng âm khác nghĩa dựa trên ngữ cảnh

**2. SỬA CÂU BỊ GÃY VÀ NGỮ PHÁP:**
- "mình không có chia. Sẻ nhiều với các bạn" → "Mình không có chia sẻ nhiều với các bạn"
- "cái chuyến là cái sự nối tiếng của mình" → "Cái chuyện là cái sự nổi tiếng của mình"
- "một con người dạy với một trường mà em là" → "Một con người học ở một trường mà em là"
- Nối các câu bị cắt đứt bởi dấu chấm sai thành câu hoàn chỉnh
- Sửa ngữ pháp để câu tự nhiên, đúng và có nghĩa
- Đảm bảo mỗi câu là một câu hoàn chỉnh về mặt ngữ pháp

**3. LOẠI BỎ KÝ TỰ RÁC VÀ DẤU CÂU THỪA:**
- "vì. ." → "vì"
- "em chỉ. ." → "em chỉ"
- ";;;" → xóa hoàn toàn
- Loại bỏ tất cả dấu chấm, dấu phẩy, dấu chấm phẩy thừa không cần thiết
- Loại bỏ các ký tự đặc biệt không có ý nghĩa (;;, ..., ,,,, etc.)
- Xóa các dấu câu đứng một mình không có từ trước/sau

**4. CHUẨN HÓA CÂU:**
- Thêm dấu câu đúng chỗ (chấm, phẩy, chấm hỏi, chấm than) dựa trên ngữ cảnh
- Viết hoa đầu câu và tên riêng
- Loại bỏ khoảng trắng thừa
- Đảm bảo mỗi câu có nghĩa và hoàn chỉnh

**5. CẢI THIỆN CÁCH DIỄN ĐẠT:**
- Làm cho văn bản tự nhiên và dễ đọc hơn
- Sửa các cụm từ lủng củng thành cách nói tự nhiên
- Giữ nguyên nội dung và ý nghĩa gốc
- KHÔNG thêm thông tin mới không có trong văn bản gốc

**Văn bản cần cải thiện:**
{text}

**YÊU CẦU NGHIÊM NGẶT:**
- Trả về CHỈ văn bản đã được cải thiện, KHÔNG thêm giải thích, comment, hay markdown
- Sửa TẤT CẢ lỗi chính tả, ngữ pháp, semantic errors, và ký tự rác
- Đảm bảo văn bản sạch, không có ký tự rác, dấu câu thừa
- Câu văn phải tự nhiên, đúng ngữ pháp tiếng Việt, và có nghĩa
- Ưu tiên sửa lỗi semantic (từ sai nghĩa) hơn là chỉ sửa dấu câu"""
        
        # Generate enhanced text
        response = gemini_model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return None
            
    except Exception as e:
        # Return None on error, caller will handle
        raise Exception(f"Lỗi khi gọi Gemini API: {str(e)}")

def is_gemini_available() -> bool:
    """
    Kiểm tra xem Gemini API có sẵn không
    
    Returns:
        True nếu có API key và có thể import library
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
        if not api_key:
            return False
        
        try:
            import google.generativeai
            return True
        except ImportError:
            return False
    except:
        return False
