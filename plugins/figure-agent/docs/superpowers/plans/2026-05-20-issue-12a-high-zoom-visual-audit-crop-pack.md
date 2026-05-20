# High-Zoom Visual Audit Crop Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic high-zoom visual audit crops to `/fig_critique` so host-LLM review sees micro-defects that are missed in full-render and standard panel-crop views.

**Architecture:** Keep `/fig_critique` host-LLM-only. Add a small image-crop helper that writes ephemeral PNG crops under `build/audit_crops/`, then make `critique_brief.py` list those crops and require a closed-set micro-visual audit in the host prompt. These crops are visual attention crops, not semantic sub-regions or patch targets. Do not change status, loop, export, accepted, golden, or final-artifact behavior.

**Tech Stack:** Python 3.12, Pillow, pytest, ruff, Claude plugin validation.

---

## File Structure

- Create: `plugins/figure-agent/scripts/critique_zoom_crops.py`
  - Owns deterministic crop generation and relative metadata.
- Create: `plugins/figure-agent/tests/test_critique_zoom_crops.py`
  - Unit-tests crop coordinates, file naming, and no-source-mutation behavior.
- Modify: `plugins/figure-agent/scripts/critique_brief.py`
  - Calls the crop helper and emits `## High-Zoom Visual Audit Crops`.
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`
  - Locks brief section text and integration with panel crops.
- Modify: `plugins/figure-agent/commands/fig_critique.md`
  - Tells the host to Read the audit crops and inspect closed-set micro-defects.

## Task 1: Pure 2x2 Crop Helper

**Files:**
- Create: `plugins/figure-agent/scripts/critique_zoom_crops.py`
- Test: `plugins/figure-agent/tests/test_critique_zoom_crops.py`

- [ ] **Step 1: Write the failing tests**

Add:

```python
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_zoom_crops import build_zoom_crop_pack  # noqa: E402


def _write_png(path: Path, size: tuple[int, int] = (120, 80)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "white").save(path)


def test_build_zoom_crop_pack_creates_full_render_quadrants(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    _write_png(render)

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=())

    assert [item["id"] for item in crops] == [
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
    ]
    assert all((example_dir / item["path"]).is_file() for item in crops)
    assert crops[0]["source"] == "full_render"
    assert crops[0]["bbox_px"] == [0, 0, 60, 40]
    assert crops[3]["bbox_px"] == [60, 40, 120, 80]


