# Issue 100BZ - Inspection Trace CLI Fixture Path Boundary

Status: completed on main in merge commit `b054992`
Type: crop-read accountability, audit evidence validation, fixture path boundary
Priority: P2

## Problem

`scripts/inspection_trace.py validate` checks optional
`inspection_trace.yaml` files that document which host/subagent/human inspected
which audit artifacts. The lower-level loader can intentionally validate a
trace in a temporary fixture directory, but the public CLI previously accepted
raw relative paths.

Before this issue, this command could return success:

```bash
python3 scripts/inspection_trace.py validate examples/../outside
```

when `outside/inspection_trace.yaml` was valid. The output looked like normal
plugin truth:

```text
inspection_trace.py: valid examples/../outside/inspection_trace.yaml
```

That is too permissive for a public audit-evidence validator.

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

The lower-level `load_optional_inspection_trace(fixture_dir)` API remains
unchanged so tests and internal callers can validate explicit temporary fixture
directories.

## Out Of Scope

- Changing inspection trace schema.
- Changing crop hash validation.
- Requiring inspection traces for every critique.
- Restricting internal API callers that pass explicit fixture directories.

## Acceptance

- CLI `validate examples/../outside` fails before validating the outside trace.
- CLI `validate outside` fails when `outside/` exists as a sibling directory
  but `examples/outside/` does not.
- CLI `<fixture-name>` and absolute `examples/<fixture-name>` remain supported.
- Existing inspection trace validation tests continue to pass.

## Verification

- `uv run pytest -q tests/test_inspection_trace.py`
- `uv run pytest -q tests/test_inspection_trace.py tests/test_critique_brief.py tests/test_fig_loop.py tests/test_status.py`
- `uv run ruff check scripts/inspection_trace.py tests/test_inspection_trace.py`
- `git diff --check`
- Final full-suite and plugin validation before merge.
