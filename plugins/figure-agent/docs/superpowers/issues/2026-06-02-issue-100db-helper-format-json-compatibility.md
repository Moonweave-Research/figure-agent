# Issue 100DB - Helper format-json compatibility

Status: implemented in this slice

Type: operator workflow, CLI compatibility, helper UX

## Problem

After primary workflow commands accepted `--format json`, two documented helper
scripts still rejected the same spelling:

```bash
uv run python3 scripts/subregion_active_set.py examples/<name>/subregion_iteration_log.md --format json
uv run python3 scripts/reference_pack.py examples/<name>/reference/reference_pack.md --format json
```

Both helpers already had `--json` output paths and are referenced in
operator-facing docs, so this left a smaller but still real output-flag trap.

## Scope

- Accept `--format json` in `subregion_active_set.py` as an alias for `--json`.
- Accept `--format json` in `reference_pack.py` as an alias for `--json`.
- Accept `--format text` as the explicit default/prose form.
- Keep parser behavior, validation, exit codes, and output schemas unchanged.

## Non-goals

- Do not alter subregion active-set parsing.
- Do not alter reference-pack validation or role semantics.
- Do not add aliases to detector scripts that use `--json-output <path>` rather
  than stdout JSON.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_subregion_active_set.py::test_cli_accepts_format_json_alias`
  - `uv run pytest -q tests/test_reference_pack.py::test_cli_accepts_format_json_alias`
  both failed with `unrecognized arguments: --format json`.
- Green:
  - `uv run pytest -q tests/test_subregion_active_set.py::test_cli_accepts_format_json_alias tests/test_reference_pack.py::test_cli_accepts_format_json_alias`
  - `uv run ruff check scripts/subregion_active_set.py scripts/reference_pack.py tests/test_subregion_active_set.py tests/test_reference_pack.py`

## Review Notes

1. **Compatibility** - Existing `--json` and text output behavior are unchanged.
2. **Scope containment** - Detector scripts with `--json-output` are not changed;
   this slice only covers stdout JSON helpers.
3. **Operator reality** - The same output spelling now works across primary
   workflow commands and documented helper parsers.
