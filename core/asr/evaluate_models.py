"""
Script đánh giá chất lượng mô hình: So sánh Whisper vs PhoWhisper
Tính WER (Word Error Rate) và CER (Character Error Rate)
"""
import os
import json
import torch
from pathlib import Path
from typing import Dict, List, Tuple
# Ensure FFmpeg configured before importing librosa (best-effort)
try:
    from core.audio.ffmpeg_setup import ensure_ffmpeg
    ensure_ffmpeg(silent=True)
except Exception:
    pass
import librosa
import soundfile as sf
import tempfile
from core.audio.audio_processor import _make_safe_temp_copy

# Import models
# Note: Cần import trực tiếp whisper và transformers vì không có streamlit context
try:
    import whisper
    from transformers import pipeline
    import torch
except ImportError as e:
    print(f"Lỗi import: {e}")
    print("Vui lòng đảm bảo đã cài đặt tất cả dependencies")
    exit(1)

from jiwer import wer, cer
import pandas as pd

def load_reference_texts(test_dir: str) -> Dict[str, str]:
    """
    Load reference texts từ file .txt trong thư mục test
    
    Format: mỗi audio file có file .txt tương ứng với cùng tên
    Ví dụ: audio1.wav -> audio1.txt
    
    Args:
        test_dir: Đường dẫn thư mục chứa test files
    
    Returns:
        Dict: {audio_filename: reference_text}
    """
    references = {}
    test_path = Path(test_dir)
    
    if not test_path.exists():
        print(f"⚠️ Thư mục {test_dir} không tồn tại. Tạo thư mục mới...")
        test_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Đã tạo thư mục {test_dir}")
        print("💡 Vui lòng thêm audio files (.wav, .mp3) và file reference text (.txt) tương ứng")
        return references
    
    # Tìm tất cả audio files
    audio_extensions = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
    audio_files = []
    for ext in audio_extensions:
        audio_files.extend(list(test_path.glob(f'*{ext}')))
    
    # Load reference texts
    for audio_file in audio_files:
        txt_file = audio_file.with_suffix('.txt')
        if txt_file.exists():
            with open(txt_file, 'r', encoding='utf-8') as f:
                references[audio_file.name] = f.read().strip()
        else:
            print(f"⚠️ Không tìm thấy file reference cho {audio_file.name}")
    
    return references

def evaluate_model_whisper(audio_path: str, model_size: str = "large") -> str:
    """
    Transcribe audio với Whisper
    
    Args:
        audio_path: Đường dẫn file audio
        model_size: Kích thước model Whisper
    
    Returns:
        str: Transcribed text
    """
    # Preflight checks to help diagnose WinError 2 (file not found) issues
    try:
        if not os.path.exists(audio_path):
            # Try creating a safe temp copy to avoid problems with odd filenames
            try:
                temp_copy = _make_safe_temp_copy(audio_path)
                audio_path = temp_copy
            except Exception as e:
                print(f"❌ Audio path not found and could not create safe copy: {e}")
                return ""

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model(model_size, device=device)

        result = model.transcribe(
            audio_path,
            language="vi",
            task="transcribe",
            fp16=False
        )

        if result:
            return result.get("text", "")
        return ""
    except Exception as e:
        print(f"❌ Lỗi khi transcribe với Whisper: {e}")
        return ""

def evaluate_model_phowhisper(audio_path: str, model_size: str = "medium") -> str:
    """
    Transcribe audio với PhoWhisper
    
    Args:
        audio_path: Đường dẫn file audio
        model_size: Kích thước model PhoWhisper
    
    Returns:
        str: Transcribed text
    """
    # Preflight checks to help diagnose WinError 2 (file not found) issues
    try:
        if not os.path.exists(audio_path):
            # Try creating a safe temp copy to avoid problems with odd filenames
            try:
                temp_copy = _make_safe_temp_copy(audio_path)
                audio_path = temp_copy
            except Exception as e:
                print(f"❌ Audio path not found and could not create safe copy: {e}")
                return ""

        device = 0 if torch.cuda.is_available() else -1
        model_name = f"vinai/PhoWhisper-{model_size}"

        transcriber = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=device
        )

        result = transcriber(audio_path, return_timestamps=True)

        if result:
            return result.get("text", "")
        return ""
    except Exception as e:
        print(f"❌ Lỗi khi transcribe với PhoWhisper: {e}")
        return ""

