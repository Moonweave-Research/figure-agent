# Issue 91B - SVG Semantic Diff Checker

Status: completed

Type: SVG semantic preservation, final-artifact safety, visual-only edit guard

Depends on:

- Issue 91A - SVG delta artifact hash and renderer provenance

## What To Build

Add a deterministic report that compares the generated SVG export and the
polished SVG before final-artifact promotion.

The checker should decide whether the polished SVG still looks like a
visual-only edit. It should not decide whether the figure is beautiful.

The report should flag:

- expected text labels missing or converted to paths;
- changed `id` or `class` inventory for meaningful elements;
- changed `viewBox`, width, height, or global frame;
- unexpected filters, masks, clips, `foreignObject`, raster images, or external
  hrefs;
- large group transforms or transforms applied to elements matching multiple
  semantic children;
- changed marker/arrow/path counts;
- color or opacity remaps that affect declared semantic classes.

## Public Contract

Write a machine-readable report under `polish/svg_semantic_diff.json`:

```yaml
schema: figure-agent.svg-semantic-diff.v1
fixture: <name>
source_svg: exports/<name>.svg
polished_svg: polish/<name>.polished.svg
summary:
  state: pass | needs_human | semantic_backport_required | invalid
  blocker_count: <int>
  warning_count: <int>
findings:
  - id: SD001
    kind: text_identity_loss | element_inventory_change | frame_change |
      unsupported_svg_feature | group_transform_risk | marker_or_path_change |
      semantic_color_remap
    severity: BLOCKER | MAJOR | MINOR | NIT
    evidence: "<specific element id/class/text/path>"
    recommended_route: semantic_backport_required | needs_human | accept_simplification
```

`fig_loop` and `fig_driver --mode polish` should surface a blocking semantic
diff state before treating a polished SVG as acceptable.

## Acceptance Criteria

- [x] A valid visual-only translate/stroke/opacity polish can pass.
- [x] Missing text label is reported as `text_identity_loss`.
- [x] Text converted to path is reported unless explicitly allowed.
- [x] New external image/filter/mask/foreignObject is reported.
- [x] ViewBox or dimensions change is reported.
- [x] Large group transform is reported as `group_transform_risk`.
- [x] Semantic diff report participates in SVG polish manifest/freshness or is
      consumed before final-artifact state becomes FRESH.
- [x] Tests cover pass, text loss, unsupported feature, frame change, group
      transform risk, and stale/missing report behavior.

## Implementation Notes

- Added `scripts/svg_semantic_diff.py`.
- The report records source/polished SVG hashes, summary state, blocker and
  warning counts, and deterministic `SD###` findings.
- `compute_final_artifact_state()` now refuses to return `FRESH` for polished
  SVG when `polish/svg_semantic_diff.json` is missing, malformed, stale, or
  reports `needs_human` / `semantic_backport_required`.
- `scripts/status_next_policy.py` now routes blocked final artifacts through
  semantic backport and `scripts/svg_semantic_diff.py` refresh.
- The script is executable as `python scripts/svg_semantic_diff.py examples/<name>`.

## Verification Results

- `uv run pytest -q tests/test_svg_semantic_diff.py tests/test_svg_polish_manifest.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py`
  - Result: 343 passed.
- `uv run ruff check scripts/svg_semantic_diff.py scripts/svg_polish_manifest.py scripts/status_next_policy.py tests/test_svg_semantic_diff.py tests/test_status.py`
  - Result: All checks passed.

## Edge Cases

- SVG namespaces differ between renderers.
- Text is split across nested `<tspan>` elements.
- Math labels appear as multiple text nodes.
- An editor rewrites attribute order without semantic change.
- A harmless metadata/title change should not block.
- A style attribute and CSS class encode the same visual change differently.

## Verification

- `uv run pytest -q tests/test_svg_semantic_diff.py tests/test_svg_polish_manifest.py tests/test_fig_driver.py`
- `uv run ruff check scripts/svg_semantic_diff.py scripts/svg_polish_manifest.py scripts/fig_driver.py`
- `git diff --check`
