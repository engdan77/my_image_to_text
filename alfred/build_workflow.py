#!/usr/bin/env python3
"""Build and package the Alfred Workflow."""

from __future__ import annotations

import os
from pathlib import Path
import plistlib
import subprocess
import zipfile

WORKFLOW_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WORKFLOW_DIR.parent
OUTPUT_PACKAGE = PROJECT_ROOT / "OCR-Clipboard-to-Markdown.alfredworkflow"

UID_KEYWORD = "8D3F376A-4A04-4530-9788-06C05A611001"
UID_HOTKEY = "8D3F376A-4A04-4530-9788-06C05A611002"
UID_UNIV_ACTION = "8D3F376A-4A04-4530-9788-06C05A611003"
UID_RUN_SCRIPT = "8D3F376A-4A04-4530-9788-06C05A611004"
UID_TEXT_VIEW = "8D3F376A-4A04-4530-9788-06C05A611005"
UID_CLIP_COPY = "8D3F376A-4A04-4530-9788-06C05A611006"
UID_CLIP_PASTE = "8D3F376A-4A04-4530-9788-06C05A611007"
UID_KEYWORD_TRANSLATE = "8D3F376A-4A04-4530-9788-06C05A611008"
UID_RUN_SCRIPT_TRANSLATE = "8D3F376A-4A04-4530-9788-06C05A611009"

SCRIPT_CODE = r"""export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:$HOME/.local/bin:$PATH"

if [ -f "./ocr_clipboard.py" ]; then
    if command -v uv >/dev/null 2>&1; then
        uv run ./ocr_clipboard.py "$1"
    else
        /usr/bin/python3 ./ocr_clipboard.py "$1"
    fi
elif command -v my-image-to-text >/dev/null 2>&1; then
    args=($1)
    if [ ${#args[@]} -ge 2 ]; then
        my-image-to-text --clipboard --lang "${args[0]}" --target-lang "${args[1]}"
    elif [ ${#args[@]} -eq 1 ]; then
        if [ -f "${args[0]}" ]; then
            my-image-to-text "${args[0]}"
        else
            my-image-to-text --clipboard --lang "${args[0]}"
        fi
    else
        my-image-to-text --clipboard
    fi
else
    /usr/bin/python3 -m my_image_to_text.cli --clipboard
fi
"""

TRANSLATE_SCRIPT_CODE = r"""export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:$HOME/.local/bin:$PATH"

if [ -f "./ocr_clipboard.py" ]; then
    if command -v uv >/dev/null 2>&1; then
        uv run ./ocr_clipboard.py --translate "$1"
    else
        /usr/bin/python3 ./ocr_clipboard.py --translate "$1"
    fi
elif command -v my-image-to-text >/dev/null 2>&1; then
    args=($1)
    if [ ${#args[@]} -ge 2 ]; then
        my-image-to-text --clipboard --lang "${args[0]}" --target-lang "${args[1]}"
    elif [ ${#args[@]} -eq 1 ]; then
        my-image-to-text --clipboard --lang "${OCR_LANG:-eng}" --target-lang "${args[0]}"
    else
        my-image-to-text --clipboard --target-lang "${TARGET_LANG:-en}"
    fi
else
    /usr/bin/python3 -m my_image_to_text.cli --clipboard
fi
"""

README_TEXT = """# OCR Clipboard to Markdown & Translation

Extracts text from images (such as multi-page TIFFs, PNGs, screenshots, and copied image files) directly from your clipboard, optionally translates the extracted text via **Argos Translate**, and renders formatted Markdown using Alfred 5's native **Text View** widget.

## Requirements

1. **Alfred 5** (with Powerpack)
2. **Tesseract OCR**:
   ```bash
   brew install tesseract
   ```
3. **my-image-to-text** installed globally or via `uv`:
   ```bash
   uv tool install .
   ```

## Workflow Usage

- **`ocr` Keyword**:
  - `ocr`: OCR clipboard image into Markdown.
  - `ocr fra`: OCR with French language model.
  - `ocr nld eng`: OCR Dutch image and translate into English Markdown.
  - `ocr dutch to english`: Specify source and target translation language.
  - `ocr to fr`: Translate default OCR text to French.
- **`ocrt` Keyword** (OCR & Translate - languages required):
  - `ocrt nl en`: OCR Dutch clipboard and translate into English Markdown (source and target languages required).
  - `ocrt dutch to english`: Specify full language names for translation.
- **Hotkey**: Configure a global shortcut (e.g., `⌥⇧O`) to immediately process clipboard image.
- **Universal Action**: Select an image file in Finder or Alfred and trigger `OCR Image to Markdown`.

## Text View Controls

- **In-place Editing**: You can freely edit and refine the OCR or translated Markdown text directly in Alfred before copying or pasting.
- `↩` (Enter): Copy edited Markdown text to clipboard.
- `⌘↩` (Cmd+Enter): Copy edited Markdown text and paste directly into the active frontmost app.
- `⇧↩` or `⌥↩` (Shift+Enter / Opt+Enter): Insert a new line while editing.
- `⎋` (Esc): Dismiss the Text View.
"""


