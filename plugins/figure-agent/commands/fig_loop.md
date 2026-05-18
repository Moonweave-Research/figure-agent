---
description: Verify-only loop evidence runner for one figure. Writes run artifacts without patching, compiling, exporting, or accepting.
---

Run one read-only figure loop iteration and record the decision evidence.

**Usage**: `/fig_loop <name> --goal "<goal>"`

Run from the plugin root:

```bash
uv run python3 scripts/fig_loop.py <name> --goal "<goal>"
```

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

If `patch_handoff` is null, do not infer a broad patch target from prose. Follow
the `stop_reason` and `recommended_next_action`; human-gated and ambiguous cases
stay outside patch-assisted automation.

When `stop_reason` is `missing_adjudication`, run:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name>
```

Then review `examples/<name>/critique_adjudication.yaml` manually. Leave
unresolved or domain-sensitive findings as `needs_human`; change exactly one
safe patch target to `apply` only when the outer agent is allowed to patch it.
