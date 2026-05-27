# Paper-Wide Aesthetic Context Closeout

Status: implemented and verified

## Scope

This slice adds explicit paper-wide aesthetic context as critique grounding and
lint accountability. It does not draw figures, mutate `.tex`, export artifacts,
accepted/golden state, or SVG polish artifacts.

## Implemented Contracts

- Optional packs live under `examples/_paper_aesthetic_contexts/<paper_id>.yaml`.
- Fixtures opt in only through `spec.yaml.paper_aesthetic_context`.
- Pack ids are safe ids only: ASCII letters, numbers, `_`, `.`, and `-`.
- An opted-in pack applies only if `figure_roles[]` contains the fixture.
- Pack content participates in `critique_input_hash` through
  `quality_manifest.critique_manifest_paths()`.
- `/fig_critique` emits `## Paper-Wide Aesthetic Context` before fixture-local
  aesthetic intent sections.
- `critique_lint.py` rejects generic opted-in critiques that omit exact
  paper-wide anchors from:
  - `top_tier_audit.cross_panel_semantic_grammar`
  - `top_tier_audit.aesthetic_coherence`
  - `editorial_art_direction.visual_identity`

## Dogfood Evidence

Synthetic fixture tests cover the full contract without modifying real figure
source or intentionally staling an active fixture:

```bash
uv run pytest -q tests/test_paper_aesthetic_context.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py
```

Result:

```text
158 passed
```

## Final Verification

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

```text
uv run pytest -q: 1263 passed, 3 skipped, 1 xfailed, 6 warnings
uv run ruff check .: All checks passed
git diff --check: clean
claude plugin validate .claude-plugin/plugin.json: passed
claude plugin validate .: passed
claude plugin validate ../../.claude-plugin/marketplace.json: passed
```

## Review Notes

- Contract correction: the initial design used
  `top_tier_audit.cross_panel_grammar`, but the actual critique schema slot is
  `top_tier_audit.cross_panel_semantic_grammar`. The spec, plan, brief, docs,
  and lint contract now use the existing schema key.
- Backward compatibility: fixtures without `spec.yaml.paper_aesthetic_context`
  keep legacy brief and lint behavior.
- Scope containment: no real example spec was opted in during this slice. A
  real paper pack can be introduced later in the figure-work branch when the
  user is ready to refresh critique state for that fixture.

## Residual Risk

The parser/lint/brief/freshness contracts are covered by tests, but no real
fixture has been opted into paper-wide context yet. The first real opt-in will
intentionally make that fixture's critique stale and should be paired with a
fresh `/fig_critique` run.
