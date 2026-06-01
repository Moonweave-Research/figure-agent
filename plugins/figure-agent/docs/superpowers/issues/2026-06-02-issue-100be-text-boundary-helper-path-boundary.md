# Issue 100BE - Text Boundary Helper Parent-Relative Path Boundary

Status: implemented

Type: authoring-helper safety, path-boundary hardening, write-surface containment

## Problem

`text_boundary_spec_helper.py` is an authoring helper that can rewrite
`spec.yaml.text_boundary_checks` when run with `--write`.

The intended operator command is:

```bash
uv run python3 scripts/text_boundary_spec_helper.py examples/<name> --write
```

The helper also supports explicit fixture/spec paths for tests and local
authoring. Before this issue, a relative parent path such as
`examples/../outside --write` was accepted when the normalized directory
existed, allowing the helper to rewrite `outside/spec.yaml`.

That path form is not a valid fixture identity and is too easy for an
operator/agent to produce accidentally. Because the helper is write-capable, it
should reject parent-relative relative paths before resolving or writing a spec.

## Decision

Reject relative input paths containing `..` inside `_fixture_dir()` with a
controlled `TextBoundarySpecHelperError`.

This is intentionally narrower than the fixture-name validator:

- `examples/<name>` and `examples/<name>/spec.yaml` remain supported;
- absolute explicit paths remain supported for isolated tests and deliberate
  local authoring;
- relative parent traversal such as `../outside`,
  `examples/../outside`, or `examples/<name>/../other` is rejected.

## Tests

Covered by:

- `tests/test_text_boundary_spec_helper.py::test_main_rejects_parent_relative_fixture_path_before_write`
- existing generation, print-only, write-mode, malformed-input, and missing
  layout tests.
