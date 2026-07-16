---
description: Verify-only loop evidence runner for one figure. Writes run artifacts without patching, compiling, exporting, or accepting.
---

Run one read-only figure loop iteration and record the decision evidence.

**Usage**: `/fig_loop <name> --goal "<goal>" [--json | --format json]`

Run from the plugin root:

```bash
fig-agent loop <name> --goal "<goal>"
```

## When To Use

Run `/fig_loop` only when `/fig_status <name>` reports `render_state: FRESH`
and `critique_state` is `FRESH` or `NOT_REQUIRED` for the active loop scope,
or when you need a verify-only patch-handoff decision against the current
status snapshot. It is **not** the full end-to-end runner: it will not run
compile, critique, export, adjudication, SVG polish, accepted/golden checks,
or git operations for you. If `/fig_status` reports `render_state` is not
`FRESH`, `critique_state: MISSING | STALE | REFERENCE_MISSING`, or
`workflow_ready: false` for any reason other than missing exports or
final-artifact promotion, return to the command that closes that gate before
re-invoking `/fig_loop`. Export and final-artifact freshness are evaluated by
later gates and are not preconditions for recording loop evidence.

Canonical pre-loop order:

1. `render_state: MISSING | STALE` -> run `/fig_compile <name>` before
   critique or loop.
2. `render_state: FRESH` plus `critique_state: MISSING | STALE |
   REFERENCE_MISSING` -> run `/fig_critique <name>` or fix declared reference
   inputs.
3. `critique_state: FRESH` plus missing/stale/invalid
   `critique_adjudication.yaml` -> run `/fig_adjudicate <name>` or repair the
   adjudication contract.
4. Only then use `/fig_loop <name> --goal "<goal>"` to record the verify-only
   state and patch/human-gate evidence.

For automation, emit a small machine-readable summary:

```bash
fig-agent loop <name> --goal "<goal>" --json
```

On success, `--json` and `--format json` keep the same run artifacts and exit
code `0`, but stdout becomes one JSON object with:

- `run_dir`
- `manifest_path`
- `iteration_path`
- `final_stop_reason`
- `escalation_level`
- `patch_handoff_present`
- `auto_patch_eligibility`
- `patch_evidence_present`
- `post_patch_evidence_verdict`
- `audit_evidence`
- `narrative_context_summary`
- `next_action_summary`
- `recommended_next_action`

`next_action_summary` uses the same shared read-only shape as `/fig_status`,
`/fig_drive`, and `/fig_closeout`. It compresses the loop stop reason,
recommended next action, patch-handoff scope, and evidence refs; it does not
change verify-only behavior or make `/fig_loop` execute the next command. Its
`decision_boundary` field distinguishes blocking gates from advisory-only
aesthetic improvement candidates.

`narrative_context_summary` is a compact, read-only visibility record derived
from `spec.yaml`, `briefing.md`, and paper-local authoring notes. It reports the
schema, read-only flag, first takeaway source, panel-story input count, human
review question count, and the `rank_scoring=false` / `source_mutation=false`
boundaries. It does not change `stop_reason`, active patch target,
`human_gate_status`, candidate rank, or apply authority.

On preflight failure, the command preserves the existing error contract: exit
code `1`, empty stdout, and a prose `fig_loop.py: ...` message on stderr.

When canonical lifecycle resolution is current, invalid, or ambiguous, direct
legacy `/fig_loop` stops before creating scratch evidence and directs the caller
to canonical status/lifecycle. A transient recoverable fixture-root coordination
lease also serializes root admission and a legacy loop run; if it is busy,
retry after the active admission or legacy run finishes.

Outputs are written under `.scratch/fig-loop-runs/<timestamp>-<name>/`:

An external `--runs-root` remains supported for test or dogfood evidence. A
workspace path, a workspace path that resolves through a symlink, or an
external alias that resolves into the workspace is accepted only under the
canonical `.scratch/fig-loop-runs/` root. The fixture source and each workspace
path component are also fail-closed against symlinks before a checkpoint write.

- `run_manifest.json` — fixture, goal, mode, branch/commit, run timing, and artifact list.
- `iteration_001.json` — `/fig_status`-equivalent state, audit-evidence
  summary, narrative context summary, per-axis verdicts,
  `critique_adjudication.yaml` status, stop reason, active patch target,
  `patch_handoff`, escalation summary, and recommended next action.
- `decision.md` — human-readable stop reason, active patch target, and
  recommended next action. It also mirrors audit-evidence state, compact
  blockers, and next action so operators do not need to dig through raw JSON.

Each `axis_verdicts.<axis>` record keeps the legacy `state` and `verdict`
fields and also includes:

- `source` — the status field or fixture artifact used for the verdict.
- `evidence_path` — the backing file path when one exists, otherwise `null`.
- `evaluation_state` — one of `passed`, `needs_action`, `blocked`,
  `not_evaluated`, or `not_configured`.

