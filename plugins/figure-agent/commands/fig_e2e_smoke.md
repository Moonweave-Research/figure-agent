---
description: Run deterministic compile/export/status/loop smoke checks for one fixture and emit JSON evidence.
---

Run a repeatable end-to-end plugin smoke check for one fixture.

**Usage**: `/fig_e2e_smoke <name> [--repeat N] [--goal "<goal>"] [--json | --format json]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_e2e_smoke.py <name> --repeat 5 --goal "<goal>" --format json
```

Each repeat runs the same command sequence:

1. `bash scripts/compile.sh examples/<name>/<name>.tex`
2. `uv run python3 scripts/run_export.py <name>`
3. `uv run python3 scripts/status.py examples/<name>`
4. `uv run python3 scripts/fig_loop.py <name> --goal "<goal> (smoke run i/N)" --json`

The command emits one JSON object to stdout. `--json` and `--format json` are
accepted as explicit no-op output flags. Exit code is `0` only if every step in
every repeat succeeds. On the first failed step, the runner stops, returns exit
code `1`, and includes `failed_run` and `failed_step`.

For `--repeat N`, the runner also compares the stable status/loop outcome of
each repeat against run 1. Unique paths and command logs are not compared, but
status states, readiness booleans, notes, final stop reason, escalation level,
and patch-handoff presence must stay stable. A mismatch reports
`failed_step: repeat_stability`.

Top-level JSON fields:

- `schema`
- `fixture`
- `goal`
- `repeat`
- `success`
- `runs`
- `failed_run` and `failed_step` when `success` is false

Per-run JSON includes command summaries for compile/export/status/fig_loop,
structured `/fig_status` state, and the compact `/fig_loop --json` summary.

This is a smoke harness for plugin behavior, not a figure-quality claim. It
does not edit source files, critique files, acceptance metadata, or golden
contracts. It does run the normal compile/export commands, so build/export
outputs may be regenerated as part of ordinary pipeline verification.
