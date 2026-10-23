#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "argostranslate>=1.11.0",
#     "pillow>=10.0.0",
#     "pytesseract>=0.3.10",
# ]
# ///
"""Alfred Workflow OCR Runner.

Extracts text from clipboard image (or input file), optionally translates it using Argos Translate,
and outputs formatted Markdown for Alfred's Text View widget.
"""

from __future__ import annotations

import binascii
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

# Ensure Homebrew and common binary directories are in PATH
EXTENDED_PATHS = [
    "/opt/homebrew/bin",
    "/opt/homebrew/sbin",
    "/usr/local/bin",
    "/usr/local/sbin",
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/.cargo/bin"),
]
for p in EXTENDED_PATHS:
    if p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{p}:{os.environ.get('PATH', '')}"

# Add local project src directory to sys.path if available
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"
if src_dir.is_dir() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Check for tesseract
tesseract_bin = shutil.which("tesseract")
if not tesseract_bin:
    for candidate in ["/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            tesseract_bin = candidate
            break

try:
    from PIL import Image, ImageGrab, ImageSequence
    import pytesseract

    if tesseract_bin:
        pytesseract.pytesseract.tesseract_cmd = tesseract_bin

    from my_image_to_text.converter import (
        clipboard_to_markdown,
        get_clipboard_image,
        image_to_markdown,
        normalize_language,
    )
    from my_image_to_text.translator import translate_text
except ImportError:
    # If package imports fail, provide a standalone fallback
    from PIL import Image, ImageGrab, ImageSequence
    import pytesseract

    if tesseract_bin:
        pytesseract.pytesseract.tesseract_cmd = tesseract_bin

    def normalize_language(lang: str | None) -> str:
        if not lang:
            return "eng"
        mapping = {
            "english": "eng", "eng": "eng", "en": "eng",
            "dutch": "nld", "nld": "nld", "nl": "nld",
            "french": "fra", "fra": "fra", "fr": "fra",
            "german": "deu", "deu": "deu", "de": "deu",
            "spanish": "spa", "spa": "spa", "es": "spa",
            "italian": "ita", "ita": "ita", "it": "ita",
            "chinese": "chi_sim", "japanese": "jpn", "russian": "rus",
        }
        return mapping.get(lang.strip().lower(), lang.strip())

    def get_clipboard_image() -> Image.Image | Path | None:
        if sys.platform == "darwin":
            p = subprocess.run(
                ["osascript", "-e", "POSIX path of (the clipboard as «class furl»)"],
                capture_output=True,
                text=True,
            )
            if p.returncode == 0:
                fpath = p.stdout.strip()
                if fpath and Path(fpath).is_file():
                    return Path(fpath)

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
                                return Image.open(io.BytesIO(binascii.unhexlify(hex_str)))
                            except Exception:
                                pass
        try:
            grab = ImageGrab.grabclipboard()
            if isinstance(grab, Image.Image):
                return grab
            if isinstance(grab, list) and grab and Path(grab[0]).is_file():
                return Path(grab[0])
        except Exception:
            pass
        return None

    TRANSLATION_LANG_MAP = {
        "english": "en", "eng": "en", "en": "en",
        "dutch": "nl", "nld": "nl", "dut": "nl", "nl": "nl",
        "french": "fr", "fra": "fr", "fre": "fr", "fr": "fr",
        "german": "de", "deu": "de", "ger": "de", "de": "de",
        "spanish": "es", "spa": "es", "es": "es",
        "italian": "it", "ita": "it", "it": "it",
        "portuguese": "pt", "por": "pt", "pt": "pt",
        "russian": "ru", "rus": "ru", "ru": "ru",
        "chinese": "zh", "chi_sim": "zh", "chi_tra": "zt", "zh": "zh",
        "japanese": "ja", "jpn": "ja", "ja": "ja",
        "arabic": "ar", "ara": "ar", "ar": "ar",
        "hindi": "hi", "hin": "hi", "hi": "hi",
        "polish": "pl", "pol": "pl", "pl": "pl",
        "swedish": "sv", "swe": "sv", "sv": "sv",
        "danish": "da", "dan": "da", "da": "da",
        "norwegian": "no", "nor": "no", "no": "no",
        "finnish": "fi", "fin": "fi", "fi": "fi",
        "turkish": "tr", "tur": "tr", "tr": "tr",
        "czech": "cs", "ces": "cs", "cze": "cs", "cs": "cs",
        "greek": "el", "ell": "el", "gre": "el", "el": "el",
        "korean": "ko", "kor": "ko", "ko": "ko",
        "ukrainian": "uk", "ukr": "uk", "uk": "uk",
    }

    def normalize_translation_language(lang: str | None) -> str:
        if not lang:
            return "en"
        cleaned = lang.strip().lower()
        return TRANSLATION_LANG_MAP.get(cleaned, cleaned)

    def _get_installed_translation(from_code: str, to_code: str):
        import argostranslate.translate
        installed_langs = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in installed_langs if l.code == from_code), None)
        to_lang = next((l for l in installed_langs if l.code == to_code), None)
        if from_lang is not None and to_lang is not None:
            return from_lang.get_translation(to_lang)
        return None

    def _install_translation_package(from_code: str, to_code: str):
        import argostranslate.package
        import argostranslate.translate
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        direct_pkg = next(
            (p for p in available_packages if p.from_code == from_code and p.to_code == to_code),
            None,
        )
        if direct_pkg is not None:
            argostranslate.package.install_from_path(direct_pkg.download())
        elif from_code != "en" and to_code != "en":
            pkg_from = next((p for p in available_packages if p.from_code == from_code and p.to_code == "en"), None)
            pkg_to = next((p for p in available_packages if p.from_code == "en" and p.to_code == to_code), None)
            if pkg_from is not None and pkg_to is not None:
                argostranslate.package.install_from_path(pkg_from.download())
                argostranslate.package.install_from_path(pkg_to.download())
        argostranslate.translate.load_installed_languages()
        return _get_installed_translation(from_code, to_code)

    def translate_text(text: str, from_lang: str = "eng", to_lang: str | None = None) -> str:
        if not text or not to_lang:
            return text
        from_code = normalize_translation_language(from_lang)
        to_code = normalize_translation_language(to_lang)
        if from_code == to_code:
            return text
        try:
            pipeline = _get_installed_translation(from_code, to_code)
            if pipeline is None:
                pipeline = _install_translation_package(from_code, to_code)
            if pipeline is not None:
                return pipeline.translate(text)
        except Exception:
            pass
        return text

    def _ocr_image_page(page: Image.Image, tess_lang: str) -> str:
        try:
            return pytesseract.image_to_string(page, lang=tess_lang)
        except pytesseract.TesseractError as e:
            if tess_lang != "eng" and ("Failed loading language" in str(e) or "Error opening data file" in str(e)):
                return pytesseract.image_to_string(page, lang="eng")
            raise

    def image_to_markdown(
        img_input: str | Path | Image.Image,
        lang: str = "eng",
        target_lang: str | None = None,
    ) -> str:
        tess_lang = normalize_language(lang)
        pages = []
        if isinstance(img_input, Image.Image):
            for page in ImageSequence.Iterator(img_input):
                text = _ocr_image_page(page, tess_lang)
                pages.append(text.strip())
        else:
            with Image.open(Path(img_input)) as img:
                for page in ImageSequence.Iterator(img):
                    text = _ocr_image_page(page, tess_lang)
                    pages.append(text.strip())
        if not pages:
            return ""

        if target_lang:
            pages = [translate_text(p, from_lang=lang, to_lang=target_lang) for p in pages]

        if len(pages) == 1:
            return pages[0]
        parts = [f"# Page {i}\n\n{text}" for i, text in enumerate(pages, start=1) if text]
        return "\n\n---\n\n".join(parts)

    def clipboard_to_markdown(lang: str = "eng", target_lang: str | None = None) -> str:
        img = get_clipboard_image()
        if img is None:
            raise ValueError("No image found in clipboard.")
        return image_to_markdown(img, lang=lang, target_lang=target_lang)