In verify-only mode, axes such as `static_visual`, configured `theory`, and
configured `story_hierarchy` can remain `not_evaluated`; their presence in the
JSON is an audit slot, not proof that the runner performed those checks.

When `critique.md` is fresh schema `figure-agent.critique.v1.2` or newer,
`/fig_loop` can populate some existing audit slots from
`critique.md` frontmatter `quality_axes`:

- `story_hierarchy` uses `message_storyline`, `panel_role_coherence`, and
  `composition_layout`.
- `reference_fidelity` uses `reference_fidelity`, unless reference input is
  missing.
- `publication_safety` uses `publication_readiness`, unless an explicit
  adjudication human gate is already required.

These records keep the same `state`, `verdict`, `source`, `evidence_path`, and
`evaluation_state` fields, and may also include `quality_axes`,
`quality_axis_verdicts`, `quality_axis_recommended_actions`, and
`quality_axis_blocking_items`. Legacy, stale, missing, or malformed critique
frontmatter falls back to the earlier placeholder/status-derived behavior.

When `critique.md` is fresh schema `figure-agent.critique.v1.3` or newer,
`/fig_loop` also surfaces
`top_tier_audit_summary` in both `iteration_001.json` and the
`--json` summary. The summary reports slot count, verdict counts,
`weak_or_failed_slots`, `blocking_high_impact_slots`,
`blocking_high_impact_count`, `worst_verdict`, and the source critique path.
This is a read-only visibility surface; it does not make score or top-tier
audit prose release-gating by itself.

When `critique.md` is fresh schema `figure-agent.critique.v1.5` or newer,
`/fig_loop` also surfaces `editorial_art_direction_summary` in both
`iteration_001.json` and the `--json` summary. This summary reports the
editorial slot verdicts, high-impact blockers, `worst_verdict`, and
`polish_recommended_path` from
`editorial_art_direction.tikz_vs_svg_polish_trigger`. It is the machine-readable
handoff used by `/fig_drive --mode polish` to distinguish `continue_tikz`,
`ready_for_svg_polish`, `needs_human_art_direction`, and
`semantic_backport_required`.

For schema `figure-agent.critique.v1.14` and newer schemas that inherit the
route-detail contract, the summary also includes `polish_route_detail` from
the route-specific rationale field:
`remaining_tikz_lever`, `svg_polish_candidate_reason`,
`semantic_backport_reason`, or `human_art_direction_reason`. This keeps a
`verdict: pass` plus `recommended_path: continue_tikz` decision explainable
without weakening the rule that SVG polish starts only on
`ready_for_svg_polish`.

When `critique.md` is fresh schema `figure-agent.critique.v1.12`, `/fig_loop`
also surfaces `journal_art_direction_playbook_summary` in both
`iteration_001.json` and the `--json` summary. The summary reports the
playbook id, venue context, design-center verdict counts, weakest design-center
ids, active human-review trigger ids, and the selected playbook route rule.
This field is read-only visibility. It does not create a new stop boundary or
override existing human, top-tier, aesthetic lever, crop, export, accepted,
golden, or publication gates.

When that editorial summary exists, `/fig_loop` also writes
`svg_polish_readiness`. This additive summary makes the polish boundary
explicit:

- `can_start_svg_polish: true` only for `ready_for_svg_polish`
- `next_action: run_fig_loop` for `continue_tikz`
- `next_action: semantic_backport` for `semantic_backport_required`
- `next_action: human_art_direction_review` for `needs_human_art_direction`

When route detail exists, it is copied into
`svg_polish_readiness.route_detail` or the relevant
`blocking_items[].route_detail`, so an outer driver can report the exact
remaining TikZ lever, SVG candidate reason, semantic backport reason, or human
art-direction reason.

The field is read-only evidence. It does not override ordinary loop blockers,
human gates, top-tier blockers, crop uncertainty, aesthetic lever gates, export
freshness, accepted/golden gates, or publication provenance.

`/fig_loop` is verify-only. It does not edit `examples/<name>/`, run compile/export,
critique scaffolding, change acceptance state, stage files, or run git mutation commands. Use it to
turn the current status + critique adjudication state into an auditable loop
checkpoint before a human or later automation decides what to patch.

If `/fig_run` previously recorded a `.scratch/fig-run-runs/` journal, treat it
only as context. `/fig_loop` state still comes from live status and its own
`.scratch/fig-loop-runs/` checkpoint records.

`/fig_loop` also records `basin_summary` when current evidence repeats the same
patch target, aesthetic bottleneck, or severe reference-aesthetic metric across
fresh loop history. A basin changes the loop stop to `basin_detected`, clears
the active patch target, and asks the operator to step out for human or
second-opinion review before another local patch cycle. The detector is
read-only and ignores stale loop history whose render/critique freshness no
longer matches the current state.

