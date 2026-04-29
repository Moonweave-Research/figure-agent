# Golden Target 001 Vector Reproduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first `figure-agent` golden fixture: a publication-grade editable vector reproduction of the user-provided converged trap-depth PNG target, with PDF/SVG/PNG exports and a defect audit.

**Architecture:** Treat the target image as a first-class golden fixture, not as a prompt-orchestration experiment. The implementation creates a controlled TikZ source with named scopes, runs the existing compile/export/check pipeline, then records visual defects as `source`, `macro`, `export`, or `QA` issues. Only after this fixture exists should macro or checker improvements be made.

**Tech Stack:** TikZ/LaTeX (`lualatex`), `styles/polymer-paper-preamble.sty`, `scripts/compile.sh`, `scripts/export_svg.sh`, `scripts/svg_to_png.sh`, `scripts/status.py`, pytest, ruff.

---

## File Structure

- Create: `examples/golden_trap_depth_picture/spec.yaml`
  - Lightweight fixture metadata, `reference_image`, and no prompt-orchestration dependency.
- Create: `examples/golden_trap_depth_picture/briefing.md`
  - Human-readable intent and invariant list for the golden target.
- Create: `examples/golden_trap_depth_picture/reference/golden_target_001.png`
  - The user-provided PNG target. This is the visual truth for the fixture.
- Create: `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`
  - Editable TikZ reproduction source with named scopes for row 1, row 2, row 3, and right-side convergence diagram.
- Create: `examples/golden_trap_depth_picture/QUALITY_AUDIT.md`
  - Defect table and pass/fail status after each render iteration.
- Modify: `tests/test_status.py`
  - Add fixture-level regression for `/fig_status` reference-image semantics.
- Modify: `scripts/status.py`
  - Teach `/fig_status` to validate `reference_image` separately from
    `selected_preview`.
- Create: `tests/test_golden_target_contract.py`
  - Contract checks for required fixture files and accepted export artifacts.
- Modify: `.gitignore`
  - Track accepted golden exports while keeping ordinary generated outputs ignored.
- Create: `scripts/check_golden_artifacts.py`
  - Minimum gates for rendered PDF labels, SVG non-emptiness, PNG size, and
    opaque-white PNG background.
- Create: `tests/test_golden_artifact_checks.py`
  - Unit tests for the minimum artifact-gate helpers.
- Optionally modify after first audit: `styles/polymer-paper-preamble.sty`
  - Only if the audit proves missing reusable primitives are a macro-layer defect.
- Optionally modify after first audit: `scripts/check_visual_clash.py` or `scripts/check_collisions.py`
  - Only if visible target defects are not detected by current QA.

---

### Task 1: Register Golden Fixture Scaffold

**Files:**
- Create: `examples/golden_trap_depth_picture/spec.yaml`
- Create: `examples/golden_trap_depth_picture/briefing.md`
- Create: `examples/golden_trap_depth_picture/reference/.gitkeep`
- Create: `examples/golden_trap_depth_picture/previews/.gitkeep`
- Create: `examples/golden_trap_depth_picture/build/.gitkeep`
- Create: `examples/golden_trap_depth_picture/exports/.gitkeep`
- Create: `examples/golden_trap_depth_picture/reference/golden_target_001.png`
- Create: `tests/test_golden_target_contract.py`

- [ ] **Step 1: Save the supplied PNG reference**

Save the image from the user message exactly here:

```text
examples/golden_trap_depth_picture/reference/golden_target_001.png
```

Expected: the file exists and opens as the converged trap-depth target.

- [ ] **Step 2: Write the failing fixture-file contract test**

Create `tests/test_golden_target_contract.py`:

```python
"""Golden target fixture contract tests."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "examples" / "golden_trap_depth_picture"


def test_golden_target_fixture_files_exist() -> None:
    required = [
        FIXTURE / "spec.yaml",
        FIXTURE / "briefing.md",
        FIXTURE / "reference" / "golden_target_001.png",
    ]

    missing = [path for path in required if not path.exists()]

    assert missing == []
```

