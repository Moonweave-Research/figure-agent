# Layer 5 Export Staleness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Precondition:** BellCurve PR (#1, branch `refactor/bell-curve-decouple`) must be merged to `main` before this plan starts. Task 2 refactors `scripts/diff_pdf_content.py`, which is added by that PR. If the PR has not merged when execution begins:

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]"
git checkout feat/layer5-export-staleness
git fetch origin && git rebase origin/main   # after BellCurve PR is merged
```

If you must proceed before BellCurve merges, rebase this branch onto `refactor/bell-curve-decouple` instead of `main` (the BellCurve PR will pull both in when it merges). Document the choice in the final commit message.

**Goal:** Detect and resolve drift between `examples/<name>/build/` (compile output) and `examples/<name>/exports/` (export pipeline output) via content-hash staleness checks, auto-rebuild on `/fig_export`, and a two-layer contract test suite. Protect git-tracked golden-fixture exports from automatic overwrite.

**Architecture:** Three Python helper modules (`git_tracked.py`, `export_freshness.py`, `run_export.py`) compose into `scripts/status.py`'s stage inference and replace `commands/fig_export.md`'s manual bash steps with a single `uv run python scripts/run_export.py <name>` invocation. Two contract tests guard the invariants: Layer A (always-on freshness, every fixture) and Layer B (opt-in cross-pipeline equivalence smoke, per-fixture `spec.yaml.export_pipeline_equivalence`).

**Tech Stack:** Python 3.12, qpdf (already required by BellCurve PR), ImageMagick `magick compare` (for Layer B), pytest, ruff, `uv` for environment management.

**Key reference paths (literal `[ ]` in absolute path):**
- Repo root: `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/`
- Plugin root (cwd for all commands below): `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/`

All `cd` and command examples below use the **plugin root** as working directory unless noted otherwise.

**Spec:** `docs/superpowers/specs/2026-05-02-layer5-export-staleness-design.md` (committed `ca68d2a`).

---

## File Structure

**New files:**
- `scripts/git_tracked.py` — `is_tracked(path: Path, repo_root: Path) -> bool` using `git ls-files --error-unmatch`. One responsibility: tracked-vs-untracked check.
- `scripts/export_freshness.py` — `compute_export_state(example_dir: Path, name: str) -> str` returning one of `MISSING | TRACKED_GOLDEN | STALE | FRESH`. Plus `compute_pdf_content_hash(pdf_path: Path) -> bytes`.
- `scripts/run_export.py` — orchestrator. Reads sub-state via `compute_export_state`, dispatches `bash scripts/export_svg.sh` / `pdftocairo -tiff` / `bash scripts/svg_to_png.sh` accordingly. Honors `--force-golden`.
- `tests/test_git_tracked.py` — unit test for the tracked-check helper.
- `tests/test_export_freshness.py` — unit tests for `compute_export_state` covering all four sub-states + Layer A end-to-end invariant.
- `tests/test_export_pipeline_equivalence.py` — Layer B opt-in smoke (skips fixtures without `spec.yaml.export_pipeline_equivalence`).

**Modified files:**
- `scripts/diff_pdf_content.py` — extract `strip_metadata(pdf_path: Path, tmp_dir: Path) -> bytes` as module-level callable. CLI behavior (positional args, exit codes 0/1/2) preserved.
- `scripts/status.py` — `infer_stage` returns dict with new `exports_substate` key.
- `commands/fig_export.md` — replace manual bash step list with single `uv run python scripts/run_export.py <name>` invocation; document `--force-golden` flag.
- `examples/dogfood_power_law_trap_pipeline/spec.yaml` — add `export_pipeline_equivalence: { ae_max: 0.02 }`.
- `docs/architecture-overview.md` (or `SKILL.md` whichever surfaces the export pipeline contract) — describe new sub-state and contract.

**Files NOT modified:**
- `scripts/export_svg.sh`, `scripts/svg_to_png.sh` — kept CLI-agnostic for direct debug use.
- `scripts/compile.sh` — out of scope.
- `examples/_macro_smoke/spec.yaml`, `examples/golden_trap_depth_picture/spec.yaml` — neither opts into Layer B (smoke fixture and golden-contract-gated fixture respectively).

---

## Task 1: Pre-work verification

Goal: Confirm preconditions before any code change. Read-only.

- [ ] **Step 1.1: Verify BellCurve PR status**

```bash
gh pr view 1 --json state,baseRefName,headRefName
```

Expected: `state: MERGED` and `baseRefName: main`. If `state: OPEN`, halt — either wait for merge or rebase this branch onto `refactor/bell-curve-decouple` per the precondition note in the plan header.

- [ ] **Step 1.2: Confirm scripts/diff_pdf_content.py exists with `_strip_metadata` and qpdf-based pipeline**

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"
test -f scripts/diff_pdf_content.py && grep -q '_strip_metadata' scripts/diff_pdf_content.py && grep -q 'qpdf' scripts/diff_pdf_content.py && echo OK || echo MISSING
```

