# Issue 100AY - Perception Pack Figure Name Boundary

Status: implemented

Type: command safety, path-boundary hardening, fixture identity consistency

## Problem

Issue 100AX left `perception_pack.py` as a separate design question because it
supports cwd-based operation: an operator may run the script from a compiled
figure directory instead of from the repository root with an `examples/<name>`
fixture.

That cwd mode still used `name` as a filename segment:

- `build/<name>.pdf`;
- `build/<name>.png`;
- fallback `examples/<name>`.

An unsafe name such as `../outside` could therefore resolve
`build/../outside.pdf` in cwd mode and proceed far enough to reset
`build/perception/`. The command should not treat path components as a figure
identity even when it is intentionally operating from the current directory.

## Decision

Reuse `fixture_identity.validate_fixture_name()` at the start of
`perception_pack.build_perception_pack()`.

This preserves cwd-based operation for safe single-component figure names while
rejecting absolute paths, `..`, and multi-component paths before any PDF/PNG
lookup or `build/perception` reset.

The CLI catches only that fixture-name `ValueError`, prints a controlled
`perception_pack.py: ...` error, and exits non-zero. Other runtime failures such
as missing/invalid PDF or PNG artifacts keep their existing behavior.

## Tests

Covered by:

- `tests/test_perception_pack.py::test_perception_pack_rejects_unsafe_name_before_resetting_cwd_perception`
- `tests/test_perception_pack.py::test_perception_pack_cli_rejects_unsafe_name_cleanly`

