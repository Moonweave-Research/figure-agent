# Issue 96 - v0.9.1 Loop Improve Release Surface

Status: completed in commit `96329c8`

Type: release metadata, operator documentation, command-surface consistency

Depends on:

- Issue 95 - loop improve orchestrator

## Problem

Issue 95 adds `/fig_improve` as the preferred one-fixture improvement-loop
entry point, but the public release surface still described v0.9.0 and the
older `/fig_run`-first operating model. That creates a real operational hazard:
new sessions may keep routing "improve this figure" requests through the lower
level driver/runner split instead of the loop-centered entry point.

## Goal

Promote `/fig_improve` into the official v0.9 operator surface without widening
automation permissions.

## Scope

Implemented:

- bump release metadata from `0.9.0` to `0.9.1`;
- add a `0.9.1` changelog entry for Issue 95;
- update README current-state and command list;
- update the v0.9 operator playbook with a Loop-Centered Improvement section;
- update the architecture overview Layer 7.5;
- update the plugin closeout status;
- extend release contract tests so stale docs fail.

Not implemented:

- no new execution allowlist;
- no source patch automation;
- no host critique authoring;
- no SVG editing;
- no accepted/golden/publication mutation.

## Verification

Targeted release-contract verification:

```bash
uv run pytest -q tests/test_release_contract.py
```

Full verification remains the standard plugin closeout gate:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Review Notes

1. Version consistency: plugin manifest, pyproject, uv.lock, README, changelog,
   and closeout status must agree on `0.9.1`.
2. Operator UX: `/fig_improve` is now documented as the default for repeated
   one-fixture improvement, while `/fig_run` remains the lower-level bounded
   mechanical executor.
3. Safety: the release notes and playbook explicitly state that `/fig_improve`
   does not cross host/human/patch/SVG/release boundaries.
