# Geometry-Aware Truth Lock — Implementation Plan (figure-agent v2, Slice 0 · Plan 1 of 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `svg_semantic_diff` geometry-aware so a `path_rewrite` that preserves path *count* but corrupts a truth-bearing curve's *shape* (smoothing a cusp, ramping a step) is caught as a BLOCKER — closing the #1 verified risk before any drawing op exists.

**Architecture:** Add a pure-geometry module (`svg_path_geometry.py`) that canonicalizes a path's `d` to a dense arc-length-sampled polyline and derives a representation-invariant signature (corner count via turning-angle threshold, curvature-sign run-lengths, sampled points for discrete Fréchet). Extend `_inventory` to attach a signature to every path tagged `data-truth-bearing != "false"` (default truth-bearing). Extend `_compare` to flag a BLOCKER `geometry_truth_violation` when a same-id truth path's signature changes or drifts past a per-figure Fréchet bound. Add the per-path op gate to recipe validation so a centerline-altering action on a truth path is rejected at plan time.

**Tech Stack:** Python 3.12, `svgpathtools` (new dep), stdlib `xml.etree`, `pytest` (existing, `tmp_path` fixtures). No lxml needed (the module already uses `xml.etree`).

**Spec:** `../specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md` §5–§7. Plan covers Slice 0 pieces (1) geometry-aware diff + (2) truth model/gate. Plans 2–4 (hand:* overlay/occlusion guard, shipped-artifact PDF/CMYK gate, `add_volume_shading` proof op) follow.

**Run tests:** from `plugins/figure-agent/`: `uv run pytest tests/ -q` (testpaths=["tests"]). Single test: `uv run pytest tests/<file>::<test> -v`.

**Import convention (verified against existing tests):** `scripts/` is **not** a package. Every test module begins with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))`, then imports modules by **bare name** (`from svg_path_geometry import …  # noqa: E402`). Source modules import their siblings the same bare way (e.g. `svg_semantic_diff.py` does `from svg_path_geometry import shape_signature`). Imports placed below the preamble keep the `# noqa: E402`.

---

## File Structure

- **Create** `scripts/svg_path_geometry.py` — pure geometry: canonicalization + signature + Fréchet. One responsibility, no SVG-tree or I/O concerns.
- **Create** `tests/test_svg_path_geometry.py` — unit tests for the geometry module (no SVG files; complex-number polylines).
- **Modify** `scripts/svg_semantic_diff.py` — `_inventory` attaches per-truth-path signatures (`:172-255`); `_compare` adds the geometry block (`:275-391`); add `geometry_truth_violation` to `FINDING_KINDS` (`:22`); read an optional per-figure `frechet_bound`.
- **Modify** `tests/test_svg_semantic_diff.py` — add cusp-falsehood, resample-invariance, decorative-allowed, and identical-pass cases (uses `tmp_path` SVG files).
- **Modify** `scripts/svg_polish_recipe.py` — per-path op gate: a centerline-altering `action_class` targeting a truth-bearing path is rejected in validation (`:115` dispatch area).
- **Modify** `pyproject.toml` — add `svgpathtools` to deps (`:30-34` area).

---

## Task 1: Geometry module — canonical dense polyline

**Files:**
- Create: `scripts/svg_path_geometry.py`
- Test: `tests/test_svg_path_geometry.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the dependency**

In `pyproject.toml`, add `"svgpathtools>=1.6.1"` to the `dependencies` array (the same array that holds `pytest`-adjacent runtime deps). Then:

Run: `cd plugins/figure-agent && uv sync`
Expected: resolves and installs `svgpathtools`.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_svg_path_geometry.py
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_path_geometry import canonical_polyline  # noqa: E402

def test_canonical_polyline_is_resample_invariant():
    # Same straight line, two different d-representations (1 segment vs 3).
    coarse = canonical_polyline("M0,0 L9,0", samples=64)
    fine = canonical_polyline("M0,0 L3,0 L6,0 L9,0", samples=64)
    assert len(coarse) == 64 and len(fine) == 64
    # Arc-length sampling makes them point-wise near-identical.
    max_dev = max(abs(a - b) for a, b in zip(coarse, fine))
    assert max_dev < 1e-6
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/test_svg_path_geometry.py::test_canonical_polyline_is_resample_invariant -v`
Expected: FAIL — `ModuleNotFoundError: scripts.svg_path_geometry`.

