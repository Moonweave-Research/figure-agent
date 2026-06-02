# Issue 100DF - Match snippet CLI help contract

Status: implemented in this slice

Type: helper CLI, operator workflow, parser hygiene

## Problem

`match_snippet.py` used a manual `main(sys.argv)` parser. It did not silently
ignore unknown arguments, but it treated common CLI help as a missing file:

```bash
uv run python3 scripts/match_snippet.py --help
# missing: --help
```

For a documented helper used to inspect snippet candidate matching, this made
the tool harder to discover and kept it outside the parser-hardening standard
applied to the primary workflow surfaces.

## Scope

- Replace manual argument counting with argparse.
- Preserve the single positional `briefing.md` contract.
- Preserve no-argument usage error and missing-file behavior.
- Reject unknown extra arguments through argparse.
- Keep snippet scoring and output unchanged.

## Non-goals

- Do not change snippet matching weights, truth fixtures, snippet index schema,
  or output ranking.
- Do not add JSON output.
- Do not alter `styles/snippets/INDEX.yaml`.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_match_snippet.py::test_cli_help_uses_argparse tests/test_match_snippet.py::test_cli_rejects_unknown_extra_arguments`
  failed because `--help` returned usage as a normal return and `--bogus` was
  treated as the briefing path.
- Green:
  - `uv run pytest -q tests/test_match_snippet.py`

## Review Notes

1. **Parser correctness** - `--help` now works through argparse.
2. **Scope containment** - Matching logic, truth data, and ranking output are
   unchanged.
3. **Operational consistency** - The helper now follows the same explicit CLI
   parser standard as the rest of the hardened workflow surface.
