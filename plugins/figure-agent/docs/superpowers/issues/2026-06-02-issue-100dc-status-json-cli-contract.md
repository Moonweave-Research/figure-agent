# Issue 100DC - Status JSON CLI contract

Status: implemented in this slice

Type: operator workflow, CLI contract, traffic-controller UX

## Problem

`/fig_status` is the canonical first workflow check, but its script used a
manual `sys.argv[1]` parser. As a result:

```bash
uv run python3 scripts/status.py <fixture> --json
uv run python3 scripts/status.py <fixture> --format json
```

printed the normal text status and silently ignored the extra arguments. This
created a worse trap than an argparse error: automation could believe it had
requested machine-readable status while receiving prose.

## Scope

- Add argparse-based parsing to `status.py`.
- Preserve default text output for one fixture and all-fixture summaries.
- Emit the existing `infer_stage()` payload for single-fixture JSON output.
- Emit a list of `infer_stage()` payloads for no-argument JSON output.
- Accept `--json` and `--format json` as equivalent machine-readable forms.
- Reject unknown extra arguments instead of silently ignoring them.

## Non-goals

- Do not change status inference, readiness policy, or next-action selection.
- Do not change `/fig_driver` as the canonical mode-aware action selector.
- Do not add mutation or repair behavior to `/fig_status`.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_status.py::test_main_json_outputs_single_status_payload tests/test_status.py::test_main_accepts_format_json_alias`
  failed because text output was emitted and JSON parsing failed.
- Green:
  - `uv run pytest -q tests/test_status.py::test_main_json_outputs_single_status_payload tests/test_status.py::test_main_accepts_format_json_alias tests/test_status.py::test_main_rejects_unknown_extra_arguments`

## Review Notes

1. **Contract correctness** - JSON output is the existing status vector, not a
   new schema with drift-prone duplicate fields.
2. **Compatibility** - Default text status behavior and no-argument summaries
   remain unchanged unless JSON output is explicitly requested.
3. **Operational safety** - Unknown extra arguments now fail at argparse rather
   than producing misleading prose.
