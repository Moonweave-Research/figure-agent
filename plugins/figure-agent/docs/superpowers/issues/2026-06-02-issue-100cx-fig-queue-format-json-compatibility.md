# Issue 100CX - Fig queue format-json compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, queue UX

## Problem

`fig_queue.py` already supported JSON output through `--json`, but rejected the
common `--format json` spelling. During a real polish-queue review, the command

```bash
uv run python3 scripts/fig_queue.py --mode polish --format json
```

failed at argparse before reaching the actual queue evidence.

This is the same operator-footgun class as Issue 100CV: a reasonable explicit
output flag prevents the operator from seeing the real driver/queue state.

## Scope

- Accept `--format json` as an alias for existing `--json` output.
- Accept `--format table` as the explicit default table form.
- Keep existing `--json`, table output, filters, command-plan, and command-only
  behavior unchanged.

## Non-goals

- Do not add new output schemas.
- Do not change queue filtering, row construction, command-plan safety, or
  driver selection.
- Do not make `/fig_queue` execute anything.

## Verification

- TDD red:
  `uv run pytest -q tests/test_fig_queue.py::test_main_accepts_format_json_alias`
  failed with `fig_queue.py: error: unrecognized arguments: --format`.
- Green:
  `uv run pytest -q tests/test_fig_queue.py::test_main_accepts_format_json_alias tests/test_fig_queue.py::test_main_prints_json`

## Review Notes

1. **Compatibility** - Existing `--json` remains supported; `--format json` is
   only an alias.
2. **Scope containment** - The change touches output selection only. It does
   not alter the queue contract or execution policy.
3. **Operator reality** - This removes a live CLI trap encountered while trying
   to inspect polish readiness across fixtures.
