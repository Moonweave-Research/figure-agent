# Issue 24A: Crop Uncertainty Stop Boundary

**Date:** 2026-05-22 KST
**Status:** implemented in branch
**Type:** audit-gate correctness
**Parent:** `2026-05-22-issue-24-audit-gate-hardening-roadmap.md`

## What to build

Make crop-read uncertainty a real driver stop boundary. If the latest
`/fig_loop` checkpoint contains `crop_audit_summary.evaluation_state:
needs_action`, `/fig_driver --dry-run` must not continue as if the checkpoint is
clean.

## Current Problem

`/fig_loop` already derives a crop-audit summary from `critique.md`:

```yaml
crop_audit_summary:
  source: critique.crop_audit_log
  uncertain_crop_ids:
    - VC001_A
  evaluation_state: needs_action
```

That is useful evidence. Before this issue, the driver checkpoint blocker only
checked patch handoff, ambiguous patch selection, human gate, top-tier blockers,
and editorial art-direction blockers. Crop uncertainty could remain visible in
JSON without becoming an action boundary.

## Acceptance Criteria

- [x] `/fig_driver --dry-run --mode review` returns `action:
  human_gate_stop` and `stop_boundary: human_gate_required` when the latest
  loop checkpoint has uncertain crop ids.
- [x] `/fig_driver --dry-run --mode release` and `--mode polish` apply the same
  blocker before release/export/polish routing.
- [x] The driver reason names the uncertain crop ids and asks for explicit crop
  reread or human review.
- [x] Clean crop-audit summaries with `evaluation_state: passed` remain
  non-blocking.
- [x] Existing human gate, top-tier, editorial, patch-handoff, and publication
  gate behavior remains backward compatible.

## Implementation Notes

- `fig_driver_checkpoint.py` now preserves `crop_audit_summary` from the latest
  loop iteration checkpoint.
- `fig_driver.py` treats uncertain crop ids as `human_gate_stop` using the
  existing `human_gate_required` stop boundary.
- Polish mode only preempts for crop uncertainty; existing editorial
  art-direction routes such as `semantic_backport_required` remain controlled by
  the polish-specific routing policy.

## Implementation Contract

Add a small helper in `scripts/fig_driver.py`:

```python
def _crop_audit_requires_human_gate(summary: Any) -> bool:
    ...
```

The helper should return true only when:

- `summary` is a mapping;
- `summary["evaluation_state"] == "needs_action"`; and
- `summary["uncertain_crop_ids"]` is a non-empty list.

Then extend `_loop_checkpoint_review_blocker()` to check
`loop_checkpoint["crop_audit_summary"]` after explicit human gate checks and
before top-tier/editorial blockers. Return the existing
`ACTION_HUMAN_GATE_STOP` with `STOP_HUMAN_GATE`; do not add a new action or stop
enum unless future Issue 24 slices need one.

Reason text should be deterministic and concise, for example:

```text
latest /fig_loop checkpoint reports uncertain crop audit verdicts for
VC001_A, VC002_B; reread those crops or request human review before export,
polish, or release.
```

## Suggested Files

- `scripts/fig_driver.py`
- `tests/test_fig_driver.py`
- `docs/superpowers/issues/2026-05-22-issue-24-audit-gate-hardening-roadmap.md`
- `docs/superpowers/issues/2026-05-22-issue-24a-crop-uncertainty-stop-boundary.md`

## TDD Plan

1. Add a failing review-mode test that stubs a latest loop checkpoint with:
   `final_stop_reason: verify_only_complete`,
   `escalation_level: none`, and
   `crop_audit_summary.evaluation_state: needs_action`.
2. Assert the driver returns `human_gate_stop`, `human_gate_required`, and a
   reason containing the uncertain crop id.
3. Run the targeted test and confirm it fails because the driver currently
   returns a non-human-gate action.
4. Implement the helper and integrate it into `_loop_checkpoint_review_blocker`.
5. Add or adjust tests for release/polish coverage and a passed-summary
   non-blocking case if not already covered by existing routing tests.
6. Run targeted tests, then the broader driver/loop assessment tests.

## Verification

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_fig_loop_assessments.py
uv run ruff check scripts/fig_driver.py tests/test_fig_driver.py
git diff --check
```

## Non-Goals

- No change to `crop_audit_summary` generation.
- No change to critique schema or lint.
- No automatic reread of crops.
- No source, export, accepted, golden, or publication-provenance mutation.
