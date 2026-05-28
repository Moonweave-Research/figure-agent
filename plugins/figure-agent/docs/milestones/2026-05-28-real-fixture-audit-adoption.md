# Real Fixture Audit Adoption - Issue 57

Status: implemented contract pass

## Summary

Issue 57 converts audit adoption from an informal memory into a tested
real-fixture contract. No figure source, exports, accepted state, golden state,
or generated build artifacts were changed in this slice.

The key result is intentionally conservative:

- `fig1_overview_v2_pair_001_vault` remains the high-risk fully adopted fixture
  for deterministic text-boundary and label-path checks.
- `smoke_trap_demo` remains the low-noise smoke fixture for line-body
  label-path checks.
- Other reference-backed fixtures are recorded as deferred rather than silently
  assumed covered.

The contract now lives at:

- `tests/real_fixture_audit_adoption.yaml`
- `tests/test_real_fixture_audit_adoption.py`

## Current Matrix

| Fixture | Reference | Text Boundary | Label Path | Aesthetic Intent | Critique Reference Pack | Paper Context | Journal Playbook | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `fig1_overview_v2_pair_001_vault` | yes | 6 | 2 | yes | no | no | no | adopted_high_risk |
| `smoke_trap_demo` | no | 0 | 3 | no | no | no | no | adopted_low_noise_smoke |
| `fig1_overview_v2` | yes | 0 | 0 | no | no | no | no | deferred_reference_only |
| `golden_trap_depth_picture` | yes | 0 | 0 | no | no | no | no | deferred_reference_only |
| `n3_trial_01_trap_depth` | yes | 0 | 0 | no | no | no | no | deferred_reference_only |
| `n3_trial_02_actuation_sequence` | yes | 0 | 0 | no | yes | no | no | deferred_reference_only |
| `fig3_trapping_concept` | no | 0 | 0 | no | no | no | no | not_applicable_no_reference |
| `fig5_floating_clip_mechanism` | no | 0 | 0 | no | no | no | no | deferred_geometry_needed |

## Adopted Fixtures

### `fig1_overview_v2_pair_001_vault`

The fixture has the strongest deterministic audit coverage:

- figure-level reference image;
- three panel references with `bbox_pdf_cm`;
- six text-boundary checks for row-2 containment, column rules, and internal
  display rectangles;
- two label-path proximity checks for Panel C semantic path hazards;
- fixture-local `aesthetic_intent.yaml`.

This is the current production reference for high-risk audit adoption.

### `smoke_trap_demo`

The fixture has three line-body-only label-path checks:

- conduction-band reference line;
- deep-trap level;
- valence-band reference line.

It intentionally remains critique-not-required. The checks stay narrow so the
right-edge endpoint labels are not turned into false-positive workflow noise.

## Deferred Fixtures

Reference-backed fixtures without deterministic geometry checks are not treated
as complete. They are explicitly deferred:

- `fig1_overview_v2`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`

The next adoption pass should add geometry only after inspecting each fixture's
actual row boxes, label boundaries, semantic reference lines, and curve/label
near-miss hazards. Copying coordinates from another fixture is forbidden.

`n3_trial_02_actuation_sequence` now carries a fixture-local
`critique_reference_pack.yaml` for reference-learning dogfood. That improves the
host critique prompt, but it does not by itself adopt deterministic
text-boundary or label-path geometry checks, so the fixture remains
`deferred_reference_only`.

`fig5_floating_clip_mechanism` has panel boxes but no reference grounding. It
needs explicit geometry review before deterministic checks should be added.

`fig3_trapping_concept` remains no-reference and no-low-noise-adoption for this
slice.

## Review

### Contract Correctness

The new pytest verifies:

- every real `examples/*/spec.yaml` fixture appears in the adoption matrix;
- `reference_image` presence matches the matrix;
- exact `text_boundary_checks[].id` values match;
- exact `label_path_proximity_checks[].id` values match;
- `aesthetic_intent.yaml` and `critique_reference_pack.yaml` presence matches;
- paper-wide and journal playbook opt-ins match;
- every row has a recognized `adoption_status` and non-empty rationale.

### Scope Containment

No new detector behavior was added. No fixture source or generated artifact was
changed. This is a contract/adoption visibility slice, not a figure-editing
slice.

### Next Issue Handoff

Issue 58 should consume this contract as the real fixture basis for
single-next-action UX. In particular, the UX should distinguish:

- adopted high-risk fixtures with deterministic blockers;
- reference-backed fixtures that still need critique but lack deterministic
  geometry adoption;
- critique-not-required fixtures where compile/export/status are the only
  relevant loop steps.

## Verification

```bash
uv run pytest -q tests/test_real_fixture_audit_adoption.py
uv run pytest -q tests/test_label_path_proximity.py tests/test_text_boundary_clash.py
```

Both commands passed during implementation.
