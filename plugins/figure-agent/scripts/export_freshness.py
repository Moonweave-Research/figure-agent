"""Compute exports/ sub-state for a figure-agent fixture.

Sub-states map to the spec's behavior matrix:
- MISSING        — exports/<name>.pdf does not exist.
- TRACKED_GOLDEN — exports/<name>.pdf is git-tracked. Skip auto-rebuild.
- STALE          — exports/<name>.pdf differs from build/<name>.pdf by content hash.
- FRESH          — exports/<name>.pdf matches build/<name>.pdf by content hash.

Content hash uses the same metadata-strip pipeline as scripts/diff_pdf_content.py
(qpdf --qdf, then drop /CreationDate, /ModDate, /ID, /Producer, /Trapped).
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from diff_pdf_content import expand_pdf, strip_metadata  # noqa: E402
from git_tracked import is_tracked  # noqa: E402

EXPORT_MISSING = "MISSING"
EXPORT_TRACKED_GOLDEN = "TRACKED_GOLDEN"
EXPORT_STALE = "STALE"
EXPORT_FRESH = "FRESH"

REPO_ROOT = Path(__file__).resolve().parents[1]


def compute_pdf_content_hash(pdf_path: Path) -> bytes:
    """SHA-256 of the metadata-stripped qdf-expansion of `pdf_path`."""
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        blob = strip_metadata(expand_pdf(pdf_path, tmp))
    return hashlib.sha256(blob).digest()


def compute_export_state(example_dir: Path, name: str) -> str:
    """Return one of MISSING | TRACKED_GOLDEN | STALE | FRESH."""
    exports_pdf = example_dir / "exports" / f"{name}.pdf"
    build_pdf = example_dir / "build" / f"{name}.pdf"

    if not exports_pdf.is_file():
        return EXPORT_MISSING
    if is_tracked(exports_pdf, REPO_ROOT):
        return EXPORT_TRACKED_GOLDEN

    # All four artifacts must be present; any missing sibling → STALE
    exports_dir = example_dir / "exports"
    tif_present = (exports_dir / f"{name}.tif").is_file() or (
        exports_dir / f"{name}.tiff"
    ).is_file()
    if not (
        (exports_dir / f"{name}.svg").is_file()
        and tif_present
        and (exports_dir / f"{name}.png").is_file()
    ):
        return EXPORT_STALE

    if not build_pdf.is_file():
        return EXPORT_STALE  # exports exist but build/ is gone — treat as stale
    try:
        exports_hash = compute_pdf_content_hash(exports_pdf)
        build_hash = compute_pdf_content_hash(build_pdf)
    except (subprocess.CalledProcessError, OSError):
        # A PDF qpdf cannot expand (corrupt/truncated) cannot be content-FRESH;
        # STALE routes the operator to regenerate.
        return EXPORT_STALE
    if exports_hash == build_hash:
        return EXPORT_FRESH
    return EXPORT_STALE