- [ ] **Step 3: Run the fixture-file contract test and verify it fails before scaffold**

Run:

```bash
uv run pytest -q tests/test_golden_target_contract.py::test_golden_target_fixture_files_exist
```

Expected before scaffold: `FAILED` with missing paths.

- [ ] **Step 4: Create fixture directories**

Create directories:

```bash
mkdir -p examples/golden_trap_depth_picture/{reference,previews,build,exports}
touch examples/golden_trap_depth_picture/reference/.gitkeep
touch examples/golden_trap_depth_picture/previews/.gitkeep
touch examples/golden_trap_depth_picture/build/.gitkeep
touch examples/golden_trap_depth_picture/exports/.gitkeep
```

- [ ] **Step 5: Create `spec.yaml`**

Write `examples/golden_trap_depth_picture/spec.yaml`:

```yaml
name: golden_trap_depth_picture
panels:
  - id: row1
    caption: Experiment to discharge reference
  - id: row2
    caption: Mathematical interpretation to trap-depth distribution
  - id: row3
    caption: Molecular origin to localized traps
  - id: right
    caption: Converged trap-depth picture
style_profile: polymer-default
selected_preview: null
reference_image: reference/golden_target_001.png
selection_notes: |
  Golden Target 001 is a reference target, not a generative preview.
  Reproduce the supplied PNG as an editable vector figure.
  Preserve all labels, row hierarchy, arrows, polymer-chain motifs, trap levels,
  and the right-side converged trap-depth energy/distribution diagram.
```

- [ ] **Step 6: Create `briefing.md`**

Write `examples/golden_trap_depth_picture/briefing.md`:

```markdown
# Briefing — golden_trap_depth_picture

## 1. What does this figure show? (1-2 sentences)

Converged trap-depth interpretation for sulfur-rich polymer charge dynamics.
The figure links experiment, mathematical interpretation, and molecular origin
to a unified trap-depth picture.

## 2. Domain vocabulary (terms, materials, mechanisms)

- Experiment: discharge current, log I, log t, Debye reference.
- Mathematical interpretation: power-law exponent n, Debye tau_d, trap-depth distribution g(E_t).
- Molecular origin: S-rich segments, chemical origin, physical origin, localized traps.
- Energy diagram: CB, VB, E_t, shallow traps, deep traps, g(E_t).

## 3. Composition intent (panel layout, flow direction)

Wide landscape schematic with three left-side narrative rows and one large right-side
converged trap-depth picture. Thin gray horizontal separators divide the rows.
Gray arrows move evidence from the left rows into a teal brace and right-side
energy/distribution diagram.

## 4. Normalize / avoid literal overfit

This is a golden reference reproduction. Do not normalize away labels, row
structure, curve shapes, colors, or sulfur/trap markers.

## 5. Style notes (optional)

White background, manuscript-readable sans-serif labels, thin gray separators
and arrows, blue power-law/electron marks, orange shallow traps, purple deep
traps, and teal convergence title/brace.

## 6. Physics invariants (preserved verbatim in prompt)

- CB is above VB.
- E_t lies between CB and VB.
- Shallow traps appear closer to CB; deep traps appear closer to VB.
- g(E_t) has two lobes: shallow and deep.
- The right-side diagram is the convergence endpoint for experiment,
  mathematical interpretation, and molecular origin.
```

- [ ] **Step 7: Run the fixture-file contract test and verify it passes**

Run:

```bash
uv run pytest -q tests/test_golden_target_contract.py::test_golden_target_fixture_files_exist
```

Expected: `1 passed`.

- [ ] **Step 8: Add and run reference-image status regressions**

Add tests proving that:

- `reference_image: reference/golden_target_001.png` is checked relative to the
  example directory.
- Missing references produce `reference_image_missing`.
- Existing references do not produce `selected_preview_missing`.

