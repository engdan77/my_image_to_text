from __future__ import annotations

import binascii
import io
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageGrab, ImageSequence
import pytesseract

from my_image_to_text.translator import translate_text

LANGUAGE_MAP: dict[str, str] = {
    "english": "eng",
    "eng": "eng",
    "en": "eng",
    "dutch": "nld",
    "nld": "nld",
    "dut": "nld",
    "nl": "nld",
    "french": "fra",
    "fra": "fra",
    "fre": "fra",
    "fr": "fra",
    "german": "deu",
    "deu": "deu",
    "ger": "deu",
    "de": "deu",
    "spanish": "spa",
    "spa": "spa",
    "es": "spa",
    "italian": "ita",
    "ita": "ita",
    "it": "ita",
    "portuguese": "por",
    "por": "por",
    "pt": "por",
    "chinese": "chi_sim",
    "japanese": "jpn",
    "russian": "rus",
    "arabic": "ara",
    "hindi": "hin",
    "polish": "pol",
    "swedish": "swe",
    "danish": "dan",
    "norwegian": "nor",
    "finnish": "fin",
    "turkish": "tur",
    "czech": "ces",
    "greek": "ell",
    "korean": "kor",
    "ukrainian": "ukr",
}


def normalize_language(lang: str | None) -> str:
    """Normalize language name or code to Tesseract-compatible language code."""
    if not lang:
        return "eng"
    cleaned = lang.strip().lower()
    return LANGUAGE_MAP.get(cleaned, lang.strip())


def clean_markdown_text(raw_text: str) -> str:
    """Clean extracted OCR text and format as Markdown paragraphs."""
    lines = raw_text.splitlines()
    cleaned_lines = [line.rstrip() for line in lines]
    
    # Remove leading and trailing empty lines
    while cleaned_lines and not cleaned_lines[0]:
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1]:
        cleaned_lines.pop()

    return "\n".join(cleaned_lines)


def get_clipboard_image() -> Image.Image | Path | None:
    """Retrieve the image currently in the system clipboard (if any).

    Supports raw image data (TIFF, PNG, JPEG) and copied image file paths.
    """
    if sys.platform == "darwin":
        # 1. Check if a file URL / POSIX path was copied in Finder
        p = subprocess.run(
            ["osascript", "-e", "POSIX path of (the clipboard as «class furl»)"],
            capture_output=True,
            text=True,
        )
        if p.returncode == 0:
            file_path = p.stdout.strip()
            if file_path and Path(file_path).is_file():
                try:
                    img = Image.open(file_path)
                    img.load()
                    return Path(file_path)
                except Exception:
                    pass

        # 2. Check for raw image data on macOS pasteboard (PNG, TIFF, JPEG)
        for fmt in ["PNGf", "TIFF", "JPEG"]:
            p = subprocess.run(
                ["osascript", "-e", f"get the clipboard as «class {fmt}»"],
                capture_output=True,
            )
            if p.returncode == 0:
                text = p.stdout.decode("utf-8", errors="ignore")
                m = re.search(r"data (?:PNGf|TIFF|JPEG)\s*([0-9a-fA-F]+)", text)
                if m:
                    hex_str = m.group(1)
                    if len(hex_str) % 2 == 0:
                        try:
                            data = binascii.unhexlify(hex_str)
                            img = Image.open(io.BytesIO(data))
                            img.load()
                            return img
                        except Exception:
                            pass

    # 3. Fallback to ImageGrab for cross-platform / general support
    try:
        grab = ImageGrab.grabclipboard()
        if isinstance(grab, Image.Image):
            return grab
        if isinstance(grab, list) and grab and Path(grab[0]).is_file():
            return Path(grab[0])
    except Exception:
        pass

    return None


def _ocr_image_page(page: Image.Image, tess_lang: str) -> str:
    """Helper to run Tesseract OCR with automatic fallback to 'eng' if language pack is not installed."""
    try:
        return pytesseract.image_to_string(page, lang=tess_lang)
    except pytesseract.TesseractError as e:
        if tess_lang != "eng" and ("Failed loading language" in str(e) or "Error opening data file" in str(e)):
            return pytesseract.image_to_string(page, lang="eng")
        raise


def process_image(image_input: str | Path | Image.Image, lang: str = "eng") -> list[str]:
    """Process an image (file path or PIL Image) and return OCR text for each page/frame.

    Args:
        image_input: File path (str/Path) or PIL Image object.
        lang: Language for OCR recognition (defaults to "eng").

    Returns:
        List of strings, one per page/frame.
    """
    tess_lang = normalize_language(lang)
    page_texts: list[str] = []

    if isinstance(image_input, Image.Image):
        for page in ImageSequence.Iterator(image_input):
            text = _ocr_image_page(page, tess_lang)
            page_texts.append(clean_markdown_text(text))
    else:
        path_obj = Path(image_input)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")

        with Image.open(path_obj) as img:
            for page in ImageSequence.Iterator(img):
                text = _ocr_image_page(page, tess_lang)
                page_texts.append(clean_markdown_text(text))

    return page_texts


def image_to_markdown(
    image_input: str | Path | Image.Image,
    lang: str = "eng",
    *,
    target_lang: str | None = None,
    include_page_headers: bool | None = None,
) -> str:
    """Process an image (TIFF, PNG, JPEG, PIL Image) and generate Markdown output.

    Args:
        image_input: Path to the image file or PIL Image object.
        lang: Language for OCR recognition (default: 'eng').
        target_lang: Optional language to translate OCR text into via Argos Translate.
        include_page_headers: If True, include `# Page N` headers for all pages.
            If None (default), headers are included only when there are multiple pages.
            If False, headers are omitted.

    Returns:
        Markdown formatted string.
    """
    pages = process_image(image_input, lang=lang)
    if not pages:
        return ""

    if target_lang:
        pages = [
            translate_text(page_text, from_lang=lang, to_lang=target_lang)
            if page_text else ""
            for page_text in pages
        ]

    if include_page_headers is None:
        include_page_headers = len(pages) > 1

    markdown_parts: list[str] = []
    for i, page_text in enumerate(pages, start=1):
        page_content: list[str] = []
        if include_page_headers:
            page_content.append(f"# Page {i}")
            if page_text:
                page_content.append("")
                page_content.append(page_text)
        else:
            if page_text:
                page_content.append(page_text)

        markdown_parts.append("\n".join(page_content))

    return "\n\n---\n\n".join(markdown_parts).strip()


def clipboard_to_markdown(
    lang: str = "eng",
    *,
    target_lang: str | None = None,
    include_page_headers: bool | None = None,
) -> str:
    """Extract image from clipboard and convert its content to Markdown via OCR.

    Args:
        lang: Language for OCR recognition (default: 'eng').
        target_lang: Optional language to translate OCR text into via Argos Translate.
        include_page_headers: If True, include page headers.

    Returns:
        Markdown formatted string.

    Raises:
        ValueError: If no image is found in the clipboard.
    """
    img = get_clipboard_image()
    if img is None:
        raise ValueError("No image found in clipboard.")

    return image_to_markdown(
        img,
        lang=lang,
        target_lang=target_lang,
        include_page_headers=include_page_headers,
    )
