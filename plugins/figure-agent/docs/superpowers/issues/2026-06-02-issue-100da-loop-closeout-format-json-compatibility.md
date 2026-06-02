# Issue 100DA - Loop and closeout format-json compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, loop/closeout UX

## Problem

After the queue, queue-run, driver, and run commands accepted `--format json`,
two adjacent automation JSON surfaces still rejected the same spelling:

```bash
uv run python3 scripts/fig_loop.py fig5_floating_clip_mechanism --goal inspect --format json
uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --format json
```

Both failed at argparse even though both commands already had an automation JSON
path through `--json`.

## Scope

- Accept `--format json` in `fig_loop.py` as an alias for existing `--json`
  summary output.
- Accept `--format json` in `fig_closeout.py` as an alias for existing
  `--json` output.
- Accept `--format text` as the explicit prose/default spelling for both
  commands.
- Keep `/fig_loop` verify-only run artifact behavior unchanged.
- Keep `/fig_closeout` read-only behavior and exit-code policy unchanged.

## Non-goals

- Do not change `/fig_loop` run artifacts or decision schema.
- Do not change `/fig_closeout` step computation or closeout completeness
  semantics.
- Do not add JSON aliases to lower-level helper scripts in this slice.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_loop.py::test_main_accepts_format_json_as_output_compatibility_alias`
  - `uv run pytest -q tests/test_fig_closeout.py::test_closeout_cli_accepts_format_json_as_output_alias`
  both failed with `unrecognized arguments: --format json`.
- Green:
  - `uv run pytest -q tests/test_fig_loop.py::test_main_accepts_format_json_as_output_compatibility_alias tests/test_fig_loop.py::test_main_without_json_keeps_legacy_prose_output`
  - `uv run pytest -q tests/test_fig_closeout.py::test_closeout_cli_accepts_format_json_as_output_alias tests/test_fig_closeout.py::test_closeout_cli_json_outputs_machine_readable_report`
- Live probe:
  - `fig_closeout.py ... --format json` emitted `figure-agent.closeout.v1`

## Review Notes

1. **Compatibility** - Existing `--json` behavior is unchanged; `--format json`
   is only an alias.
2. **Scope containment** - The change touches output selection only.
3. **Operator reality** - The primary workflow commands now share one common
   explicit JSON-output spelling.