Expected: `OK`. If `MISSING`, the BellCurve PR is not visible on this branch — halt and rebase.

- [ ] **Step 1.3: Capture pre-change pytest baseline**

```bash
uv run pytest -q 2>&1 | tail -3
```

Record the pass count (expected: 225 from BellCurve PR). The final Task 10 verification asserts ≥ 225 + new tests added by this plan.

---

## Task 2: Refactor `diff_pdf_content.py` to expose `strip_metadata`

Goal: Extract the metadata-stripping pipeline as a module-level callable so other modules can import it. CLI behavior unchanged.

**Files:**
- Modify: `scripts/diff_pdf_content.py`

- [ ] **Step 2.1: Read current `diff_pdf_content.py` to confirm structure**

```bash
cat scripts/diff_pdf_content.py
```

Verify: `_METADATA_PATTERNS` list and `_expand`, `_strip_metadata` functions are private (leading underscore). `main()` is the CLI entry. The expected current shape is identical to the BellCurve PR's `70b1174` commit version.

- [ ] **Step 2.2: Replace the file's contents with the refactored version**

Use Edit to replace the existing private helpers with public ones. Old (private):

```python
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
```

Replace with public versions (same logic, public names):

```python
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
```

Then update the `main()` body — replace the two private call sites:

```python
        old_blob = _strip_metadata(_expand(old, tmp / "old"))
        new_blob = _strip_metadata(_expand(new, tmp / "new"))
```

with:

```python
        old_blob = strip_metadata(expand_pdf(old, tmp / "old"))
        new_blob = strip_metadata(expand_pdf(new, tmp / "new"))
```

- [ ] **Step 2.3: Run ruff**

```bash
uv run ruff check scripts/diff_pdf_content.py
```

Expected: clean.

