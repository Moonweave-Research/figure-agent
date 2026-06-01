# Issue 49 - Release Docs Current-Truth Sync

**Status:** completed on main
**Builds on:** v0.7.0 release and Issue 48 SVG polish promotion readiness

## Problem

After v0.7.0 shipped, Issue 48 added `svg_polish_readiness` to `/fig_loop`
and `/fig_drive --mode polish`. The code and tests landed on `main`, but the
release-facing docs still mixed three different truths:

- the plugin manifest still reported `0.7.0`;
- the closeout milestone still described the state after Issue 33 / PR #47;
- Issue 48 still said it was implemented on a feature branch.

That drift makes the next agent session harder to route because the code,
version surfaces, and current-truth docs disagree.

## Goal

Publish a narrow patch-level release/documentation sync so the repository's
active surfaces agree on the same current state:

- plugin manifest, pyproject, lockfile, README, and changelog identify v0.7.1;
- closeout status reflects the post-Issue-48 main truth;
- Issue 48 says it is implemented on main;
- release-contract tests prevent the stale closeout wording from returning.

## Scope

In scope:

- Release metadata synchronization.
- Changelog and README current-state update.
- Closeout milestone update.
- Issue 48 status wording correction.
- A focused release-contract regression test.

Out of scope:

- New runtime behavior.
- SVG polish policy changes.
- Fixture source, export, golden, accepted, or publication provenance changes.
- GitHub release creation.
- Remote tag creation without an explicit release command.

## Acceptance Criteria

- `test_release_contract.py` fails before the docs sync and passes after it.
- `.claude-plugin/plugin.json`, `pyproject.toml`, `uv.lock`, README current
  state, and changelog agree on v0.7.1.
- The closeout milestone says it is the current main truth through v0.7.1 and
  Issue 48.
- The stale "after Issue 33 / PR #47" and "start with Issue 34" current-priority
  wording is gone from the closeout milestone.
- Issue 48 says it is implemented on main.
- Full pytest, ruff, diff check, and Claude plugin validation pass.

## Review Notes

This is intentionally a patch release sync, not a feature branch for new audit
capability. The next product issue should start from a clean current-truth base
instead of carrying stale release metadata forward.
