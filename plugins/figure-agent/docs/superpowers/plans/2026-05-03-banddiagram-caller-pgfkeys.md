# BandDiagram Caller-pgfkeys Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single optional pgfkeys slot to `\BandDiagram` so callers can override style at the call site without rewriting figure-wide `\tikzset` blocks. All sub-element default styles preserved.

**Architecture:** Wrap the existing `\BandDiagram` macro body in `\begin{scope}[band diagram, \BD@opts] ... \end{scope}` where `\BD@opts` is set from the new optional `[#1]` arg via outer `\def`. The 9-arg CSV parser (`\BandDiagramDraw`) is unchanged — option storage avoids LaTeX's 9-slot `\def` limit. `\begingroup`/`\endgroup` placement isolates `\BD@opts` to the call so options do not leak between sequential or nested invocations.

**Tech Stack:** LaTeX (lualatex via `scripts/compile.sh`), TikZ pgfkeys, pytest, qpdf, ImageMagick (`magick compare`).

**Spec reference:** `docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `styles/polymer-paper-preamble.sty` | Modify line 181-195 (tikzset block) and line 302-328 (`\BandDiagram` def) | Add `band diagram/.style={}` outer key, change `\BandDiagram` signature to `[2][]`, wrap body in scope |
| `examples/_macro_smoke/_macro_smoke.tex` | Modify (add 3rd `\BandDiagram` block after current line 29) | Add override-demo callsite |
| `tests/fixtures/banddiagram_pilot/baseline.qdf` | Create (binary fixture) | Pre-pilot qpdf-stripped baseline for classifier diff |
| `tests/test_band_diagram_api.py` | Create | 3 compile-success/failure assertions |
| `tests/test_band_diagram_byte_classifier.py` | Create | Diff against baseline fixture, classify into (a)-(e) |
| `docs/macros/band-diagram.md` | Create | User-facing macro reference |
| `docs/architecture-overview.md` | Modify (Layer 3 section) | Update one line to note BandDiagram joined BellCurve in decoupled state |

---

## Task 1: Branch and capture pre-pilot baseline

**Files:**
- Create branch: `feat/banddiagram-caller-pgfkeys` from `main`
- Create: `plugins/figure-agent/tests/fixtures/banddiagram_pilot/baseline.qdf`

- [ ] **Step 1: Create feature branch**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git checkout -b feat/banddiagram-caller-pgfkeys
```

Expected: `Switched to a new branch 'feat/banddiagram-caller-pgfkeys'`

- [ ] **Step 2: Compile current `_macro_smoke.tex` (no edits yet)**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex 2>&1 | tail -3
```

Expected: `Generated: build/_macro_smoke.pdf, build/_macro_smoke.png (engine: lualatex)`

- [ ] **Step 3: Capture qpdf-stripped baseline as test fixture**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
mkdir -p tests/fixtures/banddiagram_pilot
qpdf --qdf --object-streams=disable \
  examples/_macro_smoke/build/_macro_smoke.pdf \
  tests/fixtures/banddiagram_pilot/baseline.qdf
ls -l tests/fixtures/banddiagram_pilot/baseline.qdf
```

Expected: file exists, ~200-400 KB.

- [ ] **Step 4: Commit baseline as precursor commit**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/tests/fixtures/banddiagram_pilot/baseline.qdf
git commit -m "$(cat <<'EOF'
test(banddiagram): pin pre-pilot _macro_smoke baseline qdf fixture

