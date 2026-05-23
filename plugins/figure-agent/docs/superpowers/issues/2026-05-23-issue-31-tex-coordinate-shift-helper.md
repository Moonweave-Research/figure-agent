# Issue 31 — TeX Coordinate Shift Helper

Status: completed in commit `3de6fe4`

## Problem

During real figure authoring, panel or subregion moves often require many
literal TikZ coordinates to shift together. Manual ad-hoc scripts are risky:

- simple regex scripts can miss `\foreach` tuple coordinates;
- broad edits can accidentally move panel letters, row separators, or unrelated
  panels;
- a failed manual shift may still compile but leave layout drift that only
  appears several iterations later.

The plugin should provide a conservative helper for scoped coordinate shifts.
This is an authoring utility, not an automatic patch engine.

## Scope

Add `scripts/tex_coordinate_shift.py`.

In scope:

- Shift literal TikZ coordinate pairs like `(1.20, 3.40)`.
- Shift safe `\foreach` slash tuples when the header declares an x/y variable
  pair such as `\px/\py`, `\dx/\dy`, `\x/\y`, or `\qx/\qy`.
- Preserve tuple payload fields after the first x/y pair, e.g.
  `8.05/7.40/0.026` -> `8.15/7.30/0.026`.
- Require either `--line START:END` or explicit `--all`.
- Print a unified diff by default.
- Write changes only with explicit `--write`.
- Leave TeX comments unchanged, even when comments contain historical
  coordinate notes.
- Return a controlled error for unsupported input, zero shift, or no coordinate
  changes.
- Add focused tests.

Out of scope:

- Parsing arbitrary TeX/TikZ expressions.
- Shifting named coordinates by dependency analysis.
- Inferring panel scope from comments or visual layout.
- Running compile, critique, or status.
- Editing generated build/export artifacts.

## CLI Contract

```bash
uv run python3 scripts/tex_coordinate_shift.py examples/<name>/<name>.tex \
  --line 330:370 --dx 0.10 --dy -0.05

uv run python3 scripts/tex_coordinate_shift.py examples/<name>/<name>.tex \
  --line 330:370 --dx 0.10 --dy -0.05 --write
```

`--line` is 1-based and inclusive. Multiple `--line` flags may be used. `--all`
is allowed only when the operator intentionally wants a file-wide shift.

## Matching Rules

Literal coordinates:

```tex
(8.05, 7.40) -> (8.15, 7.35)
```

Safe foreach tuples:

```tex
\foreach \px/\py/\sz in {8.05/7.40/0.026, 9.00/7.40/0.022} {
```

with `--dx 0.10 --dy -0.05` becomes:

```tex
\foreach \px/\py/\sz in {8.15/7.35/0.026, 9.10/7.35/0.022} {
```

Unsafe tuple headers such as `\y/\n/\sn` are left unchanged because the second
field is not a y-coordinate.

## Acceptance Criteria

- The helper shifts literal `(x,y)` coordinates inside selected line ranges.
- The helper shifts safe x/y `\foreach` slash tuples, including tuples with
  payload fields after x/y.
- The helper does not shift unsafe slash tuples like `\y/\n/\sn`.
- The helper does not rewrite coordinates that appear only in TeX comments.
- The default command prints a diff and leaves the file unchanged.
- `--write` updates the file deterministically.
- The CLI rejects missing scope (`--line` or `--all`) and no-op shifts with
  controlled exit code 2.
- Tests cover literal coordinates, foreach tuple support, unsafe tuple
  preservation, dry-run behavior, write behavior, and controlled errors.

## Review Questions

- Does the helper reduce real authoring friction without pretending to be a
  full TikZ parser?
- Is file mutation explicit enough for safe agent use?
- Is the foreach heuristic conservative enough to avoid moving semantic
  payload values?
