# Issue 100CF - Source Package Hygiene Guard

Status: completed on main in merge commit `5f80875`
Type: operator UX, plugin install freshness, package hygiene
Priority: P3

## Problem

Issue 100CD made installed cache package hygiene visible, and Issue 100CE made
dirty installed hygiene fail the CLI readiness exit code.

Live operation exposed the next leak: after cleaning the installed cache,
`plugin_install_freshness.py` could report `state: fresh`,
`installed_package_hygiene.state: clean`, and exit `0` while the development
plugin tree still contained generated package junk. The next same-version
uninstall/install would copy that source junk back into the installed cache.

## Contract

Keep the source-vs-install payload contract stable:

- `state` continues to report source-vs-installed payload freshness;
- `source_package_hygiene.state` reports whether the development plugin tree is
  package-clean before install;
- `installed_package_hygiene.state` reports whether the installed cache is
  package-clean after install;
- CLI exit code is readiness-oriented and returns `0` only when `state: fresh`,
  `source_package_hygiene.state: clean`, and
  `installed_package_hygiene.state: clean`.

## Acceptance

- A matching install with clean source and clean installed cache exits `0`.
- A matching install with generated source package junk still prints
  `state: fresh`.
- That same source-dirty case prints `source_package_hygiene.state: dirty`.
- That same source-dirty case exits nonzero so reinstall automation cannot
  silently pass a source tree that will copy junk into the cache.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
- `uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `git diff --check`
