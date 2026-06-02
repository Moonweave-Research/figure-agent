# Issue 100DD - Fig improve JSON flag compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, loop UX

## Problem

`fig_improve.py` is the loop-centered operator entrypoint and emits JSON by
default, but it rejected both common explicit JSON-output spellings:

```bash
uv run python3 scripts/fig_improve.py <fixture> --goal "<goal>" --json
uv run python3 scripts/fig_improve.py <fixture> --goal "<goal>" --format json
```

This was a low-risk but confusing mismatch after `/fig_drive`, `/fig_run`,
`/fig_queue`, `/fig_queue_run`, `/fig_loop`, `/fig_closeout`, `/fig_status`,
and helper stdout JSON parsers accepted explicit JSON flags.

## Scope

- Accept `--json` as a no-op because output is already JSON.
- Accept `--format json` as a no-op because output is already JSON.
- Preserve `figure-agent.improve.v1` payload shape, execution boundaries, and
  stopping policy.

## Non-goals

- Do not add text output.
- Do not change loop execution, actor boundaries, or patch/release behavior.
- Do not make `/fig_improve` auto-author host critiques, source patches, SVG
  edits, golden roll-forward, or accepted-state changes.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_improve.py::test_main_accepts_format_json_alias`
  failed with `unrecognized arguments: --format json`.
- Green:
  - `uv run pytest -q tests/test_fig_improve.py::test_main_accepts_format_json_alias tests/test_fig_improve.py::test_main_accepts_json_noop_flag`

## Review Notes

1. **Compatibility** - Existing JSON output remains unchanged.
2. **Scope containment** - The flags are parser aliases only; no execution
   policy changes.
3. **Operator reality** - Loop-centered usage now accepts the same explicit JSON
   spelling as the other workflow surfaces.
