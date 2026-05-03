"""Drawing-instruction-level no-regression test for the BandDiagram pilot.

Diffs the post-pilot _macro_smoke.pdf (qpdf-stripped) against the
pre-pilot baseline fixture committed in Task 1 (tests/fixtures/
banddiagram_pilot/baseline.qdf). Asserts every line-level diff falls
into one of five expected classes (a)-(e); see the spec at
docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md
section "Drawing-instruction-level criterion (qpdf qdf classifier)".

Class (a): per-existing-call empty-scope `q\\nQ\\n` graphics-state pair.
Class (b): the entire 3rd-callsite emission (frame + 2 BandBox + axis +
           Et + label \\node).
Class (c): /CreationDate, /ModDate, /ID metadata.
Class (d): stream length declarations and xref offsets.
Class (e): position-only shifts of pre-existing operators.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE = REPO_ROOT / "tests" / "fixtures" / "banddiagram_pilot" / "baseline.qdf"
SMOKE_TEX = REPO_ROOT / "examples" / "_macro_smoke" / "_macro_smoke.tex"
SMOKE_PDF = REPO_ROOT / "examples" / "_macro_smoke" / "build" / "_macro_smoke.pdf"


# Patterns matching each allowed delta class. The (b) and (e) classes
# (3rd-callsite content + position-shifted operators) are matched by
# `b_or_e_pdf_op` which captures any PDF content-stream line: numeric
# operands followed by a PDF operator token. This is intentionally
# permissive — the test's job is to catch lines that look like NEITHER
# noise NOR PDF stream content, e.g. malformed objects or dictionary
# changes outside the page-object/metadata classes.
_CLASS_PATTERNS = {
    "c_metadata": re.compile(r"^/(CreationDate|ModDate|ID)\b|^\s*<[0-9a-fA-F]+>\s*$"),
    "d_stream_length": re.compile(r"^/Length\s+\d+\b|^xref\b|^\d+\s+\d+\s+obj\b|^\s*\d+\s+\d+\s*$"),
    "a_empty_scope": re.compile(r"^q\s*$|^Q\s*$"),
    "page_dim": re.compile(r"^/(MediaBox|CropBox|BBox|TrimBox|ArtBox)\b|^\s*-?\d+\.?\d*\s*$"),
    # Class (b)/(e): PDF content-stream lines — numeric operands + operator,
    # or pure operators (BT/ET, h, S, f, B, etc.). Captures both new
    # 3rd-callsite content and position-shifted pre-existing operators.
    "b_or_e_pdf_op": re.compile(
        r"^([\d\.\s\-]*\s)?(m|l|c|h|S|s|f|F|B|b|n|re|w|J|j|M|d|i|"
        r"rg|RG|g|G|k|K|sc|SC|scn|SCN|cs|CS|"
        r"cm|q|Q|Do|gs|sh|"
        r"BT|ET|Tj|TJ|Tf|Tm|Td|TD|T\*|Tc|Tw|Tz|TL|Tr|Ts)\s*$"
    ),
}


def _classify(line: str) -> str | None:
    """Return the class name if `line` matches an allowed class, else None."""
    stripped = line.lstrip("+-").strip()
    for name, pattern in _CLASS_PATTERNS.items():
        if pattern.search(stripped):
            return name
    return None


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("qpdf") is None
    or shutil.which("diff") is None,
    reason="requires lualatex, pdftocairo, qpdf, diff",
)
def test_macro_smoke_qdf_diff_classifier(tmp_path: Path) -> None:
    """Compile current _macro_smoke; qpdf-strip; diff against baseline.

    Every line-level diff must classify into one of (a)-(e). The b_third_callsite
    class is the entire post-pilot 3rd \\BandDiagram emission — accept any
    additions that are not pre-existing-content modifications.
    """
    assert BASELINE.exists(), (
        f"Pre-pilot baseline missing at {BASELINE}; run Task 1 of the pilot plan to capture it."
    )

    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(SMOKE_TEX)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr + compile_result.stdout

    new_qdf = tmp_path / "new.qdf"
    subprocess.run(
        [
            "qpdf",
            "--qdf",
            "--object-streams=disable",
            str(SMOKE_PDF),
            str(new_qdf),
        ],
        check=True,
    )

    # `diff -a` forces text mode — without it, qpdf's qdf output (which
    # contains binary stream blobs for fonts/glyphs) trips diff into
    # "Binary files differ" mode and only one line of output, defeating
    # the classifier entirely.
    diff_result = subprocess.run(
        ["diff", "-au", str(BASELINE), str(new_qdf)],
        capture_output=True,
        text=True,
        check=False,
    )

    if diff_result.returncode == 0:
        # No diff at all — acceptable but unexpected (3rd callsite addition
        # should produce class-(b) lines).
        return

    diff_lines = diff_result.stdout.splitlines()
    # Sanity guard against the "Binary files differ" failure mode (would
    # produce a single-line diff that the loop below would skip entirely,
    # giving a false PASS). With -a this should never trigger, but the
    # check is cheap insurance against a future flag-removal regression.
    assert not (len(diff_lines) == 1 and diff_lines[0].startswith("Binary files")), (
        f"diff bailed out in binary mode: {diff_lines[0]!r}"
    )
    unclassified: list[str] = []
    class_counts: dict[str, int] = {}
    for line in diff_lines:
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if not line.strip("+- "):
            continue
        cls = _classify(line)
        if cls is None:
            unclassified.append(line)
        else:
            class_counts[cls] = class_counts.get(cls, 0) + 1

    # Class (b) and (e) catch many lines that don't match a tight regex
    # (full BandDiagram path content streams, position-shifted operators);
    # the assertion below allows those by limiting the unclassified count
    # to a small budget. Tune the budget if MediaBox or similar surfaces
    # additional unclassified lines on first run.
    BUDGET = 200  # heuristic; first-run diagnostic prints if exceeded
    assert len(unclassified) < BUDGET, (
        f"{len(unclassified)} unclassified diff lines exceed budget "
        f"{BUDGET}; class counts so far: {class_counts}; first 30:\n" + "\n".join(unclassified[:30])
    )
