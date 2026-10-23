from __future__ import annotations

import os
from pathlib import Path
import sys
import pytest

alfred_dir = Path(__file__).resolve().parent.parent / "alfred"
if str(alfred_dir) not in sys.path:
    sys.path.insert(0, str(alfred_dir))

from ocr_clipboard import parse_workflow_args


def test_alfred_parse_args_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OCR_LANG", raising=False)
    monkeypatch.delenv("TARGET_LANG", raising=False)
    monkeypatch.delenv("TRANSLATE_MODE", raising=False)

    fpath, ocr_lang, target_lang = parse_workflow_args([])
    assert fpath is None
    assert ocr_lang == "eng"
    assert target_lang is None


def test_alfred_parse_args_single_lang():
    fpath, ocr_lang, target_lang = parse_workflow_args(["fra"])
    assert fpath is None
    assert ocr_lang == "fra"
    assert target_lang is None


def test_alfred_parse_args_pair_languages():
    fpath, ocr_lang, target_lang = parse_workflow_args(["nl", "en"])
    assert fpath is None
    assert ocr_lang == "nl"
    assert target_lang == "en"

    # Single argument containing space (as passed by Alfred in $1)
    fpath_quoted, ocr_lang_quoted, target_lang_quoted = parse_workflow_args(["nl en"])
    assert fpath_quoted is None
    assert ocr_lang_quoted == "nl"
    assert target_lang_quoted == "en"


def test_alfred_parse_args_arrow_syntax():
    fpath, ocr_lang, target_lang = parse_workflow_args(["dutch", "to", "english"])
    assert fpath is None
    assert ocr_lang == "dutch"
    assert target_lang == "english"

    fpath_quoted, ocr_lang_quoted, target_lang_quoted = parse_workflow_args(["dutch to english"])
    assert fpath_quoted is None
    assert ocr_lang_quoted == "dutch"
    assert target_lang_quoted == "english"

    fpath2, ocr_lang2, target_lang2 = parse_workflow_args(["nl->en"])
    assert fpath2 is None
    assert ocr_lang2 == "nl"
    assert target_lang2 == "en"


def test_alfred_parse_args_to_target():
    fpath, ocr_lang, target_lang = parse_workflow_args(["to", "english"])
    assert fpath is None
    assert ocr_lang == "eng"
    assert target_lang == "english"


def test_alfred_parse_args_translate_mode():
    fpath, ocr_lang, target_lang = parse_workflow_args(["--translate", "en"])
    assert fpath is None
    assert ocr_lang == "eng"
    assert target_lang == "en"

    fpath2, ocr_lang2, target_lang2 = parse_workflow_args(["--translate", "dutch", "english"])
    assert fpath2 is None
    assert ocr_lang2 == "dutch"
    assert target_lang2 == "english"

    # Translate mode with single quoted string "nl en"
    fpath3, ocr_lang3, target_lang3 = parse_workflow_args(["--translate", "nl en"])
    assert fpath3 is None
    assert ocr_lang3 == "nl"
    assert target_lang3 == "en"

    # Translate mode with combined string "--translate nl en"
    fpath4, ocr_lang4, target_lang4 = parse_workflow_args(["--translate nl en"])
    assert fpath4 is None
    assert ocr_lang4 == "nl"
    assert target_lang4 == "en"


def test_alfred_parse_args_file_input(tmp_path: Path):
    dummy_file = tmp_path / "sample.tiff"
    dummy_file.write_text("fake image")

    fpath, ocr_lang, target_lang = parse_workflow_args([str(dummy_file), "dutch to english"])
    assert fpath == dummy_file
    assert ocr_lang == "dutch"
    assert target_lang == "english"

    # Single string containing file path and language args
    fpath2, ocr_lang2, target_lang2 = parse_workflow_args([f"{dummy_file} nl en"])
    assert fpath2 == dummy_file
    assert ocr_lang2 == "nl"
    assert target_lang2 == "en"


def test_build_workflow_plist_structure():
    import plistlib
    import build_workflow

    plist_dict = build_workflow.generate_plist()
    assert "objects" in plist_dict
    
    script_actions = [
        obj for obj in plist_dict["objects"]
        if obj.get("type") == "alfred.workflow.action.script"
    ]
    assert len(script_actions) == 2
    for action in script_actions:
        # type 0 corresponds to /bin/bash inline script in Alfred
        assert action["config"]["type"] == 0
        assert len(action["config"]["script"]) > 0

    keywords = [
        obj for obj in plist_dict["objects"]
        if obj.get("type") == "alfred.workflow.input.keyword"
    ]
    assert len(keywords) == 2
    keyword_map = {k["config"]["keyword"]: k["config"] for k in keywords}
    assert keyword_map["ocr"]["argumenttype"] == 1  # optional
    assert keyword_map["ocrt"]["argumenttype"] == 0  # required

    text_views = [
        obj for obj in plist_dict["objects"]
        if obj.get("type") == "alfred.workflow.userinterface.text"
    ]
    assert len(text_views) == 1
    # behaviour: 1 enables editable text view in Alfred 5.5+
    assert text_views[0]["config"]["behaviour"] == 1


def test_ocr_clipboard_script_metadata():
    ocr_script_path = alfred_dir / "ocr_clipboard.py"
    content = ocr_script_path.read_text()
    assert "# /// script" in content
    assert "# requires-python" in content
    assert '"pillow' in content or "'pillow" in content
    assert '"pytesseract' in content or "'pytesseract" in content
    assert '"argostranslate' in content or "'argostranslate" in content
    assert "# ///" in content


def test_ocr_clipboard_fallback_translation_logic(monkeypatch: pytest.MonkeyPatch):
    import ocr_clipboard

    # Test normalization and translation function
    translated = ocr_clipboard.translate_text("Hallo wereld", from_lang="dutch", to_lang="english")
    assert isinstance(translated, str)
    assert len(translated) > 0
    assert "Hello" in translated or "world" in translated.lower()
