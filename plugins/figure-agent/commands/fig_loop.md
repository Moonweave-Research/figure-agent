---
description: Verify-only loop evidence runner for one figure. Writes run artifacts without patching, compiling, exporting, or accepting.
---

Run one read-only figure loop iteration and record the decision evidence.

**Usage**: `/fig_loop <name> --goal "<goal>"`

Run from the plugin root:

```bash
uv run python3 scripts/fig_loop.py <name> --goal "<goal>"
```

## When To Use

Use `/fig_loop` after `/fig_status <name>` says the normal compile, critique,
and (when in scope) adjudication prerequisites are ready enough to record loop
evidence, or when you need a verify-only patch-handoff decision. It is **not**
the full end-to-end runner: it will not run compile, critique, export,
adjudication, SVG polish, accepted/golden checks, or git operations for you.
If `/fig_status` reports `render_state: STALE`, `critique_state: MISSING |
STALE`, `export_state: MISSING | STALE`, or any unresolved blocking note,
return to the command that closes that gate before re-invoking `/fig_loop`.

For automation, emit a small machine-readable summary:

```bash
uv run python3 scripts/fig_loop.py <name> --goal "<goal>" --json
```

On success, `--json` keeps the same run artifacts and exit code `0`, but stdout
becomes one JSON object with:

- `run_dir`
- `manifest_path`
- `iteration_path`
- `final_stop_reason`
- `escalation_level`
- `patch_handoff_present`
- `auto_patch_eligibility`
- `patch_evidence_present`
- `post_patch_evidence_verdict`
- `recommended_next_action`

On preflight failure, the command preserves the existing error contract: exit
code `1`, empty stdout, and a prose `fig_loop.py: ...` message on stderr.

Outputs are written under `.scratch/fig-loop-runs/<timestamp>-<name>/`:

- `run_manifest.json` — fixture, goal, mode, branch/commit, run timing, and artifact list.
- `iteration_001.json` — `/fig_status`-equivalent state, per-axis verdicts,
  `critique_adjudication.yaml` status, stop reason, active patch target,
  `patch_handoff`, escalation summary, and recommended next action.
- `decision.md` — human-readable stop reason, active patch target, and
  recommended next action.

Each `axis_verdicts.<axis>` record keeps the legacy `state` and `verdict`
fields and also includes:

- `source` — the status field or fixture artifact used for the verdict.
- `evidence_path` — the backing file path when one exists, otherwise `null`.
- `evaluation_state` — one of `passed`, `needs_action`, `blocked`,
  `not_evaluated`, or `not_configured`.

In verify-only mode, axes such as `static_visual`, configured `theory`, and
configured `story_hierarchy` can remain `not_evaluated`; their presence in the
JSON is an audit slot, not proof that the runner performed those checks.

When `critique.md` is fresh schema `figure-agent.critique.v1.2`,
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

`/fig_loop` is verify-only. It does not edit `examples/<name>/`, run compile/export,
change acceptance state, stage files, or run git mutation commands. Use it to
turn the current status + critique adjudication state into an auditable loop
checkpoint before a human or later automation decides what to patch.

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

When `critique_state` is `MISSING` or `STALE`, `/fig_loop` reports
`status_action_required` with an ordinary `/fig_critique <name>` refresh action
before considering adjudicated human gates or manual golden roll-forward. Human
review and `--force-golden` approval are only meaningful after the critique
evidence they depend on is fresh.

## SVG Polish Handoff

`/fig_loop` remains verify-only for final-artifact polish. It may tell the user
that final-artifact polish is the next manual phase, but it must not edit SVG,
generated exports, source files, accepted metadata, or golden contracts.

Use SVG polish only after the generated-export loop is closed enough that the
remaining work is optical presentation cleanup. Blocking semantic
critique/adjudication findings must be closed before final promotion; SVG
polish must not mark unresolved findings as resolved. The polish target is one
fixture and one generated SVG:

- base export: `examples/<name>/exports/<name>.svg`
- polished target: `examples/<name>/polish/<name>.polished.svg`
- manifest: `examples/<name>/polish/svg_polish_manifest.yaml`
- audit closeout: `examples/<name>/polish/svg_polish_audit.md`

The handoff must record the base generated SVG path and hash, the target
polished SVG path, the intended `spec.yaml.final_artifact` opt-in, the allowed
visual-only edit classes, any must-backport edit class, the forbidden edit
scope, required manifest fields, and required post-polish checks.

Allowed SVG-only edit classes are limited to:

- `label_micro_position`
- `leader_line_micro_position`
- `stroke_polish`
- `icon_detail`
- `spacing_balance`
- `color_opacity_polish`
- `typography_cleanup`
- `export_cleanup`

The polisher may write only:

- `examples/<name>/polish/<name>.polished.svg`
- `examples/<name>/polish/svg_polish_manifest.yaml`
- `examples/<name>/polish/svg_polish_audit.md`
- `examples/<name>/spec.yaml`, only to add or confirm:

```yaml
final_artifact:
  kind: polished_svg
  manifest: polish/svg_polish_manifest.yaml
```

The polisher must not edit:

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

Closeout after SVG polish:

1. If TikZ, briefing, or spec semantics changed before polish, rerun compile
   and export before creating the polished SVG.
2. Refresh `/fig_critique <name>` when critique freshness requires it.
3. Add or confirm `spec.yaml.final_artifact.kind: polished_svg` only when this
   polished SVG is intended to become the declared final artifact.
4. Write `polish/svg_polish_audit.md` with the semantic-preservation decision,
   edit classes, toolchain, reviewer, and any backport decision.
5. Create or update `polish/svg_polish_manifest.yaml` last, after the audit and
   opt-in are final, so current source, export, critique, polished SVG, and
   audit hashes match.
6. Run `/fig_status <name>` and require `Final artifact: polished_svg FRESH`
   before treating the polished SVG as release-ready.
7. Do not set `accepted: true` unless publication provenance, final-artifact
   state, and the existing accepted/golden checks are closed.

If no reviewer can confidently classify every SVG edit as visual-only, set
`backport_required: true` in the manifest and return to the semantic source
loop instead of promoting the polished SVG.

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
uv run python3 scripts/critique_adjudication.py scaffold <name>
```

Then review `examples/<name>/critique_adjudication.yaml` manually. Leave
unresolved or domain-sensitive findings as `needs_human`; change exactly one
safe patch target to `apply` only when the outer agent is allowed to patch it.
