# Hand-Overlay Namespace + Occlusion / No-Truth-Replacement Guard — Implementation Plan (figure-agent v2, Slice 0 · Plan 2 of 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `svg_semantic_diff` overlay-aware: a decorative `hand:*` overlay is allowlisted (it must not trip an `element_inventory_change`), but an overlay can never *replace* a truth path — a truth path that disappears (removed / renamed / downgraded to decorative) is a BLOCKER, and an opaque `hand:*` overlay drawn on top of and covering a truth path is a BLOCKER. This closes the "overlay is not an escape" hole (spec §5 H1) that Plan 1 deliberately left open.

**Architecture:** Three additive changes inside `_compare`/`_inventory` in `scripts/svg_semantic_diff.py`, building directly on Plan 1's `truth_geometry`. (1) An id/class prefix allowlist (`hand:`) filters sanctioned overlay additions out of the `element_inventory_change` finding. (2) The geometry loop's "polished entry missing" branch becomes a BLOCKER `truth_path_removed` instead of a silent `continue`. (3) `_inventory` records each truth path's bbox + document-order index and a `hand_overlays` list (bbox + effective opacity + fill + order); `_compare` flags a BLOCKER `truth_path_occluded` when an opaque overlay is drawn above and covers a truth path's bbox. Occlusion is a deterministic bbox/opacity/paint-order proxy — not pixel-exact rendering (that is the Plan 3 shipped-artifact gate's job).

**Tech Stack:** Python 3.12, stdlib `xml.etree`, `svgpathtools` via Plan 1's `canonical_polyline` (no new dependency; bboxes are derived from the canonical polyline, so no new svgpathtools surface and no new import-time requirement — `_inventory` already calls `canonical_polyline`).

**Spec:** `../specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md` §5 (gates 1 & 5, H1), §6 (overlay-safe, overlay-lie tests). This is Slice 0 piece (3). Pieces (4) shipped-artifact PDF/CMYK gate and (5) `add_volume_shading` proof op are Plans 3 and 4 — out of scope here. Plan 2 builds the *guard* that Plan 4's overlay producer must satisfy; it does not add any overlay-producing op.

**Run tests:** from `plugins/figure-agent/`: `uv run pytest tests/ -q` (testpaths=["tests"]). Single file: `uv run pytest tests/test_svg_semantic_diff.py -q`.

**Convention reminders (verified against the Plan 1 result):**
- `scripts/` is **not** a package. `tests/test_svg_semantic_diff.py` already begins with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` and imports `_inventory`, `_compare` (and public names) by bare name with `# noqa: E402`. **No new import lines are needed** for this plan — all three tasks append tests to that existing file, which already imports `_inventory`/`_compare` and defines the `_inv(tmp_path, name, svg)` and `BASE` helpers (added in Plan 1, Task 5).
- A ruff `PostToolUse` hook strips imports that look unused at edit time; this plan adds **no new imports**, so that hazard does not apply.
- Commit per task with the message shown; co-author trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- The `hand:` overlay namespace lives in the element's **`id` or `class` token value** (e.g. `id="hand:shadow"`, `class="hand:shading"`). `:` in an attribute *value* is valid XML and parses cleanly via `xml.etree` (only element/attribute *names* use `:` for XML namespaces). This matches the spec's literal "`hand:*` namespace" wording.

---

## File Structure

- **Modify** `scripts/svg_semantic_diff.py`:
  - `FINDING_KINDS` frozenset (`:23-34`) — add `"truth_path_removed"` and `"truth_path_occluded"`.
  - New module-level constant `HAND_OVERLAY_PREFIX = "hand:"` and helper `_strip_hand_overlay` (Task 1).
  - `_compare` `element_inventory_change` block (`:372-383`) — filter `hand:`-prefixed names (Task 1).
  - `_compare` geometry loop "missing polished entry" branch (`:402-412` area) — BLOCKER `truth_path_removed` (Task 2).
  - `_inventory` (`:172-266`) — document-order index, truth bbox+order, `hand_overlays` list; new helpers `_float_attr`, `_polyline_bbox` (Task 3).
  - `_compare` — occlusion block before `return findings`; new helper `_bbox_coverage` (Task 3).
- **Modify** `tests/test_svg_semantic_diff.py` — append overlay-safe, no-truth-replacement, and occlusion tests (reusing the existing `_inv` / `BASE` helpers).

No new files. Everything composes with Plan 1's `truth_geometry` and the existing finding pipeline.

---

## Task 1: `hand:*` overlay allowlist (overlay-safe)

A new or removed element whose `id` or `class` token starts with `hand:` is a sanctioned decoration, not a structural inventory change. Filter those names out of the `element_inventory_change` finding so an added overlay path or gradient `defs` does not trip it (spec §6 overlay-safe). Adding a *non*-`hand:` element still trips it.

**Files:**
- Modify: `scripts/svg_semantic_diff.py`
- Test: `tests/test_svg_semantic_diff.py`

- [ ] **Step 1: Write the failing tests (append to `tests/test_svg_semantic_diff.py`)**

```python
def test_hand_overlay_additions_do_not_trip_inventory_change(tmp_path):
    src = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="boundary" d="M0,0 L5,5 L10,0"/></svg>'
    )
    pol = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<defs><linearGradient id="hand:grad"/></defs>'
        '<path id="boundary" d="M0,0 L5,5 L10,0"/>'
        '<path id="hand:shadow" data-truth-bearing="false" opacity="0.3" d="M0,0 L10,10"/></svg>'
    )
    s = _inv(tmp_path, "s.svg", src)
    p = _inv(tmp_path, "p.svg", pol)
    assert not [f for f in _compare(s, p) if f["kind"] == "element_inventory_change"]


def test_non_hand_addition_still_trips_inventory_change(tmp_path):
    src = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="boundary" d="M0,0 L5,5 L10,0"/></svg>'
    )
    pol = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="boundary" d="M0,0 L5,5 L10,0"/>'
        '<path id="extra-real" data-truth-bearing="false" d="M0,0 L10,10"/></svg>'
    )
    s = _inv(tmp_path, "s.svg", src)
    p = _inv(tmp_path, "p.svg", pol)
    assert [f for f in _compare(s, p) if f["kind"] == "element_inventory_change"]
```

(The first polished SVG adds only `hand:`-namespaced ids; the second adds a real id `extra-real`. Both add a decorative path, so a separate `marker_or_path_change` MINOR may also fire — that is intentional and not what these tests assert.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "hand_overlay_additions or non_hand_addition" -v`
Expected: `test_hand_overlay_additions_do_not_trip_inventory_change` FAILS (the `hand:` ids currently trip `element_inventory_change`); `test_non_hand_addition_still_trips_inventory_change` PASSES already.

- [ ] **Step 3: Add the constant + helper + filter**

In `scripts/svg_semantic_diff.py`, add near the other module constants (e.g. just after `MAX_TRANSLATE_PX = 10.0`):

```python
HAND_OVERLAY_PREFIX = "hand:"


def _strip_hand_overlay(names: list[str]) -> list[str]:
    """Drop hand:* overlay names. Added/removed hand overlays are sanctioned
    decoration (spec §6 overlay-safe), not a structural inventory change."""
    return [name for name in names if not name.startswith(HAND_OVERLAY_PREFIX)]
```

Then, in `_compare`, wrap the four set-difference lines of the `element_inventory_change` block with the filter:

```python
    removed_ids = _strip_hand_overlay(sorted(set(source["ids"]) - set(polished["ids"])))
    added_ids = _strip_hand_overlay(sorted(set(polished["ids"]) - set(source["ids"])))
    removed_classes = _strip_hand_overlay(
        sorted(set(source["classes"]) - set(polished["classes"]))
    )
    added_classes = _strip_hand_overlay(
        sorted(set(polished["classes"]) - set(source["classes"]))
    )
    if removed_ids or added_ids or removed_classes or added_classes:
        add(
            "element_inventory_change",
            "MINOR",
            f"ids removed={removed_ids} added={added_ids}; "
            f"classes removed={removed_classes} added={added_classes}",
            SEMANTIC_DIFF_NEEDS_HUMAN,
        )
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "hand_overlay_additions or non_hand_addition" -v`
Expected: PASS (both).

- [ ] **Step 5: Full file — no regressions**

Run: `uv run pytest tests/test_svg_semantic_diff.py -q`
Expected: all PASS (the filter only removes `hand:`-prefixed names; no existing fixture uses that prefix, so non-overlay inventory findings are unchanged).

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_semantic_diff.py tests/test_svg_semantic_diff.py
git commit -m "feat(overlay): allowlist hand:* additions out of element_inventory_change"
```

---

## Task 2: No-truth-replacement BLOCKER (a truth path may not vanish)

Plan 1 left a hole: when a source truth path's id is absent from the polished `truth_geometry`, `_compare` silently `continue`s (only a MINOR `element_inventory_change` notes the id loss). That lets a polisher launder a truth curve away — remove it, rename its id, or downgrade it to `data-truth-bearing="false"` — and then draw an overlay in its place. Spec §5 H1: **no overlay may replace a truth path.** Make the missing-entry case a BLOCKER.

**Files:**
- Modify: `scripts/svg_semantic_diff.py` (`FINDING_KINDS` `:23-34`; `_compare` geometry loop)
- Test: `tests/test_svg_semantic_diff.py`

- [ ] **Step 1: Write the failing tests (append to `tests/test_svg_semantic_diff.py`)**

```python
def test_truth_path_removed_is_blocked(tmp_path):
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(
        tmp_path, "p.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>',
    )
    findings = _compare(src, pol)
    assert any(
        f["kind"] == "truth_path_removed" and f["severity"] == "BLOCKER" for f in findings
    )


def test_truth_path_renamed_is_blocked(tmp_path):
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(
        tmp_path, "p.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="renamed" d="M0,0 L5,5 L10,0"/></svg>',
    )
    assert any(f["kind"] == "truth_path_removed" for f in _compare(src, pol))


def test_truth_path_downgraded_to_decorative_is_blocked(tmp_path):
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(
        tmp_path, "p.svg",
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="boundary" data-truth-bearing="false" d="M0,0 L5,5 L10,0"/></svg>',
    )
    assert any(f["kind"] == "truth_path_removed" for f in _compare(src, pol))
```

(`BASE` and `_inv` are the helpers from Plan 1. In each case `boundary` is a truth path in the source but absent from the polished `truth_geometry` — vanished, renamed, or downgraded.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "truth_path_removed or renamed or downgraded" -v`
Expected: FAIL — `truth_path_removed` is never added (current branch silently `continue`s).

- [ ] **Step 3: Add the finding kind + replace the silent continue**

Add `"truth_path_removed",` to the `FINDING_KINDS` frozenset.

In `_compare`'s geometry loop, replace the existing missing-entry branch:

```python
        if pol_entry is None:
            # Truth path dropped its id (or vanished): reported only as a MINOR
            # element_inventory_change, NOT a BLOCKER. A BLOCKER-level
            # no-truth-replacement guard is Plan 2 scope, so a renamed/stripped id
            # is a known gap in this geometry lock, not a covered case.
            continue
```

with:

```python
        if pol_entry is None:
            add(
                "truth_path_removed",
                "BLOCKER",
                f"truth path #{element_id} is gone from the polished SVG "
                "(removed, renamed, or downgraded to decorative); no overlay may "
                "replace a truth path",
                SEMANTIC_DIFF_BACKPORT,
            )
            continue
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "truth_path_removed or renamed or downgraded" -v`
Expected: PASS (all three).

- [ ] **Step 5: Full file + full suite — watch for behavior-change regressions**

Run: `uv run pytest tests/test_svg_semantic_diff.py -q`
Then: `uv run pytest tests/ -q`

Expected: green. **Integration risk (learned from Plan 1):** this task *strengthens* behavior — any pre-existing test (in this or another test file) that removes/renames an `id`'d `<path>` carrying a `d` and no `data-truth-bearing="false"` will now ALSO get a `truth_path_removed` BLOCKER. If such a test fails:
- If it was asserting "no BLOCKER findings" on what is genuinely a truth-path removal, the *test's expectation is now wrong* — the new BLOCKER is the correct, desired behavior; update that test to expect it (and note why in the commit).
- If the removed path was never meant to be truth-bearing (e.g. a pure decoration that lacked the `data-truth-bearing="false"` marker), the *fixture* is wrong — mark it `data-truth-bearing="false"`.
Do not weaken the guard to make a stale test pass. If you cannot tell which case applies, STOP and report it.

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_semantic_diff.py tests/test_svg_semantic_diff.py
git commit -m "feat(overlay): BLOCKER when a truth path is removed/renamed/downgraded (no-truth-replacement)"
```

---

## Task 3: Occlusion guard (an opaque overlay may not cover a truth path)

A `truth_path_removed` BLOCKER stops *structural* replacement, but an overlay can also lie *visually*: leave the truth path in the tree, then paint an opaque `hand:*` shape on top of it. The reader sees the overlay, not the truth. Spec §6 overlay-lie test: an overlay that visually replaces/contradicts a truth path beneath it must be rejected. Implement a deterministic proxy: an opaque (`fill != "none"`, effective opacity ≥ `OCCLUSION_OPACITY`) `hand:*` path drawn **after** (above, in document/paint order) a truth path, whose bbox covers ≥ `OCCLUSION_COVERAGE` of the truth path's bbox, is a BLOCKER `truth_path_occluded`. A translucent overlay (e.g. a soft volume-shading gradient) or one drawn beneath the truth path passes.

This proxy uses bounding-box coverage + paint order + opacity, not pixel-exact rasterization (that is the Plan 3 shipped-artifact gate). Only `id`'d truth paths are protected (Plan 1's `truth_geometry` scope). Truth paths whose bbox has zero area (a perfectly axis-aligned line) are not occlusion-checkable by this proxy — a documented limitation.

**Files:**
- Modify: `scripts/svg_semantic_diff.py` (`_inventory`, `_compare`; new helpers `_float_attr`, `_polyline_bbox`, `_bbox_coverage`)
- Test: `tests/test_svg_semantic_diff.py`

- [ ] **Step 1: Write the failing tests (append to `tests/test_svg_semantic_diff.py`)**

```python
OVR = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    '<path id="boundary" d="M0,0 L5,5 L10,0"/>'
    "{overlay}</svg>"
)


def test_opaque_hand_overlay_over_truth_is_blocked(tmp_path):
    overlay = (
        '<path id="hand:cover" data-truth-bearing="false" '
        'fill="#fff" d="M0,0 L10,0 L10,5 L0,5 Z"/>'
    )
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(tmp_path, "p.svg", OVR.format(overlay=overlay))
    findings = _compare(src, pol)
    assert any(
        f["kind"] == "truth_path_occluded" and f["severity"] == "BLOCKER" for f in findings
    )


def test_translucent_hand_overlay_over_truth_passes(tmp_path):
    overlay = (
        '<path id="hand:shade" data-truth-bearing="false" '
        'fill="#fff" opacity="0.3" d="M0,0 L10,0 L10,5 L0,5 Z"/>'
    )
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(tmp_path, "p.svg", OVR.format(overlay=overlay))
    assert not [f for f in _compare(src, pol) if f["kind"] == "truth_path_occluded"]


def test_hand_overlay_beneath_truth_passes(tmp_path):
    # overlay declared BEFORE the truth path -> painted beneath -> cannot occlude
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
        '<path id="hand:cover" data-truth-bearing="false" '
        'fill="#fff" d="M0,0 L10,0 L10,5 L0,5 Z"/>'
        '<path id="boundary" d="M0,0 L5,5 L10,0"/></svg>'
    )
    src = _inv(tmp_path, "s.svg", BASE.format(d="M0,0 L5,5 L10,0"))
    pol = _inv(tmp_path, "p.svg", svg)
    assert not [f for f in _compare(src, pol) if f["kind"] == "truth_path_occluded"]
```

(The truth path `M0,0 L5,5 L10,0` has bbox `(0,0,10,5)` — non-zero area. The opaque overlay rect covers it fully and is declared after it; the translucent variant and the beneath variant must not flag.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "occlu or hand_overlay_over or beneath or translucent" -v`
Expected: FAIL — `truth_path_occluded` does not exist yet.

- [ ] **Step 3a: Add the finding kind + helpers**

Add `"truth_path_occluded",` to the `FINDING_KINDS` frozenset.

Add these module-level helpers (near the other small helpers, e.g. after `_strip_hand_overlay` from Task 1):

```python
OCCLUSION_OPACITY = 0.95  # effective opacity at/above which an overlay hides what's beneath
OCCLUSION_COVERAGE = 0.5  # bbox-coverage fraction of a truth path that counts as occlusion


def _float_attr(element: ET.Element, name: str, default: float) -> float:
    try:
        return float(element.attrib.get(name, default))
    except (TypeError, ValueError):
        return default


def _polyline_bbox(points: list[complex]) -> tuple[float, float, float, float]:
    xs = [point.real for point in points]
    ys = [point.imag for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _bbox_coverage(
    overlay: tuple[float, float, float, float],
    truth: tuple[float, float, float, float],
) -> float:
    """Fraction of the truth bbox area covered by the overlay bbox (0 if disjoint
    or the truth bbox is degenerate)."""
    ox0, oy0, ox1, oy1 = overlay
    tx0, ty0, tx1, ty1 = truth
    ix0, iy0 = max(ox0, tx0), max(oy0, ty0)
    ix1, iy1 = min(ox1, tx1), min(oy1, ty1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    truth_area = (tx1 - tx0) * (ty1 - ty0)
    if truth_area <= 0:
        return 0.0
    return ((ix1 - ix0) * (iy1 - iy0)) / truth_area
```

- [ ] **Step 3b: Extend `_inventory` — document order, truth bbox+order, hand_overlays**

In `_inventory`:

1. Add a `hand_overlays` accumulator with the others (near `truth_geometry: dict[str, dict[str, Any]] = {}`):

```python
    hand_overlays: list[dict[str, Any]] = []
```

2. Change the element loop to track document (paint) order:

```python
    for order, element in enumerate(root.iter()):
```

3. Extend the truth-path branch to store bbox + order, and to collect opaque-capable hand overlays. Replace the existing `if tag == "path":` block:

```python
        if tag == "path":
            path_count += 1
            d = element.attrib.get("d")
            truth_bearing = element.attrib.get("data-truth-bearing") != "false"
            if d and truth_bearing and element_id:
                polyline = canonical_polyline(d)
                truth_geometry[element_id] = {
                    "signature": shape_signature(d),
                    "polyline": polyline,
                    "bbox": _polyline_bbox(polyline),
                    "order": order,
                }
            if d and element_id and element_id.startswith(HAND_OVERLAY_PREFIX):
                opacity = _float_attr(element, "opacity", 1.0) * _float_attr(
                    element, "fill-opacity", 1.0
                )
                hand_overlays.append(
                    {
                        "bbox": _polyline_bbox(canonical_polyline(d)),
                        "opacity": opacity,
                        "fill": element.attrib.get("fill", ""),
                        "order": order,
                    }
                )
```

4. Add `"hand_overlays": hand_overlays,` to the dict returned by `_inventory`.

(Note: `_inventory` already requires `svgpathtools` wherever it runs, because Plan 1 calls `canonical_polyline` for truth paths here — adding overlay polylines introduces no new import-time requirement. The `hand:`-id'd truth-vs-overlay split: a `hand:` path is decorative by convention, so it should also carry `data-truth-bearing="false"`; if a `hand:` path were left truth-bearing it would simply appear in both `truth_geometry` and `hand_overlays`, which is harmless for these checks.)

- [ ] **Step 3c: Add the occlusion block to `_compare`**

Immediately before `return findings` (after the geometry-truth block), add:

```python
    truth_geo = polished.get("truth_geometry", {})
    for overlay in polished.get("hand_overlays", []):
        if overlay["fill"] == "none" or overlay["opacity"] < OCCLUSION_OPACITY:
            continue  # stroke-only or translucent overlay cannot hide truth
        for occluded_id, truth in sorted(truth_geo.items()):
            if overlay["order"] <= truth["order"]:
                continue  # overlay painted beneath the truth path
            if _bbox_coverage(overlay["bbox"], truth["bbox"]) >= OCCLUSION_COVERAGE:
                add(
                    "truth_path_occluded",
                    "BLOCKER",
                    f"opaque hand overlay covers >= {int(OCCLUSION_COVERAGE * 100)}% of "
                    f"truth path #{occluded_id} and is painted on top; "
                    "an overlay must not visually replace a truth path",
                    SEMANTIC_DIFF_BACKPORT,
                )
```

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_svg_semantic_diff.py -k "occlu or hand_overlay_over or beneath or translucent" -v`
Expected: PASS (all three).

- [ ] **Step 5: Full file + full suite — no regressions**

Run: `uv run pytest tests/test_svg_semantic_diff.py -q`
Then: `uv run pytest tests/ -q`
Expected: green. The new inventory keys (`hand_overlays`, and `bbox`/`order` on truth entries) are additive; `hand_overlays` is empty for any SVG without `hand:`-id'd paths, so the occlusion loop is a no-op on existing fixtures.

- [ ] **Step 6: Commit**

```bash
git add scripts/svg_semantic_diff.py tests/test_svg_semantic_diff.py
git commit -m "feat(overlay): BLOCKER when an opaque hand overlay occludes a truth path"
```

---

## Done-when

- `uv run pytest tests/ -q` green (verify in a clean checkout if the working tree carries unrelated untracked fixtures).
- A `hand:*` overlay/defs addition does NOT trip `element_inventory_change`; a non-`hand:` addition still does.
- A truth path that is removed, renamed, or downgraded to `data-truth-bearing="false"` → BLOCKER `truth_path_removed`.
- An opaque `hand:*` overlay painted on top of and covering a truth path → BLOCKER `truth_path_occluded`; a translucent overlay, or one painted beneath the truth path, → clean.

This closes the spec §5 H1 "overlay is not an escape" guarantee at the structural + composite-bbox level. Remaining Slice 0 work: Plan 3 = shipped-artifact PDF/CMYK re-render gate (§5 gate 4, H3) — the pixel-exact check this plan's bbox proxy defers to; Plan 4 = `add_volume_shading` proof op (§7 piece 5) — the first true non-occluding overlay producer, which must pass this plan's occlusion guard. Out of Plan 2 scope and tracked separately: per-figure `OCCLUSION_OPACITY`/`OCCLUSION_COVERAGE` thresholds (judgment-bearing, H4, currently conservative module constants — same deferral as Plan 1's `frechet_bound`); the broader `relationship_guard` declared-spatial-relations inventory (§5 gate 5); and id-less / positional truth-path matching (Plan 1's documented limitation).