def parse_workflow_args(args: list[str]) -> tuple[Path | None, str, str | None]:
    """Parse Alfred command line arguments and environment variables.

    Returns:
        (file_path, ocr_lang, target_lang)
    """
    default_ocr_lang = os.environ.get("OCR_LANG", "").strip() or "eng"
    default_target_lang = os.environ.get("TARGET_LANG", "").strip() or None
    is_translate_mode = os.environ.get("TRANSLATE_MODE", "").strip().lower() in ("1", "true", "yes")

    all_tokens: list[str] = []
    for arg in args:
        if not arg:
            continue
        # Split individual arguments by whitespace to handle un-split query strings passed by Alfred
        for token in arg.split():
            if token == "--translate":
                is_translate_mode = True
            else:
                all_tokens.append(token)

    file_path: Path | None = None
    lang_tokens = list(all_tokens)

    # Check if a prefix of tokens forms a valid file path
    for i in range(len(all_tokens), 0, -1):
        candidate = " ".join(all_tokens[:i])
        if Path(candidate).is_file():
            file_path = Path(candidate)
            lang_tokens = all_tokens[i:]
            break

    ocr_lang = default_ocr_lang
    target_lang = default_target_lang

    remaining_text = " ".join(lang_tokens).strip()

    if remaining_text:
        m_to = re.match(r"^(?:to|->|--to-lang|--target-lang|-t)\s+([a-zA-Z_-]+)$", remaining_text, re.IGNORECASE)
        if m_to:
            target_lang = m_to.group(1).strip()
        else:
            m_pair_arrow = re.match(r"^([a-zA-Z_-]+)\s*(?:to|->)\s*([a-zA-Z_-]+)$", remaining_text, re.IGNORECASE)
            if m_pair_arrow:
                ocr_lang = m_pair_arrow.group(1).strip()
                target_lang = m_pair_arrow.group(2).strip()
            else:
                parts = remaining_text.split()
                if len(parts) >= 2:
                    # Default: space-separated pair represents (source_language, target_language)
                    ocr_lang = parts[0].strip()
                    target_lang = parts[1].strip()
                elif len(parts) == 1:
                    if is_translate_mode:
                        target_lang = parts[0].strip()
                    else:
                        ocr_lang = parts[0].strip()
    elif is_translate_mode and not target_lang:
        target_lang = default_target_lang or "en"

    return file_path, ocr_lang, target_lang


