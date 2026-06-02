# Issue 100CG - Plugin Hygiene Next-Action Quoting

Status: implemented in branch `codex/issue-100cg-quote-install-next-actions`
Type: operator UX, shell safety, plugin install freshness, package hygiene
Priority: P3

## Problem

Issue 100CF added `source_package_hygiene` and emitted cleanup commands for the
development plugin tree. Live operation immediately exposed a shell-safety gap:
the emitted `next_action` included the repository path
`/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent`
without quoting. In zsh, `[figure-agent]` was interpreted as a glob pattern and
the command failed with `no matches found`.

## Contract

All `plugin_package_audit.py ... --clean --max-mib 300` commands emitted by
`plugin_install_freshness.py` must quote path arguments so operators can copy
them directly in shells that treat brackets, spaces, or other characters as
syntax.

The quoting applies to:

- `source_package_hygiene.next_action`;
- `installed_package_hygiene.next_action`.

The top-level freshness `next_action` values for `claude plugin ...` remain
unchanged.

## Acceptance

- A dirty source path containing shell-special characters emits a quoted cleanup
  command.
- A dirty installed path containing shell-special characters emits a quoted
  cleanup command.
- Existing clean/fresh, dirty-source, and dirty-installed exit-code contracts
  continue to pass.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `git diff --check`
