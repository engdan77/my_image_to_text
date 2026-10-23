from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated
from cyclopts import App, Parameter

from my_image_to_text.converter import clipboard_to_markdown, image_to_markdown

app = App(
    name="my-image-to-text",
    help="CLI app to process images (primarily TIFF files or clipboard) and output OCR text formatted as Markdown.",
)


@app.default
def main(
    path: Annotated[
        Path | None,
        Parameter(
            show_default=False,
            help="Path to the image file (e.g. TIFF) to process. If omitted, extracts image from clipboard.",
        ),
    ] = None,
    lang: Annotated[
        str,
        Parameter(
            name=["--lang", "-l"],
            help="Language for OCR processing (default: 'eng').",
        ),
    ] = "eng",
    target_lang: Annotated[
        str | None,
        Parameter(
            name=["--target-lang", "--to-lang", "-t"],
            help="Optional target language to translate OCR text into via Argos Translate (e.g. 'eng', 'en', 'french').",
        ),
    ] = None,
    page_headers: Annotated[
        bool | None,
        Parameter(
            name=["--page-headers"],
            help="Include page headers (# Page N). By default, included for multi-page images.",
        ),
    ] = None,
    clipboard: Annotated[
        bool,
        Parameter(
            name=["--clipboard", "-c"],
            help="Extract text from the image currently in clipboard.",
        ),
    ] = False,
) -> None:
    """Extract text from an image (or clipboard) and print Markdown to stdout."""
    try:
        if path is not None and not clipboard:
            markdown_text = image_to_markdown(
                image_input=path,
                lang=lang,
                target_lang=target_lang,
                include_page_headers=page_headers,
            )
        else:
            markdown_text = clipboard_to_markdown(
                lang=lang,
                target_lang=target_lang,
                include_page_headers=page_headers,
            )

        if markdown_text:
            print(markdown_text)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing image: {e}", file=sys.stderr)
        sys.exit(1)


def run() -> None:
    """Entry point for CLI script execution."""
    app()


if __name__ == "__main__":
    run()
