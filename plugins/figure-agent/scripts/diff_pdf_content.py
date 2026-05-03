#!/usr/bin/env python3
"""Compare two PDFs' qdf-expanded structure for equality (metadata stripped).

Expands both PDFs via `qpdf --qdf --object-streams=disable` and diffs the
full qdf blobs after stripping per-invocation metadata (CreationDate,
ModDate, /ID, /Producer, /Trapped). Note this covers the whole qdf —
page Contents streams, plus object dictionaries, stream length declarations,
xref table, and trailer — not just `/Contents` stream bodies. For PDFs that
share fonts, MediaBox, and Resources, equality of this blob is a robust
proxy for drawing-instruction equivalence; for PDFs that diverge in those
auxiliary structures, expect false positives that need structural
classification (see the BellCurve PR's plan §Task 7 for an example
classifier). Exits 0 if equal, 1 if different.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

_METADATA_PATTERNS = [
    re.compile(rb"^\s*/CreationDate.*$", re.MULTILINE),
    re.compile(rb"^\s*/ModDate.*$", re.MULTILINE),
    re.compile(rb"^\s*/ID\s*\[[^\]]*\]", re.MULTILINE),
    re.compile(rb"^\s*/Producer.*$", re.MULTILINE),
    re.compile(rb"^\s*/Trapped.*$", re.MULTILINE),
]


def expand_pdf(pdf: Path, out_dir: Path) -> bytes:
    """Run `qpdf --qdf --object-streams=disable` and return the qdf bytes."""
    out_dir.mkdir(parents=True, exist_ok=True)
    qdf = out_dir / (pdf.stem + ".qdf")
    subprocess.run(
        ["qpdf", "--qdf", "--object-streams=disable", str(pdf), str(qdf)],
        check=True,
    )
    return qdf.read_bytes()


def strip_metadata(blob: bytes) -> bytes:
    """Strip per-invocation metadata (timestamps, /ID, /Producer) from a qdf blob."""
    out = blob
    for pat in _METADATA_PATTERNS:
        out = pat.sub(b"", out)
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: diff_pdf_content.py OLD.pdf NEW.pdf", file=sys.stderr)
        return 2
    old, new = Path(sys.argv[1]), Path(sys.argv[2])
    if not old.is_file() or not new.is_file():
        print(f"missing input: old={old.is_file()} new={new.is_file()}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory() as tmp_root:
        tmp = Path(tmp_root)
        old_blob = strip_metadata(expand_pdf(old, tmp / "old"))
        new_blob = strip_metadata(expand_pdf(new, tmp / "new"))
    if old_blob == new_blob:
        print(f"OK: byte-identical qdf-expanded structure ({old.name} vs {new.name})")
        return 0
    for offset, (a_byte, b_byte) in enumerate(zip(old_blob, new_blob)):
        if a_byte != b_byte:
            print(
                f"DIFFER at byte {offset}: old={a_byte:#04x} new={b_byte:#04x}",
                file=sys.stderr,
            )
            break
    if len(old_blob) != len(new_blob):
        print(
            f"DIFFER: lengths old={len(old_blob)} new={len(new_blob)}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
