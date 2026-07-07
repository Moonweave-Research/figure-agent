"""Shared PDF page-geometry and panel-crop helpers.

Callers pass their own ``error_cls`` so module-specific error types survive while the
pdfplumber page-size read and the bbox-to-pixel crop math live in one place.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


class PdfGeometryError(Exception):
    """Default error type when a caller does not supply its own."""


def pdf_page_size_cm(
    pdf_path: Path,
    *,
    error_cls: type[Exception] = PdfGeometryError,
) -> tuple[float, float]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise error_cls("pdfplumber required for panel bbox cropping") from exc
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise error_cls(f"empty PDF: {pdf_path}")
        page = pdf.pages[0]
        return float(page.width) * 2.54 / 72.0, float(page.height) * 2.54 / 72.0


def crop_panel_png(
    *,
    png_path: Path,
    bbox_pdf_cm: list[float],
    output_path: Path,
    page_width_cm: float,
    page_height_cm: float,
    error_cls: type[Exception] = PdfGeometryError,
) -> None:
    x0, y0, x1, y1 = bbox_pdf_cm
    if x1 <= x0 or y1 <= y0:
        raise error_cls("bbox_pdf_cm must satisfy x1>x0 and y1>y0")
    if x0 < 0 or y0 < 0 or x1 > page_width_cm or y1 > page_height_cm:
        raise error_cls(
            f"bbox_pdf_cm outside PDF page bounds [0, 0, {page_width_cm:.3f}, {page_height_cm:.3f}]"
        )
    with Image.open(png_path) as image:
        width_px, height_px = image.size
        crop_box = (
            round(x0 / page_width_cm * width_px),
            round(y0 / page_height_cm * height_px),
            round(x1 / page_width_cm * width_px),
            round(y1 / page_height_cm * height_px),
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop(crop_box).save(output_path)
