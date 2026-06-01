# Issue 98 - v1.17 Command Contract Sync

Status: implemented

Type: operator UX, command contract hardening, schema adoption

Depends on:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

Issue 97 implemented schema `figure-agent.critique.v1.17` and rubric
`figure-agent.critique-rubric.v1.17` for grounded critique paths, but the
operator-facing command docs still contain v1.14-centered wording. The command
docs are not passive documentation: host LLM sessions read them as instructions
for `/fig_critique`, `/fig_loop`, and `/fig_drive`.

If command docs lag the generated brief, a host critique can follow an older
mental model even though `critique_brief.py`, `quality_manifest.py`,
`critique_schema_validator.py`, and `critique_lint.py` already expect newer
contract fields.

## Goal

Make the operator-facing slash-command contract match the v1.17 critique
contract so grounded critiques consistently account for:

- `aesthetic_antipattern_audit`;
- `weakest_panel_coherence`;
- `reference_learning_accountability`;
- `ready_improvement_summary.marginal_return_summary` in driver guidance.

## Scope

Implement:

- update `/fig_critique` command guidance to describe v1.17 grounded critiques;
- update `/fig_loop` and `/fig_drive` wording where they still describe
  v1.14-only route detail;
- add regression tests that fail when command docs omit the v1.17 fields or
  describe v1.17-capable paths as v1.14-only;
- keep legacy v1.10/v1.14 wording where it describes actual legacy fallback.

Do not implement:

- a new critique schema;
- host-vision dogfood refresh;
- source/SVG/accepted/golden/export mutation;
- hidden auto-design or auto-patching.

## Acceptance

- [x] `/fig_critique` tells the host LLM that grounded v1.17 critiques must fill
  all three v1.17 fields.
- [x] `/fig_critique` still says to use the exact YAML schema printed by the brief.
- [x] `/fig_loop` and `/fig_drive` do not imply route-detail handling is limited to
  v1.14 when newer schemas inherit that contract.
- [x] Tests cover command-doc contract drift.
- [x] Full tests, lint, diff check, and plugin validation pass.

## Implementation

Added `tests/test_command_contract_docs.py` as a command-doc regression suite
and updated `/fig_critique`, `/fig_loop`, `/fig_drive`, and `SKILL.md` so the
host-facing instructions mention schema `figure-agent.critique.v1.17`,
`aesthetic_antipattern_audit`, `weakest_panel_coherence`, and
`reference_learning_accountability` where grounded critique paths require them.
Legacy v1.10/v1.14 paths remain documented as fallbacks or inherited route
detail contracts.

## Verification

- `uv run pytest -q tests/test_command_contract_docs.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_fig_driver.py tests/test_fig_loop.py`
  - Result: 247 passed.
- `uv run pytest -q`
  - Result: 1564 passed, 3 skipped, 1 xfailed, 6 warnings.
- `uv run ruff check .`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Review Questions

1. Could a host LLM still write an old v1.14 critique for a v1.17 brief because
   the command doc says so?
2. Are legacy fallback rules preserved without weakening new grounded critique
   requirements?
3. Does the driver wording explain optional aesthetic improvement without
   implying hidden edits or release-gate bypass?
