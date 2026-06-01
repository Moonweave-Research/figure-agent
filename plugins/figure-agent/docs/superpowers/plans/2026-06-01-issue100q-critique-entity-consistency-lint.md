# Issue 100Q Critique Entity Consistency Lint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block hash-fresh critiques that claim a symbolic label-target entity is visible when that entity is absent from active TeX or exists only in comments.

**Architecture:** Add a conservative source-text lint inside `critique_lint.py`. The lint only inspects `audit_enumeration.label_target_matching` entries with `matches: true`, extracts source-like symbolic tokens such as `F_Maxwell`, normalizes common TeX forms such as `F_{\mathrm{Maxwell}}`, strips comments from active TeX, and emits a blocker only for absent/comment-only symbolic entities.

**Tech Stack:** Python stdlib, existing `critique_lint.py`, existing pytest fixture helpers.

---

### Task 1: Regression Tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_critique_lint.py`

- [x] **Step 1: Add a helper override for `label_target_matching`**

Extend `_audit_enumeration_yaml()` and `_write_critique()` so tests can author a specific label-target audit entry without duplicating the entire critique scaffold.

- [x] **Step 2: Write failing comment-only entity test**

Create a fixture with `entity_drift.tex` where `F_{\mathrm{Maxwell}}` appears only after `%`, then write a critique whose `label_target_matching` says `F_Maxwell` has `matches: true`.

Expected before implementation:

```bash
uv run pytest -q tests/test_critique_lint.py::test_lint_critique_rejects_matched_entity_that_is_comment_only
```

The test fails because `lint_critique()` returns no violations.

- [x] **Step 3: Write positive active-TeX test**

Create a fixture where `F_{\mathrm{Maxwell}}` appears in active TeX and confirm the same critique entry passes lint.

### Task 2: Minimal Lint Implementation

**Files:**
- Modify: `plugins/figure-agent/scripts/critique_lint.py`

- [x] **Step 1: Normalize source-like TeX symbols**

Add helpers that normalize common forms:

- `F_Maxwell`
- `F_{Maxwell}`
- `F_{\mathrm{Maxwell}}`

to the same searchable symbolic token.

- [x] **Step 2: Strip active TeX comments**

Split each TeX line on unescaped `%`, keeping pre-comment text as active source and post-comment text as comment-only context.

- [x] **Step 3: Lint matched symbolic label-target entries**

For each `audit_enumeration.label_target_matching[]` item with `matches: true`, extract underscore-style symbolic tokens from `label`. Emit `critique_entity_consistency` blocker if a token is not present in active TeX and is either comment-only or absent.

- [x] **Step 4: Preserve legacy behavior**

Skip fixtures without a matching `<fixture>.tex` and skip prose-only labels without symbolic tokens.

### Task 3: Docs And Verification

**Files:**
- Create: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100q-critique-entity-consistency-lint.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md`

- [x] **Step 1: Document scope and non-goals**

Record that this is source-text consistency lint, not OCR or broad visual object detection.

- [x] **Step 2: Run targeted verification**

```bash
uv run pytest -q tests/test_critique_lint.py
uv run ruff check scripts/critique_lint.py tests/test_critique_lint.py
git diff --check
```

- [x] **Step 3: Run plugin validation**

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
