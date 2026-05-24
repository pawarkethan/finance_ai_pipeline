# ─────────────────────────────────────────────
# utils/ocr.py — PaddleOCR-based text extraction
# ─────────────────────────────────────────────

import os
import re
from PIL import Image
from pdf2image import convert_from_path
from paddleocr import PaddleOCR

from config import OCR_LANG, OCR_SCORE_THRESHOLD

# Initialise once — re-creating PaddleOCR on every call is expensive
_ocr = PaddleOCR(lang=OCR_LANG, use_textline_orientation=True)


def load_inputs(file_path: str) -> list[Image.Image]:
    """Load a PDF or image file and return a list of PIL RGB images."""
    if file_path.lower().endswith(".pdf"):
        images = convert_from_path(file_path)
    else:
        images = [Image.open(file_path)]
    return [img.convert("RGB") for img in images]


def extract_text(images: list[Image.Image]) -> str:
    """Run OCR over a list of page images and return the combined text."""
    final_text = []
    for i, img in enumerate(images):
        temp_path = f"_temp_ocr_{i}.jpg"
        img.save(temp_path)
        try:
            result = _ocr.predict(temp_path)
            page_text = []
            if result and len(result) > 0:
                rec_texts  = result[0].get("rec_texts", [])
                rec_scores = result[0].get("rec_scores", [])
                for text, score in zip(rec_texts, rec_scores):
                    if score > OCR_SCORE_THRESHOLD:
                        page_text.append(text)
            final_text.append("\n".join(page_text))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return "\n\n".join(final_text)


def clean_text(text: str) -> str:
    """Collapse whitespace runs into single spaces."""
    return re.sub(r'\s+', ' ', text).strip()