def main() -> None:
    # Check tesseract availability
    if not tesseract_bin:
        print(
            "### Tesseract OCR Not Found\n\n"
            "Tesseract is not installed or not in your PATH.\n\n"
            "To install it on macOS using Homebrew, run:\n"
            "```bash\n"
            "brew install tesseract tesseract-lang\n"
            "```"
        )
        sys.exit(0)

    file_path, ocr_lang, target_lang = parse_workflow_args(sys.argv[1:])

    try:
        if file_path is not None:
            markdown_output = image_to_markdown(
                file_path,
                lang=ocr_lang,
                target_lang=target_lang,
            )
        else:
            markdown_output = clipboard_to_markdown(
                lang=ocr_lang,
                target_lang=target_lang,
            )

        if not markdown_output or not markdown_output.strip():
            print(
                "### No Text Detected\n\n"
                "OCR completed, but no readable text was detected in the image."
            )
        else:
            print(markdown_output)
    except ValueError as e:
        if "No image found in clipboard" in str(e):
            print(
                "### No Image Found in Clipboard\n\n"
                "Please copy an image (or take a screenshot with `⌘⇧⌃4`) and run the workflow again."
            )
        else:
            print(
                f"### Translation Error\n\n"
                f"{e}"
            )
    except Exception as e:
        print(
            f"### Error Processing Image\n\n"
            f"An error occurred while processing the image:\n\n"
            f"```\n{e}\n```"
        )


if __name__ == "__main__":
    main()
