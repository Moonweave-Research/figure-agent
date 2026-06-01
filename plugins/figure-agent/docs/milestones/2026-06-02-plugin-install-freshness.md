# Plugin Install Freshness Check

Date: 2026-06-02

Issue: `docs/superpowers/issues/2026-06-02-issue-100w-plugin-install-freshness.md`

Status: implemented

## What Shipped

Issue 100W adds a read-only diagnostic for the recurring operator question:
"is Claude using the latest figure-agent plugin?"

```text
development plugin tree
-> latest ~/.claude/plugins/cache/figure-agent-local/figure-agent/<version>
-> generated/junk paths ignored
-> source/install fingerprints
-> changed/missing/extra payload file lists
-> next action
```

The tool intentionally ignores real `examples/` work product so active figure
edits do not pollute plugin-install freshness. It compares the operational
plugin payload: commands, scripts, skills, styles, docs, release metadata, tests,
and other non-generated package files.

## Command

```bash
python3 scripts/plugin_install_freshness.py
```

The command emits `figure-agent.plugin-install-freshness.v1` JSON and exits `0`
only when the latest local cache matches the development plugin payload.

## Local Cache Observation

Running against the current local cache reported:

```text
state: stale
changed_files: 81
missing_files: 170
extra_files: 0
next_action: claude plugin update figure-agent@figure-agent-local
```

That is expected in the development worktree because the cache predates recent
Issue 100 work and this new diagnostic itself.

## Boundary Safety

- No cache mutation.
- No automatic `claude plugin update`.
- No package cleanup.
- No source fixture, export, accepted/golden, SVG, or publication mutation.

## Verification

```text
uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py
26 passed

uv run ruff check scripts/plugin_install_freshness.py tests/test_plugin_install_freshness.py tests/test_release_contract.py
All checks passed!

git diff --check
clean
```

Full-suite and plugin validation still need to run before merge.
