# Aesthetic Intent Lint Accountability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make host critiques accountable for consuming `aesthetic_intent.yaml`
when it exists.

**Architecture:** Keep Issue 36 as a lint-only hardening slice. Reuse
`scripts/aesthetic_intent.py` for parsing and add a local
`critique_lint.py` check that inspects the four existing critique slots named by
the Issue 35 brief. No schema bump is needed because the output fields already
exist.

**Tech Stack:** Python, PyYAML-backed critique parsing, pytest, ruff.

---

### Task 1: Add Failing Lint Tests

**Files:**
- Modify: `tests/test_critique_lint.py`

- [ ] Add tests that create `aesthetic_intent.yaml`, write a generic critique,
  and assert `critique_lint.lint_critique()` returns
  `aesthetic_intent_accounting`.
- [ ] Add a passing test where the four required slots cite exact anchors such
  as `mature_restraint`, `preset_macro_feel`, `toy_diagram`, and
  `svg_micro_polish`.
- [ ] Add legacy coverage proving fixtures without `aesthetic_intent.yaml` keep
  current behavior.
- [ ] Add malformed-pack coverage proving lint returns a controlled blocker.
- [ ] Run the new tests and confirm they fail for the missing implementation.

### Task 2: Implement Minimal Lint Check

**Files:**
- Modify: `scripts/critique_lint.py`

- [ ] Import `AestheticIntentError` and `load_optional_aesthetic_intent`.
- [ ] Build a deterministic anchor set from the optional pack.
- [ ] Require each of the four slots to mention at least one anchor.
- [ ] Return `aesthetic_intent_accounting` violations instead of raising.
- [ ] Run targeted tests and confirm they pass.

### Task 3: Update Brief Instruction

**Files:**
- Modify: `scripts/critique_brief.py`
- Modify: `tests/test_critique_brief.py`

- [ ] Add brief text saying the four slots must cite exact aesthetic intent
  anchors.
- [ ] Add a focused assertion in the existing aesthetic-intent brief test.
- [ ] Run targeted tests and confirm they pass.

### Task 4: Verify And Review

**Files:**
- Modify: issue doc status after implementation

- [ ] Run `uv run pytest -q tests/test_critique_lint.py tests/test_critique_brief.py tests/test_aesthetic_intent.py`.
- [ ] Run `uv run ruff check scripts/critique_lint.py scripts/critique_brief.py tests/test_critique_lint.py tests/test_critique_brief.py`.
- [ ] Run `git diff --check`.
- [ ] Review for backward compatibility, false-positive risk, and scope creep.
- [ ] If clean, mark Issue 36 implemented and commit.