def run_evaluation(
    test_dir: str = "test_audio",
    whisper_model: str = "large",
    phowhisper_model: str = "medium",
    output_file: str = "docs/model_comparison.md"
) -> Dict:
    """
    Chạy đánh giá so sánh Whisper vs PhoWhisper
    
    Args:
        test_dir: Thư mục chứa test audio files
        whisper_model: Model Whisper để test
        phowhisper_model: Model PhoWhisper để test
        output_file: File output để lưu kết quả
    
    Returns:
        Dict: Kết quả đánh giá
    """
    print("🚀 Bắt đầu đánh giá mô hình...")
    print(f"📁 Thư mục test: {test_dir}")
    print(f"🔍 Whisper model: {whisper_model}")
    print(f"🔍 PhoWhisper model: {phowhisper_model}")
    print("-" * 60)
    
    # Load reference texts
    references = load_reference_texts(test_dir)
    
    if not references:
        print("❌ Không tìm thấy reference texts. Vui lòng thêm audio files và file .txt tương ứng.")
        return {}
    
    print(f"✅ Tìm thấy {len(references)} file test\n")
    
    # Kết quả
    results = []
    test_path = Path(test_dir)
    
    # Device info
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    for i, (audio_name, reference) in enumerate(references.items(), 1):
        audio_path = test_path / audio_name
        print(f"[{i}/{len(references)}] Đang xử lý {audio_name}...")
        
        # Transcribe với Whisper
        print("  🔄 Transcribing với Whisper...")
        whisper_text = evaluate_model_whisper(str(audio_path), whisper_model)
        
        # Transcribe với PhoWhisper
        print("  🔄 Transcribing với PhoWhisper...")
        phowhisper_text = evaluate_model_phowhisper(str(audio_path), phowhisper_model)
        
        # Tính WER và CER
        whisper_wer = wer(reference, whisper_text) if whisper_text else 1.0
        whisper_cer = cer(reference, whisper_text) if whisper_text else 1.0
        
        phowhisper_wer = wer(reference, phowhisper_text) if phowhisper_text else 1.0
        phowhisper_cer = cer(reference, phowhisper_text) if phowhisper_text else 1.0
        
        results.append({
            'file': audio_name,
            'whisper_text': whisper_text,
            'phowhisper_text': phowhisper_text,
            'reference': reference,
            'whisper_wer': whisper_wer,
            'whisper_cer': whisper_cer,
            'phowhisper_wer': phowhisper_wer,
            'phowhisper_cer': phowhisper_cer
        })
        
        print(f"  ✅ Whisper - WER: {whisper_wer:.4f}, CER: {whisper_cer:.4f}")
        print(f"  ✅ PhoWhisper - WER: {phowhisper_wer:.4f}, CER: {phowhisper_cer:.4f}\n")
    
    # Tính thống kê tổng hợp
    df = pd.DataFrame(results)
    
    summary = {
        'whisper_mean_wer': df['whisper_wer'].mean(),
        'whisper_std_wer': df['whisper_wer'].std(),
        'whisper_mean_cer': df['whisper_cer'].mean(),
        'whisper_std_cer': df['whisper_cer'].std(),
        'phowhisper_mean_wer': df['phowhisper_wer'].mean(),
        'phowhisper_std_wer': df['phowhisper_wer'].std(),
        'phowhisper_mean_cer': df['phowhisper_cer'].mean(),
        'phowhisper_std_cer': df['phowhisper_cer'].std(),
        'num_files': len(results),
        'device': device,
        'whisper_model': whisper_model,
        'phowhisper_model': phowhisper_model
    }
    
    # Tạo báo cáo markdown
    create_report(results, summary, output_file)
    
    print("=" * 60)
    print("📊 KẾT QUẢ TỔNG HỢP")
    print("=" * 60)
    print(f"Whisper-{whisper_model}:")
    print(f"  WER: {summary['whisper_mean_wer']:.4f} ± {summary['whisper_std_wer']:.4f}")
    print(f"  CER: {summary['whisper_mean_cer']:.4f} ± {summary['whisper_std_cer']:.4f}")
    print(f"\nPhoWhisper-{phowhisper_model}:")
    print(f"  WER: {summary['phowhisper_mean_wer']:.4f} ± {summary['phowhisper_std_wer']:.4f}")
    print(f"  CER: {summary['phowhisper_mean_cer']:.4f} ± {summary['phowhisper_std_cer']:.4f}")
    print(f"\n📄 Báo cáo chi tiết đã được lưu tại: {output_file}")
    
    return {
        'results': results,
        'summary': summary
    }

