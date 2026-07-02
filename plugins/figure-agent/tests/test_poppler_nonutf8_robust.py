"""Poppler-capture decode robustness on custom-font (non-UTF8) PDFs.

A custom-font PDF makes pdftotext emit glyph bytes that are not valid UTF-8,
both in the -bbox HTML it writes and (via font warnings) on poppler stderr.
The report-only collision/clash checkers must degrade gracefully instead of
raising UnicodeDecodeError — otherwise a never-fail enrichment step aborts a
successful compile and the ERR trap deletes the good PDF/PNG.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_collisions  # noqa: E402
import check_golden_artifacts  # noqa: E402
import check_visual_clash  # noqa: E402
import ocr  # noqa: E402

# Valid <word>/<page> markup plus a stray non-UTF8 glyph byte (0xff) in the
# rendered text, mimicking pdftotext output for a custom-font PDF.
NONUTF8_BBOX_HTML = (
    b'<?xml version="1.0"?>\n'
    b"<html><body>\n"
    b'<page width="200.0" height="200.0">\n'
    b'<word xMin="10.0" yMin="20.0" xMax="40.0" yMax="30.0">poly\xffmer</word>\n'
    b"</page>\n"
    b"</body></html>\n"
)
EMPTY_PAGE_BBOX_HTML = (
    b'<?xml version="1.0"?>\n'
    b"<html><body>\n"
    b'<page width="200.0" height="200.0">\n'
    b"</page>\n"
    b"</body></html>\n"
)


def _fake_pdftotext(html_bytes: bytes):
    """Return a subprocess.run stand-in that writes non-UTF8 HTML + stderr."""

    def _run(args, *_pos, **_kw):
        out_path = Path(args[-1])
        out_path.write_bytes(html_bytes)
        # poppler font warnings can also carry non-UTF8 bytes on stderr.
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="warn \udcff")

    return _run


def test_check_collisions_extract_tolerates_nonutf8(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(subprocess, "run", _fake_pdftotext(NONUTF8_BBOX_HTML))

    words = check_collisions.extract_word_bboxes(pdf)

    assert len(words) == 1
    assert words[0]["xmin"] == 10.0


def test_check_visual_clash_extract_tolerates_nonutf8(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(subprocess, "run", _fake_pdftotext(NONUTF8_BBOX_HTML))

    words, page_size = check_visual_clash.extract_pdf_words_and_page(pdf)

    assert page_size == (200.0, 200.0)
    assert len(words) == 1
    assert words[0]["xmin"] == 10.0


def test_check_collisions_extract_allows_empty_nontrivial_pdf(
    monkeypatch,
    tmp_path,
) -> None:
    pdf = tmp_path / "empty_words.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + (b"0" * 2048))
    monkeypatch.setattr(subprocess, "run", _fake_pdftotext(EMPTY_PAGE_BBOX_HTML))

    assert check_collisions.extract_word_bboxes(pdf) == []


def test_check_visual_clash_extract_allows_empty_nontrivial_pdf(
    monkeypatch,
    tmp_path,
) -> None:
    pdf = tmp_path / "empty_words.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + (b"0" * 2048))
    monkeypatch.setattr(subprocess, "run", _fake_pdftotext(EMPTY_PAGE_BBOX_HTML))

    assert check_visual_clash.extract_pdf_words_and_page(pdf) == ([], (200.0, 200.0))


def _passthrough_to_nonutf8_stderr_child(monkeypatch) -> None:
    """Redirect subprocess.run to a real child that fails with non-UTF8 stderr.

    The real subprocess.run performs the text=True decode; **kw passthrough
    means the caller's errors= (or its absence) flows into that decode. Without
    errors="replace" this raises UnicodeDecodeError before the returncode guard;
    with it, the call reaches the returncode check and the RuntimeError path.
    """
    real_run = subprocess.run
    child = [
        sys.executable,
        "-c",
        "import os,sys; os.write(2, b'\\xff\\xfe warn'); sys.exit(1)",
    ]

    def _run(_args, *_pos, **kwargs):
        return real_run(child, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)


def test_check_collisions_extract_tolerates_nonutf8_stderr(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    with pytest.raises(RuntimeError):
        check_collisions.extract_word_bboxes(pdf)


def test_check_visual_clash_extract_tolerates_nonutf8_stderr(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    with pytest.raises(RuntimeError):
        check_visual_clash.extract_pdf_words_and_page(pdf)


def test_render_pdf_first_page_tolerates_nonutf8_stderr(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    with pytest.raises(RuntimeError):
        check_visual_clash.render_pdf_first_page(pdf, dpi=72)


def test_extract_pdf_text_tolerates_nonutf8_stderr(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "custom_font.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    with pytest.raises(RuntimeError):
        check_golden_artifacts.extract_pdf_text(pdf)


def test_ocr_pass_tolerates_nonutf8_stderr(monkeypatch, tmp_path) -> None:
    reference = tmp_path / "ref.png"
    reference.write_bytes(b"")
    _passthrough_to_nonutf8_stderr_child(monkeypatch)

    with pytest.raises(RuntimeError):
        ocr._run_ocr_at_scale(reference, 1.0, ocr.DEFAULT_OCR_CONFIDENCE_FLOOR)
