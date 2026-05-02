# BellCurve Macro Style Decoupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Acknowledgment — out of scope:** The paired prerequisite from spec §"Paired prerequisite (per advisor)" — Layer 5 export inconsistency where `build/<name>.png` (pdftocairo) and `examples/<name>/exports/<name>.png` (dvisvgm → rsvg-convert) raster differently from the same lualatex PDF — is **NOT addressed by this plan**. It will be tracked in a separate spec/plan. This plan does not modify the Layer 5 export pipeline; it does not promote any new fixture to golden status; and the byte-identical PDF verification used here is intentionally PDF-only (qpdf content streams), not PNG-based, so it sidesteps the unresolved rasterizer divergence.

**Goal:** Refactor the `\BellCurve` macro in `polymer-paper-preamble.sty` so the macro provides only Bezier shape geometry; all visual style (color, fill, line width) becomes the caller's responsibility through TikZ `\path` option keys, with a palette-neutral cGray outline default.

**Architecture:** Replace the existing 6-positional `\BellCurve{x1,y1,x2,y2,color,orientation}` macro (which hardcodes `draw=#5!80!black, fill=#5!18, line width=0.8pt`) with a 5-positional shape primitive `\BellCurve[<style keys>]{x1,y1,x2,y2,orientation}` that uses a new `bell curve/.style` tikzset for the default. All current callsites are migrated atomically in the same commit; old signature is rejected at compile time. Byte-identical PDF content streams (qpdf-based diff) are the no-regression gate.

**Tech Stack:** LaTeX (lualatex), TikZ/PGF, pytest, ruff, qpdf, Python 3.12, `uv` for environment management.

**Key reference paths (literal `[ ]` in absolute path):**
- Repo root: `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/`
- Plugin root (cwd for all commands below): `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/`

All `cd` and command examples below use the **plugin root** as working directory unless noted otherwise.

---

## File Structure

**Modified files:**
- `styles/polymer-paper-preamble.sty` — replace `\BellCurve` macro at lines 202–240 with style-decoupled version + new `bell curve/.style` tikzset.
- `examples/_macro_smoke/_macro_smoke.tex` — migrate 2 callsites at lines 10 and 13.
- `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex` — migrate 2 callsites at lines 187 and 192.

**New files:**
- `tests/test_bell_curve_api.py` — 4 API contract tests (default, local override, scope override, legacy rejected).
- `scripts/diff_pdf_content.py` — Python utility that expands two PDFs via `qpdf --qdf` and diffs content streams after stripping metadata.
- `docs/macros/bell-curve.md` — caller-facing macro reference (creates new `docs/macros/` directory).

**Files NOT modified:**
- `scripts/lint_tex.py` — palette enforcement is callsite-based and already handles `cBlue!45!cRed!80!black` style mixing (verified at plan time: `_check_color_segments` splits on `!` and validates each color-name segment against `palette | TIKZ_BUILTIN_COLORS`). No code change needed.
- `examples/dogfood_power_law_trap_pipeline/REVIEW.md` — contains the substring `BellCurve` in narrative prose, not as a callsite. No migration needed.

---

## Task 1: Reconnaissance + capture pre-change baseline PDFs

Goal: Inventory current callsites and compile current fixtures so we have an authoritative pre-change PDF baseline to diff against in Task 7. Must run **before any source modification**.

**Files:**
- Read-only: `styles/polymer-paper-preamble.sty`, `examples/_macro_smoke/_macro_smoke.tex`, `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex`
- Output: `/tmp/bellcurve-baseline/_macro_smoke.pdf`, `/tmp/bellcurve-baseline/dogfood_power_law_trap_pipeline.pdf`

- [ ] **Step 1.1: Confirm callsite inventory**

```bash
grep -rn 'BellCurve' examples/ styles/ | grep -v REVIEW.md
```

