from __future__ import annotations

import pytest

from my_image_to_text.translator import (
    normalize_translation_language,
    translate_text,
)


def test_normalize_translation_language():
    assert normalize_translation_language(None) == "en"
    assert normalize_translation_language("") == "en"
    assert normalize_translation_language("english") == "en"
    assert normalize_translation_language("English") == "en"
    assert normalize_translation_language("eng") == "en"
    assert normalize_translation_language("en") == "en"
    assert normalize_translation_language("dutch") == "nl"
    assert normalize_translation_language("nld") == "nl"
    assert normalize_translation_language("nl") == "nl"
    assert normalize_translation_language("french") == "fr"
    assert normalize_translation_language("fra") == "fr"
    assert normalize_translation_language("fre") == "fr"
    assert normalize_translation_language("fr") == "fr"
    assert normalize_translation_language("german") == "de"
    assert normalize_translation_language("deu") == "de"
    assert normalize_translation_language("spanish") == "es"
    assert normalize_translation_language("spa") == "es"
    assert normalize_translation_language("italian") == "it"
    assert normalize_translation_language("japanese") == "ja"
    assert normalize_translation_language("chinese") == "zh"
    assert normalize_translation_language("custom_code") == "custom_code"


def test_translate_text_no_target_lang():
    raw = "Hello world"
    assert translate_text(raw, from_lang="eng", to_lang=None) == raw


def test_translate_text_same_language():
    raw = "Hello world"
    assert translate_text(raw, from_lang="eng", to_lang="english") == raw
    assert translate_text(raw, from_lang="en", to_lang="eng") == raw


def test_translate_text_empty_input():
    assert translate_text("", from_lang="dutch", to_lang="english") == ""


def test_translate_text_dutch_to_english():
    dutch_text = "Hoe kan ik je helpen?"
    translated = translate_text(dutch_text, from_lang="dutch", to_lang="english")
    assert "How can I help" in translated or "help you" in translated.lower()


def test_translate_text_mocked_pipeline(monkeypatch: pytest.MonkeyPatch):
    class DummyTranslation:
        def translate(self, text: str) -> str:
            return f"TRANSLATED: {text}"

    monkeypatch.setattr(
        "my_image_to_text.translator.get_translation_pipeline",
        lambda from_c, to_c: DummyTranslation(),
    )

    result = translate_text("Bonjour le monde", from_lang="fra", to_lang="eng")
    assert result == "TRANSLATED: Bonjour le monde"