- [ ] **Step 4: Implement `canonical_polyline`**

```python
# scripts/svg_path_geometry.py
"""Pure geometry for the truth lock: canonical sampling + shape signature.

No SVG-tree or file I/O here — input is a path 'd' string, output is plain
numbers. Keeps the geometry math testable in isolation.
"""
from __future__ import annotations

from svgpathtools import parse_path


def canonical_polyline(d: str, *, samples: int = 256) -> list[complex]:
    """Resample every subpath of `d` to `samples` points by arc length.

    Arc-length sampling is representation-invariant: two `d` strings that draw
    the same curve return near-identical point lists regardless of how many
    segments or control points each uses. Subpaths are concatenated in order.
    """
    path = parse_path(d)
    if path.length() == 0:
        # Degenerate (point/empty): repeat the start so callers get `samples` pts.
        start = path.start if len(path) else 0j
        return [start] * samples
    return [path.point(i / (samples - 1)) for i in range(samples)]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_svg_path_geometry.py::test_canonical_polyline_is_resample_invariant -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_path_geometry.py tests/test_svg_path_geometry.py pyproject.toml uv.lock
git commit -m "feat(geometry): arc-length canonical polyline (resample-invariant)"
```

---

## Task 2: Shape signature — corners + curvature-sign runs

**Files:**
- Modify: `scripts/svg_path_geometry.py`
- Test: `tests/test_svg_path_geometry.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_svg_path_geometry.py  (append)
from svg_path_geometry import shape_signature

def test_signature_detects_cusp_removal():
    # A sharp V (cusp) vs a smoothed arc between the same endpoints.
    cusp = shape_signature("M0,0 L5,5 L10,0")          # one sharp corner
    smooth = shape_signature("M0,0 Q5,5 10,0")          # no corner
    assert cusp.corner_count == 1
    assert smooth.corner_count == 0
    assert cusp != smooth

def test_signature_is_resample_invariant():
    a = shape_signature("M0,0 L5,5 L10,0")
    b = shape_signature("M0,0 L2.5,2.5 L5,5 L7.5,2.5 L10,0")  # same shape, more pts
    assert a == b
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_path_geometry.py -k signature -v`
Expected: FAIL — `cannot import name 'shape_signature'`.

- [ ] **Step 3: Implement `shape_signature`**

```python
# svg_path_geometry.py  (append)
import cmath
from dataclasses import dataclass

CORNER_TURN_THRESHOLD = math.radians(35.0)  # turning angle that counts as a corner
_FLAT = 1e-3  # below this |turn| the segment is treated as straight


@dataclass(frozen=True)
class ShapeSignature:
    corner_count: int
    sign_pattern: tuple[int, ...]  # consecutive distinct turn-signs (inflection structure)


def _turn_angles(points: list[complex]) -> list[float]:
    """Signed turn angle at each interior vertex (left = +, right = -)."""
    angles: list[float] = []
    for i in range(1, len(points) - 1):
        v1 = points[i] - points[i - 1]
        v2 = points[i + 1] - points[i]
        if v1 == 0 or v2 == 0:
            angles.append(0.0)
            continue
        angles.append(cmath.phase(v2 / v1))  # signed turn in (-pi, pi]
    return angles


def shape_signature(d: str, *, samples: int = 256) -> ShapeSignature:
    pts = canonical_polyline(d, samples=samples)
    turns = _turn_angles(pts)
    corner_count = sum(1 for a in turns if abs(a) >= CORNER_TURN_THRESHOLD)
    # Collapse consecutive equal turn-signs to one entry. The PATTERN of
    # left/straight/right transitions is resample-invariant (run *lengths* are
    # not, so they are dropped); it captures inflection structure.
    pattern: list[int] = []
    for a in turns:
        sign = (a > _FLAT) - (a < -_FLAT)  # +1 / 0 / -1
        if not pattern or pattern[-1] != sign:
            pattern.append(sign)
    return ShapeSignature(corner_count=corner_count, sign_pattern=tuple(pattern))
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_path_geometry.py -k signature -v`
Expected: PASS (both). If `test_signature_is_resample_invariant` is flaky at the run-length tail, raise `samples` to 512 — denser sampling makes the sign sequence converge.

