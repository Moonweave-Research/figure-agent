# Issue 100Y - Same-Version Install Refresh Guidance

Status: implemented

Type: operator UX, plugin cache freshness, read-only diagnostics

## Problem

Issue 100W added `plugin_install_freshness.py`, but live use exposed a
same-version edge case. When source and installed cache both report the same
plugin version, `claude plugin update figure-agent@figure-agent-local` can say
the plugin is already latest and skip recopying the payload. The freshness
checker still correctly reports `stale`, but its old `next_action` could point
to a command that does not repair the stale cache.

This matters during rapid plugin development because docs-only or script-only
changes can occur inside the same semantic plugin version before a release bump.

## Goal

Make `plugin_install_freshness.py` distinguish refresh strategies:

- `none` when installed cache is fresh;
- `update` when stale install has a different source/install version;
- `reinstall_same_version` when stale install has the same version as source;
- `install_missing` when no install exists;
- `reinstall_invalid` when the install path is not a plugin root.

For same-version stale caches, the emitted `next_action` should be:

```bash
claude plugin uninstall figure-agent && claude plugin install figure-agent@figure-agent-local
```

For missing caches, `next_action` should be `claude plugin install
figure-agent@figure-agent-local`. For invalid install roots, `next_action`
should use the uninstall + install form.

## Public Contract

The existing `figure-agent.plugin-install-freshness.v1` JSON remains backward
compatible and gains additive fields:

```yaml
source_version: <string or null>
installed_version: <string or null>
refresh_strategy: none | update | reinstall_same_version | install_missing | reinstall_invalid
```

The command remains read-only. It does not run update, uninstall, install,
package audit, cleanup, or cache mutation itself.

## Non-Goals

- No automatic plugin install or uninstall.
- No version bump.
- No package audit execution.
- No change to Claude plugin manager behavior.
- No command-surface or runtime figure workflow changes.

## Tests

- Same-version stale cache recommends uninstall + install.
- Different-version stale cache keeps recommending update.
- Missing and invalid installs expose controlled refresh strategies.
- Existing fresh/stale/missing/invalid behavior remains stable.

## Verification

- `uv run pytest -q tests/test_plugin_install_freshness.py`
  -> 8 passed.

## Review Results

1. Contract correctness: `state` semantics are unchanged; only explanatory
   version and refresh-strategy fields were added.
2. Scope containment: the checker remains read-only and does not mutate the
   cache or source tree.
3. Operational fit: the recommendation now matches observed Claude plugin
   manager behavior for same-version local installs.
