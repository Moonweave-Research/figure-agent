# Issue 100CJ - Source Git Hygiene Guard

Status: implemented
Type: operator UX, plugin install freshness, git hygiene, package boundary
Priority: P3

## Problem

`plugin_install_freshness.py` could report a ready install even when the
development plugin tree had uncommitted tracked changes.

Live reproduction after Issue 100CI:

- the development tree had a user-edited figure source:
  `examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex`;
- the installed Claude plugin cache contained the byte-identical dirty file;
- `plugin_install_freshness.py` still printed `state: fresh`,
  `source_package_hygiene.state: clean`,
  `installed_package_hygiene.state: clean`, and exited `0`.

This happened because payload fingerprinting intentionally excludes `examples/`
and package hygiene only detects generated junk. That is correct for those
contracts, but incomplete for install readiness: local plugin installs copy the
working directory, so dirty user figure-source work can become installed plugin
cache truth.

## Contract

Install readiness must include source git hygiene:

- emit `source_git_hygiene` in every freshness payload;
- report dirty plugin-root git paths when the development plugin tree has
  uncommitted tracked or untracked changes;
- return nonzero when source/install payloads match but source git hygiene is
  dirty;
- keep non-git temp/test plugin roots usable by reporting git hygiene as
  `unavailable` rather than failing the comparison.

## Acceptance

- TDD reproduces a git worktree where source and installed payloads match dirty
  tracked content, and the old CLI exits `0`.
- The new CLI exits nonzero for that case.
- The JSON names the dirty path relative to the plugin root.
- README release guidance explains `source_git_hygiene` and why dirty source
  changes must be committed, stashed, or moved aside before reinstalling.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
