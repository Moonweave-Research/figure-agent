# Issue 100X - Detector Feedback Ledger

Status: implemented

Type: operator UX, detector tuning, read-only diagnostics

## Problem

Issue 100N/O made detector feedback visible for one fixture through
`audit_evidence_summary.py`. That closed the local summary gap, but it still
left a workflow gap: operators had to inspect fixture summaries one at a time
to see whether detector noise or detector blind spots were recurring across a
real queue.

Detector thresholds are empirical. Without a cross-fixture ledger, false
positives, detector-linked defects, and unlinked micro-defects still drift back
into milestone prose instead of becoming a stable review input.

## Goal

Add a read-only command that aggregates existing per-fixture
`detector_feedback` into a deterministic ledger:

- selected fixture names, or all fixture directories with `critique.md`;
- per-fixture `evaluation_state`, blocking items, reason, and feedback;
- detector totals for `visual_clash`, `text_boundary`, `label_path`, and
  `undeclared_geometry`;
- fixture-qualified unlinked micro-defect ids;
- stable JSON for operators and future tuning work.

## Public Contract

Run from `plugins/figure-agent`:

```bash
python3 scripts/detector_feedback_ledger.py [fixture ...]
python3 scripts/detector_feedback_ledger.py --examples-root /path/to/examples [fixture ...]
```

Output schema:

```yaml
schema: figure-agent.detector-feedback-ledger.v1
examples_root: <path>
fixture_count: <int>
totals:
  visual_clash:
    candidate_count: <int>
    accounted_count: <int>
    accepted_false_positive_count: <int>
    linked_defect_count: <int>
  text_boundary: ...
  label_path: ...
  undeclared_geometry: ...
  unlinked_micro_defect_count: <int>
  unlinked_micro_defect_refs: ["<fixture>:<micro_defect_id>"]
fixtures:
  - fixture: <name>
    evaluation_state: <audit evidence state>
    reason: <summary reason>
    blocking_items: [<id>]
    detector_feedback: <existing audit_evidence_summary detector_feedback>
```

Exit code is `0` for a generated ledger. Unknown selected fixture names return
exit code `2` with a controlled error. The command does not mutate source,
critique, adjudication, build/export, accepted/golden, SVG, or publication
state.

## Non-Goals

- No detector threshold changes.
- No false-positive suppression edits.
- No new critique schema version.
- No new release gate.
- No automatic fixture compile, critique, or adjudication sync.

## Tests

- Aggregates detector feedback across selected fixtures in sorted order.
- Default fixture selection skips directories without `critique.md`.
- Unknown selected fixture fails with a controlled error.
- CLI emits reloadable JSON with the declared schema.

## Verification

- `uv run pytest -q tests/test_detector_feedback_ledger.py tests/test_audit_evidence_summary.py tests/test_release_contract.py`
  -> 50 passed.
- `uv run pytest -q` -> 1695 passed, 3 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.

## Review Results

1. Contract/schema correctness: the ledger reuses
   `audit_evidence_summary.py` and adds only an advisory
   `figure-agent.detector-feedback-ledger.v1` output contract.
2. Backward compatibility and scope containment: the command reads existing
   critique/build evidence only; it does not alter thresholds, schema,
   critique/adjudication files, source, exports, accepted/golden, SVG, or
   publication state.
3. Test coverage and failure modes: tests cover selected fixture aggregation,
   default conservative scanning, unknown fixture errors, and CLI JSON output.

## Review Checklist

1. Does the ledger reuse the existing `audit_evidence_summary.py` interface
   instead of duplicating detector parsing logic?
2. Is the output advisory/read-only and separate from release gates?
3. Does it avoid overclaiming unlinked micro-defects as proven detector false
   negatives?
4. Are selected fixtures deterministic and default scanning conservative?
5. Are tests focused on the ledger contract rather than fixture-specific prose?
