from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)
logging.getLogger("stanza").setLevel(logging.ERROR)
logging.getLogger("argostranslate").setLevel(logging.ERROR)

import argostranslate.package
import argostranslate.translate

if TYPE_CHECKING:
    from argostranslate.translate import ITranslation

# Normalization mapping from language names / 3-letter codes to standard Argos ISO codes
TRANSLATION_LANG_MAP: dict[str, str] = {
    "english": "en",
    "eng": "en",
    "en": "en",
    "dutch": "nl",
    "nld": "nl",
    "dut": "nl",
    "nl": "nl",
    "french": "fr",
    "fra": "fr",
    "fre": "fr",
    "fr": "fr",
    "german": "de",
    "deu": "de",
    "ger": "de",
    "de": "de",
    "spanish": "es",
    "spa": "es",
    "es": "es",
    "italian": "it",
    "ita": "it",
    "it": "it",
    "portuguese": "pt",
    "por": "pt",
    "pt": "pt",
    "russian": "ru",
    "rus": "ru",
    "ru": "ru",
    "chinese": "zh",
    "chi_sim": "zh",
    "chi_tra": "zt",
    "zho": "zh",
    "zh": "zh",
    "japanese": "ja",
    "jpn": "ja",
    "ja": "ja",
    "arabic": "ar",
    "ara": "ar",
    "ar": "ar",
    "hindi": "hi",
    "hin": "hi",
    "hi": "hi",
    "polish": "pl",
    "pol": "pl",
    "pl": "pl",
    "swedish": "sv",
    "swe": "sv",
    "sv": "sv",
    "danish": "da",
    "dan": "da",
    "da": "da",
    "norwegian": "no",
    "nor": "no",
    "no": "no",
    "finnish": "fi",
    "fin": "fi",
    "fi": "fi",
    "turkish": "tr",
    "tur": "tr",
    "tr": "tr",
    "czech": "cs",
    "ces": "cs",
    "cze": "cs",
    "cs": "cs",
    "greek": "el",
    "ell": "el",
    "gre": "el",
    "el": "el",
    "korean": "ko",
    "kor": "ko",
    "ko": "ko",
    "ukrainian": "uk",
    "ukr": "uk",
    "uk": "uk",
    "indonesian": "id",
    "ind": "id",
    "id": "id",
    "vietnamese": "vi",
    "vie": "vi",
    "vi": "vi",
    "thai": "th",
    "tha": "th",
    "th": "th",
    "hungarian": "hu",
    "hun": "hu",
    "hu": "hu",
    "romanian": "ro",
    "ron": "ro",
    "rum": "ro",
    "ro": "ro",
    "bulgarian": "bg",
    "bul": "bg",
    "bg": "bg",
    "catalan": "ca",
    "cat": "ca",
    "ca": "ca",
    "hebrew": "he",
    "heb": "he",
    "he": "he",
}


def normalize_translation_language(lang: str | None) -> str:
    """Normalize language name or code to Argos Translate ISO 639 code."""
    if not lang:
        return "en"
    cleaned = lang.strip().lower()
    return TRANSLATION_LANG_MAP.get(cleaned, cleaned)


def get_installed_translation(from_code: str, to_code: str) -> ITranslation | None:
    """Check if an installed translation path exists between from_code and to_code."""
    installed_langs = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_langs if l.code == from_code), None)
    to_lang = next((l for l in installed_langs if l.code == to_code), None)
    if from_lang is not None and to_lang is not None:
        return from_lang.get_translation(to_lang)
    return None


def install_translation_package(from_code: str, to_code: str) -> ITranslation:
    """Download and install translation models for from_code -> to_code.

    Supports direct language pairs or pivot translations through English ('en').
    """
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    # 1. Direct package match
    direct_pkg = next(
        (p for p in available_packages if p.from_code == from_code and p.to_code == to_code),
        None,
    )
    if direct_pkg is not None:
        download_path = direct_pkg.download()
        argostranslate.package.install_from_path(download_path)
    # 2. Pivot through English if no direct package is available
    elif from_code != "en" and to_code != "en":
        pkg_from = next(
            (p for p in available_packages if p.from_code == from_code and p.to_code == "en"),
            None,
        )
        pkg_to = next(
            (p for p in available_packages if p.from_code == "en" and p.to_code == to_code),
            None,
        )
        if pkg_from is not None and pkg_to is not None:
            argostranslate.package.install_from_path(pkg_from.download())
            argostranslate.package.install_from_path(pkg_to.download())
        else:
            raise ValueError(
                f"No translation models available for {from_code} -> {to_code}."
            )
    else:
        raise ValueError(
            f"No translation model available for {from_code} -> {to_code}."
        )

    argostranslate.translate.load_installed_languages()
    translation = get_installed_translation(from_code, to_code)
    if translation is None:
        raise ValueError(
            f"Failed to initialize translation pipeline for {from_code} -> {to_code}."
        )
    return translation


def get_translation_pipeline(from_code: str, to_code: str) -> ITranslation:
    """Retrieve or install the translation pipeline for from_code -> to_code."""
    translation = get_installed_translation(from_code, to_code)
    if translation is not None:
        return translation
    return install_translation_package(from_code, to_code)


def translate_text(
    text: str,
    from_lang: str = "eng",
    to_lang: str | None = None,
) -> str:
    """Translate text from source language to target language using Argos Translate.

    Args:
        text: Input text string to translate.
        from_lang: Source language name or code (default: 'eng').
        to_lang: Target language name or code (optional).

    Returns:
        Translated text if to_lang is specified, or original text if to_lang is None / same.
    """
    if not text or not to_lang:
        return text

    from_code = normalize_translation_language(from_lang)
    to_code = normalize_translation_language(to_lang)

    if from_code == to_code:
        return text

    pipeline = get_translation_pipeline(from_code, to_code)
    result = pipeline.translate(text)
    return result
