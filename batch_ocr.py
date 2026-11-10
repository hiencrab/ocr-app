"""
Xử lý hàng loạt: OCR tất cả ảnh/PDF trong một thư mục
Dùng: python batch_ocr.py <input_dir> <output_dir> [--lang vi] [--gpu]
"""
import argparse
import json
from pathlib import Path

from ocr_engine import OCREngine

SUPPORTED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
SUPPORTED_FORMATS = SUPPORTED_IMAGE | {".pdf"}


def process_file(engine: OCREngine, file: Path, output_dir: Path, as_json: bool, dpi: int):
    out_suffix = ".json" if as_json else ".txt"
    out_file = output_dir / (file.stem + out_suffix)

    if out_file.exists():
        print(f"  [skip] {file.name} (đã có kết quả)")
        return

    print(f"  OCR: {file.name}")
    try:
        if as_json:
            if file.suffix.lower() == ".pdf":
                result = engine.ocr_pdf(file, dpi=dpi)
            else:
                result = engine.ocr_image(file)
            out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            text = engine.extract_text(file, dpi=dpi)
            out_file.write_text(text, encoding="utf-8")
    except Exception as e:
        print(f"  [lỗi] {file.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="OCR hàng loạt ảnh/PDF trong một thư mục")
    parser.add_argument("input_dir", help="Thư mục chứa file cần OCR")
    parser.add_argument("output_dir", help="Thư mục lưu kết quả text")
    parser.add_argument("--lang", default="vi", help="Ngôn ngữ (mặc định: vi)")
    parser.add_argument("--gpu", action="store_true", help="Dùng GPU nếu có")
    parser.add_argument("--dpi", type=int, default=200, help="DPI khi render PDF (mặc định: 200)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Xuất JSON đầy đủ thay vì text thuần")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in sorted(input_dir.iterdir()) if f.suffix.lower() in SUPPORTED_FORMATS]
    if not files:
        print(f"Không tìm thấy file ảnh/PDF trong: {input_dir}")
        return

    print(f"Tìm thấy {len(files)} file | ngôn ngữ: {args.lang} | GPU: {args.gpu}")
    engine = OCREngine(lang=args.lang, use_gpu=args.gpu)

    for file in files:
        process_file(engine, file, output_dir, args.as_json, args.dpi)

    print(f"\nHoàn tất. Kết quả lưu tại: {output_dir}")


if __name__ == "__main__":
    main()
