# Issue 100CK - Install Next-Action Precedence Guard

Status: implemented
Type: operator UX, plugin install freshness, package hygiene, git hygiene
Priority: P3

## Problem

Issue 100CJ added `source_git_hygiene` and made
`plugin_install_freshness.py` exit nonzero when the development plugin tree has
uncommitted plugin-root changes.

However, the top-level `next_action` still came from payload freshness. A
fresh payload with dirty source git could print:

`installed plugin cache matches the development plugin tree`

while exiting `1`. A fresh payload with dirty installed package hygiene could
also print the same success-oriented action instead of the package-audit cleanup
command.

This is an operator leak: the exit code is correct, but the most visible action
can still tell the user or agent to do the wrong thing.

## Contract

`plugin_install_freshness.py` top-level `next_action` must name the readiness
blocker that currently prevents exit `0`.

Precedence:

1. dirty source package hygiene;
2. dirty source git hygiene;
3. dirty installed package hygiene;
4. payload install/update/reinstall action;
5. fresh success message.

## Acceptance

- A fresh source/install payload with dirty source git exits nonzero and has a
  top-level `next_action` equal to `source_git_hygiene.next_action`.
- A fresh source/install payload with dirty installed package hygiene exits
  nonzero and has a top-level `next_action` equal to
  `installed_package_hygiene.next_action`.
- Existing freshness, same-version reinstall, missing install, invalid install,
  and non-git test roots remain compatible.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