## Final-Artifact Surfacing

`iteration_001.json["status"]` (and the `--json` summary) exposes compatibility
final-artifact fields for the generated export:

- `final_artifact_state`
- `final_artifact_kind` (`generated_export`)
- `final_artifact_path`

`decision.md` mirrors final-artifact state on a `final_artifact_state:` line.
Legacy non-`NONE` states route through `/fig_status`'s per-state next-action
hint:

| `final_artifact_state` | Loop hands off to                                                                                  |
|---|---|
| `MISSING`  | regenerate exports before continuing |
| `INVALID`  | fix malformed final-artifact metadata or spec state |
| `STALE`    | rerun compile/export before continuing |
| `BLOCKED`  | semantic backport to TikZ / briefing / spec, then rerun compile/export/critique |
| `FRESH`    | no final-artifact block; the loop may emit `verify_only_complete` if other gates close                  |
| `NONE`     | generated-export fixture; existing loop behaviour is unchanged                 |

The loop itself never edits the polished SVG, the manifest, the audit, or
generated exports — it only surfaces the state and forwards the canonical
next-action hint emitted by `/fig_status`.

## Escalation Summary

`iteration_001.json` records:

- `escalation_level`
- `requires_user_input`
- `requires_domain_review`

Escalation levels:

| Level | Meaning |
|---|---|
| `none` | Loop is closed for the requested mode. |
| `agent_action_required` | An ordinary command or local loop-contract refresh is needed; do not ask for human/domain review. |
| `patch_allowed` | Exactly one safe patch target is selected and `patch_handoff` is non-null. |
| `manual_approval_required` | A deliberate promotion or state-changing approval is needed, such as `--force-golden` or `accepted: true`; this is not domain review. |
| `human_review_required` | Domain judgment is required for mechanism, topology, reference role, publication safety, or conflicting reviewer signals. |
| `ambiguous_patch_selection` | More than one actionable target exists, or no single safe target can be selected. |

## Patch-Assisted Handoff

When `iteration_001.json.patch_handoff` is non-null, an outer agent may patch
exactly one target. The target is either:

- `target_type: finding` with one `target_id` from `critique_adjudication.yaml`
- `target_type: subregion` with one active sub-region id from
  `subregion_iteration_log.md`

If a fixture needs a log, start the canonical text-form file with
`fig-agent helper subregion_iteration_log.py --template examples/<name> --write-template`.
After each one-target patch, append the result with
`fig-agent helper subregion_iteration_log.py --append examples/<name> ...`.

The outer agent must keep the patch scope inside `patch_handoff.allowed_edit_scope`.
By default that means `examples/<name>/<name>.tex`, with optional updates to
`authoring_plan.md` or `subregion_iteration_log.md`.

The outer agent must not edit anything listed in
`patch_handoff.forbidden_edit_scope`: accepted/golden metadata, build/export
artifacts, `critique.md`, unrelated examples, broad refactors, or multiple
findings in one patch.

Closeout after any patch:

1. Run `/fig_compile <name>` or the equivalent compile command.
2. Refresh `/fig_critique <name>` when critique freshness requires it.
3. Update or recreate `examples/<name>/critique_adjudication.yaml`.
4. Preserve unresolved findings; do not hide them in `critique.md`.
5. Run `/fig_loop <name> --goal "<goal>"` again to record the next state.

Use `/fig_closeout <name>` between patching and claiming loop progress when an
outer agent needs a read-only checklist of missing or stale closeout steps. It
only recommends the final `/fig_loop` rerun after compile, critique,
adjudication, and export prerequisites are closed; golden roll-forward remains a
manual approval checkpoint rather than an auto-executable next action.

If `patch_handoff` is null, do not infer a broad patch target from prose. Follow
the `stop_reason` and `recommended_next_action`; human-gated and ambiguous cases
stay outside patch-assisted automation.

### Optional Bounded Patch Executor

`/fig_loop` itself remains verify-only. The only mutating pilot surface is the
explicit, diff-driven executor:

```bash
fig-agent helper fig_loop_patch_executor.py <name> --patch-file <path> --apply --format json
```

This executor does not generate edits from prose. It applies one prepared
unified diff only when the latest `/fig_loop` record has:

- one `patch_handoff` with `target_type: finding`
- one fresh adjudication decision with `decision: apply` for the same target
- `auto_patch_eligibility.level: auto_patch_candidate`
- non-empty `allowed_reasons` and no `blocked_reasons`
- exactly one changed path, and that path is inside
  `patch_handoff.allowed_edit_scope`

It refuses accepted, golden, export, build, `critique.md`, final-artifact, broad
refactor, sub-region, multi-target, human-gated, and malformed patch cases. Any
successful executor run writes `patch_apply_NNN.json` into the latest loop run
directory and leaves `closeout_required: true`; run `/fig_closeout <name>` next
before claiming progress.