- [ ] **Step 5: Commit**

```bash
git add scripts/svg_path_geometry.py tests/test_svg_path_geometry.py
git commit -m "feat(geometry): resample-invariant shape signature (corners + curvature-sign runs)"
```

---

## Task 3: Discrete Fréchet distance

**Files:**
- Modify: `scripts/svg_path_geometry.py`
- Test: `tests/test_svg_path_geometry.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_svg_path_geometry.py  (append)
from svg_path_geometry import canonical_polyline, frechet_distance

def test_frechet_zero_for_identical_and_grows_with_drift():
    a = canonical_polyline("M0,0 L10,0", samples=64)
    same = canonical_polyline("M0,0 L5,0 L10,0", samples=64)   # same line
    drift = canonical_polyline("M0,0 Q5,3 10,0", samples=64)   # bows up ~3 units
    assert frechet_distance(a, same) < 1e-6
    assert frechet_distance(a, drift) > 1.0
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_svg_path_geometry.py::test_frechet_zero_for_identical_and_grows_with_drift -v`
Expected: FAIL — `cannot import name 'frechet_distance'`.

- [ ] **Step 3: Implement `frechet_distance` (iterative DP)**

```python
# scripts/svg_path_geometry.py  (append)
def frechet_distance(p: list[complex], q: list[complex]) -> float:
    """Discrete Fréchet distance between two polylines (iterative, O(n*m))."""
    n, m = len(p), len(q)
    if n == 0 or m == 0:
        return float("inf")
    prev = [0.0] * m
    for i in range(n):
        cur = [0.0] * m
        for j in range(m):
            d = abs(p[i] - q[j])
            if i == 0 and j == 0:
                cur[j] = d
            elif i == 0:
                cur[j] = max(cur[j - 1], d)
            elif j == 0:
                cur[j] = max(prev[j], d)
            else:
                cur[j] = max(min(prev[j], prev[j - 1], cur[j - 1]), d)
        prev = cur
    return prev[-1]
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_svg_path_geometry.py::test_frechet_zero_for_identical_and_grows_with_drift -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/svg_path_geometry.py tests/test_svg_path_geometry.py
git commit -m "feat(geometry): discrete Fréchet distance"
```

---

## Task 4: `_inventory` attaches per-truth-path geometry

**Files:**
- Modify: `scripts/svg_semantic_diff.py` (`_inventory` `:172-255`)
- Test: `tests/test_svg_semantic_diff.py`

A path is **truth-bearing unless** it carries `data-truth-bearing="false"`. Only truth-bearing paths get a signature + sampled polyline keyed by `id`. (Paths without an `id` are addressed by position later; out of scope for Plan 1 — only id'd truth paths are guarded now, which covers the SC-7-style named-element figures.)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_svg_semantic_diff.py  (append; reuse existing imports / add as needed)
from pathlib import Path
from svg_semantic_diff import _inventory

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    '<path id="boundary" d="M0,0 L5,5 L10,0"/>'
    '<path id="decor" data-truth-bearing="false" d="M0,9 L10,9"/>'
    '</svg>'
)

