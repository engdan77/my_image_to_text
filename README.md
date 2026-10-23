# My Image To Text

A high-performance CLI application and optional Alfred 5 workflow that extracts text from images (including multi-page TIFF, PNG, JPEG) or system clipboard images, formats the output as clean Markdown on standard output, and optionally translates it into target languages using offline machine translation ([Argos Translate](https://github.com/argosopentech/argos-translate)).

```
> [!NOTE]  
> This project was developed with help from AI (Gemini 3.7 Flash)
```

## Features

- **CLI Interface**: Built with [Cyclopts](https://github.com/BrianPugh/cyclopts) for an intuitive, modern command-line experience.
- **OCR Engine**: Powered by [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via `pytesseract` and Pillow.
- **Offline Machine Translation**: Integrated with [Argos Translate](https://github.com/argosopentech/argos-translate) for private, offline language translation (e.g., Dutch to English, French to English, Spanish to German).
- **Multi-page TIFF Support**: Seamlessly parses multi-page TIFF documents with automatic or customizable page headers (`# Page 1`, `# Page 2`, etc.).
- **Clipboard Integration**: Extract and translate text directly from macOS/system clipboard image data or copied image files.
- **Optional Alfred 5 Workflow**: Native macOS workflow rendering Markdown previews inside an editable **Text View** widget with instant copy and paste shortcuts.

## Prerequisites

Make sure `tesseract` is installed on your system:

- **macOS**: `brew install tesseract` (and optionally `brew install tesseract-lang` for multi-language OCR models)
- **Ubuntu/Debian**: `sudo apt install tesseract-ocr`

## Installation

### As a standalone CLI tool via `uv` (Recommended)

Install directly into an isolated environment as a globally available tool:

```bash
# Install from the project directory
uv tool install .

# Or install in editable mode for local development
uv tool install --editable .
```

After installation, `my-image-to-text` and `image-to-text` are immediately available in your `PATH`:

```bash
my-image-to-text path/to/document.tiff
```

You can also run it ephemerally without permanent installation:

```bash
uvx --from . my-image-to-text path/to/document.tiff
```

### In a virtual environment

```bash
uv pip install -e .
```

## CLI Usage

### 1. Basic File Processing

Process any image (single-page or multi-page TIFF, PNG, JPEG) and output Markdown to stdout:

```bash
my-image-to-text path/to/document.tiff
```

To save the Markdown output to a file:

```bash
my-image-to-text path/to/document.tiff > output.md
```

### 2. Language & Translation Options

- **Specify OCR language** with `--lang` (or `-l`):
  ```bash
  # Perform OCR using Dutch language recognition
  my-image-to-text path/to/dutch_document.tiff --lang dutch
  # Or use standard ISO codes
  my-image-to-text path/to/dutch_document.tiff -l nld
  ```

- **Translate OCR text** with `--target-lang` (or `-t` / `--to-lang`):
  ```bash
  # Extract text in Dutch and translate into English
  my-image-to-text path/to/dutch_document.tiff --lang dutch --target-lang english
  
  # Short flags
  my-image-to-text path/to/image.tiff -l nl -t en
  
  # Translate French menu into German
  my-image-to-text path/to/french_menu.png --lang fra --target-lang deu
  ```
  *Note: Argos Translate models are downloaded and cached automatically on first use.*

### 3. Clipboard Extraction

Extract text from whatever image (screenshot or copied image) is currently in your system clipboard without specifying a file path:

```bash
my-image-to-text --clipboard
# or
my-image-to-text -c
```

Translate clipboard image directly:

```bash
# Extract clipboard image and translate Dutch to English
my-image-to-text -c --lang dutch --target-lang english

# Extract clipboard image and translate to Spanish
my-image-to-text -c --target-lang spanish
```

### 4. Page Headers Control

Customize whether multi-page TIFF documents include markdown section headers (`# Page 1`, `# Page 2`, etc.):

```bash
my-image-to-text path/to/document.tiff --page-headers
my-image-to-text path/to/document.tiff --no-page-headers
```

## CLI Help & Reference

To display all available flags, options, and commands directly in your terminal, run:

```bash
my-image-to-text --help
# or
my-image-to-text -h
```

### Options Summary

| Parameter / Flag | Short Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| `PATH` / `--path` | | *None* | Path to the image file (e.g. TIFF, PNG, JPEG) to process. If omitted, extracts from clipboard. |
| `--lang` | `-l` | `eng` | Language for OCR recognition (e.g., `eng`, `nld`, `dutch`, `fra`). |
| `--target-lang` / `--to-lang` | `-t` | *None* | Target language to translate OCR text into via Argos Translate (e.g., `en`, `english`, `de`). |
| `--clipboard` / `--no-clipboard` | `-c` | `False` | Extract text from image currently in clipboard. |
| `--page-headers` / `--no-page-headers` | | `True` (multi-page) | Explicitly include or omit `# Page N` headers for multi-page documents. |
| `--version` | | | Display application version and exit. |
| `--help` | `-h` | | Display CLI help menu and command options. |

---

## Optional: Alfred 5 Workflow (macOS)

For macOS users using [Alfred 5](https://www.alfredapp.com/), an optional Alfred Workflow (`OCR-Clipboard-to-Markdown.alfredworkflow`) is included. It provides seamless keyboard triggers to OCR clipboard images and presents the rendered Markdown in an editable Alfred **Text View** widget.

> **Note:** The Alfred Workflow is completely optional. The CLI tool functions independently in any terminal or script environment.

### Workflow Installation

1. Ensure the CLI tool is installed:
   ```bash
   uv tool install .
   ```
2. Import the workflow into Alfred by double-clicking `OCR-Clipboard-to-Markdown.alfredworkflow` in the project root, or running:
   ```bash
   ./alfred/install.sh
   ```
3. Click **Import** in Alfred.

### Workflow Triggers & Keywords

- **`ocr` Keyword** (OCR Clipboard with optional translation):
  - `ocr`: OCR clipboard image into Markdown.
  - `ocr fra`: OCR with French recognition.
  - `ocr nl en` / `ocr nld eng`: OCR Dutch image and translate to English Markdown.
  - `ocr dutch to english`: Natural language source-to-target translation syntax.
  - `ocr to fr`: Translate default OCR text to French.
- **`ocrt` Keyword** (Dedicated OCR & Translation trigger - requires languages):
  - `ocrt nl en`: OCR Dutch clipboard and translate into English (source and target languages required).
  - `ocrt dutch to english`: Specify full language names for translation.
- **Hotkey Trigger**: Configure a global shortcut (e.g., `⌥⇧O`) in Alfred Workflow settings to process clipboard images instantly.
- **Universal Action**: Select any image file in Finder or Alfred and trigger **OCR Image to Markdown**.

### Alfred Text View Controls

- **In-place Editing**: Review and edit the extracted Markdown text directly within Alfred before copying or pasting.
- `↩` (Enter): Copy edited Markdown text to clipboard.
- `⌘↩` (Cmd+Enter): Paste edited Markdown text directly into the frontmost app.
- `⇧↩` or `⌥↩` (Shift+Enter / Opt+Enter): Insert a newline while editing.
- `⎋` (Esc): Dismiss preview.
