# Issue 100DI - JSON smoke/patch/harness flag compatibility

Status: implemented in this slice

Type: CLI compatibility, smoke evidence, patch handoff, SVG polish harness

## Problem

Three remaining operator-facing tools emitted JSON by default but rejected the
explicit JSON-output flags now accepted across the main workflow surface:

```bash
uv run python3 scripts/fig_e2e_smoke.py <name> --json
uv run python3 scripts/fig_loop_patch_executor.py <name> --patch-file <path> --format json
uv run python3 scripts/svg_polish_positive_harness.py --format json
```

This left the same small parser trap on deterministic smoke checks, explicit
patch handoff closeout, and SVG-polish plumbing evidence.

## Scope

- Accept `--json` as a no-op because output is already JSON.
- Accept `--format json` as a no-op because output is already JSON.
- Apply the compatibility to:
  - `fig_e2e_smoke.py`;
  - `fig_loop_patch_executor.py`;
  - `svg_polish_positive_harness.py`.

## Non-goals

- Do not add text output.
- Do not change smoke command order, patch application safety, SVG harness
  behavior, schema payloads, or exit-code policy.
- Do not relax `fig_loop_patch_executor.py --apply`; patch mutation still
  requires explicit `--apply`.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_e2e_smoke.py::test_main_accepts_json_noop_flag tests/test_fig_e2e_smoke.py::test_main_accepts_format_json_alias tests/test_fig_loop_patch_executor.py::test_executor_cli_accepts_json_noop_flag tests/test_fig_loop_patch_executor.py::test_executor_cli_accepts_format_json_alias tests/test_svg_polish_positive_harness.py::test_positive_harness_cli_accepts_json_noop_flag tests/test_svg_polish_positive_harness.py::test_positive_harness_cli_accepts_format_json_alias`
  failed with argparse `unrecognized arguments`.
- Green:
  - same command passed after adding parser aliases.

## Review Notes

1. **Contract preservation** - JSON schemas and return-code policy are
   unchanged.
2. **Mutation boundary** - `fig_loop_patch_executor.py` remains opt-in; `--json`
   and `--format json` do not imply `--apply`.
3. **Operator consistency** - Smoke, patch-handoff, and SVG-polish harness
   evidence now accept the same explicit JSON-output spelling as the primary
   driver, queue, run, loop, closeout, status, improve, install, and evidence
   helper surfaces.