Run:

```bash
uv run pytest -q \
  tests/test_status.py::test_reference_image_existing_is_not_treated_as_selected_preview \
  tests/test_status.py::test_reference_image_missing_surfaces_separate_note
```

Expected: `2 passed`.

- [ ] **Step 9: Commit scaffold**

```bash
git add \
  scripts/status.py \
  examples/golden_trap_depth_picture/spec.yaml \
  examples/golden_trap_depth_picture/briefing.md \
  examples/golden_trap_depth_picture/reference/.gitkeep \
  examples/golden_trap_depth_picture/previews/.gitkeep \
  examples/golden_trap_depth_picture/build/.gitkeep \
  examples/golden_trap_depth_picture/exports/.gitkeep \
  examples/golden_trap_depth_picture/reference/golden_target_001.png \
  .gitignore \
  tests/test_golden_target_contract.py \
  tests/test_status.py
git commit -m "test(figure-agent): register golden trap-depth fixture"
```

---

### Task 2: Add First Source Skeleton Before Rendered-Label Contract

**Files:**
- Modify: `tests/test_golden_target_contract.py`
- Create later in this task: `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`

- [ ] **Step 1: Add a failing source-skeleton smoke test**

Append to `tests/test_golden_target_contract.py`:

```python
REQUIRED_SOURCE_TOKENS = [
    "Experiment",
    "Mathematical interpretation",
    "Molecular origin",
    "I(t)",
    "slope",
    "Discharge",
    "Debye",
    "tau_d",
    "n",
    "g(E_t)",
    "shallow",
    "deep",
    "localized traps",
    "S-rich segments",
    "chemical origin",
    "physical origin",
    "converged trap-depth picture",
    "Energy",
    "CB",
    "VB",
    "E_t",
]


def test_golden_target_tex_contains_required_source_tokens() -> None:
    """Source smoke only; rendered-label acceptance is checked after compile."""
    tex_path = FIXTURE / "golden_trap_depth_picture.tex"
    text = tex_path.read_text(encoding="utf-8")

    missing = [label for label in REQUIRED_SOURCE_TOKENS if label not in text]

    assert missing == []
    assert r"font=\textsf{" not in text
```

- [ ] **Step 2: Run the source-skeleton test and verify it fails**

Run:

```bash
uv run pytest -q tests/test_golden_target_contract.py::test_golden_target_tex_contains_required_source_tokens
```

Expected: `FAILED` because `golden_trap_depth_picture.tex` does not exist.

- [ ] **Step 3: Create the first TikZ source with named scopes**

Create `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`.

Required source structure:

