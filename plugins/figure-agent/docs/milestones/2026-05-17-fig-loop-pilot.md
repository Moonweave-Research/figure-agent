# Fig Loop Pilot Handoff Protocol

**Date:** 2026-05-17
**Scope:** Issue 4A patch-assisted handoff contract
**Status:** first-stage protocol

## Purpose

The loop runner remains verify-only. It may identify a patch target, but the
patch is performed by a human or outer host agent. This document defines the
handoff contract that keeps that patch narrow, auditable, and reversible.

## Handoff Source

Run:

```bash
uv run python3 scripts/fig_loop.py <name> --goal "<goal>"
```

Read the newest `.scratch/fig-loop-runs/<timestamp>-<name>/iteration_001.json`.
Only use `patch_handoff` as a patch instruction when it is non-null.

## Single-Target Rule

Patch-assisted mode allows exactly one target per iteration:

- one `finding` target from `critique_adjudication.yaml`, or
- one `subregion` target from `subregion_iteration_log.md`.

Do not combine multiple findings, multiple sub-regions, or opportunistic cleanup
with the selected target. If the selected change exposes a second issue, leave
that issue visible for the next loop run.

## Required Handoff Fields

`patch_handoff` records:

- `target_type`
- `target_id`
- `patch_target`
- `reason`
- `allowed_edit_scope`
- `forbidden_edit_scope`
- `required_closeout_checks`
- `unresolved_findings_requirement`

If any of these fields are missing, treat the handoff as malformed and stop for
human review.

## Allowed Scope

The allowed edit scope is intentionally narrow:

- `examples/<name>/<name>.tex`
- `examples/<name>/authoring_plan.md`
- `examples/<name>/subregion_iteration_log.md`

Most patches should touch only the TikZ source. Planning/log files are allowed
only when the patch target or observed loop state needs a durable explanation.

## Forbidden Scope

The patch must not modify:

- `accepted`
- `golden_contract`
- `examples/<name>/exports/`
- `examples/<name>/build/`
- `examples/<name>/critique.md`
- unrelated examples
- broad refactors
- multiple findings in one patch

`critique.md` is reviewer output. The author/loop decision layer is
`critique_adjudication.yaml`.

## Required Closeout

After the patch, the outer agent must:

1. Run `/fig_compile <name>` or the equivalent compile command.
2. Refresh `/fig_critique <name>` when critique freshness requires it.
3. Update or recreate `examples/<name>/critique_adjudication.yaml`.
4. Preserve unresolved findings.
5. Run `/fig_loop <name> --goal "<goal>"` again.

The next loop run is the evidence that the patch closed or failed to close the
target. Do not claim resolution from source edits alone.

## Human-Gated Cases

Do not patch when:

- `patch_handoff` is null,
- `stop_reason` is `human_gate_required`,
- the target would change mechanism, topology, reference role, accepted state,
  golden state, or publication-safety status,
- the target cannot be isolated to one finding or one sub-region.

These cases require human/domain review before the next patch.

## Issue 5 Boundary

This protocol prepares safe dogfood evidence for Issue 5. It does not implement
safe auto-patch. At least five dogfood runs must show which finding classes are
reliable before any auto-patch mode is considered.

## Dogfood Run 1: fig1_overview_v2_pair_001_vault

Command:

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "dogfood Issue 4B patch handoff usability"
```

Observed state:

- `render_state: MISSING`
- `critique_state: STALE`
- `export_state: TRACKED_GOLDEN`
- notes: `coordinate_hints_missing`, `critique_stale`, `partial_export`,
  `stale_export`
- `patch_handoff: null`

Usability finding:

The first run exposed that stale/missing status prerequisites were previously
reported as `verify_only_complete`, which could be misread as a clean loop stop.
The runner now reports `status_action_required` when no patch target is selected
but `/fig_status` still requires compile/critique/export work.

Current next action:

Before patch-assisted dogfood can evaluate a real handoff on this fixture,
refresh the status prerequisites: compile, critique when freshness requires it,
and export according to the `/fig_status` next hint. Do not infer a patch target
from this run because `patch_handoff` is null.

## Dogfood Run 2: Escalation Policy on Pilot Fixture

Command:

```bash
uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault \
  --goal "Verify escalation policy on pilot fixture"
```

Observed decision:

- `stop_reason: status_action_required`
- `escalation_level: manual_approval_required`
- `requires_user_input: true`
- `requires_domain_review: false`
- `render_state: FRESH`
- `critique_state: FRESH`
- `export_state: TRACKED_GOLDEN`
- `patch_handoff: null`

Usability finding:

The desired steady state is that `/fig_loop` asks for human/domain review only
for mechanism, topology, reference-role, publication-safety, or conflicting
reviewer judgments. Routine stale-state and single-target polish work should be
agent-actionable. The current pilot state is not a domain-review request; it is
a manual approval checkpoint for tracked golden roll-forward via
`/fig_export fig1_overview_v2_pair_001_vault --force-golden`.
