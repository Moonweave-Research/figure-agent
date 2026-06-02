# Issue 100CZ - Driver and run format-json compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, driver/run UX

## Problem

After Issues 100CX and 100CY made `/fig_queue` and `/fig_queue_run` accept
`--format json`, the adjacent single-fixture driver and runner still rejected
the same spelling:

```bash
uv run python3 scripts/fig_driver.py fig5_floating_clip_mechanism --mode polish --goal inspect --dry-run --format json
uv run python3 scripts/fig_run.py fig5_floating_clip_mechanism --mode polish --goal inspect --format json
```

Both failed at argparse even though both commands emit JSON by default.

## Scope

- Accept `--format json` as a no-op output alias in `fig_driver.py`.
- Accept `--format json` as a no-op output alias in `fig_run.py`.
- Keep `fig_driver.py --dry-run` required.
- Keep `fig_run.py` plan-only by default and `--execute` as the only execution
  opt-in.

## Non-goals

- Do not add table output.
- Do not change driver action selection, runner safety predicates, journaling,
  or embedded evidence payloads.
- Do not alter `/fig_loop` or `/fig_closeout` output behavior in this slice.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_driver.py::test_main_accepts_format_json_as_output_compatibility_noop`
  - `uv run pytest -q tests/test_fig_run.py::test_main_accepts_format_json_as_output_compatibility_noop`
  both failed with `unrecognized arguments: --format json`.
- Green:
  - `uv run pytest -q tests/test_fig_driver.py::test_main_accepts_format_json_as_output_compatibility_noop tests/test_fig_driver.py::test_main_accepts_json_flag_as_output_compatibility_noop`
  - `uv run pytest -q tests/test_fig_run.py::test_main_accepts_format_json_as_output_compatibility_noop`
- Live probes:
  - `fig_driver.py ... --format json` emitted `figure-agent.driver.v1`
  - `fig_run.py ... --format json` emitted `figure-agent.run.v1`

## Review Notes

1. **Compatibility** - Existing JSON output is unchanged; the new flag only
   prevents argparse failure.
2. **Safety** - The change does not make either command execute more than it
   already could. `fig_driver.py` still requires `--dry-run`; `fig_run.py` still
   requires `--execute` for mutation.
3. **Operator reality** - The main queue/driver/run path now accepts the same
   explicit JSON-output spelling.
