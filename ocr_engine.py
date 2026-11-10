"""
OCR engine dùng PaddleOCR 2.9+ trên Linux (Docker)
"""
from pathlib import Path
from typing import Union

import numpy as np
from pdf2image import convert_from_path
from paddleocr import PaddleOCR
from PIL import Image

# langdetect ISO 639-1 → PaddleOCR lang code
_LD_TO_PADDLE: dict[str, str] = {
    "zh-cn": "ch",
    "zh-tw": "chinese_cht",
    "ja":    "japan",
    "ko":    "korean",
    "vi":    "vi",
    "fr":    "fr",
    "de":    "german",
    "ar":    "arabic",
    "hi":    "hindi",
}

_LANG_NAMES: dict[str, str] = {
    "ch":           "Tiếng Trung (Giản thể)",
    "chinese_cht":  "Tiếng Trung (Phồn thể)",
    "japan":        "Tiếng Nhật",
    "korean":       "Tiếng Hàn",
    "vi":           "Tiếng Việt",
    "fr":           "Tiếng Pháp",
    "german":       "Tiếng Đức",
    "en":           "Tiếng Anh",
    "arabic":       "Tiếng Ả Rập",
    "hindi":        "Tiếng Hindi",
}


def detect_ocr_lang(text: str) -> str:
    """Phát hiện ngôn ngữ từ text OCR, trả về PaddleOCR lang code."""
    if not text or len(text.strip()) < 10:
        return "en"
    try:
        from langdetect import detect, LangDetectException
        code = detect(text)
        return _LD_TO_PADDLE.get(code, "en")
    except Exception:
        return "en"


def lang_display_name(lang: str) -> str:
    return _LANG_NAMES.get(lang, lang)


class OCREngine:
    def __init__(self, lang: str = "vi", use_gpu: bool = False):
        self.lang = lang
        self.ocr = PaddleOCR(
            use_textline_orientation=True,
            lang=lang,
        )

    def ocr_image(self, image: Union[str, Path, np.ndarray, Image.Image]) -> list[dict]:
        if isinstance(image, Image.Image):
            image = np.array(image)
        elif isinstance(image, Path):
            image = str(image)
        result = self.ocr.ocr(image)
        return self._parse_result(result)

    def ocr_pdf(self, pdf_path: Union[str, Path], dpi: int = 200) -> list[dict]:
        pages = convert_from_path(str(pdf_path), dpi=dpi)
        all_pages = []
        for page_num, page_img in enumerate(pages, start=1):
            blocks = self.ocr_image(page_img)
            all_pages.append({
                "page": page_num,
                "blocks": blocks,
                "text": "\n".join(b["text"] for b in blocks),
            })
        return all_pages

    def extract_text(self, source: Union[str, Path], dpi: int = 200) -> str:
        source = Path(source)
        if source.suffix.lower() == ".pdf":
            pages = self.ocr_pdf(source, dpi=dpi)
            return "\n".join(
                f"\n--- Trang {p['page']} ---\n{p['text']}" for p in pages
            ).strip()
        blocks = self.ocr_image(source)
        return "\n".join(b["text"] for b in blocks)

    def _parse_result(self, result) -> list[dict]:
        blocks = []
        if not result:
            return blocks
        for page_result in result:
            if not page_result:
                continue
            for line in page_result:
                try:
                    bbox, (text, score) = line
                    if text and str(text).strip():
                        blocks.append({
                            "text":       str(text).strip(),
                            "confidence": round(float(score), 4),
                            "bbox":       bbox,
                        })
                except Exception:
                    continue
        return blocks
