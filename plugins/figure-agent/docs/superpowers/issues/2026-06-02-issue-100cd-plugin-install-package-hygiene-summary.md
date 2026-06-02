# Issue 100CD - Plugin Install Package Hygiene Summary

Status: implemented in branch `codex/issue-100cd-install-hygiene-summary`
Type: operator UX, plugin install freshness, package hygiene
Priority: P3

## Problem

`plugin_install_freshness.py` compared the development plugin payload with the
installed Claude plugin cache and correctly ignored generated cache junk for
source-vs-installed freshness.

That separation was correct, but operationally incomplete. A same-version
reinstall can leave the cache payload source-fresh while still containing
generated build/cache paths that `plugin_package_audit.py` rejects. The operator
then sees `state: fresh` and only learns about package bloat after running a
second command.

## Contract

Keep freshness and package hygiene separate:

- `state` remains the source-vs-installed freshness result;
- generated cache junk must not make a fresh payload stale;
- add `installed_package_hygiene` with `state`, `junk_count`, `junk_paths`, and
  `next_action`;
- hygiene should mirror `plugin_package_audit.py`, so the cleanup action it
  suggests can actually remove the reported paths.

## Acceptance

- A matching install with no generated junk reports
  `installed_package_hygiene.state: clean`.
- A matching install with generated package junk still reports `state: fresh`
  but also reports `installed_package_hygiene.state: dirty`.
- Missing/invalid installs report hygiene as `unknown`.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py`
- `git diff --check`
