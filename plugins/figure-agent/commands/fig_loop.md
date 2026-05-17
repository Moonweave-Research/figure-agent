---
description: Verify-only loop evidence runner for one figure. Writes run artifacts without patching, compiling, exporting, or accepting.
---

Run one read-only figure loop iteration and record the decision evidence.

**Usage**: `/fig_loop <name> --goal "<goal>"`

Run from the plugin root:

```bash
uv run python3 scripts/fig_loop.py <name> --goal "<goal>"
```

Outputs are written under `.scratch/fig-loop-runs/<timestamp>-<name>/`:

- `run_manifest.json` — fixture, goal, mode, branch/commit, run timing, and artifact list.
- `iteration_001.json` — `/fig_status`-equivalent state, per-axis verdicts,
  `critique_adjudication.yaml` status, stop reason, active patch target,
  `patch_handoff`, and recommended next action.
- `decision.md` — human-readable stop reason, active patch target, and
  recommended next action.

`/fig_loop` is verify-only. It does not edit `examples/<name>/`, run compile/export,
change acceptance state, stage files, or run git mutation commands. Use it to
turn the current status + critique adjudication state into an auditable loop
checkpoint before a human or later automation decides what to patch.

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
