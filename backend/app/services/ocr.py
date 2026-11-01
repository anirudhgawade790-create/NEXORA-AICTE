"""Optional OCR adapter; extracted text is advisory and never a fraud verdict."""


def extract_text(path: str, mime_type: str) -> tuple[str | None, bool, str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        pytesseract = None
        Image = None
    try:
        import pdfplumber
    except ImportError:
        pdfplumber = None
    if pytesseract is None and pdfplumber is None:
        return None, False, "OCR unavailable; manual verification required"
    try:
        if mime_type == "application/pdf" and pdfplumber is not None:
            with pdfplumber.open(path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return text or None, True, "Text extraction completed; officer review required"
        if mime_type.startswith("image/") and pytesseract is not None and Image is not None:
            return pytesseract.image_to_string(Image.open(path)), True, "OCR completed; officer review required"
    except Exception as exc:
        return None, True, f"Text extraction unavailable ({type(exc).__name__}); manual verification required"
    return None, False, "OCR unavailable; manual verification required"
