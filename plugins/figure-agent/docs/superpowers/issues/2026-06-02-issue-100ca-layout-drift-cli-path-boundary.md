# Issue 100CA - Layout Drift CLI Fixture Path Boundary

Status: implemented in branch `codex/issue-100ca-layout-drift-cli-boundary`
Type: compile-stage layout gate, fixture path boundary
Priority: P2

## Problem

`scripts/check_layout_drift.py` is a compile-stage gate that compares required
label positions between `coordinate_hints.yaml` and a compiled PDF. The
internal drift evaluator can legitimately run against temporary fixtures in
tests, but the public CLI previously accepted raw relative paths.

Before this issue, this command could return a normal-looking skip:

```bash
python3 scripts/check_layout_drift.py examples/../outside
```

when `outside/spec.yaml` existed. That output looked like plugin truth about an
example fixture even though the target had escaped `examples/`.

## Contract

The public CLI accepts only:

- `<fixture-name>` when `examples/<fixture-name>` exists or is the intended
  target;
- `examples/<fixture-name>`;
- an absolute path that resolves to a direct child of `examples/`;
- a literal `.` when called from inside a fixture directory by `compile.sh`.

The public CLI rejects:

- traversal-like paths such as `examples/../outside`;
- existing single-component relative directories outside `examples/`;
- nested relative paths that are not `examples/<fixture-name>`;
- unsafe names rejected by `fixture_identity`.

The lower-level `evaluate_drift()` API remains unchanged so unit tests and
internal callers can pass explicit in-memory data.

## Out Of Scope

- Changing layout-drift thresholds.
- Changing `coordinate_hints.yaml` schema.
- Changing PDF word extraction.
- Restricting arbitrary PDF paths passed through the explicit `--pdf` option.

## Acceptance

- CLI `examples/../outside` fails before reading the outside fixture.
- CLI `outside` fails when `outside/` exists as a sibling directory but
  `examples/outside/` does not.
- CLI `<fixture-name>`, `examples/<fixture-name>`, absolute
  `examples/<fixture-name>`, and compile-local `.` remain supported.
- Existing layout-drift matching behavior remains unchanged.

## Verification

- `uv run pytest -q tests/test_check_layout_drift.py`
- `uv run pytest -q tests/test_check_layout_drift.py tests/test_status.py tests/test_run_export.py tests/test_golden_artifact_checks.py`
- `uv run ruff check scripts/check_layout_drift.py tests/test_check_layout_drift.py`
- `git diff --check`
- Final full-suite and plugin validation before merge.
