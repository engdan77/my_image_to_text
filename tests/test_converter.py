from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytest

from my_image_to_text.converter import (
    clean_markdown_text,
    clipboard_to_markdown,
    get_clipboard_image,
    image_to_markdown,
    normalize_language,
    process_image,
)


def create_sample_image(text: str) -> Image.Image:
    """Helper to create a simple grayscale PIL image with rendered text."""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    # Use default font or simple drawing
    draw.text((20, 30), text, fill="black")
    return img


def create_test_tiff(tmp_path: Path, pages: list[str]) -> Path:
    """Helper to create a single or multi-page TIFF file."""
    images = [create_sample_image(text) for text in pages]
    tiff_path = tmp_path / "test_document.tiff"
    if len(images) == 1:
        images[0].save(tiff_path, format="TIFF")
    else:
        images[0].save(
            tiff_path,
            format="TIFF",
            save_all=True,
            append_images=images[1:],
        )
    return tiff_path


def test_normalize_language():
    assert normalize_language(None) == "eng"
    assert normalize_language("") == "eng"
    assert normalize_language("english") == "eng"
    assert normalize_language("English") == "eng"
    assert normalize_language("eng") == "eng"
    assert normalize_language("fra") == "fra"
    assert normalize_language("french") == "fra"
    assert normalize_language("deu") == "deu"
    assert normalize_language("dutch") == "nld"
    assert normalize_language("nld") == "nld"
    assert normalize_language("nl") == "nld"
    assert normalize_language("custom_lang") == "custom_lang"


def test_clean_markdown_text():
    raw = "   \n\nHello World   \nSecond Line  \n\n\n"
    expected = "Hello World\nSecond Line"
    assert clean_markdown_text(raw) == expected


def test_process_single_page_tiff(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path, ["Single Page Content"])
    pages = process_image(tiff_path, lang="eng")
    assert len(pages) == 1
    assert "Single" in pages[0] or "Page" in pages[0] or "Content" in pages[0]


def test_process_multi_page_tiff(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path, ["First Page", "Second Page"])
    pages = process_image(tiff_path, lang="eng")
    assert len(pages) == 2


def test_image_to_markdown_single_page(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path, ["Simple Header\nSome details here"])
    markdown = image_to_markdown(tiff_path, lang="eng")
    # For single page, by default no '# Page 1' header is added
    assert "# Page 1" not in markdown
    assert len(markdown) > 0


def test_image_to_markdown_multi_page(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path, ["Page One Text", "Page Two Text"])
    markdown = image_to_markdown(tiff_path, lang="eng")
    assert "# Page 1" in markdown
    assert "# Page 2" in markdown
    assert "---" in markdown


def test_image_to_markdown_explicit_headers(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path, ["Page One Text"])
    markdown_with_header = image_to_markdown(tiff_path, lang="eng", include_page_headers=True)
    assert "# Page 1" in markdown_with_header

    sub_dir = tmp_path / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)
    multi_tiff = create_test_tiff(sub_dir, ["Page One", "Page Two"])
    markdown_without_header = image_to_markdown(multi_tiff, lang="eng", include_page_headers=False)
    assert "# Page 1" not in markdown_without_header


def test_process_image_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        process_image("non_existent_file.tiff")


def test_process_image_pil_object():
    img = create_sample_image("In Memory PIL Image")
    pages = process_image(img, lang="eng")
    assert len(pages) == 1
    assert "Memory" in pages[0] or "Image" in pages[0] or "PIL" in pages[0]


def test_clipboard_to_markdown_success(monkeypatch: pytest.MonkeyPatch):
    sample_img = create_sample_image("Clipboard Content")
    monkeypatch.setattr("my_image_to_text.converter.get_clipboard_image", lambda: sample_img)
    
    result = clipboard_to_markdown(lang="eng")
    assert "Clipboard" in result or "Content" in result


def test_clipboard_to_markdown_empty_clipboard(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("my_image_to_text.converter.get_clipboard_image", lambda: None)
    
    with pytest.raises(ValueError, match="No image found in clipboard"):
        clipboard_to_markdown()


def test_image_to_markdown_with_target_lang(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    tiff_path = create_test_tiff(tmp_path, ["Bonjour le monde"])
    monkeypatch.setattr(
        "my_image_to_text.converter.translate_text",
        lambda text, from_lang, to_lang: f"[{from_lang}->{to_lang}] {text}",
    )
    
    markdown = image_to_markdown(tiff_path, lang="french", target_lang="english")
    assert "[french->english]" in markdown


def test_clipboard_to_markdown_with_target_lang(monkeypatch: pytest.MonkeyPatch):
    sample_img = create_sample_image("Bonjour")
    monkeypatch.setattr("my_image_to_text.converter.get_clipboard_image", lambda: sample_img)
    monkeypatch.setattr(
        "my_image_to_text.converter.translate_text",
        lambda text, from_lang, to_lang: f"TRANSLATED({text}, {to_lang})",
    )
    
    result = clipboard_to_markdown(lang="french", target_lang="english")
    assert "TRANSLATED(" in result
    assert "english" in result
