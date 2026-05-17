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
  `critique_adjudication.yaml` status, stop reason, active patch target, and
  recommended next action.
- `decision.md` — human-readable stop reason, active patch target, and
  recommended next action.

`/fig_loop` is verify-only. It does not edit `examples/<name>/`, run compile/export,
change acceptance state, stage files, or run git mutation commands. Use it to
turn the current status + critique adjudication state into an auditable loop
checkpoint before a human or later automation decides what to patch.
