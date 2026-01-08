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
        # Get API key from env if not provided
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY không được tìm thấy trong environment variables")
        
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
        
        # Create prompt for Vietnamese text enhancement
        prompt = f"""Bạn là chuyên gia cải thiện văn bản tiếng Việt. Nhiệm vụ của bạn là cải thiện đoạn văn bản sau đây:

1. Sửa lỗi chính tả và ngữ pháp
2. Cải thiện dấu câu (thêm dấu câu đúng chỗ, sửa dấu câu sai)
3. Viết hoa đầu câu và tên riêng
4. Loại bỏ khoảng trắng thừa
5. Cải thiện cách diễn đạt để văn bản tự nhiên và dễ đọc hơn
6. Giữ nguyên nội dung và ý nghĩa gốc
7. Không thêm thông tin mới không có trong văn bản gốc

Văn bản cần cải thiện:
{text}

Hãy trả về chỉ văn bản đã được cải thiện, không thêm giải thích hay comment nào khác."""
        
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
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return False
        
        try:
            import google.generativeai
            return True
        except ImportError:
            return False
    except:
        return False
