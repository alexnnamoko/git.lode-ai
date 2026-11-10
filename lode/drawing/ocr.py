"""Tesseract discovery and OCR helpers for Windows, Linux and Streamlit Cloud."""
from __future__ import annotations
import os, shutil


def configure_tesseract():
    try:
        import pytesseract
    except ImportError:
        return False, "Python package pytesseract is not installed."
    configured = os.getenv("TESSERACT_CMD", "").strip()
    candidates = [configured, shutil.which("tesseract"),
                  r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                  r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            pytesseract.pytesseract.tesseract_cmd = candidate
            break
    try:
        version = str(pytesseract.get_tesseract_version())
        langs = pytesseract.get_languages(config="")
        return True, {"version": version, "languages": langs, "path": pytesseract.pytesseract.tesseract_cmd}
    except Exception as exc:
        return False, str(exc)


def image_ocr(image):
    import pytesseract
    from pytesseract import Output
    ok, info = configure_tesseract()
    if not ok:
        raise RuntimeError(f"Tesseract engine unavailable: {info}")
    data = pytesseract.image_to_data(image, output_type=Output.DICT)
    words = []
    for i, raw in enumerate(data.get("text", [])):
        text = str(raw).strip()
        if not text:
            continue
        try: confidence = float(data["conf"][i])
        except Exception: confidence = -1.0
        words.append({"text": text, "confidence": confidence,
                      "bbox": [int(data["left"][i]), int(data["top"][i]),
                               int(data["left"][i] + data["width"][i]), int(data["top"][i] + data["height"][i])]})
    return {"text": pytesseract.image_to_string(image), "words": words, "engine": info}
