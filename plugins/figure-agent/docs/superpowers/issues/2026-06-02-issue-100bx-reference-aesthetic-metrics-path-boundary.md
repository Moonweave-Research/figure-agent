# Issue 100BX - Reference-Aesthetic Metrics CLI Fixture Path Boundary

Status: implemented in branch `codex/issue-100bx-reference-metrics-path-boundary`
Type: reference learning, aesthetic audit input, fixture path boundary
Priority: P1

## Problem

`scripts/reference_aesthetic_metrics.py` writes
`build/reference_aesthetic_metrics.json`, which is consumed by critique
briefing and reference/aesthetic routing. Its internal API can operate on
temporary fixture directories for tests, but its public CLI previously accepted
raw relative paths.

Before this issue, the CLI accepted:

```bash
python3 scripts/reference_aesthetic_metrics.py examples/../outside
python3 scripts/reference_aesthetic_metrics.py outside
```

when those paths pointed to a fixture-shaped sibling directory. That could
create a fresh-looking reference/aesthetic metrics file outside the declared
`examples/` fixture tree.

## Contract

The public CLI accepts only:

- `<fixture-name>` when `examples/<fixture-name>` exists;
- `examples/<fixture-name>`;
- an absolute path that resolves to a direct child of `examples/`.

The public CLI rejects:

- traversal-like paths such as `examples/../outside`;
- existing single-component relative directories outside `examples/`;
- nested relative paths that are not `examples/<fixture-name>`;
- unsafe names rejected by `fixture_identity`.

The lower-level `build_reference_aesthetic_metrics(example_dir)` API remains
unchanged so tests and internal callers can operate on explicit temporary
fixture directories.

## Out Of Scope

- Changing aesthetic metric formulas or thresholds.
- Changing reference-learning pack schema.
- Making reference/aesthetic metrics a hard release gate.
- Restricting detector tools that intentionally accept arbitrary image/PDF
  paths.

## Acceptance

- CLI `examples/../outside` returns failure before writing
  `build/reference_aesthetic_metrics.json`.
- CLI `outside` returns failure when `outside/` exists as a sibling directory
  but `examples/outside/` does not.
- CLI `<fixture-name>` and absolute `examples/<fixture-name>` remain supported.
- Existing reference-aesthetic metrics API tests continue to pass.

## Verification

- `uv run pytest -q tests/test_reference_aesthetic_metrics.py`
- `uv run pytest -q tests/test_reference_aesthetic_metrics.py tests/test_critique_brief.py tests/test_fig_loop.py tests/test_status.py`
- `uv run ruff check scripts/reference_aesthetic_metrics.py tests/test_reference_aesthetic_metrics.py`
- `git diff --check`
- Final full-suite and plugin validation before merge.
