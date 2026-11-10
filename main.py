"""
CLI đơn giản để OCR ảnh hoặc PDF
Dùng: python main.py <file_path> [--lang vi] [--gpu] [--out output.txt]
"""
import argparse
import json
from pathlib import Path

from ocr_engine import OCREngine


def main():
    parser = argparse.ArgumentParser(description="OCR ảnh hoặc PDF bằng PaddleOCR")
    parser.add_argument("input", help="Đường dẫn ảnh (.jpg/.png) hoặc PDF")
    parser.add_argument("--lang", default="vi", help="Ngôn ngữ: vi, en, ch, ... (mặc định: vi)")
    parser.add_argument("--gpu", action="store_true", help="Dùng GPU nếu có")
    parser.add_argument("--dpi", type=int, default=200, help="DPI khi render PDF (mặc định: 200)")
    parser.add_argument("--out", default=None, help="Lưu kết quả ra file .txt hoặc .json")
    parser.add_argument("--json", action="store_true", help="Xuất JSON đầy đủ (bbox + confidence)")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        print(f"[Lỗi] Không tìm thấy file: {source}")
        return

    print(f"Đang OCR: {source.name} | ngôn ngữ: {args.lang} | GPU: {args.gpu}")
    engine = OCREngine(lang=args.lang, use_gpu=args.gpu)

    if args.json:
        # Xuất chi tiết: bbox + confidence
        if source.suffix.lower() == ".pdf":
            result = engine.ocr_pdf(source, dpi=args.dpi)
        else:
            result = engine.ocr_image(source)

        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
            print(f"Đã lưu JSON: {args.out}")
        else:
            print(output)
    else:
        # Xuất text thuần
        text = engine.extract_text(source, dpi=args.dpi)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
            print(f"Đã lưu: {args.out}")
        else:
            print(text)


if __name__ == "__main__":
    main()
