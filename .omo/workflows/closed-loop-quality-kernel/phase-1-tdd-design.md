# Phase 1 TDD Design: Eyes Actionability Metrics

This is the first implementation slice design. It is not implementation. It is
the failing-test contract to use after the user approves source/test edits.

## Objective

Make `quality-map` and the defect ledger expose actionability metrics and prevent
stale, unknown-panel, missing-selector, or unsupported safe-looking defects from
leaking into candidate operations.

## Target Files After Approval

Likely tests:

- `plugins/figure-agent/tests/test_quality_defect_ledger.py`
- `plugins/figure-agent/tests/test_candidate_generator.py`

Likely source:

- `plugins/figure-agent/scripts/quality/quality_defect_ledger.py`
- `plugins/figure-agent/scripts/candidates/candidate_generator.py`
- possibly `plugins/figure-agent/scripts/quality/quality_patch_policy.py`

Do not edit these files until the user approves Phase 1 implementation.

## Required Failing Tests

### 1. Metrics Are Emitted

Create a synthetic fixture or fixture-local fake reports with:

- two fresh safe defects with panel, selector hash, source hash, and supported
  family;
- one fresh unsupported safe-looking defect;
- one stale detector defect;
- one unknown-panel defect.

Expected assertions:

```text
metrics.safe_candidate_defect_count == 4
metrics.candidate_supported_defect_count == 2
metrics.unsupported_safe_defect_count == 1
metrics.unknown_panel_defect_count == 1
metrics.stale_detector_evidence_count == 1
metrics.missing_selector_hash_count == 0
```

The exact denominator may change during implementation, but the test must prove
that supported, unsupported, stale, and unknown-panel buckets are distinct.

### 2. Unknown Panel Blocks Actionability

Input: a defect otherwise classified as `safe_candidate` but missing
`target.panel` or carrying `target.panel: unknown`.

Expected assertions:

- ledger records an actionability gap;
- candidate generation emits no operation for that defect;
- if candidate generation reports the defect, it is a refusal with reason
  `unknown_panel` or equivalent;
- no fallback first-coordinate offset is emitted.

### 3. Stale Detector Evidence Blocks Candidate Operations

Input: a defect with stale detector/source/build hash.

Expected assertions:

- ledger exposes `freshness.state: stale`;
- candidate generation refuses or blocks the defect;
- no `replace_text` operation is produced;
- refusal reason cites stale evidence or source hash mismatch.

### 4. Missing Selector Hash Blocks Safe Candidate Status

Input: a detector defect with line range but no source hash or selector text hash.

Expected assertions:

- metric `missing_selector_hash_count` increments;
- patchability is not `safe_candidate`, or candidate generation refuses it;
- no apply-eligible or review-only operation is emitted from that defect.

### 5. Candidate Generator Does Not Blindly Fallback

Input: one unsupported/unknown-panel defect before one supported defect in ledger
order.

Expected assertions:

- generator skips/refuses unsupported unsafe defect with reason;
- generator still reaches the supported defect;
- it does not return the first offsettable line unrelated to the supported defect.

## Adversarial Verification Prompt

After tests are drafted, run an independent verifier with this goal:

```text
Try to refute that the Phase 1 tests prevent stale evidence, unknown panels,
missing selector hashes, and first-match fallback from leaking into candidate
operations. Read quality_defect_ledger.py, candidate_generator.py, and the new
tests. Findings first, with file references. Do not edit files.
```

## Phase 1 Exit Criteria

- Failing tests exist before production edits.
- Tests fail for the current first-match or missing-actionability behavior.
- Implementation makes tests pass without weakening path, symlink, source hash,
  or human gate rules.
- Verifier has no blocking refutations.

## Forbidden In Phase 1

- No candidate rendering changes.
- No apply or acceptance changes.
- No golden/export/release changes.
- No memory or semantic reviewer changes.
- No external/cloud calls.
- No commits without explicit approval.
