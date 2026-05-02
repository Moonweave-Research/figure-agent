#!/usr/bin/env python3
"""Compare two PDFs' content streams for byte-equality.

Expands both PDFs via `qpdf --qdf --object-streams=disable`, strips
metadata (creation/mod dates, /ID, /Producer, /Trapped), and diffs
the remainder. Exits 0 if equal, 1 if different. Used to verify that
the BellCurve macro refactor preserves drawing instructions byte-for-byte.
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


def _expand(pdf: Path, out_dir: Path) -> bytes:
    out_dir.mkdir(parents=True, exist_ok=True)
    qdf = out_dir / (pdf.stem + ".qdf")
    subprocess.run(
        ["qpdf", "--qdf", "--object-streams=disable", str(pdf), str(qdf)],
        check=True,
    )
    return qdf.read_bytes()


def _strip_metadata(blob: bytes) -> bytes:
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
        old_blob = _strip_metadata(_expand(old, tmp / "old"))
        new_blob = _strip_metadata(_expand(new, tmp / "new"))
    if old_blob == new_blob:
        print(f"OK: byte-identical content streams ({old.name} vs {new.name})")
        return 0
    for offset, (a_byte, b_byte) in enumerate(zip(old_blob, new_blob)):
        if a_byte != b_byte:
            print(
                f"DIFFER at byte {offset}: old={a_byte:#04x} new={b_byte:#04x}",
                file=sys.stderr,
            )
            break
    print(
        f"DIFFER: lengths old={len(old_blob)} new={len(new_blob)}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
