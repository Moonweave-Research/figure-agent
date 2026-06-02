# Issue 100BV - Golden Artifact Gate CLI Fixture Path Boundary

Status: completed on main in merge commit `b587c52`

Type: hardening, release gate, accepted/golden boundary, path boundary

## Problem

`check_golden_artifacts.py` is a release-adjacent gate used to validate export
artifacts, accepted fixture contracts, publication compliance, final-artifact
state, and warning budgets. Its CLI accepted `example_dir` as a raw path.

That allowed traversal-like relative paths such as `examples/../outside`, or an
existing relative directory named `outside`, to be inspected as if they were a
normal fixture. With a minimal export set, the CLI could print
`OK: golden artifact gates passed for outside`.

## Goal

Make the CLI follow the same fixture identity boundary used by direct workflow
entrypoints and SVG polish command surfaces:

- allow explicit absolute paths for direct test/expert use;
- allow `examples/<fixture-name>`;
- allow a single fixture name only when it resolves under `examples/`;
- reject traversal-like paths and existing outside-relative directories before
  running the golden gate.

## Scope

In scope:

- Add a CLI-only fixture path resolver.
- Validate fixture names with `fixture_identity.validate_fixture_name()`.
- Preserve the public `check_example(Path(...))` API for tests and direct
  callers.
- Preserve all existing artifact, accepted, publication, final-artifact, and
  warning-budget gate behavior.

Out of scope:

- Changing golden contract semantics.
- Changing artifact DPI/label/source-inventory thresholds.
- Mutating exports, accepted state, golden artifacts, or publication files.

## Acceptance

- `check_golden_artifacts.py examples/../outside --no-require-accepted` exits
  with a controlled invalid fixture path error.
- `check_golden_artifacts.py outside --no-require-accepted` exits with a
  controlled invalid fixture path error when `outside/` exists outside
  `examples/`.
- Existing direct `check_example(Path(...))` tests continue to pass.
- Existing valid fixture CLI behavior remains unchanged.

## Implementation Notes

Added `_resolve_example_dir_for_cli()` and applied it only in `main()`. This
keeps the lower-level checker usable with explicit paths while preventing the
operator-facing CLI from certifying escaped relative paths.

Verification:

- `uv run pytest -q tests/test_golden_artifact_checks.py`

## Review Questions

1. Does the CLI fail before running the golden gate for traversal-like fixture
   paths?
2. Is the direct API preserved for unit tests and explicit expert calls?
3. Does this avoid changing accepted/golden semantics while strengthening the
   release boundary?
