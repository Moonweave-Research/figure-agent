# Publication Gate UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add typed publication-gate failure records and a conservative `QUALITY_AUDIT.md` scaffold while preserving current accepted-gate behavior.

**Architecture:** Add `scripts/publication_gate.py` as the focused model/scaffold module. Keep `check_golden_artifacts.py` as the accepted-gate orchestrator and convert typed records back to legacy strings so existing callers do not change.

**Tech Stack:** Python, pytest, existing script-style imports, ruff, Claude plugin validation.

---

## Task 1: Structured Publication Compliance Records

**Files:**
- Create: `plugins/figure-agent/scripts/publication_gate.py`
- Create: `plugins/figure-agent/tests/test_publication_gate.py`

- [ ] Write tests for missing audit, missing section, missing submission-safe,
  and missing disclosure-needed classification.
- [ ] Implement `PublicationGateFailure` and
  `publication_compliance_failure_records()`.
- [ ] Verify targeted tests pass.

## Task 2: Conservative QUALITY_AUDIT Scaffold

**Files:**
- Modify: `plugins/figure-agent/scripts/publication_gate.py`
- Modify: `plugins/figure-agent/tests/test_publication_gate.py`

- [ ] Write tests for required scaffold fields and conservative defaults.
- [ ] Write tests that existing files are not overwritten unless forced.
- [ ] Implement `publication_audit_scaffold_text()` and
  `write_publication_audit_scaffold()`.
- [ ] Verify targeted tests pass.

## Task 3: Wire Accepted Gate Without Changing Behavior

**Files:**
- Modify: `plugins/figure-agent/scripts/check_golden_artifacts.py`
- Modify: `plugins/figure-agent/tests/test_golden_artifact_checks.py`

- [ ] Add a regression test proving `publication_compliance_failures()` still
  returns existing strings.
- [ ] Import and delegate to `publication_compliance_failure_records()`.
- [ ] Keep `check_example()` return type as `list[str]`.
- [ ] Verify golden artifact tests pass.

## Task 4: Docs and Verification

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-20-issue-14-publication-gate-ux.md`

- [ ] Mark acceptance criteria complete after verification.
- [ ] Run targeted tests, full tests, ruff, diff check, and plugin validation.
- [ ] Commit the slice.
