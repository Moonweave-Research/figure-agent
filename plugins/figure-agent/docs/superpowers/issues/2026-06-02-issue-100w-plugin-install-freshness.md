# Issue 100W - Plugin Install Freshness Check

Status: implemented on branch `codex/issue100w-plugin-install-freshness`

Type: operator UX, plugin cache freshness, read-only diagnostics

## Problem

The plugin has many fast-moving command and script contracts. Users repeatedly
need to know whether the Claude-installed plugin cache is actually the latest
development tree. Before this issue, the README documented package bloat audit
after `claude plugin update`, but there was no single read-only command that
answered "is the installed plugin stale?"

## Goal

Add a deterministic source-vs-installed comparison tool that:

- compares the current development plugin root with the latest local Claude
  plugin cache version;
- ignores generated package junk such as `.venv`, `.scratch`, real
  `examples/` work product, build/export artifacts, and cache directories;
- reports changed, missing, and extra payload files;
- emits stable JSON for agents and humans;
- never mutates source, cache, fixtures, accepted/golden/export state, or
  plugin package contents.

## Public Contract

Run from `plugins/figure-agent`:

```bash
python3 scripts/plugin_install_freshness.py
```

Output schema:

```yaml
schema: figure-agent.plugin-install-freshness.v1
state: fresh | stale | missing | invalid
source_root: <path>
installed_root: <path or null>
source_fingerprint: sha256:<hash>
installed_fingerprint: sha256:<hash or null>
changed_files: [<plugin-relative path>]
missing_files: [<plugin-relative path>]
extra_files: [<plugin-relative path>]
next_action: <human-readable command or explanation>
```

Exit code is `0` only for `fresh`; stale/missing/invalid installs exit `1`.

## Non-Goals

- No automatic `claude plugin update`.
- No automatic cache cleanup.
- No plugin cache deletion.
- No release version bump.
- No runtime command behavior change.

## Acceptance Criteria

- [x] Matching source/install payloads report `fresh`.
- [x] Changed, missing, and extra files report `stale` with stable lists.
- [x] Generated cache junk is ignored.
- [x] Cache parents choose the highest version directory that contains a plugin
      manifest.
- [x] README documents both freshness check and package audit.
- [x] Tests cover the comparison contract.
