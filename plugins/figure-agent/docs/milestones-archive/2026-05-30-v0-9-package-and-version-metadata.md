# v0.9 Package And Version Metadata

**Date:** 2026-05-30 KST
**Issue:** 89B - Package And Version Metadata
**Status:** implemented on `codex/issue70-guided-autonomy-roadmap`

## Scope

Issue 89B freezes the release-candidate version surface for the operator-grade
workflow without changing runtime behavior.

## Version Decision

The plugin version is bumped from `0.8.2` to `0.9.0`.

Rationale:

- Issues 70-88 add a new operator-grade layer: guided autonomy, bounded
  single-fixture execution, multi-fixture queue triage, queue-run delegation,
  blocked-row operator handoffs, and closeout follow-through.
- The change is larger than a patch release because it changes the default
  operating model, even though it does not add hidden mutation or new drawing
  behavior.
- v0.9 remains a release candidate for the operator workflow, not a claim that
  the plugin can certify Nature/Science acceptance.

## Files Updated

- `.claude-plugin/plugin.json`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `CHANGELOG.md`
- `tests/test_release_contract.py`
- `docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md`

## Package Audit

Running `plugin_package_audit.py` directly on the development checkout correctly
flags local generated paths such as `.venv`, build folders, export folders, and
tool caches. Those files are development artifacts and must not be staged.

For package validation, the plugin was copied to an isolated temporary package
root with generated build/export/cache paths excluded, then audited:

```bash
rsync -a --delete \
  --exclude .claude \
  --exclude .pytest_cache \
  --exclude .ralph \
  --exclude .ruff_cache \
  --exclude .venv \
  --exclude build \
  --exclude exports \
  --exclude __pycache__ \
  plugins/figure-agent/ /tmp/figure-agent-package-audit.0NNq3y/

python3 scripts/plugin_package_audit.py \
  /tmp/figure-agent-package-audit.0NNq3y --max-mib 300
```

Result:

- `package_size_mib=49.8`
- no package junk reported

## Verification

```bash
uv run pytest -q tests/test_release_contract.py
uv run ruff check tests/test_release_contract.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- Release contract tests: `18 passed`
- Ruff: clean
- Diff whitespace check: clean
- Claude plugin validation: manifest, plugin directory, and marketplace passed

## Review Notes

1. Contract consistency: manifest, `pyproject.toml`, `uv.lock`, README,
   changelog, release contract tests, and closeout status now agree on v0.9.0.
2. Package safety: generated local development artifacts remain excluded from
   the package candidate and are not release files.
3. Runtime safety: this slice changes no command behavior, no fixture source,
   no generated exports, no accepted/golden state, and no hidden automation
   boundary.

No known Issue 89B blocker remains.
