# Aesthetic Intent Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional fixture-level aesthetic intent grounding to `/fig_critique`.

**Architecture:** Keep the feature as an input contract. A new parser validates
`aesthetic_intent.yaml`; `critique_brief.py` emits the section; `quality_manifest.py`
adds it to critique freshness. No output schema or gate behavior changes.

**Tech Stack:** Python, PyYAML, pytest, existing `critique_brief.py` and
`quality_manifest.py` patterns.

---

## Task 1: Parser

**Files:**
- Create: `scripts/aesthetic_intent.py`
- Test: `tests/test_aesthetic_intent.py`

- [x] Write tests for valid pack, invalid enum, duplicate ids, and fixture mismatch.
- [x] Run focused parser tests and confirm they fail because the module is missing.
- [x] Implement the parser with controlled `AestheticIntentError`.
- [x] Run focused parser tests and confirm they pass.

## Task 2: Brief Integration

**Files:**
- Modify: `scripts/critique_brief.py`
- Test: `tests/test_critique_brief.py`

- [x] Write tests for section inclusion, section omission, and malformed pack error.
- [x] Run focused tests and confirm they fail for missing integration.
- [x] Load the optional pack in `generate_for()` and emit `## Aesthetic Intent Calibration`.
- [x] Run focused tests and confirm they pass.

## Task 3: Freshness Integration

**Files:**
- Modify: `scripts/quality_manifest.py`
- Test: `tests/test_quality_manifest.py`

- [x] Write a test proving `aesthetic_intent.yaml` participates in critique manifest paths and hash.
- [x] Run the focused test and confirm it fails.
- [x] Add `aesthetic_intent.yaml` to `critique_manifest_paths()` when present.
- [x] Run focused quality manifest tests and confirm they pass.

## Task 4: Review And Verification

**Files:**
- Modify: `docs/superpowers/issues/2026-05-23-issue-35-aesthetic-intent-contract.md`

- [x] Update the issue status after tests pass.
- [x] Run:

```bash
uv run pytest -q tests/test_aesthetic_intent.py tests/test_critique_brief.py tests/test_quality_manifest.py
uv run ruff check scripts/aesthetic_intent.py scripts/critique_brief.py scripts/quality_manifest.py tests/test_aesthetic_intent.py tests/test_critique_brief.py tests/test_quality_manifest.py
git diff --check
```

- [x] Run full verification:

```bash
uv run pytest -q
uv run ruff check .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [x] Review for scope containment: no generated artifacts, no figure source
  edits, no schema mutation, no release/golden behavior changes.
