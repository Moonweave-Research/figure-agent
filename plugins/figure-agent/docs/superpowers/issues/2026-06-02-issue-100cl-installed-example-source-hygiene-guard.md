# Issue 100CL - Installed Example-Source Hygiene Guard

Status: implemented
Type: operator UX, plugin install freshness, installed cache hygiene
Priority: P3

## Problem

`plugin_install_freshness.py` intentionally excludes `examples/` from payload
freshness so generated figure work products and fixture outputs do not dominate
plugin command/script/doc freshness.

That payload rule is still useful, but it left a cache-readiness gap:
installed example source files could differ from the development plugin tree
while the diagnostic still printed `state: fresh`, `changed_files: []`, clean
package hygiene, and exit `0`.

This matters because local plugin installs copy examples into the Claude plugin
cache. Claude or operators can inspect those examples as plugin reference
material, so stale or dirty installed example sources should not be invisible.

## Contract

Keep payload freshness semantics unchanged:

- `state` and `changed_files` still ignore `examples/`.

Add a separate readiness signal:

- emit `installed_example_source_hygiene`;
- compare non-generated files under `examples/` between source and installed
  cache;
- ignore generated example build/export/cache products;
- exit nonzero when installed example source differs from source;
- top-level `next_action` should point at clean-source reinstall for this
  blocker after source/package/git hygiene blockers.

## Acceptance

- TDD reproduces differing `examples/demo/demo.tex` source/install content
  passing payload freshness.
- The new diagnostic keeps `state: fresh` and `changed_files: []` for that
  payload contract.
- The new diagnostic reports
  `installed_example_source_hygiene.state: dirty`, names the changed example
  path, and exits nonzero.
- README documents the separate example-source hygiene field.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
