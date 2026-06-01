# Issue 100BI - Critique Brief CLI Fixture Path Boundary

Status: implemented

Type: host-critique input safety, path-boundary hardening, operator trust

## Problem

`critique_brief.py` produces the prompt-context block consumed by
`/fig_critique`. The brief tells the host LLM which render, crops, references,
source, and schema/rubric contract to inspect.

Before this issue, the CLI accepted traversal-like relative input such as
`examples/../review_demo`. If the normalized outside directory had the expected
fixture files, the script emitted a full `# Critique brief` and audit crop list
for that escaped path. That makes the host-vision entrypoint look like it is
reviewing the normal `/fig_critique <name>` target when the CLI input is not a
valid fixture identity.

## Decision

Harden only the CLI resolver. The public `generate_for(Path)` API remains
path-explicit for tests and internal/ad hoc review use.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
and invalid fixture names before generating a brief. Invalid input exits through
the existing controlled `CritiqueBriefError` path with code `2`.

## Tests

Covered by:

- `tests/test_critique_brief.py::test_critique_brief_cli_accepts_examples_fixture_path`
- `tests/test_critique_brief.py::test_critique_brief_cli_rejects_parent_relative_example_path`
- `tests/test_critique_brief.py::test_critique_brief_cli_reports_controlled_error_for_invalid_fixture_name`
- existing CLI error/freshness tests.

## Review Notes

- This does not change `generate_for(Path)` behavior.
- Absolute path support is preserved because existing tests and ad hoc review
  helpers use explicit temporary fixture paths.
- The normal documented `/fig_critique` bridge command
  `uv run python3 scripts/critique_brief.py examples/<name>` remains valid.
- The command now fails closed before an escaped directory can be presented to
  the host LLM as a normal critique target.