When render is missing or stale, `/fig_loop` reports `status_action_required`
and forwards `/fig_status`'s canonical compile/export freshness hint before
considering critique refresh. When render is already fresh and
`critique_state` is `MISSING` or `STALE`, it reports `status_action_required`
with an ordinary `/fig_critique <name>` refresh action before considering
adjudicated human gates or manual golden roll-forward. Human review and
`--force-golden` approval are only meaningful after the render and critique
evidence they depend on is fresh.

## SVG Polish Handoff

`/fig_loop` remains verify-only for final-artifact polish. It may tell the user
that final-artifact polish is the next manual phase, but it must not edit SVG,
generated exports, source files, accepted metadata, or golden contracts.

Use `ready_for_svg_polish` only as an external handoff label after the
generated-export loop is closed enough that the remaining work is optical
presentation cleanup. Blocking semantic critique/adjudication findings must be
closed before final promotion; external SVG polish must not mark unresolved
findings as resolved.

Allowed SVG-only edit classes are limited to:

- `label_micro_position`
- `leader_line_micro_position`
- `stroke_polish`
- `icon_detail`
- `spacing_balance`
- `color_opacity_polish`
- `typography_cleanup`
- `export_cleanup`

An external polisher must not edit:

- `examples/<name>/exports/`
- `examples/<name>/build/`
- `examples/<name>/critique.md`
- `accepted` or `golden_contract` state
- unrelated fixtures
- TikZ, briefing, or spec semantics under the label of SVG polish
- multiple fixture artifacts in one polish handoff

Any edit that changes scientific content must be backported before the polished
SVG can be treated as final. Backport-required changes include adding, removing,
renaming, or retargeting a scientific component; changing material identity,
mechanism arrows, charge/current/force direction, panel order, scale/proximity
meaning, or storyline; adding apparatus parts that critique marked as
structural defects; or fixing a root cause that belongs in TikZ, briefing, or
`spec.yaml`.

Closeout after external SVG polish:

1. If TikZ, briefing, or spec semantics changed, rerun compile/export and
   refresh `/fig_critique <name>` when freshness requires it.
2. Treat the in-repo generated export as the release gate; the retired
   final-artifact manifest no longer makes a polished SVG release-ready.
3. Do not set `accepted: true` unless publication provenance and the existing
   accepted/golden checks are closed.

## Auto-Patch Eligibility

`/fig_loop` records `auto_patch_eligibility` in `iteration_001.json` and in
`--json` stdout. The field is always present and nullable: it is `null` unless
exactly one `patch_handoff` exists. This field is advisory and read-only; it
does not grant edit permission.

- `auto_patch_candidate` means the target appears to be a small label, overlap,
  clipping, whitespace, palette/style, or line-weight issue.
- `patch_assisted_only` means the target can be handed to an outer agent or
  human, but is not classified as safe for future automation.
- `human_review_required` means the target touches science, mechanism,
  topology, theory, reference interpretation, accepted/golden state, or
  publication safety.

Generic label wording changes are `patch_assisted_only` unless the finding also
states a concrete geometry problem such as overlap, clipping, label offset,
crowding, or collision. Generic `offset` and `style` language is not enough.

In this version, `auto_patch_eligibility.may_edit` is always `false`. The runner
must not edit figure source, critique output, exports, accepted metadata, or
golden contracts.

## Patch Evidence Baseline

When `patch_handoff` is non-null, `/fig_loop` also records `patch_evidence` in
`iteration_001.json`. This is a read-only pre-patch baseline:

- `phase: pre_patch`
- `verdict: not_evaluated`
- `may_edit: false`
- hashes for every path in `patch_handoff.allowed_edit_scope`
- required future post-patch verdicts: `resolved`, `unresolved`, `regressed`,
  or `ambiguous`

`patch_evidence` is `null` when no single patch handoff exists. It is not a
patch executor; it only gives the next loop or closeout step something concrete
to compare against.

When a later `/fig_loop` run sees a previous pre-patch baseline for the same
fixture, it records `post_patch_evidence` with a read-only verdict:

- `resolved`
- `unresolved`
- `regressed`
- `ambiguous`

The verdict compares allowed edit-scope hashes against the baseline and checks
the current adjudication decision for the target id. It still does not edit
source or artifacts. A run that records `post_patch_evidence` does not also
write a new `patch_evidence` baseline, so unresolved attempts do not silently
reset the comparison point.

When `stop_reason` is `missing_adjudication`, run:

```bash
fig-agent adjudicate <name>
```

Then review `examples/<name>/critique_adjudication.yaml` manually. Leave
unresolved or domain-sensitive findings as `needs_human`; change exactly one
safe patch target to `apply` only when the outer agent is allowed to patch it.
