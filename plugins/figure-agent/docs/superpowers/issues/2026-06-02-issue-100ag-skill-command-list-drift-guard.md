# Issue 100AG - Skill command list drift guard

Status: implemented

Type: command contract, documentation drift guard, release contract

## Problem

The README core command list included `/fig_e2e_smoke`, but the agent-facing
`skills/figure-agent/SKILL.md` quick command list did not. That made the
deterministic compile/export/status/loop smoke harness discoverable in user docs
but less visible to the actual host agent running the plugin.

## Contract

- The SKILL quick command list must cover every slash command listed in the
  README core command block.
- The guard is intentionally command-name only. Descriptions may differ because
  README and SKILL serve different audiences.
- The guard does not require every command doc to appear in every workflow
  section; it only protects the canonical command inventory.

## Implementation

- Added `/fig_e2e_smoke <name>` to the SKILL quick command list.
- Added a release-contract pytest that parses README core commands and fails if
  any are missing from the SKILL quick command list.

## Verification

- `uv run pytest -q tests/test_release_contract.py -q`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
