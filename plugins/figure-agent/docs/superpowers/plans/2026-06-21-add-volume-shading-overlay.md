# add_volume_shading Non-Occluding Overlay — Implementation Plan (figure-agent v2, Slice 0 piece (5))

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (or superpowers:executing-plans). Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship one real end-to-end illustrator op — `add_volume_shading` — as a *true non-occluding overlay*, plus the first `*.polished.svg` fixture in the corpus, so that Plan 2's occlusion guard and Plan 3's render-ship gate (both dormant today — zero polished SVGs exist) run **live** end-to-end. The op adds a filter-free gradient `<defs>` + a translucent `hand:*` overlay over a target object, mutating **no** truth path and **not** recoloring the object's own fill (H9). This implements spec §Slice 0 piece (5): "proves the v2 recipe fields + the path/composite/ship safety model with a visible A win and no truth-path mutation."

**Architecture:** A new standalone, pure module `scripts/add_volume_shading.py`: an SVG-string → SVG-string transform. It parses with `xml.etree`, finds the target element by `id`, computes its bbox, builds a **filter-free** linear gradient in `<defs>` (id `hand:vshade-<target>`), and inserts a `hand:*`-namespaced overlay element (`data-truth-bearing="false"`, translucent) filled with that gradient, positioned over the target's bbox. The op is **standalone** (recipe-executor wiring is deferred to Slice 1 — the v2 recipe schema). A new synthetic fixture `examples/_volume_shading_demo/` carries a base SVG (a truth-bearing object) in `exports/`, the op's output as `polish/<name>.polished.svg` + a valid `svg_polish_manifest.yaml` + `spec.yaml.final_artifact: {kind: polished_svg}`, so both gates fire on it.

**Determinism (spec §4 three axes):** `reproducible` (pure/deterministic given params) × `judgment_bearing` (`light_direction` + `hero_strength` are REQUIRED — the op raises if absent; "never silently defaulted") × `truth_affecting=false` (overlay only; no truth-path mutation).

**Tech Stack:** Python 3.12, stdlib `xml.etree`/`re`. Reuses Plan 1–3 modules (`svg_semantic_diff`, `svg_ship_gate`, `svg_polish_manifest`). System tools `rsvg-convert`+`pdftoppm` only for the render-gated test. **No new dependency.**

**Spec:** `../specs/2026-06-21-figure-agent-v2-svg-illustrator-design.md` §5 (safety model), §6 (overlay-safe, Export-A, overlay-lie tests), §7 Slice 0 piece (5). Out of scope (later slices/plans): the v2 recipe schema + recipe-executor wiring (Slice 1), `path_rewrite`/B ops (Slice 3), composite-CVD H6, precise CMYK (Plan 3B).

**Run tests:** from `plugins/figure-agent/`: `uv run pytest tests/ -q`. Render-dependent: `uv run pytest tests/test_add_volume_shading.py -m render`.

---

## Verified infrastructure (do not re-investigate)

- **Plan 2 `hand:*` + occlusion guard** (`scripts/svg_semantic_diff.py`): namespace = `id` OR `class` token starting with `hand:` (`HAND_OVERLAY_PREFIX="hand:"`, `_is_hand_namespaced`). `hand:*` additions are allowlisted out of `element_inventory_change` (`_strip_hand_overlay`). Occlusion BLOCKER `truth_path_occluded` fires only when an overlay is opaque (`fill != "none"` AND effective opacity ≥ `OCCLUSION_OPACITY = 0.95`), drawn **after** (above) a truth path, covering ≥ `OCCLUSION_COVERAGE = 0.5` of its bbox. **A translucent overlay (opacity < 0.95) or one covering < 0.5 PASSES.** Truth-bearing opt-out: `data-truth-bearing="false"` (default true). `_compare(source, polished)` returns the findings list.
- **Plan 3 render-ship gate** (`scripts/svg_ship_gate.py`): `render_ship_gate_failures(example_dir, spec_path, *, dpi=600) -> list[str]` resolves the manifest-declared polished SVG via `compute_final_artifact_state` and renders SVG→PDF→raster; BLOCKER when a truth path's on-path window-samples match neither declared fill/stroke (± `COLOR_DELTA = 60`, ≥ `MIN_MATCH_FRACTION = 0.5`). `build_render_ship_findings(svg_path, *, dpi=600)` is the per-SVG entry.
- **Polished fixture shape** (`tests/test_svg_polish_manifest.py` `_make_fixture`/`_valid_manifest` + `scripts/svg_polish_manifest.py`): `exports/<n>.svg` + `<n>.pdf`; `polish/<n>.polished.svg` + `svg_polish_manifest.yaml` (`schema: figure-agent.svg-polish-manifest.v1`; `base{source_set_hash,...hashes}`; `polished{path, polished_svg_hash, audit_hash, editor, toolchain[], edit_classes[], semantic_change_declared, backport_required}`; `provenance{reviewer, reviewed_at, notes}`) + `svg_polish_audit.md`; `spec.yaml` with `final_artifact: {kind: polished_svg, manifest: polish/svg_polish_manifest.yaml}`. Manifest path MUST be `polish/svg_polish_manifest.yaml` (`SVG_POLISH_MANIFEST_RELATIVE_PATH`). `compute_final_artifact_state(example_dir, name, spec, *, style_lock_path=, base_dir=)` validates it.
- **Import convention:** `scripts/` not a package. Tests: `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` then bare import + `# noqa: E402`. Source modules import siblings bare. New module-level imports go in the top block in the SAME edit as their use (a ruff PostToolUse hook strips momentarily-unused imports). `@pytest.mark.render` marker exists in `pyproject.toml`.

