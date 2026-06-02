# Issue 100CP - Polish Prerequisite Gate Alignment

Status: implemented

Type: operator workflow, SVG polish readiness, driver contract

## Problem

After Issue 100CO, `/fig_drive --mode polish` correctly keeps completion
mode-scoped, but a clean checkout exposed a smaller operator-facing mismatch:
when an earlier prerequisite such as render or export freshness blocked polish
mode, the top-level driver action said `run_compile` or `run_export` while the
additive `svg_polish_gate.next_action` still said `rerun_fig_loop` through the
generic no-current-checkpoint path.

That was safe, because the top-level driver action remained authoritative, but
it was confusing. An operator looking at SVG-specific columns in `/fig_queue
--mode polish` could read "rerun loop" even though the first real step was to
compile or export.

## Scope

Keep the SVG polish route conservative:

- no change to `ready_for_svg_polish` thresholds;
- no positive real-fixture promotion;
- no SVG, export, accepted, golden, publication, or source mutation;
- no change to editorial readiness semantics once compile/export/critique gates
  are closed.

Only align the operator-facing SVG polish gate when the driver stops before the
loop checkpoint can be meaningful.

## Implemented Contract

In polish mode, if the selected driver action is an earlier prerequisite,
`svg_polish_gate` now reports:

- `state: blocked`;
- `source: driver_prerequisite`;
- `can_start_svg_polish: false`;
- `next_action` aligned with the authoritative driver action:
  - `run_compile` -> `run_fig_compile`;
  - `run_critique` -> `run_fig_critique`;
  - `run_adjudicate` -> `run_fig_adjudicate`;
  - `run_export` -> `run_fig_export`;
- `blocking_items: [{source: driver_prerequisite, id: <driver action>}]`.

Once those prerequisites are closed, the existing
`latest_loop_checkpoint`/`ready_for_svg_polish` gate remains unchanged.

## Tests

- `tests/test_fig_driver.py` covers render-missing polish mode and requires the
  SVG gate to point to `run_fig_compile`.
- `tests/test_fig_driver.py` covers export-missing polish mode and requires the
  SVG gate to point to `run_fig_export`.

## Review

1. **Contract correctness** - PASS. The top-level driver action remains the
   authority, and the additive SVG gate now explains the same prerequisite
   instead of naming a later loop step.
2. **Scope containment** - PASS. No SVG polish threshold, recipe, executor,
   manifest, or critique schema behavior changes.
3. **Integration readiness** - PASS. Queue rows copy `svg_polish_gate` as
   before; the copied fields are now less misleading for clean checkouts where
   ignored build/export artifacts are absent.
