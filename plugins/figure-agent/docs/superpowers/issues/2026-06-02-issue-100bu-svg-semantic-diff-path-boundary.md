# Issue 100BU - SVG Semantic Diff CLI Fixture Path Boundary

Status: completed; see git history for implementation commit

Type: hardening, SVG polish, final-artifact contract, path boundary

## Problem

`svg_semantic_diff.py` already enforced fixture-relative `source_svg` and
`polished_svg` values inside the report. The CLI entrypoint, however, accepted
the top-level `example_dir` argument as a raw path.

That meant traversal-like relative paths such as `examples/../outside`, or an
existing relative directory named `outside`, could be treated as normal fixture
directories. If matching `exports/<name>.svg` and `polish/<name>.polished.svg`
files existed, the script wrote `polish/svg_semantic_diff.json` outside the
declared `examples/` fixture namespace.

## Goal

Make the CLI follow the same fixture identity boundary as the other SVG polish
tools:

- allow explicit absolute paths for test/direct expert use;
- allow `examples/<fixture-name>`;
- allow a single fixture name only when it resolves under `examples/`;
- reject traversal-like paths and existing outside-relative directories before
  report generation.

## Scope

In scope:

- Add a CLI-only fixture path resolver.
- Validate fixture names with `fixture_identity.validate_fixture_name()`.
- Preserve the programmatic `build_svg_semantic_diff_report(Path(...))` API.
- Preserve existing SVG semantic diff report schema and freshness behavior.

Out of scope:

- Changing semantic diff finding kinds, severity routing, or final artifact
  status behavior.
- Changing SVG polish executor, recipe, handoff, delta, or manifest contracts.
- Mutating real examples or generated polish artifacts.

## Acceptance

- `svg_semantic_diff.py examples/../outside` exits with a controlled invalid
  fixture path error and writes no report.
- `svg_semantic_diff.py outside` exits with a controlled invalid fixture path
  error when `outside/` exists outside `examples/`.
- Existing absolute-path CLI tests continue to pass.
- Existing semantic diff behavior for valid fixtures is unchanged.

## Implementation Notes

Added a small `_resolve_example_dir_for_cli()` helper and applied it in
`main()`. The helper mirrors the boundary used by the other SVG polish command
surfaces while leaving the lower-level builder untouched.

Verification:

- `uv run pytest -q tests/test_svg_semantic_diff.py`

## Review Questions

1. Does the CLI reject unsafe fixture syntax before writing
   `polish/svg_semantic_diff.json`?
2. Does the change avoid narrowing the programmatic API used by tests and status
   fixtures?
3. Does this keep final-artifact evidence inside declared examples before status
   or release gates consume it?
