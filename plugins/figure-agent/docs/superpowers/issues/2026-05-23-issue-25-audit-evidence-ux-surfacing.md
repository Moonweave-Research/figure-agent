# Issue 25: Audit Evidence UX Surfacing

**Date:** 2026-05-23 KST
**Status:** 25A-D implemented
**Type:** post-Issue-24 usability and operator-readiness hardening

## Problem

Issue 24 made the audit pipeline stricter: missing visual-clash reports, stale
or mismatched crop files, uncertain crop reads, historical visual-clash
regressions, and vague `accept_simplification` claims now fail more
deterministically.

The remaining risk is operator UX. A human or outer agent can still see a
generic stop such as `human_gate_required`, `critique_stale`, or
`visual_clash_accept_simplification` without a compact explanation of:

- which audit surface caused the stop;
- which crop or `VC###` id needs attention;
- whether the next step is agent-actionable or genuinely human-gated;
- which command should be rerun after fixing the audit artifact;
- whether the issue is about figure content, audit evidence, or schema
  bookkeeping.

This is not a correctness gap in the validators. It is a workflow gap: strong
gates are less useful if the operator has to grep JSON, lint output, and loop
records to understand the next move.

## Direction

Add a compact, machine-readable and human-readable audit evidence summary that
is shared by `/fig_status`, `/fig_drive`, and `/fig_loop` where appropriate.
The summary should not weaken any gate or infer visual quality. It should only
surface existing audit state in a more usable form.

## Priority Order

1. **Issue 25A: Audit Evidence Summary Model**
   - Implemented in this branch.
   - Define a small shared model for audit-evidence status.
   - Inputs:
     - `build/visual_clash.json` presence/count;
     - `build/audit_crops/manifest.json` presence/hash integrity where
       available;
     - latest `critique.md` schema/rubric;
     - `micro_defects[].visual_clash_ref` accounting;
     - `micro_defects[].accept_simplification_reason` usage for v1.10+;
     - `crop_audit_log` verdict counts and uncertain crop ids.
   - Output:
     - `evaluation_state`: `passed | needs_action | missing_input |
       stale_or_mismatched | legacy | not_applicable`;
     - `blocking_items`: compact ids such as `VC050`, `full_q1`, `M001`;
     - `next_action`: one canonical command or human-review instruction;
     - `reason`: one sentence.

2. **Issue 25B: `/fig_status` Audit UX**
   - Implemented in this branch.
   - Add a concise "Audit evidence" line or block to `/fig_status`.
   - Must distinguish:
     - no critique required;
     - critique required but missing/stale;
     - audit inputs missing;
     - crop uncertainty;
     - structured accept-simplification failure;
     - audit evidence passed.
   - Must not change existing public state enums.

3. **Issue 25C: `/fig_drive` Next-Action Explanation**
   - Implemented in this branch.
   - Include the audit evidence summary in driver JSON when it influences
     `safe_command`, `stop_boundary`, or `reason`.
   - Driver remains dry-run and non-mutating.
   - Must keep current action vocabulary backward compatible.

4. **Issue 25D: `/fig_loop` Operator Closeout**
   - Implemented in this branch.
   - When loop stops on audit evidence, print a compact closeout:
     - what was inspected;
     - what remains uncertain or malformed;
     - exact command to rerun after repair.
   - Must not auto-edit critique, adjudication, source, export, accepted, or
     golden state.

## First Slice: Issue 25A

Implement only the shared summary model and tests first. Do not change command
output until the model is stable.

### Expected Files

- `scripts/audit_evidence_summary.py`
- `tests/test_audit_evidence_summary.py`
- this issue doc

### Required Behavior

- [x] Read only fixture-local files.
- [x] Return controlled states for missing/malformed `visual_clash.json`.
- [x] Return controlled states for missing/malformed `build/audit_crops/manifest.json`.
- [x] Count visual-clash candidates and accounted `micro_defects[].visual_clash_ref`.
- [x] Count duplicate visual-clash refs once in the compact summary.
- [x] Count `crop_audit_log` verdicts and list uncertain crop ids.
- [x] Detect missing required `crop_audit_log` entries from manifest ids.
- [x] Reject stale/mismatched crop manifest paths that are absolute, escaping,
  outside `build/audit_crops`, or not PNG files.
- [x] Detect v1.10 accepted visual-clash candidates missing structured reason or
  rationale by reusing existing lint semantics where possible.
- [x] Preserve legacy compatibility: older schemas may report `legacy`, not
  blocker, unless existing lint already blocks them.
- [x] Avoid generated artifact mutation.

### Verification

```bash
uv run pytest -q tests/test_audit_evidence_summary.py tests/test_critique_lint.py tests/test_fig_loop_assessments.py
uv run ruff check scripts/audit_evidence_summary.py tests/test_audit_evidence_summary.py
git diff --check
```

## Non-Goals

- No visual-quality scoring.
- No source figure edits.
- No host-vision or external model call.
- No accepted/golden/export mutation.
- No command output changes in 25A.
- No new release gate.

## Success Definition

Issue 25 is complete when an operator can run the normal figure-agent workflow
and see, without digging through raw JSON, whether the current blocker is caused
by missing/stale audit inputs, uncertain crops, visual-clash accounting,
structured accept-simplification, or actual figure content.

## Issue 25B Implementation Notes

- `infer_stage()` now includes the shared `audit_evidence` object.
- Single-figure `/fig_status <name>` prints an `Audit evidence:` line with
  state, reason, compact blockers, and next action.
- No-argument `/fig_status` appends `audit: <state>` only for actionable states.
- Existing stage/state enums and `Next:` selection are unchanged.

## Issue 25C Implementation Notes

- `/fig_drive --dry-run` copies `audit_evidence` from `/fig_status` as an
  additive top-level JSON field.
- Actionable audit evidence states append context to `reason`.
- The driver action vocabulary, dry-run guarantee, and selected command remain
  unchanged.

## Issue 25D Implementation Notes

- `iteration_001.json` now stores top-level `audit_evidence` copied from
  `/fig_status`.
- `/fig_loop --json` includes `audit_evidence` in stdout summary.
- `decision.md` prints audit-evidence state, compact blockers, and next action.
- `/fig_loop` remains verify-only and does not mutate critique, adjudication,
  source, export, accepted, or golden state.
