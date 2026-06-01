# Issue 100BR - TeX Coordinate Shift Suffix Boundary

Status: implemented

Type: source authoring safety, mutation containment

## Problem

`tex_coordinate_shift.py` is documented as a helper for shifting scoped literal
TikZ coordinates in a `.tex` file. Before this issue, the CLI accepted any
existing file path. With `--write`, a non-TeX file containing coordinate-like
text could be mutated:

```bash
uv run python3 scripts/tex_coordinate_shift.py spec.yaml \
  --line 1:1 --dx 0.10 --dy 0.10 --write
```

This is a sharp operational edge because the helper is an authoring mutation
tool and users run it during iterative figure polishing.

## Decision

Fail closed at the CLI boundary unless `tex_path` ends in `.tex`.

The lower-level `shift_tex_coordinates()` function remains text-only and
path-agnostic for tests and controlled internal use. The CLI now rejects
non-TeX paths before reading and before `--write` can mutate them.

## Tests

Covered by:

- `tests/test_tex_coordinate_shift.py::test_main_rejects_non_tex_file_before_write`
- existing scoped line-range, safe `\foreach`, comment preservation, dry-run,
  write, missing-scope, zero-shift, and no-change tests

The new test was red before implementation: `spec.yaml` was rewritten by the
TeX-only helper and returned exit code `0`.

## Review Notes

- Valid `.tex` source edits are unchanged.
- The helper remains intentionally path-explicit because the command takes a TeX
  file path, not a fixture name.
- `--write` still requires `--line` or explicit `--all`.
- The change does not alter compile, critique, status, loop, export, accepted,
  golden, SVG polish, or publication behavior.
