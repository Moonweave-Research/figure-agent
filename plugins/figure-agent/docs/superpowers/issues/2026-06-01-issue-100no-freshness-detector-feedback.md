# Issue 100N/O - Freshness Diagnostics and Detector Feedback

Status: implemented on branch `codex/issue100no-freshness-detector-feedback`

Type: operator UX, freshness explainability, detector feedback

## Problem

The plugin already computes hash-based critique freshness and structured audit
evidence, but the operator-facing summary still hides two practical facts:

1. A stale critique does not say which hash leg changed: input source set,
   rubric/schema, generator code, or legacy missing metadata.
2. Detector quality feedback is scattered across critique prose and milestone
   notes. Operators can see candidate/accounted counts, but not a compact split
   between detector-backed defects, accepted false positives, and defects found
   without detector refs.

This creates long-session friction: the user sees `critique_stale` or a large
candidate count, but still has to inspect raw frontmatter to know whether this
is a real figure change, a plugin-version bump, noisy detector output, or a
detector blind spot.

## Scope

Implement only low-risk read-only diagnostics:

- Add a shared critique freshness diagnostic helper in `quality_manifest.py`.
- Surface the diagnostic through `/fig_status` when `critique.md` exists.
- Add compact detector feedback counts to `audit_evidence_summary.py`.
- Keep all decisions advisory/read-only. Do not change freshness truth,
  critique lint policy, export/accepted/golden state, or any fixture source.

## Non-Goals

- No new schema version bump.
- No hidden critique/adjudication hash repair.
- No detector threshold changes.
- No automatic false-positive suppression edits.
- No release, accepted, golden, export, SVG, or publication mutation.

## Expected Behavior

### Critique Freshness Diagnostics

`quality_manifest.py` should expose a helper that returns:

- whether hash metadata is complete;
- actual and expected `critique_input_hash`;
- actual and expected `rubric_version`;
- actual and expected `generator_version`;
- whether the critique schema matches the expected rubric;
- a stable list of mismatch reason ids:
  - `missing_hash_metadata`
  - `critique_input_hash`
  - `rubric_version`
  - `generator_version`
  - `schema_rubric`

`status.py` should attach this under a read-only key such as
`critique_freshness` whenever `critique.md` exists. `/fig_status` explanation
may remain unchanged, but JSON callers can now show the exact stale cause.

### Detector Feedback

`audit_evidence_summary.py` should attach a read-only `detector_feedback`
object:

- per detector source (`visual_clash`, `text_boundary`, `label_path`,
  `undeclared_geometry`):
  - `candidate_count`
  - `accounted_count`
  - `accepted_false_positive_count`
  - `linked_defect_count`
- global:
  - `unlinked_micro_defect_count` for open/resolved/accepted micro-defects
    with no detector reference;
  - `unlinked_micro_defect_ids`;
  - `summary`, a short stable sentence operators can read.

This does not decide whether a detector is good or bad. It gives future tuning
work a consistent signal.

## Tests

- `tests/test_quality_manifest.py`
  - fresh metadata returns no mismatch reasons.
  - generator mismatch returns `generator_version`.
  - missing metadata returns `missing_hash_metadata`.
  - schema/rubric mismatch returns `schema_rubric`.
- `tests/test_status.py`
  - stale critique status includes `critique_freshness.mismatch_reasons`.
- `tests/test_audit_evidence_summary.py`
  - accepted false-positive detector refs are counted.
  - linked defect detector refs are counted.
  - micro-defects without detector refs are counted as unlinked.

## Implemented

- `quality_manifest.py` exposes `critique_freshness_diagnostics()` with stable
  mismatch ids and actual/expected metadata.
- `status.py` attaches `critique_freshness` whenever a readable `critique.md`
  exists, without changing `compute_critique_state()`.
- `audit_evidence_summary.py` attaches `detector_feedback` counts for detector
  refs, accepted false positives, detector-linked defects, and unlinked
  micro-defects.
- `/fig_status` and `/fig_drive` docs describe the new read-only fields.

## Review Results

1. Freshness correctness: the diagnostic explains the existing freshness
   decision; it does not repair hashes, alter mtime fallback, or create a new
   freshness policy.
2. Detector feedback wording: the implementation reports "unlinked
   micro-defects" rather than overclaiming deterministic false negatives.
3. Scope containment: no source/export/accepted/golden/SVG/publication mutation,
   no detector thresholds, no new schema version.

## Review Checklist

1. Does this explain stale critique state without changing the freshness
   decision?
2. Does detector feedback avoid overclaiming false negatives?
3. Does it preserve legacy critique behavior and existing pass/fail gates?
4. Does `/fig_status` stay read-only?
5. Are tests focused on the new diagnostic fields rather than brittle prose?
