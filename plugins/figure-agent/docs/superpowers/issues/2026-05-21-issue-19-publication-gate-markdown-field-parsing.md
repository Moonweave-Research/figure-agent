# Issue 19: Publication Gate Markdown Field Parsing

**Date:** 2026-05-21 KST
**Status:** implemented
**Type:** provenance gate parser hardening

## Problem

Issue 14 added structured publication-gate records and a conservative
`QUALITY_AUDIT.md` scaffold. The parser accepted plain fields such as
`submission-safe: true`, but rejected common Markdown audit notation where the
field label is bolded:

```markdown
**submission-safe:** true
**disclosure-needed:** no
```

That created a false provenance blocker even though the human-authored audit
declared the required values.

## Scope

- Keep publication-gate behavior conservative.
- Accept plain fields and Markdown-bolded field labels.
- Preserve existing failure records and messages.
- Do not infer `submission-safe: true`.
- Do not change accepted, golden, export, status, or driver behavior.

## Acceptance Criteria

- [x] `publication_compliance_failure_records()` accepts
  `**submission-safe:** true`.
- [x] `publication_compliance_failure_records(..., require_disclosure=True)`
  accepts `**disclosure-needed:** no`.
- [x] Partial truthy values such as `true-ish` and `not-applicable-ish` do not
  satisfy the publication gate.
- [x] Missing/false fields still produce the existing typed human provenance
  failures.
- [x] Targeted publication-gate tests pass.

## Verification

```bash
uv run pytest -q plugins/figure-agent/tests/test_publication_gate.py
```