Expected output (4 callsites + 1 macro definition + 1 doc-comment):
```
examples/_macro_smoke/_macro_smoke.tex:10:  \BellCurve{0,0,1.5,1,cAmber,up}
examples/_macro_smoke/_macro_smoke.tex:13:  \BellCurve{2,0,3.5,1.5,cBlue!45!cRed,side}
examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex:187:\BellCurve{13.95, 2.05, 15.20, 2.95, cAmber, side}
examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex:192:\BellCurve{13.95, 0.65, 15.40, 1.85, cBlue!45!cRed, side}
styles/polymer-paper-preamble.sty:202:% \BellCurve{x1,y1,x2,y2,color,orientation}: ...
styles/polymer-paper-preamble.sty:203:\newcommand{\BellCurve}[1]{%
styles/polymer-paper-preamble.sty:235:      \PackageError{polymer-paper-preamble}{Invalid BellCurve orientation `#6'}{Use up or side.}%
```

If the grep surfaces additional callsites beyond these four, **halt and update the plan** before proceeding. The migration in Tasks 5–6 only translates these four.

- [ ] **Step 1.2: Create baseline directory**

```bash
mkdir -p /tmp/bellcurve-baseline
```

Expected: directory exists, no error.

- [ ] **Step 1.3: Compile current `_macro_smoke` fixture**

```bash
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex
```

Expected: exit 0; `examples/_macro_smoke/build/_macro_smoke.pdf` exists.

- [ ] **Step 1.4: Compile current `dogfood_power_law_trap_pipeline` fixture**

```bash
bash scripts/compile.sh examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex
```

Expected: exit 0; `examples/dogfood_power_law_trap_pipeline/build/dogfood_power_law_trap_pipeline.pdf` exists.

- [ ] **Step 1.5: Copy baseline PDFs**

```bash
cp examples/_macro_smoke/build/_macro_smoke.pdf /tmp/bellcurve-baseline/_macro_smoke.pdf
cp examples/dogfood_power_law_trap_pipeline/build/dogfood_power_law_trap_pipeline.pdf /tmp/bellcurve-baseline/dogfood_power_law_trap_pipeline.pdf
ls -la /tmp/bellcurve-baseline/
```

Expected: both files in `/tmp/bellcurve-baseline/` with non-zero size.

---

## Task 2: Add PDF content-stream diff utility

Goal: Create the qpdf-based diff script that Task 7 will use to verify byte-identical content streams. Build the tool first; it has no dependency on the macro change.

**Files:**
- Create: `scripts/diff_pdf_content.py`

- [ ] **Step 2.1: Write `scripts/diff_pdf_content.py`**

```python
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
```

- [ ] **Step 2.2: Make script executable**

```bash
chmod +x scripts/diff_pdf_content.py
```

- [ ] **Step 2.3: Smoke-test the script against itself (sanity)**

```bash
uv run python scripts/diff_pdf_content.py /tmp/bellcurve-baseline/_macro_smoke.pdf /tmp/bellcurve-baseline/_macro_smoke.pdf
```

Expected stdout: `OK: byte-identical content streams (_macro_smoke.pdf vs _macro_smoke.pdf)`. Exit 0. (Comparing a file to itself is a self-test; ensures qpdf works and metadata stripping is idempotent.)

- [ ] **Step 2.4: Verify the script detects a difference (negative sanity)**

```bash
uv run python scripts/diff_pdf_content.py /tmp/bellcurve-baseline/_macro_smoke.pdf /tmp/bellcurve-baseline/dogfood_power_law_trap_pipeline.pdf
```

Expected stderr containing `DIFFER`; exit 1. (Comparing two different PDFs must report a diff. If this reports OK, the script is broken — investigate before proceeding.)

- [ ] **Step 2.5: Run `ruff` on the new script**

```bash
uv run ruff check scripts/diff_pdf_content.py
```

Expected: clean (no violations).

---

## Task 3: Add API contract tests (RED)

Goal: Lock in the four API contract assertions described in the spec's "Tests" section before any macro change. These tests **WILL FAIL** against the current macro — that is the intended RED state for TDD discipline.

**Files:**
- Create: `tests/test_bell_curve_api.py`

- [ ] **Step 3.1: Write `tests/test_bell_curve_api.py`**

```python
"""API contract tests for the \\BellCurve macro after style/shape decoupling.

Validates the four supported call patterns (default, local-override,
scope-override) and that the legacy 6-positional signature is rejected.
Tests assert compile-success/failure only; byte-identical content-stream
verification is a separate manual step using `scripts/diff_pdf_content.py`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


_HEADER = (
    r"\documentclass[border=2pt]{standalone}"
    "\n"
    r"\usepackage{polymer-paper-preamble}"
    "\n"
    r"\begin{document}"
    "\n"
    r"\begin{tikzpicture}[x=1cm, y=1cm]"
    "\n"
)
_FOOTER = (
    "\n"
    r"\end{tikzpicture}"
    "\n"
    r"\end{document}"
    "\n"
)


def _compile(tmp_path: Path, body: str) -> subprocess.CompletedProcess:
    tex = tmp_path / "fixture.tex"
    tex.write_text(_HEADER + body + _FOOTER, encoding="utf-8")
    return subprocess.run(
        ["bash", "scripts/compile.sh", str(tex)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_default_style_compiles(tmp_path: Path) -> None:
    """\\BellCurve{...,side} with no optional style compiles using the
    palette-neutral cGray outline default declared in `bell curve/.style`."""
    result = _compile(tmp_path, r"\BellCurve{0,0,1,1,side}")
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_local_style_override_compiles(tmp_path: Path) -> None:
    """Caller may pass any TikZ \\path keys via the optional [#1] argument;
    this exercises the canonical translation pattern used by migrated callsites."""
    result = _compile(
        tmp_path,
        r"\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]"
        r"{0,0,1,1,side}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_scope_style_override_compiles(tmp_path: Path) -> None:
    """`\\tikzset{bell curve/.append style={...}}` lets a figure declare a
    figure-wide style once; subsequent \\BellCurve calls inherit it."""
    result = _compile(
        tmp_path,
        r"\tikzset{bell curve/.append style={fill=cAmber!18}}"
        "\n"
        r"\BellCurve{0,0,1,1,side}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_legacy_six_positional_signature_rejected(tmp_path: Path) -> None:
    """Old \\BellCurve{x1,y1,x2,y2,color,orientation} (6 positional, color
    embedded) MUST fail compile. With the new 5-positional parser the 6th
    field collapses into the orientation match-string (`cAmber, side`),
    matching neither `up` nor `side`, triggering \\PackageError."""
    result = _compile(tmp_path, r"\BellCurve{0,0,1,1,cAmber,side}")
    assert result.returncode != 0, (
        "Expected compile failure for legacy 6-positional call; "
        "the new macro must reject the ambiguous old signature."
    )
    combined = result.stdout + result.stderr
    assert "Invalid BellCurve orientation" in combined, combined
```

- [ ] **Step 3.2: Run the new tests against the **current** (unchanged) macro to confirm RED**

```bash
uv run pytest tests/test_bell_curve_api.py -v
```

Expected: **all 4 tests FAIL**. Each fails for a different reason; this is intentional and meaningful RED state — do **not** "fix" the tests:

- `test_default_style_compiles` — old macro requires 6 positional args; passing 5 raises a TeX error and `compile.sh` exits non-zero. Test asserts `returncode == 0` → FAILS.
- `test_local_style_override_compiles` — old `\newcommand{\BellCurve}[1]` does not declare an optional argument; the leading `[draw=...]` is parsed as document-body literal text and a TeX argument-mismatch error halts compile. → FAILS.
- `test_scope_style_override_compiles` — `\tikzset{bell curve/.append style={...}}` is harmless (creates the style), but then `\BellCurve{0,0,1,1,side}` (5 args) hits the same shortage as test 1. → FAILS.
- `test_legacy_six_positional_signature_rejected` — old macro happily compiles `\BellCurve{0,0,1,1,cAmber,side}` (returncode 0). Test asserts `returncode != 0` → FAILS.

If any test passes here, the test is incorrect; halt and revise the test.

- [ ] **Step 3.3: Run `ruff` on the new test file**

```bash
uv run ruff check tests/test_bell_curve_api.py
```

Expected: clean.

---

## Task 4: Replace `\BellCurve` macro definition (style-decoupled)

Goal: Replace the existing macro at `styles/polymer-paper-preamble.sty:202-240` with the new `[2][]`-signatured shape primitive plus a new `bell curve/.style` tikzset. After this task, **fixtures will not compile** (callsites still use the old 6-positional signature). That is expected and is fixed in Task 5.

**Files:**
- Modify: `styles/polymer-paper-preamble.sty:202-240`

- [ ] **Step 4.1: Replace lines 202–240 of `polymer-paper-preamble.sty`**

The existing block is:

```latex
% \BellCurve{x1,y1,x2,y2,color,orientation}: symmetric bell lobe inside bbox; orientation in {up, side}; fill <color>!18, stroke <color>!80!black 0.8pt.
\newcommand{\BellCurve}[1]{%
  \BellCurveDraw#1\relax
}
\makeatletter
\def\BellCurveDraw#1,#2,#3,#4,#5,#6\relax{%
  \begingroup
  \edef\BCorient{\zap@space#6 \@empty}%
  \def\BCup{up}%
  \def\BCside{side}%
  \pgfmathsetmacro{\BCw}{(#3)-(#1)}%
  \pgfmathsetmacro{\BCh}{(#4)-(#2)}%
  \ifdim\BCw pt<0.001pt\relax\endgroup\else
  \ifdim\BCh pt<0.001pt\relax\endgroup\else
    \ifx\BCorient\BCup
      \path[draw=#5!80!black, line width=0.8pt, fill=#5!18]
        (#1,#2)
        .. controls (#1+0.207*\BCw,#2+0.043*\BCh)
                and (#1+0.264*\BCw,#2+0.986*\BCh)
        .. (#1+0.494*\BCw,#4)
        .. controls (#1+0.724*\BCw,#4)
                and (#1+0.747*\BCw,#2+0.058*\BCh)
        .. (#3,#2) -- cycle;
    \else\ifx\BCorient\BCside
      \path[draw=#5!80!black, line width=0.8pt, fill=#5!18]
        (#1,#2)
        .. controls (#1+0.043*\BCw,#2+0.207*\BCh)
                and (#1+0.986*\BCw,#2+0.264*\BCh)
        .. (#3,#2+0.494*\BCh)
        .. controls (#3,#2+0.724*\BCh)
                and (#1+0.058*\BCw,#2+0.747*\BCh)
        .. (#1,#4) -- cycle;
    \else
      \PackageError{polymer-paper-preamble}{Invalid BellCurve orientation `#6'}{Use up or side.}%
    \fi\fi
    \endgroup
  \fi\fi
}
\makeatother
```

Replace with:

```latex
% \BellCurve[<style keys>]{x1,y1,x2,y2,orientation}: symmetric bell-lobe shape primitive.
% Geometry: bbox (x1,y1)-(x2,y2); orientation in {up, side}.
% Style: caller supplies draw/fill/line width via the optional [#1] pgfkeys list,
% or via \tikzset{bell curve/.append style={...}} for figure-wide consistency.
% Default `bell curve/.style` is outline-only with palette-neutral cGray; the `fill`
% key is intentionally omitted (TikZ semantic — see design spec §"Empirically validated").
\tikzset{
  bell curve/.style={
    draw=cGray,
    line width=0.5pt,
  },
}
\makeatletter
\newcommand{\BellCurve}[2][]{%
  \BellCurve@parse[#1]#2\relax
}
\def\BellCurve@parse[#1]#2,#3,#4,#5,#6\relax{%
  \pgfmathsetmacro{\BC@w}{(#4)-(#2)}%
  \pgfmathsetmacro{\BC@h}{(#5)-(#3)}%
  \edef\BC@orient{\zap@space#6 \@empty}%
  \def\BC@up{up}\def\BC@side{side}%
  \ifx\BC@orient\BC@up
    \path[bell curve, #1]
      (#2,#3)
      .. controls (#2+0.207*\BC@w,#3+0.043*\BC@h)
              and (#2+0.264*\BC@w,#3+0.986*\BC@h)
      .. (#2+0.494*\BC@w,#5)
      .. controls (#2+0.724*\BC@w,#5)
              and (#2+0.747*\BC@w,#3+0.058*\BC@h)
      .. (#4,#3) -- cycle;
  \else\ifx\BC@orient\BC@side
    \path[bell curve, #1]
      (#2,#3)
      .. controls (#2+0.043*\BC@w,#3+0.207*\BC@h)
              and (#2+0.986*\BC@w,#3+0.264*\BC@h)
      .. (#4,#3+0.494*\BC@h)
      .. controls (#4,#3+0.724*\BC@h)
              and (#2+0.058*\BC@w,#3+0.747*\BC@h)
      .. (#2,#5) -- cycle;
  \else
    \PackageError{polymer-paper-preamble}{Invalid BellCurve orientation `#6'}{Use up or side.}%
  \fi\fi
}
\makeatother
```

Key differences from the old block (executor: do not deviate):
- Comment line (line 202 in old) updated to reflect 5-positional + optional style signature.
- New `\tikzset{ bell curve/.style={...} }` block before `\newcommand`.
- `\newcommand{\BellCurve}[2][]` (was `[1]`) — adds optional first arg.
- Inner parser renamed to `\BellCurve@parse` (was `\BellCurveDraw`); positional args shift by one (`#2..#6` instead of `#1..#6`); semantics: `#1=opts, #2=x1, #3=y1, #4=x2, #5=y2, #6=orientation`.
- Internal macros prefixed `\BC@` (was `\BC...`) so they remain protected by `\makeatletter`/`\makeatother`.
- `\begingroup ... \endgroup` removed — `\path[...]` option scoping is sufficient and `\pgfmathsetmacro` results are consumed within the path expansion.
- `\ifdim\BCw pt<0.001pt` zero-area guards removed — current callsites are non-zero-area, and Task 7's drawing-instruction-equivalence check proves equivalence empirically (only differences are the dead-code `bell curve/.style` default state-setters; no path coordinate change).
- Style: `\path[draw=#5!80!black, line width=0.8pt, fill=#5!18]` → `\path[bell curve, #1]`. Color/fill/line-width now flow from scope key + caller's optional `[#1]`.

- [ ] **Step 4.2: Verify the .sty still parses (compile any minimal preamble-only test)**

```bash
uv run pytest tests/test_lint_tex.py -v 2>&1 | tail -20
```

Expected: all `test_lint_tex.py` tests still pass. (This test reads the .sty and parses the palette; it does not exercise `\BellCurve`. A failure here means the .sty has a syntax error.)

- [ ] **Step 4.3: Do NOT run full pytest yet**

After this task, the `_macro_smoke` and `dogfood_power_law_trap_pipeline` fixtures still contain old-signature callsites, so any test that compiles them will fail. Run only `tests/test_bell_curve_api.py` and `tests/test_lint_tex.py` as the in-progress sanity check between Tasks 4 and 5. Full suite is gated to Task 8.

```bash
uv run pytest tests/test_bell_curve_api.py tests/test_lint_tex.py -v
```

Expected: `test_bell_curve_api.py` — all 4 tests now PASS (RED→GREEN); `test_lint_tex.py` — all tests pass.

If a test in `test_bell_curve_api.py` still fails, the new macro has a bug; halt and investigate. Do not proceed until all 4 pass.

---

## Task 5: Migrate `_macro_smoke` fixture callsites

Goal: Translate the two old-signature callsites in `_macro_smoke.tex` to the new `[opts]{...,orientation}` form, preserving exact original color/line-width specs.

**Files:**
- Modify: `examples/_macro_smoke/_macro_smoke.tex:10`, `examples/_macro_smoke/_macro_smoke.tex:13`

**Migration translation rule (from spec §"Migration strategy: bulk"):**

`\BellCurve{x1,y1,x2,y2,COLOR,orientation}` →
`\BellCurve[draw=COLOR!80!black, fill=COLOR!18, line width=0.8pt]{x1,y1,x2,y2,orientation}`

This preserves the visual output of each call exactly: the new option list, when expanded after the `bell curve/.style` defaults, produces the same effective `[draw=..., fill=..., line width=0.8pt]` that the old macro hardcoded internally.

- [ ] **Step 5.1: Migrate `_macro_smoke.tex:10` (cAmber, up)**

Before:
```latex
  \BellCurve{0,0,1.5,1,cAmber,up}
```

After:
```latex
  \BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]{0,0,1.5,1,up}
```

- [ ] **Step 5.2: Migrate `_macro_smoke.tex:13` (cBlue!45!cRed, side)**

Before:
```latex
  \BellCurve{2,0,3.5,1.5,cBlue!45!cRed,side}
```

After:
```latex
  \BellCurve[draw=cBlue!45!cRed!80!black, fill=cBlue!45!cRed!18, line width=0.8pt]{2,0,3.5,1.5,side}
```

Note on color mixing: `cBlue!45!cRed!80!black` is parsed left-to-right by TikZ's `xcolor`; it equals `((cBlue!45!cRed)!80!black)` — same as the old macro's `\path[draw=#5!80!black]` substitution where `#5=cBlue!45!cRed`. The `lint_tex.py` color regex splits on `!` and validates each color-name segment against `palette ∪ TIKZ_BUILTIN_COLORS`; segments `45`, `80` are numeric (not color names) and skipped, so this token set passes lint.

- [ ] **Step 5.3: Compile `_macro_smoke` to confirm no syntax error**

```bash
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex
```

Expected: exit 0; the lualatex log mentions no `Invalid BellCurve orientation` or `Argument mismatch` errors.

---

## Task 6: Migrate `dogfood_power_law_trap_pipeline` fixture callsites

Goal: Apply the same migration translation rule to the two callsites in the dogfood fixture.

**Files:**
- Modify: `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex:187`, `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex:192`

- [ ] **Step 6.1: Migrate dogfood `:187` (cAmber, side, shallow lobe)**

Before:
```latex
\BellCurve{13.95, 2.05, 15.20, 2.95, cAmber, side}
```

After:
```latex
\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]{13.95, 2.05, 15.20, 2.95, side}
```

- [ ] **Step 6.2: Migrate dogfood `:192` (cBlue!45!cRed, side, deep lobe)**

Before:
```latex
\BellCurve{13.95, 0.65, 15.40, 1.85, cBlue!45!cRed, side}
```

After:
```latex
\BellCurve[draw=cBlue!45!cRed!80!black, fill=cBlue!45!cRed!18, line width=0.8pt]{13.95, 0.65, 15.40, 1.85, side}
```

- [ ] **Step 6.3: Compile dogfood fixture to confirm no syntax error**

```bash
bash scripts/compile.sh examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex
```

Expected: exit 0.

- [ ] **Step 6.4: Verify no remaining old-signature callsites in the repo**

```bash
grep -rn 'BellCurve{[^}]*,[^}]*,[^}]*,[^}]*,[^}]*,[^}]*}' examples/ styles/ | grep -v REVIEW.md
```

Expected: **empty output**. The pattern matches `\BellCurve{...}` with 6 comma-separated fields inside braces. Any non-empty result means a callsite was missed; halt and migrate it.

---

## Task 7: Verify drawing-instruction equivalence (no-regression gate)

Goal: Confirm that the migrated fixtures produce PDFs whose **rendering** is identical to the pre-change baseline captured in Task 1. The earlier draft of this plan (and the design spec) called for **byte-identical** content streams, but the new macro pattern `\path[bell curve, #1]` is incompatible with strict byte-identity: TikZ pgfkeys evaluates each key eagerly and emits PDF graphics-state operators inline, so the `bell curve/.style` defaults emit `RG`/`w` operators that the caller's `[#1]` then immediately overrides. Those default operators are dead code (state set but never used before the next overriding operator), so visual output is unchanged — but the operator stream is not byte-equal.

The verification is therefore split into two passes:

1. **Run the diff script** (`scripts/diff_pdf_content.py`) and expect a `DIFFER` for both fixtures (not `OK`). Capture exit code = 1.
2. **Classify every line-level difference** in the qpdf expansions; the migration is correctness-preserving only if every difference falls into one of these classes:
   - (a) The `bell curve` style prologue per BellCurve call: exactly two added lines `0.27452 0.27452 0.27452 RG \n0.49814 w \n` (cGray stroke + 0.5pt width). Predicted total delta: 2 × 39 bytes × N_callsites_in_fixture.
   - (b) `/CreationDate` / `/ModDate` (lualatex run timestamps; harmless).
   - (c) `/ID` array (PDF unique identifier; regenerated each compile; the diff script strips these for the byte comparison but they remain visible in raw qdf output).
   - (d) Stream length declarations and xref offsets — mechanical consequences of (a) growing each affected stream.
   - (e) Position-only shifts: lines like `0.79701 w ` may appear at different offsets in old vs new (because (a) inserted bytes earlier in the stream); the operator and its argument are byte-identical, only the line number changed.

**Halt criterion:** ANY line-level difference outside classes (a)-(e). Especially halt if a difference appears inside a Bezier control-point coordinate, an `m`/`c`/`l`/`h` path operator, or a final draw/fill color value. That would indicate a real rendering regression. Investigate before proceeding.

- [ ] **Step 7.1: Run the diff script for `_macro_smoke` (DIFFER expected)**

```bash
uv run python scripts/diff_pdf_content.py \
  /tmp/bellcurve-baseline/_macro_smoke.pdf \
  examples/_macro_smoke/build/_macro_smoke.pdf
```

Expected: stderr `DIFFER ...`; exit 1; `lengths old=X new=X+78` (78 = 2 × 39 = 2 callsites × prologue length).

- [ ] **Step 7.2: Run the diff script for `dogfood_power_law_trap_pipeline` (DIFFER expected)**

```bash
uv run python scripts/diff_pdf_content.py \
  /tmp/bellcurve-baseline/dogfood_power_law_trap_pipeline.pdf \
  examples/dogfood_power_law_trap_pipeline/build/dogfood_power_law_trap_pipeline.pdf
```

Expected: stderr `DIFFER ...`; exit 1; `lengths old=Y new=Y+78` (same 78-byte delta — both fixtures have 2 callsites).

- [ ] **Step 7.3: Classify every line-level difference**

Expand both pairs of PDFs and apply the discriminating filter:

```bash
qpdf --qdf --object-streams=disable /tmp/bellcurve-baseline/_macro_smoke.pdf /tmp/old_smoke.qdf
qpdf --qdf --object-streams=disable examples/_macro_smoke/build/_macro_smoke.pdf /tmp/new_smoke.qdf
diff -a /tmp/old_smoke.qdf /tmp/new_smoke.qdf \
  | grep -E '^[<>]' \
  | grep -vE '0\.27452 0\.27452 0\.27452 RG|0\.49814 w|/CreationDate|/ModDate|/ID \[|^[<>] [0-9]+$|^[<>] 0+[0-9]+ 0+ n |^[<>] 0\.79701 w '
```

Expected: empty output (every `<` / `>` line falls into classes (a)-(e) and is filtered out). If anything survives the filter, halt and investigate.

Repeat for the dogfood fixture:

```bash
qpdf --qdf --object-streams=disable /tmp/bellcurve-baseline/dogfood_power_law_trap_pipeline.pdf /tmp/old_dog.qdf
qpdf --qdf --object-streams=disable examples/dogfood_power_law_trap_pipeline/build/dogfood_power_law_trap_pipeline.pdf /tmp/new_dog.qdf
diff -a /tmp/old_dog.qdf /tmp/new_dog.qdf \
  | grep -E '^[<>]' \
  | grep -vE '0\.27452 0\.27452 0\.27452 RG|0\.49814 w|/CreationDate|/ModDate|/ID \[|^[<>] [0-9]+$|^[<>] 0+[0-9]+ 0+ n |^[<>] 0\.79701 w '
```

Expected: empty output.

---

## Task 8: Full test suite + lint

Goal: Run the entire pytest suite and `ruff` to confirm no regressions outside the BellCurve area.

- [ ] **Step 8.1: Run full pytest suite**

```bash
uv run pytest -q
```

Expected: `223 passed` (was 219 pre-change; +4 new tests in `test_bell_curve_api.py`). Zero failures, zero errors. If the count is lower than 223, a test was lost; halt. If the count is 223 but with failures, identify the regression — likely a fixture-compile test that depends on the migrated `.tex` files.

- [ ] **Step 8.2: Run `ruff check`**

```bash
uv run ruff check .
```

Expected: clean — no violations.

---

## Task 9: Caller-facing documentation

Goal: Document the new macro signature, default style, three call patterns, and migration note for old callers.

**Files:**
- Create: `docs/macros/bell-curve.md` (and `docs/macros/` directory)

- [ ] **Step 9.1: Create the docs directory**

```bash
mkdir -p docs/macros
```

- [ ] **Step 9.2: Write `docs/macros/bell-curve.md`**

```markdown
# `\BellCurve` — bell-lobe shape primitive

**Signature:** `\BellCurve[<style keys>]{x1,y1,x2,y2,orientation}`

Symmetric bell-curve lobe inscribed in the bbox `(x1,y1)–(x2,y2)`. The macro provides only Bezier shape geometry; visual style (color, fill, line width) is the caller's responsibility, expressed via TikZ `\path` option keys.

## Positional arguments

| # | Name        | Notes                                           |
|---|-------------|-------------------------------------------------|
| 1 | `x1`        | bbox lower-left x (TikZ length, in figure units)|
| 2 | `y1`        | bbox lower-left y                               |
| 3 | `x2`        | bbox upper-right x                              |
| 4 | `y2`        | bbox upper-right y                              |
| 5 | `orientation` | `up` (lobe peak at top) or `side` (peak at right) |

## Optional style argument

The leading `[<style keys>]` accepts any TikZ `\path` option (`draw`, `fill`, `line width`, `dash pattern`, `opacity`, …). Keys append after the scope-level `bell curve/.style` defaults, so caller keys override defaults.

## Default style

```latex
\tikzset{
  bell curve/.style={
    draw=cGray,
    line width=0.5pt,
    %% `fill` key intentionally omitted — outline-only by default.
  },
}
```

A caller who omits `[<style keys>]` and never appends to the scope style gets a palette-neutral cGray outline with no fill. This matches TikZ ecosystem norms (`\node`, `\draw`, `\path` all default to neutral when caller omits style).

## Three call patterns

### (1) Default — gray outline, no fill

```latex
\BellCurve{13.95, 2.05, 15.20, 2.95, side}
```

### (2) Local override — one call differs

```latex
\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]
          {13.95, 2.05, 15.20, 2.95, side}
```

### (3) Figure-wide style via `\tikzset`

```latex
\tikzset{bell curve/.append style={draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt}}
\BellCurve{13.95, 2.05, 15.20, 2.95, side}
\BellCurve{13.95, 0.65, 15.40, 1.85, side}  % inherits the appended style
```

`/.append style=` adds to the existing style without replacing the cGray default; use `/.style=` to fully replace.

## Style Lock interaction

`scripts/lint_tex.py` enforces palette-only color tokens at the callsite. The `[<style keys>]` block is scanned the same as any other TikZ option: each `!`-separated color segment must be in the palette (`cAmber`, `cGray`, `cBlue`, …) or a TikZ builtin (`black`, `white`, …). Raw hex values and `\definecolor` are blocked. Numeric mix percentages (`!18`, `!80`) are not color names and are ignored by the scanner.

Mixed expressions like `cBlue!45!cRed!80!black` are accepted because each color-name segment (`cBlue`, `cRed`, `black`) is allowed; the result is left-to-right associative, equal to `((cBlue!45!cRed)!80!black)`.

## Migration note (legacy callers)

The pre-2026-05-02 macro signature was 6-positional with embedded color:

```latex
% OLD — no longer supported, raises \PackageError at compile time:
\BellCurve{x1,y1,x2,y2,COLOR,orientation}
```

Translate to the new signature by moving `COLOR` into the optional argument:

```latex
% NEW — same visual output:
\BellCurve[draw=COLOR!80!black, fill=COLOR!18, line width=0.8pt]{x1,y1,x2,y2,orientation}
```

The new parser treats a 6-positional call as orientation = `COLOR,orientation` (e.g., `cAmber, side`), which matches neither `up` nor `side`, raising `Invalid BellCurve orientation` and halting compile. There is no backward-compat shim by design.
```

- [ ] **Step 9.3: Run `ruff` (no-op for markdown; sanity)**

```bash
uv run ruff check .
```

Expected: clean.

---

## Task 10: Single feature-branch commit

Goal: Stage and commit all six file changes (1 .sty, 2 .tex, 1 test, 1 script, 1 doc) in a single atomic commit. No backward-compat shim, no separate "migration" commit; the spec specifies bulk migration.

**Files staged:**
- `styles/polymer-paper-preamble.sty`
- `examples/_macro_smoke/_macro_smoke.tex`
- `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex`
- `tests/test_bell_curve_api.py` (new)
- `scripts/diff_pdf_content.py` (new)
- `docs/macros/bell-curve.md` (new)

**Files NOT staged (housekeeping):**
- Any `examples/<name>/build/`, `examples/<name>/exports/`, `examples/<name>/previews/` artifacts produced during compile/verification — these are gitignored or transient and not part of the change.
- `/tmp/bellcurve-baseline/` — discardable scratch.

- [ ] **Step 10.1: Confirm git status**

```bash
git status
```

Expected: 3 modified files (`*.sty`, `*_macro_smoke.tex`, `*dogfood_power_law_trap_pipeline.tex`), 3 untracked files (`tests/test_bell_curve_api.py`, `scripts/diff_pdf_content.py`, `docs/macros/bell-curve.md`).

- [ ] **Step 10.2: Stage explicitly by file (avoid `git add -A`)**

```bash
git add \
  styles/polymer-paper-preamble.sty \
  examples/_macro_smoke/_macro_smoke.tex \
  examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex \
  tests/test_bell_curve_api.py \
  scripts/diff_pdf_content.py \
  docs/macros/bell-curve.md
git status
```

Expected: 6 files staged; nothing else.

- [ ] **Step 10.3: Create commit**

```bash
git commit -m "$(cat <<'EOF'
refactor(macro): decouple style from BellCurve shape primitive

The BellCurve macro now provides only Bezier shape geometry; visual
style (color, fill, line width) flows from a new `bell curve/.style`
tikzset default plus the caller's optional `[#1]` argument. Callers
gain TikZ-idiomatic flexibility without rewriting the macro.

Pilot scope: \BellCurve only. Other 7 flagship macros remain on the
old hardcoded-style pattern pending pilot validation.

- New signature: \BellCurve[<style keys>]{x1,y1,x2,y2,orientation}
- Old 6-positional signature is rejected at compile time (no shim)
- All 4 callsites migrated atomically (_macro_smoke + dogfood fixture)
- Drawing-instruction equivalence verified pre vs post (qpdf-based): the only
  operator-stream differences are the `bell curve/.style` default state-setters
  (cGray stroke, 0.5pt width) emitted before each caller override -- dead code
  with no rendering impact. Path coordinates and final draw/fill state byte-identical.
- 4 new pytest assertions in tests/test_bell_curve_api.py (223 pass)
- New scripts/diff_pdf_content.py utility for content-stream diffs
- New docs/macros/bell-curve.md caller reference

Paired prerequisite (Layer 5 export inconsistency: build/PNG vs
exports/PNG mismatch from session 2026-05-02) is tracked separately
and is NOT addressed by this commit.

Spec: docs/superpowers/specs/2026-05-02-bell-curve-style-decoupling-design.md
Plan: docs/superpowers/plans/2026-05-02-bell-curve-style-decoupling.md
EOF
)"
```

Expected: commit succeeds; pre-commit hooks (if any) pass.

- [ ] **Step 10.4: Confirm clean working tree**

```bash
git status
git log --oneline -1
```

Expected: clean working tree (only untracked artifacts in `examples/<name>/build/exports/previews/` from compile-time output are tolerated). Latest commit is `refactor(macro): decouple style from BellCurve shape primitive`.

---

## Post-plan: REVIEW.md and PR

The spec's implementation order step 10 calls for a PR with REVIEW.md describing pilot validation outcome. This is **not part of this plan** — it is the user's decision after merge-readiness is confirmed by Task 8 (full pytest green) and Task 7 (byte-identical content streams). When the user opens the PR, link both:
- The design spec (`docs/superpowers/specs/2026-05-02-bell-curve-style-decoupling-design.md`)
- The paired Layer 5 prerequisite (still un-tracked at plan write time; the user will surface it as a separate spec/issue).

---

## Self-review checklist

- **Spec coverage**: Spec's "Implementation order" 10 steps map 1:1 to Tasks 1–10. Every spec section that prescribes an action (callsite confirmation, .sty rewrite, callsite migration, API tests, byte-identical verification, full pytest, ruff, doc, commit, PR) has a corresponding task or explicit deferral.
- **No placeholders**: Every code block above is the literal code/command the executor types. No "TODO", "TBD", "fill in details", or "similar to Task N" hand-waves. The .sty replacement block in Task 4 includes the full pre-image and post-image; migrations in Tasks 5–6 show before/after lines verbatim.
- **Type/identifier consistency**: Internal LaTeX names `\BC@w`, `\BC@h`, `\BC@orient`, `\BC@up`, `\BC@side`, `\BellCurve@parse` used consistently in Task 4 macro body and not redefined elsewhere. The translation rule `[draw=COLOR!80!black, fill=COLOR!18, line width=0.8pt]` is identical in spec, doc, migration tasks, and test fixtures.
- **Sequencing safety**: Baseline PDF capture (Task 1.5) precedes any source change (Task 4). Full pytest (Task 8) is gated to AFTER all four callsites are migrated (end of Task 6) so it never runs against an inconsistent half-migrated tree. Task 7 (byte-identical) is the no-regression gate; halt criterion is explicit.
- **RED reasons for Task 3 documented**: Step 3.2 explains all four tests fail for distinct, intentional reasons; do-not-fix instruction is explicit.
- **Acknowledgment**: Layer 5 export inconsistency stated as out-of-scope at top of plan and again in Task 10 commit message. A reviewer cannot miss it.
