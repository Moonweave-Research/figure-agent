# Issue 15B: Audit Evidence Completeness Linter

**Date:** 2026-05-21 KST
**Status:** proposed
**Parent:** Issue 15
**Spec:** `../specs/2026-05-21-plugin-loop-automation-audit-design.md`

## Problem

The v1.4 critique contract asks the host LLM to use high-zoom crops,
print-scale crops, top-tier slots, and micro-defects. `critique_lint.py`
currently validates schema and finding id safety, but it does not fully enforce
that required evidence surfaces were actually represented in findings or
blocking items.

## What to Build

Extend the critique linter with evidence-completeness checks for fresh v1.4
critiques. This linter should catch incomplete critique authorship, not decide
whether a figure is good.

## Acceptance Criteria

- [ ] v1.4 critiques require `micro_defects` to be a present list.
- [ ] Open `BLOCKER`/`MAJOR` micro-defects must link to a normal finding or
  explicitly use `accept_simplification` only where the schema allows it.
- [ ] Failed or `needs_human` top-tier slots with `blocks_high_impact: true`
  must be represented in `findings` or `quality_axes.*.blocking_items`.
- [ ] `journal_polish: pass` and `publication_readiness: pass` require
  evidence text that names print-scale audit evidence.
- [ ] Errors are deterministic and actionable.
- [ ] Legacy critique schemas remain compatible.

## Verification

```bash
uv run pytest -q tests/test_critique_lint.py tests/test_critique_schema_validator.py tests/test_critique_adjudication.py
uv run pytest -q
uv run ruff check scripts/critique_lint.py tests/test_critique_lint.py
git diff --check
```
