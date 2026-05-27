# Issue 62 - v0.8 Release Hardening

Status: proposed

Depends on: Issues 57-61, or an explicit decision to defer any unfinished item

## Problem

The plugin has accumulated many useful audit and workflow contracts through
v0.7.1. Before cutting the next release, the repo needs a release-hardening pass
that distinguishes production-ready behavior from proposed or experimental
directions.

Without this pass, users and agents can confuse completed audit gates with
future roadmap items, or rely on docs that no longer match the current command
surface.

## Goal

Prepare a v0.8 release candidate that accurately reflects the current plugin:
what is production-ready, what is opt-in, what is semi-automatic, and what is
still proposed.

## Order

Run last. This issue closes the roadmap slice after adoption, UX, SVG route,
pack catalog, and external-evidence decisions are either implemented or
explicitly deferred.

## Scope

In scope:

- Reconcile current-truth docs:
  - README;
  - `skills/figure-agent/SKILL.md`;
  - command docs;
  - plugin development closeout/status docs;
  - issue status lines.
- Verify plugin metadata:
  - `.claude-plugin/plugin.json`;
  - `pyproject.toml`;
  - `uv.lock` if version changes.
- Run full verification:
  - targeted tests for recently touched modules;
  - `uv run pytest -q`;
  - `uv run ruff check .`;
  - `git diff --check`;
  - three `claude plugin validate` commands;
  - full-render CI when release candidate is opened.
- Prepare release notes describing:
  - deterministic gates;
  - host-vision critique boundaries;
  - aesthetic/journal/paper-wide opt-ins;
  - SVG polish limits;
  - remaining experimental features.

Out of scope:

- Adding new audit features.
- Editing figure source.
- Forcing golden or accepted updates.
- Deleting unrelated user branches/worktrees.
- Claiming automatic Nature/Science acceptance.

## Acceptance

- Docs and command behavior agree.
- All release verification commands pass.
- Open proposed issues are explicitly marked as proposed/deferred if not in
  v0.8.
- The release note states that the plugin is a quality/audit kernel, not a
  hidden auto-designer.
- No unrelated figure source or generated artifact is staged.

## Review Questions

1. Can a new user tell which commands to run in order?
2. Can an agent tell which step is automatic, semi-automatic, or manual?
3. Are all opt-in audit layers documented as opt-in?
4. Does the release claim stay below the evidence?
