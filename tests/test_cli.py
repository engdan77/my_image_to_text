from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw
import pytest

from my_image_to_text.cli import app


def create_test_tiff(path: Path, pages: list[str]) -> Path:
    images = []
    for text in pages:
        img = Image.new("RGB", (300, 80), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 25), text, fill="black")
        images.append(img)

    if len(images) == 1:
        images[0].save(path, format="TIFF")
    else:
        images[0].save(path, format="TIFF", save_all=True, append_images=images[1:])
    return path


def test_cli_execution_via_app(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    tiff_path = create_test_tiff(tmp_path / "doc.tiff", ["Hello OCR World"])
    
    app([str(tiff_path)], result_action="return_value")
    
    captured = capsys.readouterr()
    assert "Hello" in captured.out or "OCR" in captured.out or "World" in captured.out


def test_cli_execution_with_lang_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    tiff_path = create_test_tiff(tmp_path / "doc.tiff", ["Bonjour"])
    
    app([str(tiff_path), "--lang", "eng"], result_action="return_value")
    
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0


def test_cli_execution_multi_page(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    tiff_path = create_test_tiff(tmp_path / "multi.tiff", ["Page 1 Content", "Page 2 Content"])
    
    app([str(tiff_path)], result_action="return_value")
    
    captured = capsys.readouterr()
    assert "# Page 1" in captured.out
    assert "# Page 2" in captured.out


def test_cli_execution_page_headers_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    tiff_path = create_test_tiff(tmp_path / "single.tiff", ["Single Page Flag Test"])
    
    app([str(tiff_path), "--page-headers"], result_action="return_value")
    captured = capsys.readouterr()
    assert "# Page 1" in captured.out

    multi_path = create_test_tiff(tmp_path / "multi_no_headers.tiff", ["P1", "P2"])
    app([str(multi_path), "--no-page-headers"], result_action="return_value")
    captured_no_headers = capsys.readouterr()
    assert "# Page 1" not in captured_no_headers.out


def test_cli_png_image(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    png_path = tmp_path / "sample.png"
    img = Image.new("RGB", (300, 80), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 25), "PNG Test", fill="black")
    img.save(png_path, format="PNG")

    app([str(png_path)], result_action="return_value")
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0


def test_cli_nonexistent_file(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc_info:
        app(["non_existent_image.tiff"])
    
    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "Error:" in captured.err


def test_cli_subprocess(tmp_path: Path):
    tiff_path = create_test_tiff(tmp_path / "sub_test.tiff", ["Test Subprocess CLI"])
    result = subprocess.run(
        [sys.executable, "-m", "my_image_to_text.cli", str(tiff_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert len(result.stdout.strip()) > 0


def test_cli_clipboard_flag(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    img = Image.new("RGB", (300, 80), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 25), "Clipboard OCR Text", fill="black")
    monkeypatch.setattr("my_image_to_text.cli.clipboard_to_markdown", lambda **kwargs: "Clipboard OCR Text")

    app(["--clipboard"], result_action="return_value")
    captured = capsys.readouterr()
    assert "Clipboard OCR Text" in captured.out


def test_cli_clipboard_empty_error(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    def raise_value_error(**kwargs):
        raise ValueError("No image found in clipboard.")

    monkeypatch.setattr("my_image_to_text.cli.clipboard_to_markdown", raise_value_error)

    with pytest.raises(SystemExit) as exc_info:
        app(["--clipboard"])

    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "Error: No image found in clipboard." in captured.err


def test_cli_target_lang_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    tiff_path = create_test_tiff(tmp_path / "doc.tiff", ["Bonjour"])
    monkeypatch.setattr(
        "my_image_to_text.cli.image_to_markdown",
        lambda **kwargs: f"TRANSLATED TO {kwargs.get('target_lang')}",
    )

    app([str(tiff_path), "--target-lang", "english"], result_action="return_value")
    captured = capsys.readouterr()
    assert "TRANSLATED TO english" in captured.out

    app([str(tiff_path), "-t", "es"], result_action="return_value")
    captured_short = capsys.readouterr()
    assert "TRANSLATED TO es" in captured_short.out


def test_cli_clipboard_with_target_lang(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(
        "my_image_to_text.cli.clipboard_to_markdown",
        lambda **kwargs: f"CLIPBOARD TO {kwargs.get('target_lang')} (from {kwargs.get('lang')})",
    )

    app(["--clipboard", "--lang", "dutch", "-t", "english"], result_action="return_value")
    captured = capsys.readouterr()
    assert "CLIPBOARD TO english (from dutch)" in captured.out