def create_report(results: List[Dict], summary: Dict, output_file: str):
    """
    Tạo báo cáo markdown
    
    Args:
        results: Danh sách kết quả từng file
        summary: Thống kê tổng hợp
        output_file: Đường dẫn file output
    """
    # Tạo thư mục nếu chưa có
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# So sánh Whisper vs PhoWhisper\n\n")
        f.write("## Thông tin đánh giá\n\n")
        f.write(f"- **Số file test**: {summary['num_files']}\n")
        f.write(f"- **Device**: {summary['device']}\n")
        f.write(f"- **Whisper model**: {summary['whisper_model']}\n")
        f.write(f"- **PhoWhisper model**: {summary['phowhisper_model']}\n\n")
        
        f.write("## Kết quả tổng hợp\n\n")
        f.write("| Model | WER (Mean ± Std) | CER (Mean ± Std) |\n")
        f.write("|-------|------------------|------------------|\n")
        f.write(f"| Whisper-{summary['whisper_model']} | "
                f"{summary['whisper_mean_wer']:.4f} ± {summary['whisper_std_wer']:.4f} | "
                f"{summary['whisper_mean_cer']:.4f} ± {summary['whisper_std_cer']:.4f} |\n")
        f.write(f"| PhoWhisper-{summary['phowhisper_model']} | "
                f"{summary['phowhisper_mean_wer']:.4f} ± {summary['phowhisper_std_wer']:.4f} | "
                f"{summary['phowhisper_mean_cer']:.4f} ± {summary['phowhisper_std_cer']:.4f} |\n\n")
        
        f.write("## Kết quả chi tiết từng file\n\n")
        f.write("| File | Whisper WER | Whisper CER | PhoWhisper WER | PhoWhisper CER |\n")
        f.write("|------|-------------|-------------|----------------|----------------|\n")
        
        for r in results:
            f.write(f"| {r['file']} | {r['whisper_wer']:.4f} | {r['whisper_cer']:.4f} | "
                   f"{r['phowhisper_wer']:.4f} | {r['phowhisper_cer']:.4f} |\n")
        
        f.write("\n## Kết luận\n\n")
        if summary['phowhisper_mean_wer'] < summary['whisper_mean_wer']:
            f.write("✅ **PhoWhisper có WER thấp hơn Whisper**, cho thấy độ chính xác tốt hơn cho tiếng Việt.\n\n")
        else:
            f.write("⚠️ **Whisper có WER thấp hơn PhoWhisper** trong test này. Có thể cần thêm test cases.\n\n")
        
        f.write("### Khuyến nghị\n\n")
        f.write("- Sử dụng **PhoWhisper** cho audio tiếng Việt để đạt độ chính xác tốt nhất\n")
        f.write("- Sử dụng **Whisper** nếu cần hỗ trợ đa ngôn ngữ\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Đánh giá chất lượng Whisper vs PhoWhisper")
    parser.add_argument("--test_dir", type=str, default="test_audio",
                       help="Thư mục chứa test audio files (default: test_audio)")
    parser.add_argument("--whisper_model", type=str, default="large",
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Model Whisper để test (default: large)")
    parser.add_argument("--phowhisper_model", type=str, default="medium",
                       choices=["small", "medium", "base"],
                       help="Model PhoWhisper để test (default: medium)")
    parser.add_argument("--output", type=str, default="docs/model_comparison.md",
                       help="File output (default: docs/model_comparison.md)")
    
    args = parser.parse_args()
    
    run_evaluation(
        test_dir=args.test_dir,
        whisper_model=args.whisper_model,
        phowhisper_model=args.phowhisper_model,
        output_file=args.output
    )

