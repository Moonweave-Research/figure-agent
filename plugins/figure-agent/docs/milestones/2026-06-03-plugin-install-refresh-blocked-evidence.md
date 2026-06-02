# Plugin Install Refresh Blocked Evidence

Date: 2026-06-03

Related issues:

- `docs/superpowers/issues/2026-06-02-issue-100cj-source-git-hygiene-guard.md`
- `docs/superpowers/issues/2026-06-02-issue-100ck-install-next-action-precedence-guard.md`
- `docs/superpowers/issues/2026-06-02-issue-100cl-installed-example-source-hygiene-guard.md`
- `docs/superpowers/issues/2026-06-02-issue-100cm-marketplace-source-hygiene-guard.md`

Status: blocked by user-owned dirty figure source; diagnostic behavior is correct

## Goal

Verify the remaining Issue 100 installed-cache refresh candidate against the
current worktree. The question is whether the plugin correctly refuses to
recommend reinstall/update while user-owned dirty figure source is present.

## Cleanup Before Diagnosis

Running repeated queue, driver, pytest, and validation commands created package
junk. The final package cleanup command was:

```bash
python3 scripts/plugin_package_audit.py . --clean --max-mib 300
```

It removed generated build/export paths and reported:

```text
package_size_mib=172.5
```

After cleanup, package hygiene was clean.

## Install Freshness Diagnosis

Command:

```bash
python3 scripts/plugin_install_freshness.py --json
```

Exit code: `1`

Observed states after package cleanup:

| Field | State | Meaning |
| --- | --- | --- |
| `state` | `stale` | install/cache cannot be trusted as fresh |
| `source_package_hygiene` | `clean` | generated package junk is not the remaining blocker |
| `source_git_hygiene` | `dirty` | user-owned source edit is present |
| `marketplace_source_hygiene` | `clean` | `figure-agent-local` marketplace source matches this repo root |
| `installed_package_hygiene` | `clean` | installed plugin cache has no generated junk |
| `installed_example_source_hygiene` | `dirty` | installed examples differ and should not be trusted until reinstall from clean source |

Top-level `next_action`:

```text
commit, stash, or move aside plugin-root changes before reinstalling the plugin
```

Dirty source path:

```text
examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

## Judgment

The installed-cache refresh is correctly blocked. The diagnostic prioritizes
the source-git hygiene blocker before recommending reinstall, which prevents a
dirty user figure edit from being copied into the installed Claude plugin cache
as if it were reviewed plugin state.

No plugin code change is needed in this slice. The next valid install refresh
can happen only after the user-owned dirty figure source is committed, stashed,
or moved aside intentionally.
