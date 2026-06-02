# Issue 100CY - Fig queue-run format-json compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, queue-run UX

## Problem

`fig_queue_run.py` emits JSON by default and already accepted `--json` as a
compatibility no-op, but rejected the common `--format json` spelling. During a
real polish-queue continuation check, the command

```bash
uv run python3 scripts/fig_queue_run.py --mode polish --goal "inspect" --format json --dry-run
```

failed at argparse before the plan-only queue-run evidence could be inspected.

## Scope

- Accept `--format json` as a no-op alias for the existing JSON-only output.
- Keep `--json` and `--dry-run` compatibility behavior unchanged.
- Keep queue filtering, plan-only default, `--execute` policy, and embedded
  `/fig_run` results unchanged.

## Non-goals

- Do not add table output to `fig_queue_run.py`; the command is JSON-only.
- Do not compact or restructure the queue-run result schema in this slice.
- Do not change execution policy or command safety predicates.

## Verification

- TDD red:
  `uv run pytest -q tests/test_fig_queue_run.py::test_main_accepts_format_json_as_output_compatibility_noop`
  failed with `fig_queue_run.py: error: unrecognized arguments: --format`.
- Green:
  `uv run pytest -q tests/test_fig_queue_run.py::test_main_accepts_format_json_as_output_compatibility_noop tests/test_fig_queue_run.py::test_main_accepts_json_and_dry_run_flags_as_plan_only_noops`

## Review Notes

1. **Compatibility** - Existing JSON output and `--json` behavior are unchanged.
2. **Scope containment** - Only the CLI parser changes; queue construction and
   execution safety are untouched.
3. **Operator reality** - This closes the next live output-flag trap after
   Issues 100CV and 100CX.
