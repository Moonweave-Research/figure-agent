# Fig Loop Dogfood Evidence Matrix

**Date:** 2026-05-18
**Scope:** Issue 5A.2 pre-5B evidence checkpoint
**Status:** read-only evidence checkpoint

## Purpose

Issue 5B must not start from the assumption that auto-patching is safe just
because `/fig_loop` can classify one patch target. This checkpoint asks a
narrower question:

> Does the verify-only loop record and block the major patch states correctly
> before any source-editing mode exists?

This document records machine-observed evidence for that question. It does not
approve hidden source mutation or safe auto-patch execution.

## Method

The ten-run evidence matrix was run against temporary repo roots, not tracked examples.
Each temporary fixture had:

- `examples/<name>/spec.yaml`
- `examples/<name>/briefing.md`
- `examples/<name>/<name>.tex`
- `examples/<name>/critique.md`
- `examples/<name>/critique_adjudication.yaml`

The harness imported `scripts/fig_loop.py::run_loop()` and wrote loop artifacts
under the temporary root's ignored `.scratch/fig-loop-runs/`.

This proves runner-state behavior without modifying real fixture source,
accepted/golden state, build outputs, export outputs, or critique files.

## Evidence Matrix

| Scenario | Stop reason | Handoff | Eligibility | Pre-patch evidence | Post-patch verdict | `may_edit` | Interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| safe label/spacing candidate | `patch_target_recommended` | yes | `auto_patch_candidate` | yes | none | `false` | The loop can identify a narrow visual candidate while still refusing edit permission. |
| unresolved after attempted patch | `patch_target_recommended` | yes | `auto_patch_candidate` | no | `unresolved` | `false` | The loop detects allowed-scope file changes but keeps the target actionable when adjudication still says `apply`. |
| resolved after patch plus adjudication | `status_action_required` | no | none | no | `resolved` | `false` | The loop records closure only after the adjudication decision changes to `resolved`; source edits alone are not enough. |
| ambiguous multiple apply | `ambiguous_patch_selection` | no | none | no | none | none | The loop blocks broad patching when more than one `apply` target exists. |
| mechanism-class blocked | `patch_target_recommended` | yes | `human_review_required` | yes | none | `false` | The loop records the handoff but classifies mechanism/causal-arrow edits as not auto-patchable. |
| explicit `needs_human` gate | `human_gate_required` | no | none | no | none | none | The loop stops before handoff when adjudication requests human review. |
| regressed when render stale | `status_action_required` | no | none | no | `regressed` | `false` | The loop does not call a patch resolved when render freshness regresses. |
| generic label wording is assisted-only | `patch_target_recommended` | yes | `patch_assisted_only` | yes | none | `false` | Generic label copy changes do not become auto-patch candidates without a concrete geometry defect. |
| non-label offset is assisted-only | `patch_target_recommended` | yes | `patch_assisted_only` | yes | none | `false` | Generic offset language outside label geometry does not become an auto-patch candidate. |
| publication-safety blocked | `patch_target_recommended` | yes | `human_review_required` | yes | none | `false` | Accepted/golden/publication-safety changes stay out of auto-patch scope. |

## Live Fixture Check

The current `fig1_overview_v2_pair_001_vault` working copy has a fresh
`critique_adjudication.yaml` whose decisions are all `needs_human`.

Command:

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "Check current dogfood evidence readiness" --json
```

Observed:

- `final_stop_reason: human_gate_required`
- `escalation_level: human_review_required`
- `patch_handoff_present: false`
- `patch_evidence_present: false`
- `post_patch_evidence_verdict: null`
- `recommended_next_action: human review required for P-E-001`

This is a correct safety stop. It is not evidence that auto-patch is ready,
because no single real `apply` handoff was selected.

## Readiness Judgment

Issue 5A.2 validates the verify-only evidence contract:

- safe candidates remain `may_edit: false`,
- ambiguous multi-target patching is blocked,
- human-gated findings stop before handoff,
- unsafe mechanism-class changes are classified as human-review required,
- post-patch results can be recorded as `resolved`, `unresolved`, or
  `regressed`,
- generic label wording and non-label offset language remain patch-assisted
  only,
- publication-safety changes are classified as human-review required,
- unresolved attempts do not write a new baseline that resets the comparison.

This still does not authorize Issue 5B auto-editing on real figures. The missing
evidence is real-fixture reliability: at least ten real `apply` handoffs should
be adjudicated and replayed through the loop before a source-editing mode is
designed.

## Next Required Work

Before Issue 5B:

1. Select one real safe candidate finding from the active dogfood fixture.
2. Change only that finding to `apply` in `critique_adjudication.yaml`; leave
   unrelated findings visible.
3. Run `/fig_loop` to record pre-patch evidence.
4. Apply the narrow patch by host agent or human, not by `/fig_loop`.
5. Compile, refresh critique when needed, update adjudication, and rerun
   `/fig_loop`.
6. Repeat until there are at least ten real apply-handoff examples with
   before/after evidence and outcome verdicts.

Only after that evidence exists should Issue 5B decide whether auto-patch is a
runner mode or an external host-agent protocol.
