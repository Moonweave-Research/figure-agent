# Issue 100DE - Critique brief CLI argument contract

Status: implemented in this slice

Type: host-vision workflow, CLI contract, operator safety

## Problem

`critique_brief.py` is the API-free prompt-context generator for
`/fig_critique`, but its CLI read only `sys.argv[1]`. Unknown extra arguments
were silently ignored:

```bash
uv run python3 scripts/critique_brief.py examples/<fixture> --bogus
```

This could let an operator believe an option was applied to the host-vision
brief when it was not. Because the brief controls the audit prompt, silent
argument loss is unsafe even when the generated brief itself is valid.

## Scope

- Replace the manual `sys.argv[1]` CLI parse with argparse.
- Preserve the existing no-argument usage error and return code.
- Preserve fixture-name, `examples/<name>`, and absolute-path resolution.
- Reject unknown extra arguments instead of silently ignoring them.

## Non-goals

- Do not add new critique brief options.
- Do not change brief contents, schema/rubric versions, freshness hashing, or
  crop/reference/aesthetic sections.
- Do not change `/fig_critique` host-only behavior.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_cli_rejects_unknown_extra_arguments`
  initially generated a full brief instead of rejecting `--bogus`.
- Green:
  - `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_cli_rejects_unknown_extra_arguments tests/test_critique_brief.py::test_critique_brief_cli_accepts_examples_fixture_path tests/test_critique_brief.py::test_critique_brief_cli_rejects_parent_relative_example_path tests/test_critique_brief.py::test_critique_brief_cli_reports_controlled_error_for_invalid_fixture_name tests/test_critique_brief.py::test_critique_brief_errors_when_png_missing`

## Review Notes

1. **Contract correctness** - The positional fixture contract is unchanged.
2. **Scope containment** - This is parser hardening only; no prompt text or hash
   inputs changed.
3. **Operational safety** - Unknown host-brief options now fail immediately
   rather than producing misleading audit input.
