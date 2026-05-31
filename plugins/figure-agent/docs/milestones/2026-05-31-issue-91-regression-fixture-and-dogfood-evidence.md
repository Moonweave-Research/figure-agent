# Issue 91 Regression Fixture And Dogfood Evidence

Status: completed

Recorded at: 2026-05-31T13:12:38Z

## Scope

This milestone closes the evidence pass for Issue 91A-91D. The pass used
synthetic pytest fixtures instead of real paper figures so it could exercise
unsafe edge cases without mutating accepted, golden, export, publication, SVG,
or TikZ source state.

## Evidence Matrix

| Case | Test evidence | Expected state | Observed |
| --- | --- | --- | --- |
| SVG delta artifact drift | `tests/test_svg_polish_delta.py::test_changed_delta_artifact_marks_delta_stale` | Mutating `before.png`, `after.png`, or `diff.png` after manifest generation makes delta stale | Covered in targeted run |
| SVG semantic text drift | `tests/test_svg_semantic_diff.py::test_missing_text_label_reports_identity_loss` | Removed label text reports `text_identity_loss` and `needs_human` | Covered in targeted run |
| SVG group transform overreach | `tests/test_svg_semantic_diff.py::test_group_transform_reports_group_transform_risk` | Parent transform reports `group_transform_risk` | Covered in targeted run |
| TikZ undeclared boundary | `tests/test_undeclared_geometry.py::test_undeclared_rect_boundary_is_reported` and `test_undeclared_column_rule_is_reported` | Undeclared boxes/rules become UG candidates | Covered in targeted run |
| TikZ near-miss | `tests/test_undeclared_geometry.py::test_label_endpoint_near_miss_is_reported` | Label endpoint proximity emits a near-miss candidate without requiring bbox overlap | Covered in targeted run |
| Shallow crop evidence | `tests/test_critique_schema_validator.py::test_validate_critique_schema_rejects_v1_16_missing_crop_observed_objects`, `test_validate_critique_schema_rejects_v1_16_generic_crop_relationship`, and `test_validate_critique_schema_rejects_v1_16_missing_candidate_ref` | v1.16 rejects syntactically complete but locally ungrounded crop entries | Covered in targeted run |
| Shallow SVG delta evidence | `tests/test_critique_schema_validator.py::test_validate_critique_schema_rejects_v1_16_generic_delta_observation` | v1.16 rejects generic delta-image observation prose | Covered in targeted run |
| Undeclared geometry accounting | `tests/test_critique_lint.py::test_lint_critique_rejects_unaccounted_undeclared_geometry_candidate` | Non-empty `build/undeclared_geometry.json` must be accounted in critique micro-defects | Covered in targeted run |

## Commands And Results

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_svg_semantic_diff.py tests/test_undeclared_geometry.py tests/test_critique_schema_validator.py tests/test_critique_lint.py`
  - Result: 216 passed.
- `uv run pytest -q`
  - Result: 1529 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Mutation Safety

No real `examples/<name>/*.tex`, accepted flag, tracked golden export,
publication artifact, polished SVG, or build/export artifact was intentionally
changed by this evidence pass. All regression cases were executed through
temporary pytest fixtures.

## Review Notes

1. Contract coverage: the targeted tests cover all six required Issue 91E
   evidence cases and include both deterministic reports and host-critique
   schema/lint accountability.
2. False-positive containment: synthetic fixtures keep unsafe regression shapes
   isolated from real figures; Issue 91C remains warning/report-driven through
   compile unless strict policy is separately enabled.
3. Integration readiness: the new contracts are additive. Existing final
   artifact, release, golden, accepted, and publication mutation boundaries
   remain outside Issue 91.