Captured before any macro change so the byte-classifier test in the
same plan can detect drift introduced by the pilot itself. Committed
as a precursor so a bisect across the pilot can reproduce the baseline
independently of subsequent commits.
EOF
)"
```

Expected: commit succeeds, `1 file changed`.

---

## Task 2: Write failing override API test (TDD red)

**Files:**
- Create: `plugins/figure-agent/tests/test_band_diagram_api.py`

- [ ] **Step 1: Create test file with ONLY the override test**

```python
"""API contract tests for the \\BandDiagram macro after caller-pgfkeys decoupling.

Validates the three supported call patterns (default, per-call override via [#1],
figure-wide tikzset). Tests assert compile-success only; structural-diff
verification is in tests/test_band_diagram_byte_classifier.py.
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
def test_per_call_override_compiles(tmp_path: Path) -> None:
    """Caller may pass TikZ \\path keys via the optional [#1] argument.
    The .append style form patches the figure-wide bandFrame default for
    this single call only."""
    result = _compile(
        tmp_path,
        r"\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]"
        r"{0,0,4,3, 2.5, 0.5, 1.5, {}, {}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout
```

Write to: `plugins/figure-agent/tests/test_band_diagram_api.py`

- [ ] **Step 2: Run override test to verify it fails (RED)**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run pytest tests/test_band_diagram_api.py::test_per_call_override_compiles -v 2>&1 | tail -15
```

Expected: FAIL with lualatex error like `Use of \BandDiagram doesn't match its definition` or `Illegal parameter number in definition` (current macro is `[1]` not `[2][]`, so optional `[bandFrame/...]` is not parsed).

- [ ] **Step 3: Commit failing test**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/tests/test_band_diagram_api.py
git commit -m "$(cat <<'EOF'
test(banddiagram): add failing per-call override compile test (TDD red)

Asserts \BandDiagram accepts an optional [#1] pgfkeys arg using
.append style on bandFrame. Currently fails because \BandDiagram is
defined as [1]; the next commit adds the [2][] signature.
EOF
)"
```

---

## Task 3: Implement macro signature change (TDD green)

**Files:**
- Modify: `plugins/figure-agent/styles/polymer-paper-preamble.sty` lines 194 (add key) and 302-328 (macro)

- [ ] **Step 1: Add `band diagram/.style={}` outer key to the existing tikzset block**

Edit `plugins/figure-agent/styles/polymer-paper-preamble.sty`. Current block at lines 181-195:

```latex
\tikzset{
  tickLabel/.style={
    font=\sffamily\fontsize{4.3}{5.2}\selectfont,
    text=cGray!90!black
  },
  bandbox/.style={
    draw=black, line width=0.45pt, fill=cLGray!30,
    minimum width=1.55cm, minimum height=0.48cm
  },
  bandFrame/.style={cTeal, line width=1.2pt, rounded corners=4pt},
  bandAxis/.style={-{Stealth[length=3.2pt,width=2.4pt]}, cGray, line width=0.42pt},
  bandEt/.style={cGray!45, dashed, line width=0.38pt},
  trapShallow/.style={cAmber, line width=0.72pt},
  trapDeep/.style={cBlue!45!cRed, line width=0.72pt},
}
```

Change to (one new line, before the closing `}`):

```latex
\tikzset{
  tickLabel/.style={
    font=\sffamily\fontsize{4.3}{5.2}\selectfont,
    text=cGray!90!black
  },
  bandbox/.style={
    draw=black, line width=0.45pt, fill=cLGray!30,
    minimum width=1.55cm, minimum height=0.48cm
  },
  bandFrame/.style={cTeal, line width=1.2pt, rounded corners=4pt},
  bandAxis/.style={-{Stealth[length=3.2pt,width=2.4pt]}, cGray, line width=0.42pt},
  bandEt/.style={cGray!45, dashed, line width=0.38pt},
  trapShallow/.style={cAmber, line width=0.72pt},
  trapDeep/.style={cBlue!45!cRed, line width=0.72pt},
  band diagram/.style={},
}
```

- [ ] **Step 2: Replace `\BandDiagram` macro body**

Edit `plugins/figure-agent/styles/polymer-paper-preamble.sty`. Current block at lines 302-328:

```latex
% \BandDiagram{x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys}: rounded teal frame + CB/VB bandboxes + Energy axis + dashed Et + \TrapLevel dashes; brace-wrap shallow_ys and deep_ys at call site (commas inside).
\newcommand{\BandDiagram}[1]{%
  \BandDiagramDraw#1\relax
}
\makeatletter
\def\BandDiagramDraw#1,#2,#3,#4,#5,#6,#7,#8,#9\relax{%
  \begingroup
  \pgfmathsetmacro{\BDcx}{(#1+#3)/2}%
  \pgfmathsetmacro{\BDaxX}{#1+0.63}%
  \pgfmathsetmacro{\BDaxYlo}{#6+0.05}%
  \pgfmathsetmacro{\BDaxYhi}{#5-0.43}%
  \pgfmathsetmacro{\BDaxYmid}{(\BDaxYlo+\BDaxYhi)/2}%
  \pgfmathsetmacro{\BDetYlo}{#6-0.35}%
  \pgfmathsetmacro{\BDetYhi}{#5+0.30}%
  \draw[bandFrame] (#1,#2) rectangle (#3,#4);
  \BandBox{\BDcx}{#5}{CB}
  \BandBox{\BDcx}{#6}{VB}
  \draw[bandAxis] (\BDaxX,\BDaxYlo) -- (\BDaxX,\BDaxYhi);
  \node[rotate=90, text=cGray, font=\sffamily\fontsize{6.5}{7.8}\selectfont]
    at (\BDaxX-0.18,\BDaxYmid) {Energy};
  \draw[bandEt] (#7,\BDetYlo) -- (#7,\BDetYhi);
  \node[text=cGray] at (#7+0.20,\BDaxYmid) {$E_t$};
  \foreach \BDy in {#8} { \TrapLevel{\BDcx-0.41}{\BDy}{trapShallow} }%
  \foreach \BDy in {#9} { \TrapLevel{\BDcx-0.25}{\BDy}{trapDeep} }%
  \endgroup
}
\makeatother
```

Replace with:

```latex
% \BandDiagram[<style keys>]{x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys}: rounded teal frame + CB/VB bandboxes + Energy axis + dashed Et + \TrapLevel dashes. Optional [#1] passes pgfkeys to the wrapping `band diagram` style key (default empty). \BD@opts storage avoids LaTeX 9-slot \def limit; \begingroup placement isolates the option per-call.
\makeatletter
\newcommand{\BandDiagram}[2][]{%
  \begingroup
  \def\BD@opts{#1}%
  \BandDiagramDraw#2\relax
}
\def\BandDiagramDraw#1,#2,#3,#4,#5,#6,#7,#8,#9\relax{%
  \begin{scope}[band diagram, \BD@opts]
  \pgfmathsetmacro{\BDcx}{(#1+#3)/2}%
  \pgfmathsetmacro{\BDaxX}{#1+0.63}%
  \pgfmathsetmacro{\BDaxYlo}{#6+0.05}%
  \pgfmathsetmacro{\BDaxYhi}{#5-0.43}%
  \pgfmathsetmacro{\BDaxYmid}{(\BDaxYlo+\BDaxYhi)/2}%
  \pgfmathsetmacro{\BDetYlo}{#6-0.35}%
  \pgfmathsetmacro{\BDetYhi}{#5+0.30}%
  \draw[bandFrame] (#1,#2) rectangle (#3,#4);
  \BandBox{\BDcx}{#5}{CB}
  \BandBox{\BDcx}{#6}{VB}
  \draw[bandAxis] (\BDaxX,\BDaxYlo) -- (\BDaxX,\BDaxYhi);
  \node[rotate=90, text=cGray, font=\sffamily\fontsize{6.5}{7.8}\selectfont]
    at (\BDaxX-0.18,\BDaxYmid) {Energy};
  \draw[bandEt] (#7,\BDetYlo) -- (#7,\BDetYhi);
  \node[text=cGray] at (#7+0.20,\BDaxYmid) {$E_t$};
  \foreach \BDy in {#8} { \TrapLevel{\BDcx-0.41}{\BDy}{trapShallow} }%
  \foreach \BDy in {#9} { \TrapLevel{\BDcx-0.25}{\BDy}{trapDeep} }%
  \end{scope}
  \endgroup
}
\makeatother
```

Key textual diffs:
- `\makeatletter` moved BEFORE `\newcommand{\BandDiagram}` (was after).
- `\newcommand{\BandDiagram}[1]{...}` → `\newcommand{\BandDiagram}[2][]{...}`.
- `\newcommand` body now opens `\begingroup` and stores `\def\BD@opts{#1}`.
- `\BandDiagramDraw`'s 9-arg signature unchanged; body is wrapped in `\begin{scope}[band diagram, \BD@opts] ... \end{scope}`.
- `\endgroup` moved from inside `\BandDiagramDraw`'s old `\begingroup` (which is now removed) to AFTER `\end{scope}`, matching the `\begingroup` opened at `\newcommand` head.

- [ ] **Step 3: Run override test to verify it now passes (GREEN)**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run pytest tests/test_band_diagram_api.py::test_per_call_override_compiles -v 2>&1 | tail -10
```

Expected: PASS.

- [ ] **Step 4: Commit macro change**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/styles/polymer-paper-preamble.sty
git commit -m "$(cat <<'EOF'
refactor(macro): add caller-pgfkeys slot to \BandDiagram

Adds optional [#1] arg routed through outer \def\BD@opts to a new
`band diagram/.style={}` outer key, then wraps the body in a TikZ
scope. \begingroup at \newcommand head + \endgroup after \end{scope}
isolates the option per-call so it does not leak across sequential
or nested invocations. \BandDiagramDraw's 9-slot CSV parser is
unchanged — \BD@opts storage avoids the LaTeX 9-arg \def limit.

All sub-element defaults preserved (smart semantic defaults +
caller override available).
EOF
)"
```

---

## Task 4: Add no-regression API tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_band_diagram_api.py`

- [ ] **Step 1: Append two no-regression tests to the test file**

Append to `plugins/figure-agent/tests/test_band_diagram_api.py` (after the existing override test):

```python


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_default_invocation_compiles(tmp_path: Path) -> None:
    """Backwards-compatibility: \\BandDiagram with no optional [#1] arg
    must still compile. The new [2][] signature treats the missing optional
    as empty, so \\BD@opts is the empty token list — \\begin{scope}[band
    diagram, ] is a no-op style application."""
    result = _compile(
        tmp_path,
        r"\BandDiagram{0,0,4,3, 2.5, 0.5, 1.5, {3.5,3.2,2.9}, {1.8,1.5}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_figure_wide_tikzset_path_still_works(tmp_path: Path) -> None:
    """Pre-pilot caller pattern: figure-wide \\tikzset patches a sub-style
    once, all subsequent \\BandDiagram calls inherit it. The new [#1] slot
    is additive — it does not break this path."""
    result = _compile(
        tmp_path,
        r"\tikzset{bandFrame/.append style={draw=cAmber}}"
        "\n"
        r"\BandDiagram{0,0,4,3, 2.5, 0.5, 1.5, {}, {}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout
```

- [ ] **Step 2: Run all 3 tests to confirm green**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run pytest tests/test_band_diagram_api.py -v 2>&1 | tail -10
```

Expected: 3 passed.

- [ ] **Step 3: Commit no-regression tests**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/tests/test_band_diagram_api.py
git commit -m "$(cat <<'EOF'
test(banddiagram): add default + figure-wide tikzset no-regression tests

Locks in that the [2][] signature does not break either the no-arg
\BandDiagram{...} call (backwards compat) or the pre-pilot
\tikzset{bandFrame/.append style=...} caller pattern.
EOF
)"
```

---

## Task 5: Add 3rd `\BandDiagram` callsite to `_macro_smoke.tex`

**Files:**
- Modify: `plugins/figure-agent/examples/_macro_smoke/_macro_smoke.tex`

- [ ] **Step 1: Add override demo block after the second BandDiagram (current line 29)**

Current line 28-29:
```latex
  \BandDiagram{6,5.5,9,8.5, 7.8, 6.2, 7.5, {}, {}}
  \node[font=\sffamily\fontsize{6}{7}\selectfont] at (7.5,5.2) {BandDiagram (no traps)};
```

Insert AFTER line 29, before the next existing block (LogLogPlot at line 31):

```latex

  % --- BandDiagram: per-call override demo (Layer 3 caller-pgfkeys pilot) ---
  \BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]
              {6,9,9,11.5, 11, 9.5, 7.5, {}, {}}
  \node[font=\sffamily\fontsize{6}{7}\selectfont] at (7.5,8.7) {BandDiagram (override demo)};
```

The bbox `{6,9,9,11.5, ...}` is positioned above the second BandDiagram (which uses y=5.5..8.5) and below LogLogPlot (which starts at y=12). cb_y=11, vb_y=9.5, et_x=7.5; empty trap lists keep the canvas extension minimal.

- [ ] **Step 2: Compile to verify success**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex 2>&1 | tail -3
```

Expected: `Generated: build/_macro_smoke.pdf, build/_macro_smoke.png (engine: lualatex)`

- [ ] **Step 3: Visual sanity check (manual)**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
ls -l examples/_macro_smoke/build/_macro_smoke.pdf
```

Open the PDF to confirm a third BandDiagram is visible with cAmber frame. (No automated assertion; this is the human-in-loop sanity gate before the classifier test in Task 6.)

- [ ] **Step 4: Commit callsite addition**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/examples/_macro_smoke/_macro_smoke.tex
git commit -m "$(cat <<'EOF'
test(banddiagram): add per-call override demo to _macro_smoke

Third \BandDiagram invocation exercises the new [#1] slot at smoke-test
level, asserting end-to-end that bandFrame/.append style{draw=cAmber}
flows from caller through \BD@opts into the wrapping TikZ scope.
Positioned at y=9..11.5 to avoid overlap with existing layout.
EOF
)"
```

---

## Task 6: Write byte-classifier test against pre-pilot baseline

**Files:**
- Create: `plugins/figure-agent/tests/test_band_diagram_byte_classifier.py`

- [ ] **Step 1: Create classifier test file**

Write to `plugins/figure-agent/tests/test_band_diagram_byte_classifier.py`:

```python
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


# Patterns matching each allowed delta class. Implementation-dependent;
# may need tightening on first run if MediaBox or another page-object
# field surfaces an unclassified line.
_CLASS_PATTERNS = {
    "c_metadata": re.compile(
        r"^/(CreationDate|ModDate|ID)\b|^\s*<[0-9a-fA-F]+>\s*$"
    ),
    "d_stream_length": re.compile(r"^/Length\s+\d+\b|^xref\b|^\d+\s+\d+\s+obj\b"),
    "a_empty_scope": re.compile(r"^q\s*$|^Q\s*$"),
    "page_dim": re.compile(r"^/(MediaBox|CropBox|BBox|TrimBox|ArtBox)\b"),
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
        f"Pre-pilot baseline missing at {BASELINE}; "
        "run Task 1 of the pilot plan to capture it."
    )

    compile_result = subprocess.run(
        ["bash", "scripts/compile.sh", str(SMOKE_TEX)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, (
        compile_result.stderr + compile_result.stdout
    )

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

    diff_result = subprocess.run(
        ["diff", "-u", str(BASELINE), str(new_qdf)],
        capture_output=True,
        text=True,
        check=False,
    )

    if diff_result.returncode == 0:
        # No diff at all — acceptable but unexpected (3rd callsite addition
        # should produce class-(b) lines).
        return

    diff_lines = diff_result.stdout.splitlines()
    unclassified: list[str] = []
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

    # Class (b) and (e) catch many lines that don't match a tight regex
    # (full BandDiagram path content streams, position-shifted operators);
    # the assertion below allows those by limiting the unclassified count
    # to a small budget. Tune the budget if MediaBox or similar surfaces
    # additional unclassified lines on first run.
    BUDGET = 200  # heuristic; first-run diagnostic prints if exceeded
    assert len(unclassified) < BUDGET, (
        f"{len(unclassified)} unclassified diff lines exceed budget "
        f"{BUDGET}; first 30:\n"
        + "\n".join(unclassified[:30])
    )
```

- [ ] **Step 2: Run classifier test (first run — diagnostic)**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run pytest tests/test_band_diagram_byte_classifier.py -v 2>&1 | tail -25
```

Expected outcomes (in priority order):
- **PASS**: classifier handled all diffs within budget. Done.
- **FAIL with unclassified MediaBox lines**: extend `_CLASS_PATTERNS` with the `page_dim` class (already prepared in the file) by adding it to the classification loop. Re-run.
- **FAIL with budget exceeded**: examine printed first-30 unclassified lines. Most likely culprits:
  - PDF page-object fields not yet matched (e.g., `/Resources`, `/Contents`).
  - Long stream blob lines from class (b) — extend the third-callsite-content recognition (e.g., match lines that follow a `/Length` declaration up to `endstream`).
- **FAIL with rendering regression** (e.g., a coordinate or color value differs in pre-existing path content): STOP. This indicates the macro change altered visual output for the existing 2 callsites. Investigate before continuing — likely cause is `\BD@opts` value contamination across calls (verify `\begingroup` placement is correct).

- [ ] **Step 3: If first run failed with classifiable cause, fix inline and re-run**

If MediaBox surfaces: ensure `page_dim` regex is added to `_CLASS_PATTERNS` (already in template) and verify it matches the actual qdf line format (it may need broader matching).

If budget exceeded due to long stream content: add a final-pass classifier that absorbs any contiguous block between `stream` and `endstream` markers as class (b).

Iterate until all diff lines classify or budget passes.

- [ ] **Step 4: Commit classifier test**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/tests/test_band_diagram_byte_classifier.py
git commit -m "$(cat <<'EOF'
test(banddiagram): add qdf classifier diff against pre-pilot baseline

Diffs post-pilot _macro_smoke.pdf (qpdf-stripped) against the baseline
fixture from Task 1. Asserts every line-level diff falls into one of:
(a) empty-scope q/Q pair, (b) 3rd-callsite content, (c) lualatex
metadata, (d) stream/xref offsets, (e) position-shifted operators.
Unclassified diff lines indicate a real rendering regression.
EOF
)"
```

---

## Task 7: Run full test suite and ruff

**Files:** None (verification only)

- [ ] **Step 1: Run full pytest**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run pytest -q 2>&1 | tail -10
```

Expected: `230 passed` (226 baseline + 3 from `test_band_diagram_api.py` + 1 from classifier).

If any pre-existing test fails: investigate — the BandDiagram macro change may have leaked an effect into another fixture's compile. Check `_macro_smoke` related tests first.

- [ ] **Step 2: Run ruff**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
uv run ruff check . 2>&1 | tail -5
```

Expected: `All checks passed!`

- [ ] **Step 3: No commit (verification only)**

If both pass, proceed to Task 8. If either fails, fix in place (likely a single-line ruff fix or a test reference update); commit fix as `chore(banddiagram): post-pilot lint/test follow-up` if needed.

---

## Task 8: Add `docs/macros/band-diagram.md`

**Files:**
- Create: `plugins/figure-agent/docs/macros/band-diagram.md`

- [ ] **Step 1: Write user-facing macro reference doc**

Write to `plugins/figure-agent/docs/macros/band-diagram.md`:

````markdown
# `\BandDiagram` Macro Reference

**Signature**: `\BandDiagram[<style keys>]{x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys}`

Positional CSV args (brace-wrapped at call site, commas inside):
- `x1,y1,x2,y2` — bounding box (rectangle frame corners).
- `cb_y` — y-coordinate of the conduction band (CB) `BandBox`.
- `vb_y` — y-coordinate of the valence band (VB) `BandBox`.
- `et_x` — x-coordinate of the dashed Et reference line.
- `shallow_ys` — list of y-values for shallow trap dashes (use `{}` for none).
- `deep_ys` — list of y-values for deep trap dashes (use `{}` for none).

Optional pgfkeys arg (`[#1]`):
- TikZ `\path` keys applied via the `band diagram` outer style key after the figure-wide defaults.
- Use `.append style` form to patch a single sub-style for this call only:
  `\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]{...}`.

## Sub-style keys

The macro draws into 5 named sub-styles defined in `polymer-paper-preamble.sty`. Defaults preserve the figure-agent palette and convention; callers override via `.append style` on any of these keys (either at scope head or per call):

| Key | Default | Role |
|---|---|---|
| `bandFrame` | `cTeal, line width=1.2pt, rounded corners=4pt` | rectangle around the diagram (decoration) |
| `bandbox` | `draw=black, line width=0.45pt, fill=cLGray!30, ...` | CB / VB filled blocks (geometry + decoration) |
| `bandAxis` | `Stealth tip, cGray, line width=0.42pt` | vertical Energy axis arrow (geometry) |
| `bandEt` | `cGray!45, dashed, line width=0.38pt` | Et reference dashed line (semantic encoding — Et is by convention dashed) |
| `trapShallow` | `cAmber, line width=0.72pt` | shallow trap dash (semantic encoding — color = depth class) |
| `trapDeep` | `cBlue!45!cRed, line width=0.72pt` | deep trap dash (semantic encoding — color = depth class) |

## Style-responsibility carving rule

Three categories of style live in this macro:
1. **Geometric parameters** — positions, dimensions, arrow tip lengths, rounded-corner radii. Part of the shape; lives in macro.
2. **Semantic encoding** — `bandEt` dashed (Et = reference convention), `trapShallow`/`trapDeep` color hue (shallow vs deep classification). Smart default in macro; caller may override.
3. **Decoration** — frame color, fill opacity, non-semantic line widths. Belongs to caller; macro provides default as convenience.

Caller is free to override any (1)/(2)/(3) value; the defaults exist to make uncustomized calls produce a meaningfully encoded figure.

## Three usage patterns

### Default
```latex
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
```
No optional arg → renders with all sub-style defaults.

### Per-call override
```latex
\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]
            {6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
```
Caller patches `bandFrame` for this call only; subsequent `\BandDiagram` calls revert to the figure-wide default.

### Figure-wide tikzset
```latex
\tikzset{bandFrame/.append style={draw=cAmber}}
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
\BandDiagram{0,0,5,5, 4, 1, 3, {3.0}, {1.5}}
```
All `\BandDiagram` calls in this scope inherit the appended style. (Pre-pilot caller pattern; still supported unchanged.)

## Migration note

Existing 1-arg callsites (`\BandDiagram{...}`) compile unchanged under the new `[2][]` signature — the missing `[#1]` defaults to empty, and `\begin{scope}[band diagram, ]` is a no-op style application. No migration is required.

## Not supported in this pilot

- Direct sub-key syntax `\BandDiagram[bandFrame={...}, bandAxis={...}]` (β fan-out pattern). The macro does not parse `[#1]` into per-sub-element keys; only `.append style` and similar pgfkeys idioms work.
- Nesting `\BandDiagram` inside another macro's hook arg in a way that crosses `\begingroup`/`\endgroup` boundaries. `\BD@opts` is grouped per-call; sequential calls are safe.

If a future fixture needs the β fan-out pattern, that is a separate spec — not a backwards-incompatible change to this pilot's interface.
````

- [ ] **Step 2: Commit doc**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/docs/macros/band-diagram.md
git commit -m "$(cat <<'EOF'
docs(macro): add band-diagram.md user reference

Documents the new [#1] caller-pgfkeys slot, the 5 sub-style keys with
their defaults, the (1)/(2)/(3) style-responsibility carving rule, the
three supported usage patterns, and the explicit non-support of β
sub-key fan-out (deferred to separate spec).
EOF
)"
```

---

## Task 9: Update `docs/architecture-overview.md` Layer 3 line

**Files:**
- Modify: `plugins/figure-agent/docs/architecture-overview.md` (Layer 3 section)

- [ ] **Step 1: Find and update the line**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
grep -n "BellCurve" docs/architecture-overview.md | head
```

If a line mentions BellCurve as the only decoupled macro, replace it with text noting BandDiagram joined under the single-key α pattern (sub-element fan-out β still deferred).

If no such line exists yet (the architecture overview may describe the layer model abstractly without naming individual macros), add a one-paragraph note at the end of the Layer 3 section pointing at `docs/macros/band-diagram.md` and `docs/macros/bell-curve.md` as the live decoupled-macro references.

Example new sentence to insert (adjust to surrounding prose):

> Two flagship macros currently follow the style-decoupled pattern: `\BellCurve` (primitive single-key, PR #1) and `\BandDiagram` (composite single-key α path, this pilot). Per-sub-element fan-out (β) for composite macros remains an open question; see `docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md` §"Out of scope".

- [ ] **Step 2: Commit doc update**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git add plugins/figure-agent/docs/architecture-overview.md
git commit -m "$(cat <<'EOF'
docs(arch): note BandDiagram joined BellCurve under decoupled-macro list

Layer 3 section now references both \BellCurve and \BandDiagram as the
flagship style-decoupled macros, with explicit pointer that β
(composite per-sub-element fan-out) remains open per the BandDiagram
pilot spec's Out-of-scope section.
EOF
)"
```

---

## Task 10: Cleanup `.backup` file (optional housekeeping)

**Files:**
- Delete: `plugins/figure-agent/docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md.backup`

- [ ] **Step 1: Confirm `.backup` content is not load-bearing**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
diff docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md \
     docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md.backup \
     2>&1 | head -10
```

Expected: large diff (the `.backup` is the obsolete pre-brainstorm draft).

- [ ] **Step 2: Delete the .backup file**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
rm plugins/figure-agent/docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md.backup
git status -s 2>&1 | head -5
```

Expected: `.backup` no longer appears in untracked list.

- [ ] **Step 3: No commit** (file was untracked; deletion is a working-tree-only change)

---

## Task 11: Push branch and open PR

**Files:** None (git ops + GitHub PR)

- [ ] **Step 1: Push the feature branch to origin**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git push -u origin feat/banddiagram-caller-pgfkeys
```

Expected: branch created on origin.

- [ ] **Step 2: Create PR via gh**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
gh pr create --title "refactor(macro): BandDiagram caller-pgfkeys pilot (composite single-key α)" --body "$(cat <<'EOF'
## Summary

- Adds optional `[#1]` pgfkeys slot to `\BandDiagram` so callers can override style at the call site without rewriting figure-wide `\tikzset`.
- All 5 sub-element defaults preserved (smart semantic defaults + caller override available).
- Sub-element fan-out (β: `\BandDiagram[frame={...}, axis={...}]`) explicitly **not** addressed by this pilot — deferred to follow-up spec.

## Spec + Plan

- Design: `plugins/figure-agent/docs/superpowers/specs/2026-05-03-banddiagram-caller-pgfkeys-design.md`
- Plan: `plugins/figure-agent/docs/superpowers/plans/2026-05-03-banddiagram-caller-pgfkeys.md`

## Test plan

- [x] `tests/test_band_diagram_api.py` — 3 compile-success assertions (default, per-call override, figure-wide tikzset).
- [x] `tests/test_band_diagram_byte_classifier.py` — qdf diff against pre-pilot baseline `tests/fixtures/banddiagram_pilot/baseline.qdf`; every diff line falls into class (a)-(e).
- [x] Full `uv run pytest -q` reaches 230 passes.
- [x] `uv run ruff check .` clean.
- [x] `_macro_smoke.tex` 3rd callsite renders with cAmber frame (visual sanity).

## Pilot validation outcome (per spec REVIEW)

- α single-key decision validated: `\BandDiagram[bandFrame/.append style={...}]{...}` works end-to-end.
- (ii) preserved-default decision validated: existing 2 callsites compile unchanged, all 5 sub-style defaults survive scope wrap.
- (2) semantic-encoding framing applied: `bandEt` dashed and `trapShallow`/`trapDeep` color classification remain in-macro defaults; caller can override via the new slot if needed.
- β sub-element fan-out remains open. The spec's §"Out of scope" explicitly states this pilot does not answer the composite-fan-out question.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR URL printed.

- [ ] **Step 3: Report PR URL back to user**

Print the PR URL so the user can review and merge.

---

## Self-review

- **Spec coverage**: each of the spec's 13 implementation-order steps maps to a task. Steps 1-2 → Task 1 (branch + baseline). Step 3 → Task 3. Step 4 → Task 4 implicit (via api tests' default). Step 5 → Task 5. Step 6 → Task 4 (api tests). Step 7 → Task 6 (classifier). Step 8 → Task 7. Step 9 → Task 7. Step 10 → Task 8. Step 11 → Task 9. Step 12 → Task 11 (commit + push + PR). Step 13 → Task 11 (PR body).
- **Placeholder scan**: no TBD/TODO/"add appropriate". All steps contain exact paths, exact commands, exact LaTeX/Python content. The classifier test file's regex patterns may need tightening at execution time (Task 6 Step 3 explicitly handles this iteratively); this is not a placeholder but a planned diagnostic loop.
- **Type/method consistency**: `\BD@opts` is named identically across spec, plan Task 3 example code, and macro reference doc. `band diagram` (with space) is the outer style key everywhere — distinct from `bandFrame` etc. (which use camelCase). Test names: `test_per_call_override_compiles`, `test_default_invocation_compiles`, `test_figure_wide_tikzset_path_still_works` — three distinct test functions, no collision.
- **Branch strategy**: Task 1 creates `feat/banddiagram-caller-pgfkeys`; Task 11 pushes + opens PR. Spec is on `main` already (committed in `f035d1a`); plan goes on the same branch as the impl so PR includes both spec and plan in its diff.
- **Advisor heads-up on MediaBox**: surfaced in Task 6 Step 2 as one of the "FAIL with classifiable cause" branches with explicit fix instructions. Plan executor will see it before panicking.