---

## Critical design constraint (the load-bearing subtlety)

The overlay must pass **BOTH** gates simultaneously:
1. **Occlusion guard (Plan 2):** overlay must be translucent → cap effective opacity strictly below `OCCLUSION_OPACITY = 0.95`. `hero_strength ∈ [0,1]` maps to opacity in a safe band (e.g. `0.10 + 0.45*hero_strength`, max ~0.55). Overlay carries `data-truth-bearing="false"`.
2. **Render-ship gate (Plan 3):** the truth path beneath must still render with its declared colour in ≥ 50% of on-path samples (± `COLOR_DELTA = 60`). A translucent gradient over the object's **interior/fill** tints the fill but leaves the truth **outline stroke** largely its own colour. **Therefore: shade the object's interior region, not its truth outline.** In the demo fixture the truth path is the object's dark outline stroke; the overlay is a lighter translucent gradient inset within the bbox so on-outline pixels stay within tolerance. (If a future overlay shifts a truth stroke past `COLOR_DELTA`, the render-ship gate correctly BLOCKs — that is the gate working, not a bug.)

The op also must **not** emit any `<filter>` (blur rasterizes on PDF — spec §6 Export-A); volume = a vector gradient only.

---

## File Structure

- **Create** `scripts/add_volume_shading.py` — pure helpers (bbox, gradient-defs builder, light-direction→vector, hero-strength→opacity) + the public `add_volume_shading(svg, target_id, *, light_direction, hero_strength) -> str`.
- **Create** `tests/test_add_volume_shading.py` — pure unit tests (synthetic SVG) for Tasks 1–2; a `@pytest.mark.render` integration test for Task 3.
- **Create** `examples/_volume_shading_demo/` — the first polished-SVG fixture (base export + op-produced polished SVG + manifest + audit + spec).

---

## Task 1: Pure shading helpers

**Files:** create `scripts/add_volume_shading.py`, `tests/test_add_volume_shading.py`

- [ ] **Step 1: failing tests** — `_element_bbox(svg, target_id)` returns the target's (x,y,w,h); `_opacity_for(hero_strength)` maps `[0,1]` into a band strictly `< 0.95` (assert `0 < _opacity_for(1.0) < 0.95`, monotonic, and raises/clamps out-of-range); `_gradient_vector(light_direction_degrees)` returns `(x1,y1,x2,y2)` fractional gradient coords for a direction (e.g. 0°→left-right, 90°→top-bottom). Pure, synthetic inputs.
- [ ] **Step 2:** run `uv run pytest tests/test_add_volume_shading.py -q` → FAIL (import error).
- [ ] **Step 3:** implement the three pure helpers. Bbox: parse the target element; support `<rect>` (x/y/width/height), `<circle>`/`<ellipse>` (cx/cy/r or rx/ry), and `<path>` via `svg_path_geometry.canonical_polyline` bbox (reuse Plan 1). `_opacity_for`: `max(0.0, min(1.0, hero_strength))` then `0.10 + 0.45*clamped` (range 0.10–0.55, well under 0.95). `_gradient_vector`: trig from degrees → unit vector mapped to `[0,1]²` gradient endpoints.
- [ ] **Step 4:** run → PASS.
- [ ] **Step 5:** commit `feat(hand): pure volume-shading helpers (bbox, opacity band, gradient vector)`.

## Task 2: The `add_volume_shading` op

**Files:** modify `scripts/add_volume_shading.py`, `tests/test_add_volume_shading.py`