def test_inventory_signs_only_truth_paths(tmp_path: Path):
    f = tmp_path / "a.svg"; f.write_text(SVG)
    inv = _inventory(f)
    assert "boundary" in inv["truth_geometry"]
    assert "decor" not in inv["truth_geometry"]
    assert inv["truth_geometry"]["boundary"]["signature"].corner_count == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_svg_semantic_diff.py::test_inventory_signs_only_truth_paths -v`
Expected: FAIL — `KeyError: 'truth_geometry'`.

- [ ] **Step 3: Extend `_inventory`**

In `scripts/svg_semantic_diff.py`, add the import near the top:
```python
from svg_path_geometry import shape_signature, canonical_polyline
```
Inside `_inventory`, before the `return {`, add a `truth_geometry` accumulator. In the `for element in root.iter():` loop, in the `if tag == "path":` branch (`:202-203`), extend it:
```python
        if tag == "path":
            path_count += 1
            d = element.attrib.get("d")
            truth_bearing = element.attrib.get("data-truth-bearing") != "false"
            if d and truth_bearing and element_id:
                truth_geometry[element_id] = {
                    "signature": shape_signature(d),
                    "polyline": canonical_polyline(d),
                }
```
Declare `truth_geometry: dict[str, dict[str, Any]] = {}` with the other accumulators (near `:183`), and add `"truth_geometry": truth_geometry,` to the returned dict (near `:247`).

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_svg_semantic_diff.py::test_inventory_signs_only_truth_paths -v`
Expected: PASS.

- [ ] **Step 5: Run the full existing suite (no regressions)**

Run: `uv run pytest tests/test_svg_semantic_diff.py -q`
Expected: all existing tests still PASS (the new key is additive).

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_semantic_diff.py tests/test_svg_semantic_diff.py
git commit -m "feat(lock): _inventory attaches geometry signatures to id'd truth paths"
```

---

## Task 5: `_compare` flags geometry truth violations

**Files:**
- Modify: `scripts/svg_semantic_diff.py` (`FINDING_KINDS` `:22`, `_compare` `:275-391`)
- Test: `tests/test_svg_semantic_diff.py`

Default Fréchet bound is **per-figure, declared** (§5 H4) — not a global constant. Plan 1 threads it as a parameter with a conservative default of `0.5` user units; the recipe/brief supplies the real value later.

- [ ] **Step 1: Write the failing tests (the §6 fixtures)**

```python
# tests/test_svg_semantic_diff.py  (append)
from svg_semantic_diff import _inventory, _compare

def _inv(tmp_path, name, svg):
    f = tmp_path / name; f.write_text(svg); return _inventory(f)

BASE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="boundary" d="{d}"/></svg>')

def test_cusp_falsehood_is_blocked(tmp_path):
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))      # cusp
    pol = _inv(tmp_path, "p.svg", BASE.format(d="M0,0 Q5,5 10,0"))       # smoothed
    findings = _compare(src, pol)
    kinds = {f["kind"] for f in findings}
    assert "geometry_truth_violation" in kinds
    assert any(f["severity"] == "BLOCKER" for f in findings if f["kind"] == "geometry_truth_violation")

def test_pure_resample_passes(tmp_path):
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(tmp_path, "p.svg", BASE.format(d="M0,0 L2.5,2.5 L5,5 L7.5,2.5 L10,0"))
    assert not [f for f in _compare(src, pol) if f["kind"] == "geometry_truth_violation"]