def test_build_zoom_crop_pack_adds_panel_quadrants(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    panel = example_dir / "build" / "panel_crops" / "A.png"
    _write_png(render)
    _write_png(panel, size=(80, 60))

    crops = build_zoom_crop_pack(example_dir, render, panel_crop_paths=(panel,))

    ids = [item["id"] for item in crops]
    assert "panel_A_q1" in ids
    assert "panel_A_q4" in ids
    assert (example_dir / "build" / "audit_crops" / "panel_A_q1.png").is_file()


def test_build_zoom_crop_pack_rejects_non_fixture_relative_panel_crop(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "demo"
    render = example_dir / "build" / "demo.png"
    outside = tmp_path / "outside.png"
    _write_png(render)
    _write_png(outside)

    try:
        build_zoom_crop_pack(example_dir, render, panel_crop_paths=(outside,))
    except ValueError as exc:
        assert "panel crop must be inside example_dir" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_critique_zoom_crops.py
```

Expected: import error for `critique_zoom_crops`.

- [ ] **Step 3: Implement minimal helper**

Create `scripts/critique_zoom_crops.py`:

```python
"""High-zoom audit crop generation for critique briefs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image


def _safe_stem(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return safe.strip("._") or "crop"


def _relative_to_example(example_dir: Path, path: Path) -> str:
    return str(path.relative_to(example_dir))


def _quadrant_boxes(width: int, height: int) -> list[list[int]]:
    mid_x = width // 2
    mid_y = height // 2
    return [
        [0, 0, mid_x, mid_y],
        [mid_x, 0, width, mid_y],
        [0, mid_y, mid_x, height],
        [mid_x, mid_y, width, height],
    ]


def _write_quadrants(
    *,
    source_path: Path,
    output_dir: Path,
    id_prefix: str,
    source_label: str,
    example_dir: Path,
) -> list[dict[str, Any]]:
    crops: list[dict[str, Any]] = []
    with Image.open(source_path) as image:
        width, height = image.size
        for index, box in enumerate(_quadrant_boxes(width, height), start=1):
            crop_id = f"{id_prefix}_q{index}"
            output_path = output_dir / f"{crop_id}.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.crop(tuple(box)).save(output_path)
            crops.append(
                {
                    "id": crop_id,
                    "source": source_label,
                    "path": _relative_to_example(example_dir, output_path),
                    "source_path": _relative_to_example(example_dir, source_path),
                    "bbox_px": box,
                }
            )
    return crops


def build_zoom_crop_pack(
    example_dir: Path,
    render_path: Path,
    *,
    panel_crop_paths: tuple[Path, ...],
) -> list[dict[str, Any]]:
    output_dir = example_dir / "build" / "audit_crops"
    crops = _write_quadrants(
        source_path=render_path,
        output_dir=output_dir,
        id_prefix="full",
        source_label="full_render",
        example_dir=example_dir,
    )
    for panel_crop_path in panel_crop_paths:
        try:
            panel_crop_path.relative_to(example_dir)
        except ValueError as exc:
            raise ValueError("panel crop must be inside example_dir") from exc
        panel_id = _safe_stem(panel_crop_path.stem)
        crops.extend(
            _write_quadrants(
                source_path=panel_crop_path,
                output_dir=output_dir,
                id_prefix=f"panel_{panel_id}",
                source_label=f"panel:{panel_id}",
                example_dir=example_dir,
            )
        )
    return crops
```

- [ ] **Step 4: Run tests and confirm GREEN**

Run:

```bash
uv run pytest -q tests/test_critique_zoom_crops.py
```

Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/critique_zoom_crops.py tests/test_critique_zoom_crops.py
git commit -m "Add high-zoom critique crop helper"
```

## Task 2: Wire Crop Pack Into Critique Brief

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_brief.py`
- Modify: `plugins/figure-agent/tests/test_critique_brief.py`

- [ ] **Step 1: Write failing brief integration tests**

Add:

```python
def test_critique_brief_includes_high_zoom_audit_crops(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir)

    brief = generate_for(example_dir)

    assert "## High-Zoom Visual Audit Crops" in brief
    assert "`examples/review_demo/build/audit_crops/full_q1.png`" in brief
    assert "`examples/review_demo/build/audit_crops/full_q4.png`" in brief
    assert "line_crosses_label" in brief
    assert "arrow_tip_fused" in brief
    assert (example_dir / "build" / "audit_crops" / "full_q1.png").is_file()


def test_critique_brief_includes_panel_high_zoom_crops(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir)
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (80, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: A\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "`examples/review_demo/build/panel_crops/A.png`" in brief
    assert "`examples/review_demo/build/audit_crops/panel_A_q1.png`" in brief
    assert "`examples/review_demo/build/audit_crops/panel_A_q4.png`" in brief
```

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_high_zoom_audit_crops tests/test_critique_brief.py::test_critique_brief_includes_panel_high_zoom_crops
```

Expected: fail because the section and crops are not emitted.

- [ ] **Step 3: Return panel crop paths from `_panel_reference_sections`**

Change `_panel_reference_sections` to return a third value:

```python
def _panel_reference_sections(
    example_dir: Path, spec: dict, png_path: Path, pdf_path: Path
) -> tuple[str, str, tuple[Path, ...]]:
    contexts: list[str] = []
    warnings: list[str] = []
    panel_crop_paths: list[Path] = []
```

After successful `_crop_panel_png(...)`, append:

```python
panel_crop_paths.append(crop_path)
```

Return:

```python
return warning_section, context_section, tuple(panel_crop_paths)
```

Update the call site:

```python
panel_warning_section, panel_context_section, panel_crop_paths = _panel_reference_sections(
    example_dir, spec, png_path, pdf_path
)
```

- [ ] **Step 4: Emit high-zoom audit section**

Import:

```python
from critique_zoom_crops import build_zoom_crop_pack
```

Add helper:

```python
_MICRO_DEFECT_CHECKS = (
    "line_crosses_label",
    "wire_crosses_label",
    "arrow_tip_fused",
    "label_target_detached",
    "floating_semantic_cue",
    "drawing_order_suspect",
)


def _zoom_audit_section(example_dir: Path, crops: list[dict]) -> str:
    if not crops:
        return ""
    lines = [
        "## High-Zoom Visual Audit Crops",
        "Host LLM MUST inspect these crops before finalizing `critique.md`.",
        "For each crop, check these closed-set micro-defects: "
        + ", ".join(_MICRO_DEFECT_CHECKS)
        + ".",
        "",
    ]
    for crop in crops:
        lines.append(
            f"- `{_example_relative_path(example_dir, example_dir / crop['path'])}` "
            f"from `{_example_relative_path(example_dir, example_dir / crop['source_path'])}` "
            f"bbox_px={crop['bbox_px']}"
        )
    return "\n" + "\n".join(lines) + "\n"
```

In `generate_for`, after panel context generation:

```python
zoom_crops = build_zoom_crop_pack(
    example_dir,
    png_path,
    panel_crop_paths=panel_crop_paths,
)
zoom_audit_section = _zoom_audit_section(example_dir, zoom_crops)
```

Place `{zoom_audit_section}` after `{image_context_sections}` and before
`## Author intent`.

- [ ] **Step 5: Run targeted tests**

Run:

```bash
uv run pytest -q tests/test_critique_zoom_crops.py tests/test_critique_brief.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/critique_brief.py tests/test_critique_brief.py
git commit -m "Surface high-zoom crops in critique brief"
```

## Task 3: Update Slash Command Contract

**Files:**
- Modify: `plugins/figure-agent/commands/fig_critique.md`

- [ ] **Step 1: Add command-facing behavior**

In step 2 of `/fig_critique`, add:

```markdown
If the brief contains `## High-Zoom Visual Audit Crops`, also Read every listed
crop before writing `critique.md`. Inspect each crop for the closed-set
micro-defects named in the brief. Do not treat a clean full-render view as
proof that high-zoom crops are clean.
```

In step 3, add:

```markdown
High-zoom crop findings must be represented as normal panel/top-level findings
for the 12A evidence-only slice. Issue 12B supersedes this with first-class
`micro_defects` schema evidence.
```

- [ ] **Step 2: Validate docs**

Run:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add commands/fig_critique.md
git commit -m "Document high-zoom critique audit reads"
```

## Task 4: Regression and Review Loop

**Files:**
- Review all files changed by Tasks 1-3.

- [ ] **Step 1: Run focused verification**

```bash
uv run pytest -q tests/test_critique_zoom_crops.py tests/test_critique_brief.py
uv run ruff check scripts/critique_zoom_crops.py scripts/critique_brief.py tests/test_critique_zoom_crops.py tests/test_critique_brief.py
```

Expected: pass.

- [ ] **Step 2: Run full verification**

```bash
uv run pytest -q
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: pass.

- [ ] **Step 3: Review 1, crop correctness**

Check:

- full-render crop quadrants cover the image without gaps;
- panel crop quadrants use the actual generated panel crop image;
- crop output paths are deterministic;
- helper refuses paths outside `example_dir`;
- no source or export artifact is touched.

Fix any defect, rerun focused verification, and repeat this review until clean.

- [ ] **Step 4: Review 2, host-LLM usability**

Check:

- brief tells the host to Read every crop;
- micro-defect terms are closed-set and concrete;
- the host is warned not to trust full-render cleanliness;
- panel-reference warning behavior is preserved.

Fix any defect, rerun focused verification, and repeat this review until clean.

- [ ] **Step 5: Review 3, scope containment**

Check:

- no schema v1.4 work slipped in;
- no status/export/loop/accepted/golden behavior changed;
- no external API or Gemini integration was added;
- no existing example source or critique file was modified.

Fix any defect, rerun focused verification, and repeat this review until clean.

- [ ] **Step 6: Final commit if review fixes were needed**

```bash
git status --short
git add scripts/critique_zoom_crops.py scripts/critique_brief.py tests/test_critique_zoom_crops.py tests/test_critique_brief.py commands/fig_critique.md
git commit -m "Harden high-zoom critique audit pack"
```

Only run the final commit if there are review-fix changes after Tasks 1-3.

## Self-Review

Spec coverage:

- Issue 12A crop generation is covered by Tasks 1 and 2.
- Brief and command-facing behavior are covered by Tasks 2 and 3.
- No-mutation and scope containment are covered by Task 4.
- Full-render fallback for fixtures without panel references is covered by
  `test_critique_brief_includes_high_zoom_audit_crops`.
- Panel crop integration is covered by
  `test_critique_brief_includes_panel_high_zoom_crops`.

Placeholder scan:

- This plan contains no placeholder markers and no deferred implementation
  steps inside Issue 12A.

Type consistency:

- The public helper is `build_zoom_crop_pack(...)`.
- Crop metadata keys are `id`, `source`, `path`, `source_path`, and `bbox_px`.
- The brief helper consumes those exact keys.
