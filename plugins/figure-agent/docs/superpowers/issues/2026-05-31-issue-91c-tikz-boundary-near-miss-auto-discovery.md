# Issue 91C - TikZ Boundary And Near-Miss Auto-Discovery

Status: completed

Type: TikZ deterministic audit, undeclared geometry detection, near-miss metrics

Depends on:

- Issue 29 - text-boundary clash detection
- Issue 31 - label-path proximity audit

## What To Build

Add a deterministic audit layer that detects when LLM-authored TikZ creates
boundary/path risks that are not represented in `spec.yaml`.

This slice is not a full TikZ parser. It is a conservative warning layer:
when it cannot prove that a drawn rectangle, rule, or path is already covered
by declared checks, it should emit a machine-readable candidate and force the
critique pipeline to account for it.

## Public Contract

Write a report under `build/undeclared_geometry.json`:

```yaml
schema: figure-agent.undeclared-geometry.v1
fixture: <name>
render_pdf: build/<name>.pdf
candidates:
  - id: UG001
    kind: undeclared_rect_boundary | undeclared_column_rule |
      undeclared_horizontal_rule | undeclared_path_near_label |
      label_endpoint_near_miss | low_clearance_inside_boundary
    evidence: "<render or source evidence>"
    bbox_pt: [x0, y0, x1, y1]
    nearest_text: "<text or empty>"
    distance_pt: <number or null>
    recommended_action: add_spec_check | add_micro_defect |
      accept_simplification | human_review
total: <int>
```

The critique brief should include this report when non-empty, and
`critique_lint.py` should require each candidate to be referenced by a
micro-defect, crop audit entry, or explicit accept-simplification rationale.

## Acceptance Criteria

- [x] Compile writes `build/undeclared_geometry.json`.
- [x] Report is empty for fixtures with no detectable undeclared geometry.
- [x] A rendered text label outside a declared or discovered box creates a
      candidate.
- [x] A label close to an undeclared line/path creates a near-miss candidate.
- [x] Existing declared `text_boundary_checks` and `label_path_proximity_checks`
      suppress duplicate undeclared candidates.
- [x] Critique brief includes the candidate table.
- [x] Lint rejects missing accounting for non-empty candidate reports.
- [x] Tests cover empty report, undeclared rect, undeclared column rule,
      declared suppression, near-miss distance, and critique accounting.

## Implementation Notes

- Added `scripts/check_undeclared_geometry.py`.
- `scripts/compile.sh` now emits `build/undeclared_geometry.json` after
  label-path proximity checks.
- `critique_brief.py` includes a mandatory undeclared-geometry candidate
  section when the report is non-empty.
- `critique_lint.py` requires non-empty candidate reports to be accounted for
  by `micro_defects[].undeclared_geometry_ref`.

## Verification Results

- `uv run pytest -q tests/test_undeclared_geometry.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: 173 passed.
- `uv run ruff check scripts/check_undeclared_geometry.py scripts/critique_brief.py scripts/critique_lint.py tests/test_undeclared_geometry.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: All checks passed.
- `bash -n scripts/compile.sh`
  - Result: clean.

## Edge Cases

- TikZ macros or `foreach` generate geometry that is not visible in raw source.
- PDF extraction cannot map a path back to TeX line numbers.
- Decorative background waves should not explode the candidate count.
- Panel letters and tiny superscripts should remain suppressible through
  existing false-positive controls.
- Candidate ids must be deterministic across repeated compile runs.

## Verification

- `uv run pytest -q tests/test_undeclared_geometry.py tests/test_critique_lint.py tests/test_critique_brief.py`
- `uv run ruff check scripts/check_undeclared_geometry.py scripts/compile.sh scripts/critique_lint.py scripts/critique_brief.py`
- `git diff --check`