```tex
\documentclass[border=4pt]{standalone}
\usepackage{polymer-paper-preamble}

\begin{document}
\begin{tikzpicture}[
  every node/.style={font=\sffamily\fontsize{7.5}{9}\selectfont},
  rowlabel/.style={font=\sffamily\fontsize{8.5}{10}\selectfont, align=center},
  titleTeal/.style={font=\sffamily\bfseries\fontsize{9}{11}\selectfont, text=cTeal},
  axis/.style={-{Stealth[length=3.5pt,width=2.5pt]}, cGray, line width=0.45pt},
  evidenceArrow/.style={-{Stealth[length=4pt,width=3pt]}, cGray, line width=0.55pt},
  sep/.style={cGray!55, line width=0.35pt},
  trapShallow/.style={cAmber, line width=0.8pt},
  trapDeep/.style={cTeal!70!cBlue, line width=0.8pt},
  electron/.style={circle, draw=cBlue!70!black, fill=cBlue!45, inner sep=0pt, minimum size=2.0mm},
]

% Canvas and separators
\draw[sep] (0,6.35) -- (18.8,6.35);
\draw[sep] (0,3.95) -- (18.8,3.95);

% Row 1: Experiment
\begin{scope}[shift={(0,6.65)}]
\node[rowlabel] at (1.1,0.8) {Experiment};
\node[draw=cGray, rounded corners=0.5pt, minimum width=0.75cm, minimum height=0.65cm] at (1.1,1.55) {};
\node[text=cBlue, font=\sffamily\fontsize{4}{5}\selectfont] at (1.1,1.55) {$\sim$};
\draw[axis] (3.0,0.05) -- (5.9,0.05);
\draw[axis] (3.0,0.05) -- (3.0,2.05);
\node at (4.45,-0.38) {$\log\,t$};
\node[rotate=90] at (2.55,1.05) {$\log\,I$};
\draw[cBlue, line width=0.9pt] (3.2,1.9) -- (5.7,0.18);
\draw[cBlue, dashed, line width=0.55pt] (4.35,1.28) -- (4.35,0.55);
\node[text=cBlue, font=\sffamily\fontsize{9}{11}\selectfont] at (5.25,1.45) {$I(t)\propto t^{-n}$};
\node[text=cBlue, font=\sffamily\fontsize{7}{9}\selectfont] at (4.2,0.45) {slope = $-n$};

\node[draw=cGray, rounded corners=2pt, minimum width=3.2cm, minimum height=2.65cm, anchor=south west] at (7.0,-0.15) {};
\node[font=\sffamily\itshape\fontsize{8}{10}\selectfont] at (8.6,2.15) {Discharge (Debye reference)};
\draw[axis] (7.15,0.05) -- (9.7,0.05);
\draw[axis] (7.15,0.05) -- (7.15,1.95);
\node at (8.45,-0.38) {$\log\,t$};
\node[rotate=90] at (6.75,1.0) {$\log\,I$};
\draw[cGray, line width=0.9pt] (7.35,1.65) .. controls (8.3,1.62) and (9.15,1.45) .. (9.55,0.2);
\draw[cGray, dashed, line width=0.5pt] (8.9,1.28) -- (8.9,0.42);
\node[text=cGray, align=left] at (7.8,0.85) {Debye\\exp($-t/\tau$)};
\node at (8.95,0.32) {$\tau_d$};
\draw[evidenceArrow] (10.45,1.25) -- (12.55,1.25);
\end{scope}

% Row 2: Mathematical interpretation
\begin{scope}[shift={(0,4.25)}]
\node[rowlabel] at (1.1,0.55) {Mathematical\\interpretation};
\node[draw=cGray, minimum width=0.6cm, minimum height=0.65cm] at (1.1,1.25) {$\Sigma=\int$};
\node[text=cBlue, font=\sffamily\fontsize{10}{12}\selectfont] at (3.8,1.05) {$I(t)\propto t^{-n}$};
\draw[evidenceArrow] (4.75,1.05) -- (5.6,1.05);
\node[text=cBlue, font=\sffamily\fontsize{11}{13}\selectfont] at (6.0,1.05) {$n$};
\node[align=center, text=cGray] at (7.9,1.45) {Debye\\exp($-t/\tau$)};
\draw[evidenceArrow] (8.8,1.05) -- (9.75,1.05);
\draw[evidenceArrow] (7.9,1.05) -- (7.9,0.45);
\node[text=cGray] at (7.9,0.05) {$\tau_d$};
\node at (10.35,1.05) {$g(E_t)$};
\draw[cAmber, line width=0.7pt] (11.0,0.75) .. controls (11.25,0.8) and (11.35,1.85) .. (11.6,0.75);
\draw[cTeal!70!cBlue, line width=0.7pt] (12.05,0.75) .. controls (12.3,0.8) and (12.45,1.9) .. (12.75,0.75);
\node[text=cAmber] at (11.35,0.38) {shallow};
\node[text=cTeal!70!cBlue] at (12.45,0.38) {deep};
\draw[evidenceArrow] (12.9,1.05) -- (14.25,1.05);
\end{scope}

% Row 3: Molecular origin
\begin{scope}[shift={(0,0.25)}]
\node[rowlabel] at (1.1,1.4) {Molecular\\origin};
\draw[cGray, line width=1.0pt] plot[smooth] coordinates {(2.0,2.5) (2.5,2.45) (3.0,2.55) (3.5,2.45) (4.0,2.55) (4.5,2.45) (5.0,2.55) (5.5,2.45) (6.0,2.55) (6.5,2.45) (7.0,2.55)};
\draw[cGray, line width=1.0pt] plot[smooth] coordinates {(2.0,1.65) (2.5,1.6) (3.0,1.7) (3.5,1.6) (4.0,1.7) (4.5,1.6) (5.0,1.7) (5.5,1.6) (6.0,1.7) (6.5,1.6) (7.0,1.7)};
\draw[cGray, line width=1.0pt] plot[smooth] coordinates {(2.0,0.8) (2.5,0.75) (3.0,0.85) (3.5,0.75) (4.0,0.85) (4.5,0.75) (5.0,0.85) (5.5,0.75) (6.0,0.85) (6.5,0.75) (7.0,0.85)};
\foreach \x/\y in {2.8/2.5,4.2/2.5,5.4/2.5,6.5/2.5,3.7/1.65,5.35/1.65,5.9/1.65,6.35/1.65,2.8/0.8,4.4/0.8} {
  \node[text=cAmber] at (\x,\y+0.35) {S};
  \draw[cAmber, fill=white, line width=0.7pt] (\x,\y+0.12) circle (0.055);
}
\node[text=cAmber] at (3.9,0.15) {S-rich segments};
\draw[cGray, dashed, rounded corners=2pt] (4.95,1.35) rectangle (6.75,1.95);
\node[align=center] at (6.2,-0.05) {chemical origin\\(electronegativity,\\polarizability of S)};
\draw[evidenceArrow] (5.8,0.35) -- (5.8,1.35);

\node[draw=cGray, dashed, rounded corners=2pt, minimum width=2.25cm, minimum height=1.55cm, anchor=south west] at (8.1,0.95) {};
\node at (9.2,2.68) {localized traps};
\draw[trapShallow] (8.45,2.2) -- (8.85,2.2); \node[electron] at (8.65,2.33) {};
\draw[trapShallow] (9.45,2.15) -- (9.85,2.15); \node[text=cAmber] at (10.2,2.15) {$\cdots$};
\draw[trapDeep] (8.55,1.55) -- (8.95,1.55); \node[electron] at (8.75,1.7) {};
\draw[trapDeep] (9.55,1.5) -- (9.95,1.5); \node[text=cTeal!70!cBlue] at (10.25,1.5) {$\cdots$};
\node[align=center] at (11.1,-0.1) {physical origin\\(local potential\\fluctuations)};
\draw[evidenceArrow] (7.6,1.65) -- (8.1,1.8);
\draw[evidenceArrow] (10.35,1.65) -- (13.8,1.65);
\end{scope}

% Right-side converged trap-depth picture
\begin{scope}[shift={(13.0,1.05)}]
\draw[cTeal, line width=1.2pt] (0.5,1.0) .. controls (0.1,1.0) and (0.1,1.0) .. (0.1,1.4) -- (0.1,5.9) .. controls (0.1,6.3) and (0.1,6.3) .. (0.5,6.3);
\node[titleTeal, anchor=west] at (1.0,6.3) {converged trap-depth picture};
\draw[axis] (1.45,2.05) -- (1.45,4.95);
\node[rotate=90] at (1.15,3.55) {Energy};
\node[draw=cGray, fill=cLGray!35, minimum width=1.6cm, minimum height=0.5cm] at (2.65,5.0) {CB};
\node[draw=cGray, fill=cLGray!35, minimum width=1.6cm, minimum height=0.5cm] at (2.65,2.0) {VB};
\draw[cGray, dashed] (3.65,1.65) -- (3.65,5.55);
\node at (3.9,3.65) {$E_t$};
\foreach \x/\y in {2.1/4.55,2.55/4.35,2.15/3.95,2.6/3.85} {
  \draw[trapShallow] (\x-0.18,\y-0.1) -- (\x+0.22,\y-0.1);
  \node[electron] at (\x,\y) {};
}
\foreach \x/\y in {2.25/2.9,2.65/3.1} {
  \draw[trapDeep] (\x-0.18,\y-0.1) -- (\x+0.22,\y-0.1);
  \node[electron] at (\x,\y) {};
}
\node[text=cTeal!70!cBlue] at (3.1,3.0) {$\cdots$};
\draw[axis] (4.2,2.15) -- (4.2,5.05);
\draw[axis] (4.2,2.15) -- (6.0,2.15);
\node at (4.95,5.35) {$g(E_t)$};
\node at (5.25,1.8) {$g(E_t)$};
\draw[cAmber, line width=0.9pt] (4.2,4.55) .. controls (4.65,4.25) and (5.35,4.45) .. (5.2,3.8) .. controls (5.0,3.3) and (4.55,3.4) .. (4.2,3.2);
\draw[cTeal!70!cBlue, line width=0.9pt] (4.2,3.05) .. controls (4.75,2.7) and (5.55,2.95) .. (5.35,2.4) .. controls (5.15,1.95) and (4.55,2.0) .. (4.2,2.1);
\node[text=cAmber, anchor=west] at (5.35,3.85) {shallow};
\node[text=cTeal!70!cBlue, anchor=west] at (5.35,2.55) {deep};
\end{scope}

\end{tikzpicture}
\end{document}
```