def test_decorative_reshape_allowed(tmp_path):
    dec = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path id="d1" data-truth-bearing="false" d="{d}"/></svg>'
    src = _inv(tmp_path, "s.svg", dec.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(tmp_path, "p.svg", dec.format(d="M0,0 Q5,5 10,0"))
    assert not [f for f in _compare(src, pol) if f["kind"] == "geometry_truth_violation"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "cusp or resample or decorative_reshape" -v`
Expected: FAIL — `geometry_truth_violation` never added.

- [ ] **Step 3: Add the finding kind + the compare block**

Add `"geometry_truth_violation",` to the `FINDING_KINDS` frozenset (`:22-32`). Change `_compare`'s signature to accept the bound:
```python
def _compare(source, polished, *, frechet_bound: float = 0.5):
```
At the end of `_compare`, before `return findings`, add:
```python
    from svg_path_geometry import frechet_distance
    src_geo = source.get("truth_geometry", {})
    pol_geo = polished.get("truth_geometry", {})
    for element_id, src_entry in sorted(src_geo.items()):
        pol_entry = pol_geo.get(element_id)
        if pol_entry is None:
            continue  # disappearance handled by the existing inventory/text findings
        if src_entry["signature"] != pol_entry["signature"]:
            add(
                "geometry_truth_violation",
                "BLOCKER",
                f"truth path #{element_id} shape signature changed "
                f"({src_entry['signature']} -> {pol_entry['signature']})",
                SEMANTIC_DIFF_BACKPORT,
            )
            continue
        drift = frechet_distance(src_entry["polyline"], pol_entry["polyline"])
        if drift > frechet_bound:
            add(
                "geometry_truth_violation",
                "BLOCKER",
                f"truth path #{element_id} drifted {drift:.3f} > bound {frechet_bound}",
                SEMANTIC_DIFF_BACKPORT,
            )
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "cusp or resample or decorative_reshape" -v`
Expected: PASS (all three).

- [ ] **Step 5: Thread the bound through the public entry + full suite**

In `build_svg_semantic_diff_report` (`:400`), accept `frechet_bound: float = 0.5` and pass it to `_compare(...)`. Then:

Run: `uv run pytest tests/ -q`
Expected: full suite PASS (new behavior is additive; existing reports unaffected when no truth-geometry change occurs).

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_semantic_diff.py tests/test_svg_semantic_diff.py
git commit -m "feat(lock): geometry_truth_violation BLOCKER for cusp/shape/drift on truth paths"
```

---

## Task 6: Per-path op gate at recipe validation time

**Files:**
- Modify: `scripts/svg_polish_recipe.py` (validation near `:115`)
- Test: `tests/test_svg_polish_recipe*` or `tests/test_svg_semantic_diff.py`

The recipe schema does not yet carry `action_class`/`layer` (that is Plan 2's v2-schema work). For Plan 1, add the **forward gate**: a recipe action whose `type` is in a new `CENTERLINE_ALTERING` set, targeting a selector that resolves to a truth-bearing path, is rejected. Until the v2 schema lands, `CENTERLINE_ALTERING` is empty (no such action types exist yet — verified: `ACTION_TYPES` is 5 scalar setters), so this task installs the *gate mechanism + its test* with a synthetic action type, ready for Plan 3's B ops.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_truth_op_gate.py  (new)
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_polish_recipe import reject_centerline_op_on_truth  # noqa: E402

def test_centerline_op_on_truth_path_rejected():
    with pytest.raises(ValueError, match="truth-bearing"):
        reject_centerline_op_on_truth(action_type="smooth", target_truth_bearing=True)

def test_centerline_op_on_decorative_path_ok():
    reject_centerline_op_on_truth(action_type="smooth", target_truth_bearing=False)

def test_stroke_op_on_truth_path_ok():
    reject_centerline_op_on_truth(action_type="taper_texture", target_truth_bearing=True)
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_truth_op_gate.py -v`
Expected: FAIL — `cannot import name 'reject_centerline_op_on_truth'`.

- [ ] **Step 3: Implement the gate**

```python
# scripts/svg_polish_recipe.py  (append near the validation helpers)
CENTERLINE_ALTERING = frozenset(
    {"smooth", "simplify", "roughen", "jitter", "soften_corners", "resample"}
)


def reject_centerline_op_on_truth(*, action_type: str, target_truth_bearing: bool) -> None:
    """Plan-time gate (spec §5 gate 1): a centerline-altering op on a truth path
    is forbidden outright — overlay is not an escape (H1)."""
    if action_type in CENTERLINE_ALTERING and target_truth_bearing:
        raise SvgPolishRecipeError(
            f"action {action_type!r} alters the centerline of a truth-bearing path; "
            "only centerline-preserving stroke ops are allowed on truth paths"
        )
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_truth_op_gate.py -v`
Expected: PASS (all three).

- [ ] **Step 5: Commit**

```bash
git add scripts/svg_polish_recipe.py tests/test_truth_op_gate.py
git commit -m "feat(gate): reject centerline-altering ops on truth-bearing paths (no overlay escape)"
```

---

## Done-when

- `uv run pytest tests/ -q` green.
- A smoothed/ramped truth curve → BLOCKER `geometry_truth_violation`; a pure resample or a decorative reshape → clean.
- The op gate raises on a centerline-altering action targeting a truth path.

This proves the **geometry-aware + per-path-truth** half of the v2 safety model. Plan 2 = `hand:*` overlay namespace + occlusion/no-truth-replacement guard; Plan 3 = shipped-artifact PDF/CMYK gate; Plan 4 = `add_volume_shading` proof op (true non-occluding overlay).
