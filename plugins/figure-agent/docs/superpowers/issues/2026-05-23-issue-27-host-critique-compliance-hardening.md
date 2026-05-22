# Issue 27: Host Critique Compliance Hardening

**Date:** 2026-05-23 KST
**Status:** implemented in this branch
**Type:** post-Issue-25 critique-output compliance hardening

## Problem

Issues 23-25 made audit evidence visible and gateable: visual-clash candidates
produce crops, required crop reads are tracked, and `/fig_status`, `/fig_drive`,
and `/fig_loop` surface audit evidence state.

The remaining host-output gap is narrower: v1.10 critiques require structured
`micro_defects[].accept_simplification_reason`, but a host LLM could still write
a non-empty yet vague `accept_simplification_rationale` such as "acceptable
after review." That satisfies shape validation while failing the operator need:
the rationale does not name the visual-clash candidate or explain the concrete
geometry/context that makes the candidate a non-defect.

## Scope

Harden `critique_lint.py` for v1.10 visual-clash-linked
`accept_simplification` items only.

## Required Behavior

- For schema `figure-agent.critique.v1.10`, every visual-clash-linked
  `status: accept_simplification` item must include:
  - a supported `accept_simplification_reason`;
  - a non-empty `accept_simplification_rationale`;
  - a concrete rationale that names the `VC###` candidate and explains why the
    candidate is not a defect using specific geometry/context.
- Legacy v1.9 and older critiques keep their existing heuristic path.
- This does not change the schema version, command output, figure source,
  export, accepted, golden, or publication provenance state.

## Acceptance

- [x] A v1.10 critique with `accept_simplification_rationale: acceptable after
  review` is rejected.
- [x] A v1.10 critique with a concrete candidate-naming rationale still passes.
- [x] Existing v1.9 legacy accept-simplification behavior is preserved.

## Verification

```bash
uv run pytest -q plugins/figure-agent/tests/test_critique_lint.py -k "v1_10_accept_simplification or vague_accept_simplification"
uv run pytest -q plugins/figure-agent/tests/test_critique_lint.py plugins/figure-agent/tests/test_audit_evidence_summary.py
uv run ruff check plugins/figure-agent/scripts/critique_lint.py plugins/figure-agent/tests/test_critique_lint.py
git diff --check
```
