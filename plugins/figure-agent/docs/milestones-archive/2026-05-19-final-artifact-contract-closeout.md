# Final Artifact Contract Closeout

**Date:** 2026-05-19
**Scope:** Issues 7A-7D status closeout
**Status:** complete

## Purpose

This closeout records the final-artifact contract implementation commits and
clears stale `implemented; pending final verification commit` issue statuses.
No runtime behavior changed in this closeout.

## Issue Map

| Issue | Contract | Completion commits | Notes |
|---|---|---|---|
| 7A | SVG polish manifest schema | `2daa9e8`, `89ad2a1` | `2daa9e8` added the schema module and tests. `89ad2a1` hardened canonical manifest path and shared final-artifact state classification. |
| 7B | Final artifact status state | `832d72d`, `89ad2a1` | `832d72d` exposed final-artifact state in `/fig_status`. `89ad2a1` aligned malformed-spec handling and shared classifier behavior. |
| 7C | SVG polish audit handoff | `bc3fd26` | Docs-only handoff protocol for one polished SVG, bounded edit classes, audit, manifest ordering, and forbidden writes. |
| 7D | Accepted gate final-artifact integration | `89ad2a1` | Accepted-mode gate now validates polished-SVG manifests only when `spec.yaml.final_artifact.kind: polished_svg` opts in. |

## Contract State

The final-artifact layer now has:

- manifest load/validate/write/freshness support in `scripts/svg_polish_manifest.py`
- `/fig_status` final-artifact state, kind, path, next-action surfacing
- accepted-mode validation through `scripts/check_golden_artifacts.py`
- `/fig_loop` visibility and non-final-ready blocking
- docs for SVG polish handoff and final-artifact release boundaries

Generated-export fixtures remain on the legacy path unless `spec.yaml` opts into:

```yaml
final_artifact:
  kind: polished_svg
  manifest: polish/svg_polish_manifest.yaml
```

## Verification References

The implementation was verified during Issue 7D and 7E completion with:

```bash
uv run pytest -q tests/test_golden_artifact_checks.py tests/test_status.py tests/test_svg_polish_manifest.py tests/test_inputs.py tests/test_fig_loop.py
uv run pytest
git ls-files -z '*.py' | xargs -0 uv run ruff check
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

This closeout reruns only documentation/plugin validation because it changes
issue status and milestone text, not runtime code.

## Remaining Work

The next product work should focus on SVG polish UX and semantic-backport
classification, or on real fixture operation through `/fig_drive` and
`/fig_loop` now that the driver and final-artifact gates are documented and
dogfooded.

**No known Issue 7A-7D closeout blocker remains.**
