# Issue 28: Adjudication Contract Parity

**Date:** 2026-05-23 KST
**Status:** implemented in this branch
**Type:** post-Issue-27 loop-state hardening

## Problem

Issue 27 hardened `critique_lint.py` so schema v1.10 critiques cannot pass when
a visual-clash-linked `accept_simplification` has only a vague rationale such as
"acceptable after review." That catches bad host output before the user runs
`/fig_adjudicate`.

The remaining gap was direct scaffolding: `critique_adjudication.py scaffold`
validates the schema contract before turning `critique.md` into loop state, but
the concrete visual-clash rationale check lived only in the lint layer. If an
operator skipped lint, a vague simplification could still enter
`critique_adjudication.yaml`.

## Scope

Move the v1.10 visual-clash simplification rationale specificity rule into the
schema validator path used by adjudication scaffolding. Keep the manifest-backed
accounting checks in `critique_lint.py`.

## Required Behavior

- v1.10 `micro_defects[]` entries with `status: accept_simplification` still
  require a supported `accept_simplification_reason`.
- If such an item also has `visual_clash_ref`, its
  `accept_simplification_rationale` must:
  - be concrete enough to be reviewable;
  - name the `VC###` candidate id;
  - explain the non-defect geometry/context.
- `critique_lint.py` and `critique_schema_validator.py` share the same marker
  and minimum-length constants.
- Legacy schemas keep their existing compatibility paths.

## Acceptance

- [x] `build_adjudication_scaffold()` rejects a v1.10 critique whose
  visual-clash simplification rationale is "acceptable after review."
- [x] Existing critique lint behavior remains green.
- [x] Existing schema validator tests remain green.

## Verification

```bash
uv run pytest -q plugins/figure-agent/tests/test_critique_adjudication.py plugins/figure-agent/tests/test_critique_lint.py plugins/figure-agent/tests/test_critique_schema_validator.py
uv run ruff check plugins/figure-agent/scripts/critique_schema_validator.py plugins/figure-agent/scripts/critique_lint.py plugins/figure-agent/scripts/critique_schema_vocab.py plugins/figure-agent/tests/test_critique_adjudication.py
git diff --check
```
