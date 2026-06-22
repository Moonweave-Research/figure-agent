# Issue 13: Auto Adjudication Policy

**Date:** 2026-05-20 KST
**Status:** implemented and verified
**Spec:** `../specs/2026-05-20-auto-adjudication-policy-design.md`

## Problem

`critique_adjudication.py scaffold` currently maps every unresolved critique
finding to `decision: needs_human`. This is safe, but it makes the loop ask for
human review on routine style/polish findings that the policy could handle
deterministically.

The v1.4 host-critique dogfood exposed the issue clearly: five findings gated
the loop, but only the target-journal art-direction decision was a fundamental
human judgment.

## Goal

Add opt-in deterministic policy support so routine findings can be converted
to `dismiss`, `defer`, or at most one safe `apply`, while science/policy/domain
questions remain `needs_human`.

## Acceptance Criteria

- [x] Default scaffold behavior remains unchanged without `--policy`.
- [x] `--policy conservative-v1` is supported by `scaffold` and `sync`.
- [x] Policy auto-dismisses `MINOR`/`NIT` style-like findings whose observation
  or suggested fix explicitly says `accept_simplification`.
- [x] Policy auto-defers non-gateable thumbnail-only readability/polish
  findings.
- [x] Policy may auto-apply at most one safe `NIT` local style/label/whitespace
  finding with a concrete two-int `tex_lines` range.
- [x] Policy keeps `BLOCKER`, `MAJOR`, `physics`, `structural`,
  target-journal, high-impact, reference-interpretation, accepted/golden/export,
  final-artifact, and semantic-backport questions as `needs_human`.
- [x] Automatic decisions include a rule id in `reason`.
- [x] `apply` decisions include non-empty `patch_target` and `evidence`.
- [x] Policy output validates under the existing
  `figure-agent.critique-adjudication.v1` schema.
- [x] `/fig_loop` behavior remains unchanged and consumes policy-produced
  adjudication normally.

## Dogfood

Recorded in
`../../milestones-archive/2026-05-20-auto-adjudication-policy-dogfood.md`.

## Out of Scope

- Hidden auto-editing.
- Auto-accepting final artifacts.
- Auto-mutating `critique.md`.
- LLM-authored adjudication as the deterministic core path.

## Verification

Minimum commands:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
