# Issue 100BY - Reference Extract CLI Fixture Path Boundary

Status: implemented in branch `codex/issue-100by-reference-extract-cli-boundary`
Type: reference authoring evidence, coordinate hints, fixture path boundary
Priority: P1

## Problem

`scripts/reference_extract.py` reads a fixture reference image and writes
`coordinate_hints.yaml`. Issue 100BS already hardened
`spec.yaml.reference_image` so a fixture cannot point to a reference image
outside itself. The public CLI still accepted raw fixture path syntax, though.

Before this issue, this command could succeed:

```bash
python3 scripts/reference_extract.py examples/../outside --ocr-passes 1.0
```

when `outside/` was a fixture-shaped sibling directory. It wrote
`outside/coordinate_hints.yaml`, making escaped fixture evidence look like a
normal `/fig_extract` result.

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

The lower-level `extract_coordinate_hints(example_dir)` API remains unchanged
so tests and internal callers can still operate on explicit temporary fixture
directories.

## Out Of Scope

- Changing OCR behavior.
- Changing palette/structural region extraction.
- Changing coordinate-hints freshness semantics.
- Restricting internal API callers that pass explicit fixture directories.

## Acceptance

- CLI `examples/../outside --ocr-passes 1.0` fails before writing
  `coordinate_hints.yaml`.
- CLI `outside --ocr-passes 1.0` fails when `outside/` exists as a sibling
  directory but `examples/outside/` does not.
- CLI `<fixture-name>`, `examples/<fixture-name>`, and absolute
  `examples/<fixture-name>` remain supported.
- Existing reference extraction tests continue to pass.

## Verification

- `uv run pytest -q tests/test_reference_extract.py`
- `uv run pytest -q tests/test_reference_extract.py tests/test_status.py tests/test_critique_brief.py tests/test_run_export.py`
- `uv run ruff check scripts/reference_extract.py tests/test_reference_extract.py`
- `git diff --check`
- Final full-suite and plugin validation before merge.