- [ ] **Step 2.4: Verify CLI backward compatibility (BellCurve PR's usage must keep working)**

```bash
uv run python scripts/diff_pdf_content.py /tmp/nonexistent.pdf /tmp/also_nonexistent.pdf
echo "exit=$?"
```

Expected: stderr `missing input: old=False new=False`; exit 2 (matches the existing usage exit codes).

To do a positive end-to-end check, regenerate a baseline pair from any current fixture:

```bash
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex
uv run python scripts/diff_pdf_content.py examples/_macro_smoke/build/_macro_smoke.png examples/_macro_smoke/build/_macro_smoke.png 2>&1 | tail -3
```

Wait — the second command above passes a PNG, not a PDF, which qpdf will reject. Use:

```bash
uv run python scripts/diff_pdf_content.py examples/_macro_smoke/build/_macro_smoke.pdf examples/_macro_smoke/build/_macro_smoke.pdf
echo "exit=$?"
```

Expected: stdout `OK: byte-identical content streams (_macro_smoke.pdf vs _macro_smoke.pdf)`; exit 0.

---

## Task 3: Add `scripts/git_tracked.py`

Goal: Provide a single-purpose helper to determine whether a given file path is git-tracked. Used by `export_freshness.py` to decide TRACKED_GOLDEN.

**Files:**
- Create: `scripts/git_tracked.py`
- Test: `tests/test_git_tracked.py`

- [ ] **Step 3.1: Write `tests/test_git_tracked.py` (RED)**

```python
"""Tests for scripts/git_tracked.is_tracked — git ls-files-based check."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from git_tracked import is_tracked  # noqa: E402


def test_is_tracked_true_for_known_tracked_file() -> None:
    """polymer-paper-preamble.sty is committed; must report True."""
    sty = REPO_ROOT / "styles" / "polymer-paper-preamble.sty"
    assert sty.is_file()
    assert is_tracked(sty, REPO_ROOT) is True


def test_is_tracked_false_for_known_ignored_file(tmp_path: Path) -> None:
    """A file in build/ (gitignored) must report False even when present on disk.

    Use tmp_path inside the repo to ensure the file is under the repo root yet
    matches the gitignore pattern via name.
    """
    build_dir = REPO_ROOT / "examples" / "_macro_smoke" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    test_file = build_dir / "ephemeral_marker.tmp"
    test_file.write_text("ephemeral", encoding="utf-8")
    try:
        assert is_tracked(test_file, REPO_ROOT) is False
    finally:
        test_file.unlink(missing_ok=True)


def test_is_tracked_false_for_nonexistent_file(tmp_path: Path) -> None:
    """A path that does not exist must report False, not raise."""
    ghost = REPO_ROOT / "examples" / "ghost_fixture" / "exports" / "ghost.pdf"
    assert is_tracked(ghost, REPO_ROOT) is False
```

- [ ] **Step 3.2: Verify the test fails (helper does not exist)**

```bash
uv run pytest tests/test_git_tracked.py -v
```

Expected: `ImportError: cannot import name 'is_tracked' from 'git_tracked'` (the module does not exist yet).

- [ ] **Step 3.3: Write `scripts/git_tracked.py`**

```python
"""Helper: is a path git-tracked?

Used by the export-staleness pipeline to identify TRACKED_GOLDEN fixtures
whose curated exports/ artifacts must never be auto-clobbered.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def is_tracked(path: Path, repo_root: Path) -> bool:
    """Return True iff `git ls-files --error-unmatch` finds `path` in `repo_root`.

    Returns False when `path` does not exist, is not under `repo_root`, or is
    not git-tracked. Never raises on subprocess failure — git's exit code 1
    means "not tracked," which is the False answer.
    """
    if not path.exists():
        return False
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(rel)],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0
```

- [ ] **Step 3.4: Verify tests pass (GREEN)**

```bash
uv run pytest tests/test_git_tracked.py -v
```

Expected: 3 tests pass.

- [ ] **Step 3.5: Run ruff**

```bash
uv run ruff check scripts/git_tracked.py tests/test_git_tracked.py
```

Expected: clean.

---

## Task 4: Add `scripts/export_freshness.py`

Goal: Compute the four-state export sub-state per the spec's behavior matrix. Reuses `strip_metadata` from Task 2 and `is_tracked` from Task 3.

**Files:**
- Create: `scripts/export_freshness.py`
- Extend: `tests/test_export_freshness.py` (more added in Task 7's Layer A invariant)

- [ ] **Step 4.1: Write `tests/test_export_freshness.py` (Task 4 portion only — Layer A invariant added later in Task 7)**

```python
"""Tests for scripts/export_freshness.compute_export_state — sub-state logic.

Layer A end-to-end invariant test (`test_freshness_invariant_after_export`)
is added in Task 7 of the implementation plan; this file currently covers
only the four sub-state branches.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_MISSING,
    EXPORT_STALE,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)


def _scaffold_minimal_fixture(root: Path, name: str) -> Path:
    """Create a fixture dir with a minimal compiled PDF in build/."""
    fixture = root / "examples" / name
    (fixture / "build").mkdir(parents=True, exist_ok=True)
    (fixture / "exports").mkdir(parents=True, exist_ok=True)
    (fixture / name + ".tex").write_text(
        r"\documentclass[border=2pt]{standalone}"
        "\n"
        r"\begin{document}hello\end{document}"
        "\n",
        encoding="utf-8",
    )
    if shutil.which("lualatex") is None:
        pytest.skip("requires lualatex")
    subprocess.run(
        ["lualatex", "-output-directory", str(fixture / "build"), "-interaction=nonstopmode", str(fixture / (name + ".tex"))],
        check=True,
        capture_output=True,
    )
    return fixture


def test_state_missing_when_no_exports_pdf(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_missing")
    assert compute_export_state(fixture, "fix_missing") == EXPORT_MISSING


def test_state_fresh_when_exports_pdf_matches_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_fresh")
    shutil.copy(fixture / "build" / "fix_fresh.pdf", fixture / "exports" / "fix_fresh.pdf")
    assert compute_export_state(fixture, "fix_fresh") == EXPORT_FRESH


def test_state_stale_when_exports_pdf_differs_from_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_stale_a")
    other = _scaffold_minimal_fixture(tmp_path, "fix_stale_b")
    shutil.copy(other / "build" / "fix_stale_b.pdf", fixture / "exports" / "fix_stale_a.pdf")
    assert compute_export_state(fixture, "fix_stale_a") == EXPORT_STALE


def test_state_tracked_golden_when_exports_pdf_is_git_tracked(monkeypatch: pytest.MonkeyPatch) -> None:
    """The repo's golden_trap_depth_picture fixture has its exports/ artifacts
    git-tracked via .gitignore exclusion. compute_export_state must see them
    as TRACKED_GOLDEN regardless of build state."""
    fixture = REPO_ROOT / "examples" / "golden_trap_depth_picture"
    pdf = fixture / "exports" / "golden_trap_depth_picture.pdf"
    if not pdf.is_file():
        pytest.skip("golden fixture exports/PDF not present in checkout")
    state = compute_export_state(fixture, "golden_trap_depth_picture")
    assert state == EXPORT_TRACKED_GOLDEN
```

- [ ] **Step 4.2: Verify tests fail (helper does not exist)**

```bash
uv run pytest tests/test_export_freshness.py -v
```

Expected: `ImportError`.

- [ ] **Step 4.3: Write `scripts/export_freshness.py`**

```python
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
    if not build_pdf.is_file():
        return EXPORT_STALE  # exports exist but build/ is gone — treat as stale
    if compute_pdf_content_hash(exports_pdf) == compute_pdf_content_hash(build_pdf):
        return EXPORT_FRESH
    return EXPORT_STALE
```

- [ ] **Step 4.4: Verify tests pass (GREEN)**

```bash
uv run pytest tests/test_export_freshness.py -v
```

Expected: 4 tests pass (or skip if `lualatex` unavailable). The TRACKED_GOLDEN test skips if the fixture's PDF isn't checked out — that's expected on minimal CI without LFS.

- [ ] **Step 4.5: Run ruff**

```bash
uv run ruff check scripts/export_freshness.py tests/test_export_freshness.py
```

Expected: clean.

---

## Task 5: Wire exports sub-state into `scripts/status.py`

Goal: `infer_stage` returns an additional `exports_substate` key so `/fig_status` can surface the new state.

**Files:**
- Modify: `scripts/status.py`

- [ ] **Step 5.1: Read current `scripts/status.py` lines 177-220 to find `infer_stage`**

```bash
sed -n '177,220p' scripts/status.py
```

Identify the dict-returning entry point and where `exports_dir` and `name` are computed.

- [ ] **Step 5.2: Add the import and the sub-state field**

Use Edit. At the top of `scripts/status.py` (after the existing imports), add:

```python
from export_freshness import compute_export_state
```

Inside `infer_stage`, after `exports_dir = example_dir / "exports"` is established (around line 194 in the existing file), add:

```python
    exports_substate = compute_export_state(example_dir, name)
```

Then in EVERY return-dict construction inside `infer_stage` (the function returns multiple dicts at different stage values; there are roughly 6 of them based on the existing structure), add the new key. Example for the stage-6 return:

```python
            return {
                "stage": 6,
                ...existing fields...,
                "exports_substate": exports_substate,
            }
```

The simplest implementation: declare `exports_substate` once at the top of `infer_stage` and rely on Python's dict-merge / explicit field add at each return site.

- [ ] **Step 5.3: Add a unit test for the new field**

Edit `tests/test_status.py` — add a test:

```python
def test_infer_stage_returns_exports_substate_field(tmp_path: Path) -> None:
    """infer_stage must include exports_substate in its return dict so
    /fig_status can surface MISSING / TRACKED_GOLDEN / STALE / FRESH.
    """
    fixture = tmp_path / "examples" / "no_files"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: no_files\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# stub\n", encoding="utf-8")
    result = infer_stage(fixture)
    assert "exports_substate" in result
    assert result["exports_substate"] == "MISSING"
```

- [ ] **Step 5.4: Run pytest**

```bash
uv run pytest tests/test_status.py tests/test_export_freshness.py tests/test_git_tracked.py -v 2>&1 | tail -10
```

Expected: all green. The new `test_infer_stage_returns_exports_substate_field` passes; existing `test_status.py` tests continue passing.

- [ ] **Step 5.5: Run ruff**

```bash
uv run ruff check scripts/status.py
```

Expected: clean.

---

## Task 6: Add `scripts/run_export.py` orchestrator

Goal: A single Python script that reads sub-state, decides action (rebuild / skip / no-op), and runs the underlying bash export pipeline. Supports `--force-golden` to override TRACKED_GOLDEN.

**Files:**
- Create: `scripts/run_export.py`
- Modify: `commands/fig_export.md`

- [ ] **Step 6.1: Write `scripts/run_export.py`**

```python
"""Orchestrator for /fig_export.

Reads exports/ sub-state for `<name>` and dispatches:

  MISSING / STALE  -> regenerate (PDF copy, dvisvgm SVG, pdftocairo TIFF, rsvg-convert PNG)
  FRESH            -> no-op
  TRACKED_GOLDEN   -> skip with warning. --force-golden overrides.

Usage: uv run python scripts/run_export.py <name> [--force-golden]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_MISSING,
    EXPORT_STALE,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _regenerate(example_dir: Path, name: str) -> None:
    build_pdf = example_dir / "build" / f"{name}.pdf"
    exports_dir = example_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    exports_pdf = exports_dir / f"{name}.pdf"
    exports_svg = exports_dir / f"{name}.svg"
    exports_png = exports_dir / f"{name}.png"
    exports_tif_stem = str(exports_dir / name)

    shutil.copy(build_pdf, exports_pdf)
    subprocess.run(
        ["bash", "scripts/export_svg.sh", str(build_pdf), str(exports_svg)],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(
        ["pdftocairo", "-tiff", "-r", "600", "-singlefile", str(build_pdf), exports_tif_stem],
        cwd=REPO_ROOT,
        check=True,
    )
    subprocess.run(
        ["bash", "scripts/svg_to_png.sh", str(exports_svg), str(exports_png)],
        cwd=REPO_ROOT,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="fixture name under examples/")
    parser.add_argument("--force-golden", action="store_true", help="override TRACKED_GOLDEN protection")
    args = parser.parse_args()

    example_dir = REPO_ROOT / "examples" / args.name
    if not example_dir.is_dir():
        print(f"run_export.py: examples/{args.name}/ not found", file=sys.stderr)
        return 1

    build_pdf = example_dir / "build" / f"{args.name}.pdf"
    if not build_pdf.is_file():
        print(
            f"run_export.py: build/{args.name}.pdf not found; run /fig_compile first",
            file=sys.stderr,
        )
        return 1

    state = compute_export_state(example_dir, args.name)

    if state == EXPORT_FRESH:
        print(f"run_export.py: exports/ already FRESH for {args.name}; no-op")
        return 0

    if state == EXPORT_TRACKED_GOLDEN and not args.force_golden:
        print(
            f"run_export.py: exports/ for {args.name} is TRACKED_GOLDEN; "
            f"use --force-golden to overwrite",
            file=sys.stderr,
        )
        return 0  # not an error — golden protection is the success path

    _regenerate(example_dir, args.name)
    print(f"run_export.py: regenerated exports/ for {args.name} (was {state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6.2: Replace `commands/fig_export.md` with the new instructions**

Use Edit to replace the existing "Steps:" block. Old:

```markdown
Steps:
1. Verify compile succeeded (`examples/<name>/build/<name>.pdf` exists).
2. Copy PDF to `examples/<name>/exports/<name>.pdf`.
3. Run `bash scripts/export_svg.sh examples/<name>/build/<name>.pdf examples/<name>/exports/<name>.svg`.
4. For TIFF: `pdftocairo -tiff -r 600 -singlefile examples/<name>/build/<name>.pdf examples/<name>/exports/<name>`. For PNG 600 dpi: `bash scripts/svg_to_png.sh examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.png`.
5. Report file sizes and paths.
6. Suggest commit if user is happy: `git add -f examples/<name>/exports/<name>.pdf examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.tif examples/<name>/exports/<name>.png`.
```

New:

```markdown
Steps:
1. Run: `uv run python scripts/run_export.py <name>`. The orchestrator reads the exports/ sub-state and dispatches:
   - **MISSING** or **STALE** -> regenerate PDF / SVG / TIFF / PNG.
   - **FRESH** -> no-op.
   - **TRACKED_GOLDEN** -> skip with warning. Pass `--force-golden` to overwrite the curated golden artifacts (rare; only when intentionally rolling forward the reference).
2. Report file sizes and paths from the script output.
3. Suggest commit if user is happy: `git add -f examples/<name>/exports/<name>.pdf examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.tif examples/<name>/exports/<name>.png`. Only relevant for promoting a new golden fixture; routine work leaves exports/ ignored.
```

- [ ] **Step 6.3: Smoke-test the orchestrator on `_macro_smoke`**

```bash
bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex
rm -f examples/_macro_smoke/exports/*.pdf examples/_macro_smoke/exports/*.svg examples/_macro_smoke/exports/*.png examples/_macro_smoke/exports/*.tif
uv run python scripts/run_export.py _macro_smoke
ls examples/_macro_smoke/exports/
uv run python scripts/run_export.py _macro_smoke   # second invocation: no-op
```

Expected: first invocation regenerates 4 artifacts (PDF, SVG, TIFF, PNG); second prints `exports/ already FRESH ... no-op`.

- [ ] **Step 6.4: Run ruff**

```bash
uv run ruff check scripts/run_export.py
```

Expected: clean.

---

## Task 7: Layer A invariant — freshness assertion

Goal: After `run_export.py` returns success on a non-golden fixture, the freshness invariant must hold: `compute_pdf_content_hash(build/PDF) == compute_pdf_content_hash(exports/PDF)`.

**Files:**
- Extend: `tests/test_export_freshness.py` (append the invariant test)

- [ ] **Step 7.1: Append `test_freshness_invariant_after_export` to `tests/test_export_freshness.py`**

Add at the end of the file:

```python
def test_freshness_invariant_after_run_export(tmp_path: Path) -> None:
    """After run_export.py succeeds on a non-golden fixture, build/PDF and
    exports/PDF must hash-equal. Lock this as the Layer A always-on contract.
    """
    if shutil.which("lualatex") is None or shutil.which("dvisvgm") is None or shutil.which("rsvg-convert") is None or shutil.which("pdftocairo") is None:
        pytest.skip("requires lualatex, dvisvgm, rsvg-convert, pdftocairo")

    # Use a real fixture so all toolchain pieces are exercised.
    fixture_name = "_macro_smoke"
    fixture = REPO_ROOT / "examples" / fixture_name

    # Prime build/.
    subprocess.run(
        ["bash", "scripts/compile.sh", str(fixture / f"{fixture_name}.tex")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )

    # Prime exports/ via the orchestrator.
    result = subprocess.run(
        ["uv", "run", "python", "scripts/run_export.py", fixture_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    # Layer A invariant.
    from export_freshness import compute_pdf_content_hash  # noqa: PLC0415

    build_pdf = fixture / "build" / f"{fixture_name}.pdf"
    exports_pdf = fixture / "exports" / f"{fixture_name}.pdf"
    assert compute_pdf_content_hash(build_pdf) == compute_pdf_content_hash(exports_pdf), (
        "Layer A invariant violated: exports/PDF content hash differs from build/PDF "
        "after run_export.py reported success."
    )
```

- [ ] **Step 7.2: Run the new test**

```bash
uv run pytest tests/test_export_freshness.py::test_freshness_invariant_after_run_export -v
```

Expected: pass.

- [ ] **Step 7.3: Run ruff**

```bash
uv run ruff check tests/test_export_freshness.py
```

Expected: clean.

---

## Task 8: Add `export_pipeline_equivalence` to dogfood `spec.yaml`

Goal: Declare the AE threshold for the dogfood fixture. This is the only fixture opting into Layer B (per spec recommendation).

**Files:**
- Modify: `examples/dogfood_power_law_trap_pipeline/spec.yaml`

- [ ] **Step 8.1: Append the new section to `spec.yaml`**

Use Edit. The current file ends with `reference_image: reference/dogfood_concept.png`. Append:

```yaml
export_pipeline_equivalence:
  ae_max: 0.02      # AE / total_pixels upper bound; 0.02 = 2% with default fuzz
  fuzz_pct: 5       # passes through to magick compare -fuzz
```

Final tail of `spec.yaml` should look like:

```yaml
reference_image: reference/dogfood_concept.png
export_pipeline_equivalence:
  ae_max: 0.02
  fuzz_pct: 5
```

- [ ] **Step 8.2: Verify YAML parses cleanly**

```bash
uv run python -c "import yaml; print(yaml.safe_load(open('examples/dogfood_power_law_trap_pipeline/spec.yaml'))['export_pipeline_equivalence'])"
```

Expected: `{'ae_max': 0.02, 'fuzz_pct': 5}`.

---

## Task 9: Layer B opt-in equivalence smoke

Goal: Per-fixture `magick compare`-based assertion that `build/PNG` and `exports/PNG` agree within the declared AE threshold. Skips fixtures without `spec.yaml.export_pipeline_equivalence`.

**Files:**
- Create: `tests/test_export_pipeline_equivalence.py`

- [ ] **Step 9.1: Write the test file**

```python
"""Layer B: cross-pipeline equivalence smoke for fixtures opting in.

A fixture opts in by adding `export_pipeline_equivalence: { ae_max: <float> }`
to its spec.yaml. This test asserts that the AE (absolute error pixel count
under fuzz_pct% color tolerance) divided by total pixel count does not exceed
ae_max. Fixtures without the section are skipped — equivalence is forward-
looking insurance, not the operational fix.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fixtures_with_equivalence_contract() -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for spec_path in (REPO_ROOT / "examples").glob("*/spec.yaml"):
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(spec, dict) and isinstance(spec.get("export_pipeline_equivalence"), dict):
            out.append((spec_path.parent, spec))
    return out


@pytest.mark.skipif(
    shutil.which("magick") is None
    or shutil.which("lualatex") is None
    or shutil.which("dvisvgm") is None
    or shutil.which("rsvg-convert") is None,
    reason="requires magick, lualatex, dvisvgm, rsvg-convert",
)
@pytest.mark.parametrize(
    "fixture_dir,spec",
    _fixtures_with_equivalence_contract(),
    ids=lambda x: x.name if isinstance(x, Path) else "spec",
)
def test_layer_b_equivalence_smoke(fixture_dir: Path, spec: dict) -> None:
    """build/PNG and exports/PNG must agree within the declared AE threshold."""
    name = spec["name"]
    contract = spec["export_pipeline_equivalence"]
    ae_max = float(contract["ae_max"])
    fuzz_pct = int(contract.get("fuzz_pct", 5))

    # Prime build/ and exports/ via the canonical pipeline.
    subprocess.run(
        ["bash", "scripts/compile.sh", str(fixture_dir / f"{name}.tex")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "run", "python", "scripts/run_export.py", name],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )

    build_png = fixture_dir / "build" / f"{name}.png"
    exports_png = fixture_dir / "exports" / f"{name}.png"
    assert build_png.is_file(), build_png
    assert exports_png.is_file(), exports_png

    # magick compare exits 1 on any difference even within tolerance; capture metric instead.
    result = subprocess.run(
        [
            "magick", "compare",
            "-metric", "AE",
            "-fuzz", f"{fuzz_pct}%",
            str(build_png),
            str(exports_png),
            "null:",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # AE is reported on stderr as an integer (or "<int> (<float>)" with -compose).
    raw = result.stderr.strip().split()[0]
    ae = int(raw)

    # Compare to total pixels.
    dim_result = subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(build_png)],
        capture_output=True,
        text=True,
        check=True,
    )
    width, height = (int(s) for s in dim_result.stdout.split())
    total = width * height
    fraction = ae / total

    assert fraction <= ae_max, (
        f"Layer B equivalence violated for {name}: "
        f"AE={ae} ({fraction:.4f}) exceeds ae_max={ae_max:.4f}. "
        f"build/PNG and exports/PNG diverge beyond declared tolerance."
    )
```

- [ ] **Step 9.2: Run the test**

```bash
uv run pytest tests/test_export_pipeline_equivalence.py -v
```

Expected: 1 test passes (only `dogfood_power_law_trap_pipeline` opts in). Other fixtures auto-skip via the parametrize filter.

If the dogfood test fails because the measured AE fraction exceeds 0.02, investigate whether (i) the BellCurve or other intervening change perturbed AA beyond the expected envelope, or (ii) the threshold needs tuning. The previously measured 0.0149 leaves a 0.005 (33%) margin, so a single fixture change ought not push it over.

- [ ] **Step 9.3: Run ruff**

```bash
uv run ruff check tests/test_export_pipeline_equivalence.py
```

Expected: clean.

---

## Task 10: Documentation + final verification + atomic commit

Goal: Update workflow docs that describe the export pipeline; run full pytest + ruff; create a single feature commit.

**Files:**
- Modify: `docs/architecture-overview.md` (or `skills/figure-agent/SKILL.md` — confirm at task time which surface most accurately describes the pipeline contract)

- [ ] **Step 10.1: Locate the existing pipeline-contract documentation**

```bash
grep -rln 'fig_export\|exports/\|pdftocairo\|rsvg-convert' docs/ skills/ 2>&1 | head -10
```

Identify the file with the most authoritative "exports pipeline" description.

- [ ] **Step 10.2: Update that file with a paragraph explaining the new contract**

Append (or insert near the existing `/fig_export` description):

```markdown
### Export staleness contract (Layer 5)

`/fig_export` reads the `examples/<name>/exports/` sub-state — `MISSING`, `TRACKED_GOLDEN`, `STALE`, or `FRESH` — and dispatches:

- `MISSING` / `STALE` → regenerate PDF / SVG / TIFF / PNG from the current `build/<name>.pdf`.
- `FRESH` → no-op.
- `TRACKED_GOLDEN` → skip with warning. Use `--force-golden` to override (rare; intended for intentionally rolling forward the reference snapshot).

Sub-state is computed via content hash of the metadata-stripped qpdf-expansion (see `scripts/diff_pdf_content.py`'s `strip_metadata`). mtime is **not** used: it would be fragile to `git checkout`, `cp`, and `tar -x`.

Two contract layers guard the invariants:

- **Layer A (always on):** after `/fig_export` succeeds on a non-golden fixture, `build/<name>.pdf` and `exports/<name>.pdf` must hash-equal. Tested by `tests/test_export_freshness.py::test_freshness_invariant_after_run_export`.
- **Layer B (opt-in per-fixture):** fixtures declaring `export_pipeline_equivalence: { ae_max: <float> }` in `spec.yaml` are subject to a `magick compare`-based pixel equivalence assertion between `build/<name>.png` (pdftocairo direct) and `exports/<name>.png` (dvisvgm + rsvg-convert). Defaults to `fuzz_pct: 5`. Tested by `tests/test_export_pipeline_equivalence.py`.

Adding a new fixture to Layer B: edit its `spec.yaml`, set `ae_max` based on a measured baseline (run the test once, observe the printed AE fraction, add ~30% margin).
```

- [ ] **Step 10.3: Run full pytest**

```bash
uv run pytest -q 2>&1 | tail -3
```

Expected: 225 (BellCurve baseline) + 4 (test_git_tracked.py) + 5 (test_export_freshness.py: 4 sub-state + 1 invariant) + 1 (test_export_pipeline_equivalence.py for dogfood) + 1 (test_status.py new field) ≈ 236 passed. Exact count may differ ±2 depending on the existing `tests/test_status.py` shape.

- [ ] **Step 10.4: Run ruff**

```bash
uv run ruff check .
```

Expected: clean.

- [ ] **Step 10.5: Confirm git status**

```bash
git status --short
```

Expected: 5 new files (`scripts/git_tracked.py`, `scripts/export_freshness.py`, `scripts/run_export.py`, `tests/test_git_tracked.py`, `tests/test_export_freshness.py`, `tests/test_export_pipeline_equivalence.py`) and 4 modified files (`scripts/diff_pdf_content.py`, `scripts/status.py`, `commands/fig_export.md`, `examples/dogfood_power_law_trap_pipeline/spec.yaml`, `tests/test_status.py`, plus the doc file from Step 10.2).

- [ ] **Step 10.6: Stage explicitly and commit**

```bash
git add \
  plugins/figure-agent/scripts/git_tracked.py \
  plugins/figure-agent/scripts/export_freshness.py \
  plugins/figure-agent/scripts/run_export.py \
  plugins/figure-agent/scripts/diff_pdf_content.py \
  plugins/figure-agent/scripts/status.py \
  plugins/figure-agent/commands/fig_export.md \
  plugins/figure-agent/examples/dogfood_power_law_trap_pipeline/spec.yaml \
  plugins/figure-agent/tests/test_git_tracked.py \
  plugins/figure-agent/tests/test_export_freshness.py \
  plugins/figure-agent/tests/test_export_pipeline_equivalence.py \
  plugins/figure-agent/tests/test_status.py \
  plugins/figure-agent/docs/architecture-overview.md
git status
```

Stage only the files listed (avoid `git add -A`). Adjust the doc path in 10.2 if Step 10.1 located a different file.

```bash
git commit -m "$(cat <<'EOF'
feat(layer5): export-pipeline staleness detection + auto-rebuild

The original "Layer 5 inconsistency" hypothesis (rsvg-convert mis-rasterizes
SVG paths) was empirically refuted during the design phase: the build/
(pdftocairo) and exports/ (dvisvgm + rsvg-convert) pipelines produce
equivalent output modulo anti-aliasing (n=2 measurement: _macro_smoke 0.39%,
dogfood 1.49%). The actual problem was staleness — exports/ never auto-
rebuilds when build/ updates.

This commit ships:

- /fig_status learns MISSING | TRACKED_GOLDEN | STALE | FRESH for exports/
  via content-hash comparison (qpdf metadata-strip pipeline reused from
  scripts/diff_pdf_content.py; mtime intentionally avoided as fragile).
- /fig_export becomes a single-line uv-run invocation of the new
  scripts/run_export.py orchestrator. Auto-rebuilds STALE / MISSING.
  TRACKED_GOLDEN is honored unless --force-golden overrides.
- Layer A always-on contract: build/PDF and exports/PDF must hash-equal
  after /fig_export. Tested in tests/test_export_freshness.py.
- Layer B per-fixture opt-in contract: spec.yaml.export_pipeline_equivalence
  declares ae_max for magick-compare pixel-equivalence assertion. Currently
  declared on dogfood_power_law_trap_pipeline (ae_max: 0.02) only.

Spec: docs/superpowers/specs/2026-05-02-layer5-export-staleness-design.md
Plan: docs/superpowers/plans/2026-05-02-layer5-export-staleness.md

Resolves the BellCurve PR's "Paired prerequisite" by re-scoping it from
"diagnose rasterizer divergence" to "fix exports staleness."

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 10.7: Confirm clean working tree**

```bash
git status
git log --oneline main..HEAD
```

Expected: clean working tree (only untracked artifacts in `examples/<name>/build/exports/previews/` from compile-time output are tolerated). Latest commit on the branch is the feature commit; the branch is now ready for PR creation.

---

## Post-plan: PR

This plan does not create the PR. After Task 10's commit lands, the user opens a PR via:

```bash
gh pr create --title "feat(layer5): export-pipeline staleness + auto-rebuild" \
  --body-file <draft body referencing spec, plan, and BellCurve PR resolution>
```

The PR body should:
- Link the spec (`docs/superpowers/specs/2026-05-02-layer5-export-staleness-design.md`)
- Link the BellCurve PR (#1) and note that the "Paired prerequisite" mentioned in that spec is now resolved by this PR.
- Surface the empirical measurement table (n=2: `_macro_smoke` 0.39%, `dogfood` 1.49%) so reviewers can see the threshold rationale.

---

## Self-review checklist

- **Spec coverage:** Spec's "Implementation order" 10 steps map to Tasks 1-10 (with Task 1 = pre-work verification, Tasks 2-9 = spec steps 1-8, Task 10 = spec steps 9-10 bundled).
- **No placeholders:** Every code block above is the literal code/command the executor types. No "TODO" / "TBD" / hand-waving. The single open detail (the specific doc file in 10.1) is flagged as a one-grep operation; the executor confirms at task time.
- **Type/identifier consistency:** `compute_export_state`, `compute_pdf_content_hash`, `EXPORT_FRESH | EXPORT_MISSING | EXPORT_STALE | EXPORT_TRACKED_GOLDEN`, `is_tracked` used identically across Tasks 3-9. The orchestrator's `--force-golden` flag matches the doc's documented flag.
- **Sequencing safety:** Task 1 verifies BellCurve PR is merged before any code change. Tests written before implementation in Tasks 3-4 (TDD). Layer A test (Task 7) follows orchestrator (Task 6). Layer B test (Task 9) follows the spec.yaml declaration (Task 8) so the parametrize sees the dogfood entry.
- **Acknowledgment:** Cross-branch dependency (BellCurve PR #1 → this branch) explicit at the top of the plan.
