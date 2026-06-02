# Issue 100CE - Plugin Install Hygiene Exit-Code Guard

Status: implemented in branch `codex/issue-100ce-install-hygiene-exit-code`
Type: operator UX, plugin install freshness, package hygiene
Priority: P3

## Problem

Issue 100CD made `plugin_install_freshness.py` report
`installed_package_hygiene`, but the CLI still exited `0` whenever the
source-vs-installed payload was fresh.

That meant a shell script or CI check that used only the exit code could treat
the installed plugin as ready even when the JSON said the installed cache still
contained generated package junk.

## Contract

Keep the JSON contract explicit:

- `state` continues to report source-vs-installed payload freshness;
- `installed_package_hygiene.state` continues to report package cleanliness;
- CLI exit code is readiness-oriented and returns `0` only when
  `state: fresh` and `installed_package_hygiene.state: clean`.

## Acceptance

- A fresh install with generated package junk still prints `state: fresh`.
- That same case prints `installed_package_hygiene.state: dirty`.
- That same case exits nonzero so shell automation cannot silently pass it.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py`
- `git diff --check`