- [ ] **Step 1: failing tests** for `add_volume_shading(svg, target_id, *, light_direction, hero_strength) -> str`:
  - REQUIRES params: calling with `light_direction=None` or `hero_strength=None` raises `ValueError` (judgment-bearing, never silently defaulted).
  - Adds a `<linearGradient id="hand:vshade-<target>">` into `<defs>` and a `hand:*` overlay element (`id="hand:vshade-overlay-<target>"`, `data-truth-bearing="false"`, `fill="url(#hand:vshade-<target>)"`, `opacity` < 0.95) AFTER the target in document order.
  - **Overlay-safe (spec §6):** `svg_semantic_diff._compare(base, polished)` yields NO `element_inventory_change` finding (only `hand:*` ids added).
  - **H9 (no structural paint):** the target element's own `fill`/`stroke` attributes are byte-unchanged.
  - **Export-A (spec §6):** the output contains no `<filter>` element.
  - **No truth mutation:** `_compare` yields no BLOCKER (`truth_path_removed`/`truth_path_occluded`).
- [ ] **Step 2:** run → FAIL (cannot import `add_volume_shading`).
- [ ] **Step 3:** implement. Parse SVG; locate target by id (raise `ValueError` if absent); compute bbox; ensure a `<defs>`; append the gradient (stops from a base→shadow tint along `_gradient_vector(light_direction)`); append the overlay rect over the bbox interior with the capped opacity + `data-truth-bearing="false"` + `hand:` id. Do NOT touch the target's attributes. Serialize back to string.
- [ ] **Step 4:** run → PASS (full file green).
- [ ] **Step 5:** commit `feat(hand): add_volume_shading non-occluding overlay op (overlay-safe, filter-free, H9-safe)`.

## Task 3: First polished-SVG fixture + live gates

**Files:** create `examples/_volume_shading_demo/...`; modify `tests/test_add_volume_shading.py`

- [ ] **Step 1: failing test (render-gated)** — build the fixture in the test or as committed files, then assert:
  - **Occlusion guard PASS:** `_compare(base_svg, polished_svg)` has no BLOCKER (translucent overlay passes).
  - **Render-ship PASS (`@pytest.mark.render`):** `build_render_ship_findings(polished_svg_path, dpi=150) == []` (truth outline renders faithfully under the interior shading).
  - **Negative (overlay-lie caught):** an OPAQUE variant (opacity ≥ 0.95, covering the truth bbox, drawn above) → `_compare` yields a `truth_path_occluded` BLOCKER — proving the gate catches an abusive overlay the op itself refuses to emit.
- [ ] **Step 2:** run → FAIL.
- [ ] **Step 3:** create the committed fixture: `exports/<n>.svg` (a truth-bearing dark-outline object, e.g. an electrode `<rect id="electrode">` or sphere `<circle id="bead">`, default truth-bearing) + `<n>.pdf` (rsvg-convert); `polish/<n>.polished.svg` = `add_volume_shading` output; `polish/svg_polish_manifest.yaml` (valid, `edit_classes` incl. an overlay class, `semantic_change_declared:false`, `backport_required:false`); `polish/svg_polish_audit.md`; `spec.yaml` with `name`, `final_artifact: {kind: polished_svg, manifest: polish/svg_polish_manifest.yaml}`. Make the helper compute hashes so the manifest is non-stale under the test's `base_dir`/`style_lock_path`.
- [ ] **Step 4:** run `-m render` → PASS; run the pure suite → PASS.
- [ ] **Step 5: full suite — no regressions.** `uv run pytest tests/ -q`. The new fixture is the FIRST `polished_svg` fixture, so `check_golden_artifacts`/`status` now exercise the occlusion + render-ship gates on it — confirm any new finding is the gate working as intended, not a regression. (Working-tree note: a single pre-existing unrelated failure may exist from untracked fig2-5 fixtures.)
- [ ] **Step 6:** commit `feat(hand): first polished-SVG fixture exercises occlusion + render-ship gates live`.

---

## Done-when

- `add_volume_shading(svg, id, light_direction=..., hero_strength=...)` returns a polished SVG that: adds only `hand:*` ids (overlay-safe), has no `<filter>` (Export-A), leaves the target's own fill unchanged (H9), and mutates no truth path.
- Calling it without `light_direction` or `hero_strength` raises (judgment-bearing).
- The `examples/_volume_shading_demo/` polished fixture PASSES Plan 2's occlusion guard (`_compare` no BLOCKER) and Plan 3's render-ship gate (`build_render_ship_findings == []`), and an opaque variant is correctly BLOCKED — i.e. both formerly-dormant gates now run live on a real fixture.
- `uv run pytest tests/ -q` green (modulo the known untracked-fixture failure) + `-m render` green.

**Out of scope (documented):** recipe-executor wiring + v2 recipe schema (Slice 1); B/`path_rewrite` (Slice 3); composite-CVD H6; precise CMYK (Plan 3B); critique-driven *proposal* of light_direction/hero_strength (op only enforces they are supplied).