This first source is expected to be imperfect. It must contain every required label and a complete first-pass structure so compile/export/QA can begin.

- [ ] **Step 4: Run the source-skeleton test and verify it passes**

Run:

```bash
uv run pytest -q tests/test_golden_target_contract.py::test_golden_target_tex_contains_required_source_tokens
```

Expected: `1 passed`.

- [ ] **Step 5: Commit source-skeleton smoke contract and first source**

```bash
git add tests/test_golden_target_contract.py examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
git commit -m "feat(figure-agent): add golden trap-depth vector source"
```

---

### Task 3: Compile, Export, And Capture First Defect Audit

**Files:**
- Create: `examples/golden_trap_depth_picture/QUALITY_AUDIT.md`
- Generate ignored artifacts under `examples/golden_trap_depth_picture/build/`
- Generate ignored artifacts under `examples/golden_trap_depth_picture/exports/`

- [ ] **Step 1: Compile the golden source**

Run:

```bash
bash scripts/compile.sh examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
```

Expected:

```text
Generated: build/golden_trap_depth_picture.pdf, build/golden_trap_depth_picture.png
```

The command also runs `check_collisions.py` and `check_visual_clash.py`.

- [ ] **Step 2: Export PDF/SVG/TIFF/PNG**

Run:

```bash
mkdir -p examples/golden_trap_depth_picture/exports
cp examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf
bash scripts/export_svg.sh \
  examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg
pdftocairo -tiff -r 600 -singlefile \
  examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture
bash scripts/svg_to_png.sh \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.png
```

