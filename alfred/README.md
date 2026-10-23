# Alfred Workflow: OCR Clipboard to Markdown & Translation

An Alfred 5 Workflow that extracts OCR text from your macOS clipboard (images, screenshots, copied image files) or selected files, optionally translates the extracted text into your target language using **Argos Translate**, and displays rendered Markdown directly in Alfred's native **Text View** widget.

## Features

- **Clipboard Image OCR**: Automatically extracts text from screenshots (e.g. `⌘⇧⌃4`), copied images, or multi-page TIFF/PNG/JPEG files.
- **Offline Machine Translation**: Integrated with [Argos Translate](https://github.com/argosopentech/argos-translate) to translate OCR text into target languages (e.g. Dutch to English, French to English).
- **Alfred 5 Text View Widget**: Displays editable Markdown text in Alfred's native text view for quick inspection and corrections before copying.
- **Keyboard Actions**:
  - `↩` (Enter): Copy edited Markdown text to clipboard.
  - `⌘↩` (Cmd+Enter): Copy edited Markdown and paste directly into the active frontmost application.
  - `⇧↩` or `⌥↩` (Shift+Enter / Opt+Enter): Insert a newline while editing.
  - `⎋` (Esc): Dismiss the Text View.
- **Flexible Triggers & Keywords**:
  - **`ocr` Keyword**:
    - `ocr`: OCR clipboard image into Markdown.
    - `ocr fra`: OCR with French language model.
    - `ocr nl en` / `ocr nld eng`: OCR Dutch image and translate into English.
    - `ocr dutch to english`: Natural language source and target translation syntax.
    - `ocr to fr`: Translate to French.
  - **`ocrt` Keyword** (Dedicated Translation Trigger - languages required):
    - `ocrt nl en`: OCR Dutch clipboard and translate into English.
    - `ocrt dutch to english`: Specify full language names for translation.
  - **Hotkey Trigger**: Assign a custom keyboard shortcut (e.g., `⌥⇧O`) to immediately OCR clipboard images.
  - **Universal Action**: Select any image file in Finder or Alfred and choose **OCR Image to Markdown**.
- **User Configuration in Alfred 5**:
  - Configure `Default OCR Language` (default: `eng`) and `Default Target Language` in Alfred's workflow configuration panel.

## Installation

1. Ensure prerequisites are installed:
   ```bash
   # Install Tesseract OCR
   brew install tesseract

   # Install the CLI tool
   uv tool install .
   ```

2. Double-click `OCR-Clipboard-to-Markdown.alfredworkflow` in the repository root, or run:
   ```bash
   ./alfred/install.sh
   ```

3. Click **Import** when Alfred prompts you.
