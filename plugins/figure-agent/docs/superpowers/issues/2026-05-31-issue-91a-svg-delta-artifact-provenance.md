# Issue 91A - SVG Delta Artifact Hash And Renderer Provenance

Status: completed

Type: SVG polish freshness, delta artifact integrity, renderer provenance

Depends on:

- Issue 90 - SVG polish and aesthetic gate hardening

## What To Build

Make SVG polish delta freshness bind the visible review artifacts, not only the
source SVG, polished SVG, and recipe.

`polish/aesthetic_delta/delta_manifest.json` should include hashes for:

- `before.png`
- `after.png`
- `diff.png`

It should also include renderer provenance for the command that produced those
images. At minimum, record the renderer script identity and the executable
version or a controlled "unknown" value when version discovery is unavailable.

## Why This Matters

The v1.15 critique path requires the host LLM to inspect before/after/diff
images. If those PNGs can change without the manifest becoming stale, the
critique can remain fresh while the actual audited pixels drift.

## Acceptance Criteria

- [x] `build_svg_polish_delta_pack()` writes delta artifact hashes into
      `delta_manifest.json`.
- [x] `load_svg_polish_delta_manifest()` validates those hashes as
      sha256-prefixed values.
- [x] `svg_polish_delta_is_stale()` returns true when any delta PNG changes.
- [x] The manifest records renderer/toolchain provenance.
- [x] `critique_lint.py` keeps rejecting stale or malformed delta manifests.
- [x] Tests cover changed `before.png`, changed `after.png`, changed
      `diff.png`, malformed hash, missing artifact, and renderer metadata.

## Implementation Notes

- `delta_manifest.json` now carries `artifact_hashes.before_png_hash`,
  `artifact_hashes.after_png_hash`, and `artifact_hashes.diff_png_hash`.
- The manifest records renderer provenance as `renderer.executable`,
  `renderer.version`, and `renderer.script_hash`.
- Manifest validation now requires lowercase `sha256:<64 hex chars>` for
  source, polished, recipe, artifact, and renderer script hashes.
- Staleness checks now compare the current visible delta PNGs against the
  manifest hashes.

## Verification Results

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_fig_driver.py tests/test_svg_polish_clean_dogfood.py`
  - Result: 246 passed.
- `uv run ruff check scripts/svg_polish_delta.py tests/test_svg_polish_delta.py tests/test_critique_lint.py tests/test_fig_driver.py`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.

## Edge Cases

- Delta images exist but are zero-byte or unreadable.
- Delta image hash is well-formed but points to old content.
- Renderer command succeeds but produces dimensions that differ between before
  and after.
- Renderer version is unavailable on the local system.
- Legacy fixtures without SVG delta manifests remain unaffected.

## Verification

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_critique_lint.py`
- `uv run ruff check scripts/svg_polish_delta.py scripts/critique_lint.py`
- `git diff --check`