Expected files:

```text
examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf
examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg
examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.tif
examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.png
```

- [ ] **Step 3: Check status**

Run:

```bash
uv run python3 scripts/status.py examples/golden_trap_depth_picture
```

Expected:

```text
golden_trap_depth_picture — stage 6/6
```

No `selected_preview_missing`, `reference_image_missing`, `missing_briefing`, or
`stale_export` note should appear after all artifacts are current.

- [ ] **Step 4: Write first audit file**

Create `examples/golden_trap_depth_picture/QUALITY_AUDIT.md`:

```markdown
# Golden Target 001 Quality Audit

## Rendered Artifacts

- Reference PNG: `reference/golden_target_001.png`
- Build PDF: `build/golden_trap_depth_picture.pdf`
- Build PNG: `build/golden_trap_depth_picture.png`
- Export PDF: `exports/golden_trap_depth_picture.pdf`
- Export SVG: `exports/golden_trap_depth_picture.svg`
- Export PNG: `exports/golden_trap_depth_picture.png`

## Current Verdict

Status: first-pass vector reconstruction, not yet accepted as manuscript-ready.

## Defect Table

| severity | layer | target area | defect | next action |
|---|---|---|---|---|
| MAJOR | source | full layout | First pass must be visually compared against the reference PNG before acceptance. | Open build PNG and reference side by side; replace this row with concrete findings. |

## Checker Output

Record the exact `compile.sh` collision and visual-clash output here after the first compile.

## Acceptance Checklist

- [ ] All required labels present.
- [ ] All rows present.
- [ ] Right-side converged trap-depth diagram present.
- [ ] No visible text collision.
- [ ] PDF export acceptable.
- [ ] SVG export opens correctly.
- [ ] PNG export has white background.
```