def generate_plist() -> dict:
    objects = [
        {
            "config": {
                "argumenttype": 1,
                "keyword": "ocr",
                "subtext": "Extract text from clipboard image and display as Markdown (e.g. 'ocr', 'ocr fra', 'ocr nl en', 'ocr nl to en')",
                "text": "OCR Clipboard Image",
                "withspace": True,
            },
            "type": "alfred.workflow.input.keyword",
            "uid": UID_KEYWORD,
            "version": 1,
        },
        {
            "config": {
                "argumenttype": 0,
                "keyword": "ocrt",
                "subtext": "Extract text and translate via Argos Translate (requires source & target, e.g. 'ocrt nl en')",
                "text": "OCR & Translate Clipboard Image",
                "withspace": True,
            },
            "type": "alfred.workflow.input.keyword",
            "uid": UID_KEYWORD_TRANSLATE,
            "version": 1,
        },
        {
            "config": {
                "action": 0,
                "argument": 1,
                "focusedappvariable": False,
                "focusedappvariablename": "",
                "hotkey": 0,
                "hotmod": 0,
                "leftcursor": False,
                "modsmode": 0,
                "relatedAppsMode": 0,
            },
            "type": "alfred.workflow.trigger.hotkey",
            "uid": UID_HOTKEY,
            "version": 2,
        },
        {
            "config": {
                "acceptsfiles": True,
                "acceptsmulti": 0,
                "acceptstext": False,
                "acceptsurls": False,
                "name": "OCR Image to Markdown",
            },
            "type": "alfred.workflow.trigger.universalaction",
            "uid": UID_UNIV_ACTION,
            "version": 1,
        },
        {
            "config": {
                "concurrently": False,
                "escaping": 102,
                "script": SCRIPT_CODE,
                "scriptargtype": 1,
                "scriptfile": "",
                "type": 0,
            },
            "type": "alfred.workflow.action.script",
            "uid": UID_RUN_SCRIPT,
            "version": 2,
        },
        {
            "config": {
                "concurrently": False,
                "escaping": 102,
                "script": TRANSLATE_SCRIPT_CODE,
                "scriptargtype": 1,
                "scriptfile": "",
                "type": 0,
            },
            "type": "alfred.workflow.action.script",
            "uid": UID_RUN_SCRIPT_TRANSLATE,
            "version": 2,
        },
        {
            "config": {
                "behaviour": 1,
                "fontmode": 0,
                "fontsizing": 0,
                "footertext": "↩ Copy to Clipboard · ⌘↩ Paste to Active App · ⇧↩ New Line · ⎋ Close",
                "inputfile": "",
                "inputtype": 0,
                "loadingtext": "Processing image with OCR & Translation…",
                "outputmode": 0,
                "scriptinput": 0,
                "spellchecking": 0,
                "stackview": False,
            },
            "type": "alfred.workflow.userinterface.text",
            "uid": UID_TEXT_VIEW,
            "version": 1,
        },
        {
            "config": {
                "autopaste": False,
                "clipboardtext": "{query}",
                "ignoredynamicplaceholders": False,
                "transient": False,
            },
            "type": "alfred.workflow.output.clipboard",
            "uid": UID_CLIP_COPY,
            "version": 3,
        },
        {
            "config": {
                "autopaste": True,
                "clipboardtext": "{query}",
                "ignoredynamicplaceholders": False,
                "transient": False,
            },
            "type": "alfred.workflow.output.clipboard",
            "uid": UID_CLIP_PASTE,
            "version": 3,
        },
    ]

    connections = {
        UID_KEYWORD: [
            {
                "destinationuid": UID_RUN_SCRIPT,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": True,
            }
        ],
        UID_KEYWORD_TRANSLATE: [
            {
                "destinationuid": UID_RUN_SCRIPT_TRANSLATE,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": True,
            }
        ],
        UID_HOTKEY: [
            {
                "destinationuid": UID_RUN_SCRIPT,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": True,
            }
        ],
        UID_UNIV_ACTION: [
            {
                "destinationuid": UID_RUN_SCRIPT,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": True,
            }
        ],
        UID_RUN_SCRIPT: [
            {
                "destinationuid": UID_TEXT_VIEW,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": False,
            }
        ],
        UID_RUN_SCRIPT_TRANSLATE: [
            {
                "destinationuid": UID_TEXT_VIEW,
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": False,
            }
        ],
        UID_TEXT_VIEW: [
            {
                "destinationuid": UID_CLIP_COPY,
                "modifiers": 0,
                "modifiersubtext": "Copy to Clipboard",
                "vitoclose": True,
            },
            {
                "destinationuid": UID_CLIP_PASTE,
                "modifiers": 1048576,
                "modifiersubtext": "Paste to Active Application",
                "vitoclose": True,
            },
        ],
    }

    uidata = {
        UID_KEYWORD: {"xpos": 50, "ypos": 60},
        UID_KEYWORD_TRANSLATE: {"xpos": 50, "ypos": 180},
        UID_HOTKEY: {"xpos": 50, "ypos": 300},
        UID_UNIV_ACTION: {"xpos": 50, "ypos": 420},
        UID_RUN_SCRIPT: {"xpos": 280, "ypos": 120},
        UID_RUN_SCRIPT_TRANSLATE: {"xpos": 280, "ypos": 240},
        UID_TEXT_VIEW: {"xpos": 520, "ypos": 180},
        UID_CLIP_COPY: {"xpos": 760, "ypos": 120},
        UID_CLIP_PASTE: {"xpos": 760, "ypos": 260},
    }

    user_config = [
        {
            "config": {
                "default": "eng",
                "placeholder": "eng",
                "required": False,
                "trim": True,
            },
            "description": "Default source language for OCR recognition (e.g. eng, nld, fra, deu, spa).",
            "label": "Default OCR Language",
            "type": "textfield",
            "variable": "OCR_LANG",
        },
        {
            "config": {
                "default": "",
                "placeholder": "e.g. en, nl, fr, de, es (leave empty for no translation)",
                "required": False,
                "trim": True,
            },
            "description": "Default target language to translate OCR text into via Argos Translate.",
            "label": "Default Target Language",
            "type": "textfield",
            "variable": "TARGET_LANG",
        },
    ]

    plist_data = {
        "bundleid": "com.edo.ocr.clipboard.markdown",
        "category": "Tools",
        "connections": connections,
        "createdby": "Edo",
        "description": "Extract text from clipboard image or file, optionally translate, and display as Markdown in Alfred Text View.",
        "disabled": False,
        "name": "OCR Clipboard to Markdown",
        "objects": objects,
        "readme": README_TEXT,
        "uidata": uidata,
        "userconfigurationconfig": user_config,
        "version": "1.1.0",
        "webaddress": "https://github.com/edo/my_image_to_text",
    }

    return plist_data


def build() -> None:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    plist_path = WORKFLOW_DIR / "info.plist"
    plist_data = generate_plist()

    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)
    print(f"Generated {plist_path}")

    # Validate plist with plutil
    try:
        res = subprocess.run(["plutil", "-lint", str(plist_path)], capture_output=True, text=True)
        if res.returncode == 0:
            print("info.plist validation passed.")
        else:
            print(f"info.plist validation error: {res.stderr}")
    except Exception as e:
        print(f"Could not run plutil: {e}")

    # Build .alfredworkflow zip package
    files_to_pack = [
        "info.plist",
        "icon.png",
        "ocr_clipboard.py",
    ]

    with zipfile.ZipFile(OUTPUT_PACKAGE, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_pack:
            fpath = WORKFLOW_DIR / fname
            if fpath.exists():
                zf.write(fpath, arcname=fname)
                print(f"Added {fname} to workflow package.")

    print(f"Successfully built {OUTPUT_PACKAGE}")


if __name__ == "__main__":
    build()
