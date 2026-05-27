# Issue 61 External Vision Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional, local-only external vision review evidence contract that can inform critique/loop decisions without calling providers or mutating figure state.

**Architecture:** Add a focused parser module for `examples/<name>/external_vision_review.yaml`, gated by explicit `spec.yaml.external_vision_review: true`. Include the review file in critique input hashing only when opted in. Surface stale or conflicting external evidence in `/fig_loop` as action/human-review state; do not let it override host critique or release gates.

**Tech Stack:** Python 3.12, PyYAML, pytest, existing quality manifest and fig_loop summary hooks.

---

### Task 1: Parser And Freshness Contract

**Files:**
- Create: `plugins/figure-agent/scripts/external_vision_review.py`
- Create: `plugins/figure-agent/tests/test_external_vision_review.py`

- [x] **Step 1: Write failing parser tests**

Cover:

- valid review loads;
- missing review returns `None` when fixture is not opted in;
- opted-in missing review raises controlled error;
- malformed YAML raises controlled error;
- fixture mismatch raises controlled error;
- invalid confidence/action/severity fails;
- reviewed artifact hash mismatch reports stale.

- [x] **Step 2: Implement parser**

Schema:

```yaml
schema: figure-agent.external-vision-review.v1
fixture: <name>
reviewer: "<human/model/tool name>"
reviewed_at: "<ISO-ish timestamp>"
confidence: low | medium | high
reviewed_artifact:
  path: build/<name>.png
  hash: sha256:<hash>
reviewed_crops:
  - crop_id: <crop id or image id>
    path: build/audit_crops/<crop>.png
    hash: sha256:<hash>
findings:
  - id: EV001
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<what external reviewer saw>"
    evidence_ref: "<crop id, path, or note>"
    suggested_action: patch | human_review | revise_briefing | accept_simplification
conflicts:
  - external_finding_id: EV001
    host_finding_id: C001
    summary: "<conflict requiring human reconciliation>"
```

### Task 2: Critique Hash And Brief Input

**Files:**
- Modify: `plugins/figure-agent/scripts/quality_manifest.py`
- Modify: `plugins/figure-agent/scripts/critique_brief.py`
- Test: `plugins/figure-agent/tests/test_quality_manifest.py`
- Test: `plugins/figure-agent/tests/test_critique_brief.py`

- [x] **Step 1: Write failing tests**

Cover:

- `external_vision_review.yaml` is ignored by critique manifest when spec does
  not opt in;
- it is included when `spec.yaml.external_vision_review: true`;
- changing the review file changes `critique_input_hash`;
- `/fig_critique` brief includes an external second-opinion section when opted
  in;
- malformed opted-in review raises controlled `CritiqueBriefError`.

- [x] **Step 2: Implement manifest and brief wiring**

Do not bump critique schema. This is input evidence and conflict context, not a
required critique output schema change.

### Task 3: Loop Surfacing

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_loop_assessments.py`
- Modify: `plugins/figure-agent/scripts/fig_loop.py`
- Modify: `plugins/figure-agent/scripts/fig_loop_records.py`
- Test: `plugins/figure-agent/tests/test_external_vision_review.py`
- Test: `plugins/figure-agent/tests/test_fig_loop.py`

- [x] **Step 1: Write failing tests**

Cover:

- fresh review with no conflicts summarizes as `passed`;
- stale review summarizes as `stale`;
- review with conflicts summarizes as `needs_human`;
- `/fig_loop --json` includes `external_vision_review_summary`;
- conflicts set `stop_reason: human_gate_required`;
- stale external evidence sets a non-pass state and cannot disappear from the
  JSON summary.

- [x] **Step 2: Implement summary and stop behavior**

Use existing human-gate semantics. Do not add provider-specific fields or
network calls.

### Task 4: Docs And Issue Status

**Files:**
- Create: `plugins/figure-agent/docs/external-vision-review.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-61-external-second-opinion-vision.md`

- [x] **Step 1: Document contract**

Explain opt-in, provenance, freshness, conflict semantics, and out-of-scope
provider automation.

- [x] **Step 2: Update Issue 61 status**

Record files changed, behavior, and verification.

### Task 5: Verification And Review

- [x] **Step 1: Run targeted tests**

```bash
uv run pytest -q tests/test_external_vision_review.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_fig_loop.py
```

- [x] **Step 2: Run full verification**

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [x] **Step 3: Critical review**

Check:

- no provider API or network dependency;
- no global external-review requirement;
- stale review cannot silently pass;
- conflicts route to human review;
- external review does not outrank host critique or release gates;
- no source/export/accepted/golden/generated artifacts are staged.

- [x] **Step 4: Commit**

Commit code, tests, docs, and Issue 61 status only.