- [ ] **Step 5: Commit first audit**

```bash
git add examples/golden_trap_depth_picture/QUALITY_AUDIT.md
git commit -m "docs(figure-agent): record first golden target audit"
```

---

### Task 4: Add Export Artifact And Rendered-Quality Gates

**Files:**
- Modify: `tests/test_golden_target_contract.py`

- [ ] **Step 1: Add failing export contract test**

Append to `tests/test_golden_target_contract.py`:

```python
def test_golden_target_exports_exist_when_fixture_is_accepted() -> None:
    exports = FIXTURE / "exports"
    expected = [
        exports / "golden_trap_depth_picture.pdf",
        exports / "golden_trap_depth_picture.svg",
        exports / "golden_trap_depth_picture.tif",
        exports / "golden_trap_depth_picture.png",
    ]

    missing = [path for path in expected if not path.exists()]

    assert missing == []
```

- [ ] **Step 2: Verify golden export tracking policy**

Golden fixtures are reproducibility baselines, so accepted exports are tracked.
Ordinary examples still ignore generated export contents. Confirm `.gitignore`
contains explicit exceptions for these files:

```bash
git check-ignore -v examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf || true
```

Expected: no ignore rule blocks accepted golden exports. Use ordinary `git add`
for these four files once they exist.

- [ ] **Step 3: Run export contract test**

Run:

```bash
uv run pytest -q tests/test_golden_target_contract.py::test_golden_target_exports_exist_when_fixture_is_accepted
```

Expected after exports are present: `1 passed`.

- [ ] **Step 4: Run rendered artifact gates**

Run:

```bash
uv run python3 scripts/check_golden_artifacts.py \
  examples/golden_trap_depth_picture \
  --min-svg-elements 80 \
  --min-png-width 1800
```

Expected after the first accepted render: the command exits 0. If it fails, do
not mark the fixture accepted; record the failure in `QUALITY_AUDIT.md`.

- [ ] **Step 5: Commit export and artifact contracts**

```bash
git add \
  scripts/check_golden_artifacts.py \
  tests/test_golden_artifact_checks.py \
  tests/test_golden_target_contract.py
git commit -m "test(figure-agent): require golden target export artifacts"
```

---

### Task 5: First Visual Review Loop

**Files:**
- Modify: `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`
- Modify: `examples/golden_trap_depth_picture/QUALITY_AUDIT.md`
- Optionally modify: `styles/polymer-paper-preamble.sty`
- Optionally modify: `tests/test_lint_tex.py`

- [ ] **Step 1: Open visual artifacts side by side**

Compare:

```text
examples/golden_trap_depth_picture/reference/golden_target_001.png
examples/golden_trap_depth_picture/build/golden_trap_depth_picture.png
examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg
```

Expected: concrete visible defects are identified, not vague quality judgments.

- [ ] **Step 2: Replace the initial audit row with concrete defects**

Update `QUALITY_AUDIT.md` defect table using this format:

```markdown
| severity | layer | target area | defect | next action |
|---|---|---|---|---|
| MAJOR | source | row 1 power-law plot | The plot is too small relative to the target and the `I(t)` label sits too close to the line. | Increase row 1 plot width and move label to upper right. |
| MAJOR | source | right-side energy diagram | CB/VB boxes and g(E_t) distribution are not aligned to the same vertical energy range. | Align both scopes to a shared y-coordinate system. |
```

- [ ] **Step 3: Fix only source defects first**

Edit `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`.

Rules:

- Do not edit macros until the same drawing pattern repeats at least twice.
- Do not edit export scripts unless PDF is visually correct and SVG/PNG is degraded.
- Do not edit QA scripts unless a visible defect is stable and current checks miss it.

- [ ] **Step 4: Recompile after source fixes**

Run:

```bash
bash scripts/compile.sh examples/golden_trap_depth_picture/golden_trap_depth_picture.tex
```

Expected: compile succeeds and check output is recorded in `QUALITY_AUDIT.md`.

- [ ] **Step 5: Re-export after source fixes**

Run:

```bash
cp examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.pdf
bash scripts/export_svg.sh \
  examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg
pdftocairo -tiff -r 600 -singlefile \
  examples/golden_trap_depth_picture/build/golden_trap_depth_picture.pdf \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture
bash scripts/svg_to_png.sh \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.svg \
  examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.png
```

- [ ] **Step 6: Commit source-fix iteration**

```bash
git add \
  examples/golden_trap_depth_picture/golden_trap_depth_picture.tex \
  examples/golden_trap_depth_picture/QUALITY_AUDIT.md
git add examples/golden_trap_depth_picture/exports/golden_trap_depth_picture.*
git commit -m "fix(figure-agent): improve golden trap-depth vector reproduction"
```

---

### Task 6: Full Verification Gate

**Files:**
- No new files unless earlier tasks found macro/export/QA defects.

- [ ] **Step 1: Run focused golden tests**

```bash
uv run pytest -q tests/test_golden_target_contract.py tests/test_golden_artifact_checks.py
```

Expected: all tests in the golden contract and artifact-check files pass.

- [ ] **Step 2: Run core regression tests**

```bash
uv run pytest -q tests/test_release_contract.py tests/test_status.py tests/test_compile_contract.py
```

Expected: all tests pass.

- [ ] **Step 3: Run full suite**

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Run ruff**

```bash
uv run ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 5: Run plugin validation**

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all three validations pass.

- [ ] **Step 6: Run status**

```bash
uv run python3 scripts/status.py examples/golden_trap_depth_picture
```

Expected: `stage 6/6` with no stale or missing notes.

- [ ] **Step 7: Run golden artifact gates**

```bash
uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture
```

Expected: artifact gates pass, including rendered labels, SVG visible-element
floor, PNG size, and opaque-white PNG corners.

- [ ] **Step 8: Run diff check**

```bash
git diff --check
```

Expected: no output, exit 0.

---

## Self-Review

Spec coverage:

- `docs/golden-target-trap-depth-picture.md` requires editable vector source, PDF, SVG, PNG, labels, no collisions, visual hierarchy, style consistency, export fidelity, and defect classification.
- Task 1 covers fixture registration and reference target.
- Task 2 covers source creation and label completeness.
- Task 3 covers compile/export and first defect audit.
- Task 4 covers accepted export artifacts.
- Task 5 covers visual comparison and defect classification.
- Task 6 covers final verification gates.

Placeholder scan:

- The plan intentionally includes a first-pass TikZ source. It is allowed to be visually imperfect, but not structurally incomplete.
- The only open branch is whether export artifacts are tracked. The plan recommends tracking them for Golden Target 001 and gives the exact command.

Scope check:

- This plan does not attempt automatic PNG-to-TikZ. It creates the first golden fixture and uses its defects to decide whether source, macro, export, or QA work is needed.
