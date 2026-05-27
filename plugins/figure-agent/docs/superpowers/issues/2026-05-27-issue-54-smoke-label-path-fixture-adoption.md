# Issue 54 - Smoke Trap Demo Label-Path Fixture Adoption

Status: completed

## Problem

Issue 51 introduced `check_label_path_proximity.py`, and Issue 52 adopted the
gate for the high-risk `fig1_overview_v2_pair_001_vault` fixture. The next
useful plugin-level hardening step is to expand real fixture adoption without
turning the detector into broad visual noise.

`smoke_trap_demo` is a good second adoption target because it is a compact band
diagram with three explicit semantic horizontal lines:

- conduction-band reference line
- deep-trap level
- valence-band reference line

The fixture is intentionally critique-not-required, so this adoption must not
create unaccounted `LP###` candidates in the normal render.

## Design Decision

Declare only the line bodies, not the intentionally adjacent endpoint labels.
The right-edge labels (`CB`, `E_t`, `VB`) are part of the band-diagram idiom.
Including the full drawn line endpoint in the detector range would risk
flagging the correct label placement as a false positive.

The adopted checks therefore use measured PDF-cm coordinates and trim the
right-side endpoint-label gap:

```yaml
label_path_proximity_checks:
  - id: smoke_cb_reference_line
    kind: horizontal_line
    role: reference_line
    y_pdf_cm: 2.30
    x_range_pdf_cm: [1.72, 7.02]
    clearance_pt: 3.0
  - id: smoke_deep_trap_line
    kind: horizontal_line
    role: semantic_line
    y_pdf_cm: 4.62
    x_range_pdf_cm: [2.99, 5.94]
    clearance_pt: 3.0
  - id: smoke_vb_reference_line
    kind: horizontal_line
    role: reference_line
    y_pdf_cm: 6.87
    x_range_pdf_cm: [1.72, 7.02]
    clearance_pt: 3.0
```

## Scope

In scope:

- Add the three minimal checks to `examples/smoke_trap_demo/spec.yaml`.
- Add a focused regression test that the fixture declares exactly those checks.
- Compile the fixture and confirm `build/label_path_proximity.json` is present
  and clean for the current render.

Out of scope:

- Editing `smoke_trap_demo.tex`.
- Adding critique/reference grounding to the fixture.
- Making label-path proximity auto-infer every TikZ path.
- Treating endpoint labels as defects when they are intentionally placed.

## Acceptance

- `tests/test_label_path_proximity.py` covers the fixture contract.
- `tests/test_label_path_proximity.py` locks the current endpoint-label
  geometry as a zero-candidate case.
- `/fig_compile` equivalent emits `build/label_path_proximity.json`.
- Current render has zero label-path proximity candidates.
- Generated build artifacts are not committed.

## Review Notes

- False-positive risk is controlled by trimming the endpoint label area.
- The adoption remains fixture-local and does not change plugin code or schema.
- Because `smoke_trap_demo` has no critique requirement, a nonzero LP report
  here would become workflow friction rather than useful critique evidence.
