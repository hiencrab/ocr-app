"""
Debug script - in ra raw result từ PaddleOCR 2.9+ để xem format thực tế
Dùng: python debug_ocr.py <file_anh_hoac_pdf>
"""
import sys
import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["FLAGS_new_ir_enabled"] = "0"
from paddleocr import PaddleOCR

img = sys.argv[1] if len(sys.argv) > 1 else None
if not img:
    print("Dùng: python debug_ocr.py <file_anh>")
    sys.exit(1)

ocr = PaddleOCR(use_textline_orientation=True, lang="vi")
result = ocr.predict(img)

print("=== TYPE của result ===")
print(type(result))
print("\n=== len(result) ===")
print(len(result) if result else 0)

if result:
    first_page = result[0]
    print("\n=== TYPE result[0] ===")
    print(type(first_page))
    print("\n=== dir(result[0]) ===")
    print([x for x in dir(first_page) if not x.startswith('_')])
    print("\n=== repr(result[0]) (200 chars) ===")
    print(repr(first_page)[:500])
