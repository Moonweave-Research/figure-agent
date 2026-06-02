# Issue 100CW - Package audit evidence-preserving clean

Status: implemented in this slice

Type: operator workflow, package hygiene, evidence preservation

## Problem

`plugin_package_audit.py --clean` correctly removes generated package junk such
as `.venv`, tool caches, fixture `build/`, and fixture `exports/`. That behavior
is right for validating an installable plugin package, because generated fixture
artifacts should not be copied into Claude's plugin cache.

During an evidence-driven SVG-polish pass, however, the operator may want to
remove only local Python/test caches created by `uv run` while preserving freshly
compiled fixture `build/` and `exports/` evidence for queue inspection. Running
the broad package cleanup directly after compile evidence can erase that local
evidence before the next queue or driver check.

## Scope

Add an explicit development-cleanup mode:

- `plugin_package_audit.py <root> --clean --preserve-fixture-artifacts`
  removes generated non-fixture junk such as `.venv`, `.pytest_cache`, and
  `.ruff_cache`;
- the same mode keeps `examples/<name>/build` and
  `examples/<name>/exports`;
- default package-audit behavior remains unchanged and still treats fixture
  build/export artifacts as package junk.

## Non-goals

- Do not make fixture build/export artifacts package-safe by default.
- Do not preserve ignored fixture artifacts during actual install-package
  validation unless the operator explicitly asks for this development cleanup
  mode.
- Do not alter plugin install freshness payload hashing or example-source
  hygiene.

## Verification

- TDD red: `--preserve-fixture-artifacts` was rejected by argparse.
- Green:
  `uv run pytest -q tests/test_release_contract.py::test_plugin_package_audit_can_preserve_fixture_artifacts_in_dev_cleanup tests/test_release_contract.py::test_plugin_package_audit_detects_and_removes_generated_junk tests/test_release_contract.py::test_plugin_package_audit_does_not_remove_tracked_paths_in_dev_worktree`
- `uv run ruff check scripts/plugin_package_audit.py tests/test_release_contract.py`

## Review Notes

1. **Safety** - The default package-clean path is unchanged. The new flag only
   narrows deletion scope when explicitly requested.
2. **Architecture fit** - Package hygiene and fixture evidence remain separate:
   package validation still rejects generated artifacts, while evidence loops
   can keep fresh local renders.
3. **Operator reality** - This avoids a real evidence-loop footgun observed
   after compiling fixtures and then cleaning `uv`/pytest cache junk.
