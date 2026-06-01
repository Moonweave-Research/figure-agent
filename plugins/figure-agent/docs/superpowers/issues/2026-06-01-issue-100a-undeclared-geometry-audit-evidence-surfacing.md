# Issue 100A - Undeclared Geometry Audit Evidence Surfacing

Status: completed on branch `codex/issue100-evidence-surfacing`

Type: audit evidence parity, operator UX, status/driver consistency

## Problem

Issue 99 added `check_undeclared_geometry.py` and `build/undeclared_geometry.json`.
`critique_lint.py` also accepts and validates
`micro_defects[].undeclared_geometry_ref`.

The remaining gap was evidence parity: `audit_evidence_summary.py` surfaced
visual clash, text boundary, label path, and crop audit accounting, but did not
surface undeclared-geometry accounting. That meant a label-frame/boundary risk
could be linted by `critique_lint.py` while remaining less visible in
`/fig_status`, `/fig_loop`, and `/fig_drive` operator summaries.

## Implemented Behavior

`scripts/audit_evidence_summary.py` now includes an `undeclared_geometry` block:

```yaml
undeclared_geometry:
  present: true | false
  candidate_count: <int>
  accounted_count: <int>
  missing_refs: [<candidate_id>, ...]
  unknown_refs: [<candidate_id>, ...]
```

For schemas listed in `UNDECLARED_GEOMETRY_ACCOUNTING_SCHEMAS`:

- missing `build/undeclared_geometry.json` returns `missing_input`;
- malformed JSON or malformed candidate lists return `missing_input`;
- unaccounted candidates return `needs_action`;
- unknown `micro_defects[].undeclared_geometry_ref` values return
  `needs_action`;
- zero-candidate reports pass with `present: true` and `candidate_count: 0`;
- fully accounted candidates pass.

No new stop boundary was introduced. `/fig_status`, `/fig_loop`, and
`/fig_drive` inherit the existing `audit_evidence` summary path.
`commands/fig_status.md` and `commands/fig_drive.md` now name
undeclared-geometry accounting as part of that shared evidence surface.

## Non-Goals

- Do not add a new detector.
- Do not change `check_undeclared_geometry.py` candidate generation.
- Do not mutate source, critique, adjudication, export, golden, accepted, SVG,
  or publication state.
- Do not change host-vision critique schema.
- Do not make undeclared geometry a separate state machine.

## Tests

Added coverage in `tests/test_audit_evidence_summary.py` for:

- missing undeclared-geometry report;
- malformed undeclared-geometry report;
- unaccounted undeclared-geometry candidate;
- unknown undeclared-geometry reference;
- fully accounted candidate;
- zero-candidate report.
- v1.4-v1.6 undeclared-only critiques surface undeclared-geometry blockers even
  though they predate visual-clash accounting.

Existing audit evidence tests were updated so fixture helpers generate the
current compile contract's empty `build/undeclared_geometry.json` by default.

## Design Review

### Review 1 - Contract Correctness

The summary mirrors the existing visual/text/label candidate accounting shape
instead of inventing a new schema. This keeps operator consumers stable.
`figure-agent.audit-evidence-summary.v1` remains unchanged because the new field
is additive and existing consumers already treat `audit_evidence` as a read-only
object with compact blockers rather than a closed JSON schema.

### Review 2 - Backward Compatibility

Legacy critiques still return `legacy` before current accounting is applied.
For current schemas, missing undeclared-geometry input is surfaced as a compile
input gap, matching the fact that `/fig_compile` owns the report.

### Review 3 - Scope Containment

The change only touches evidence summarization and tests. It does not alter
detector thresholds, critique generation, release gating, or source artifacts.
Command docs were updated only to describe the existing shared evidence path.

## Follow-Up

Issue 100B/100C should use this summary block when building a clearer guided
entrypoint and final-readiness preset.

## Verification

- `uv run pytest -q tests/test_audit_evidence_summary.py` -> 22 passed.
- `uv run pytest -q tests/test_audit_evidence_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py` -> 322 passed, 1 skipped.
- `uv run pytest -q tests/test_audit_evidence_summary.py tests/test_audit_evidence_dogfood.py tests/test_critique_lint.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py` -> 441 passed, 1 skipped.
- `uv run pytest -q` -> 1594 passed, 3 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> passed.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
