# Post-Issue91 Real-Fixture Migration

Status: completed

## Commands

- `uv run python3 scripts/fig_queue.py --mode review --goal "post-Issue91 migration review" --json`
  - Result: exit 0; snapshot saved to `/tmp/figure-agent-issue92/queue-review.json`.
- `uv run python3 scripts/fig_queue.py --mode release --goal "post-Issue91 migration release check" --json`
  - Result: exit 0; snapshot saved to `/tmp/figure-agent-issue92/queue-release.json`.
- `uv run python3 scripts/fig_queue.py --mode polish --goal "post-Issue91 SVG polish readiness check" --json`
  - Result: exit 0; snapshot saved to `/tmp/figure-agent-issue92/queue-polish.json`.
- `uv run python3 - <<'PY' ... status.infer_stage(...) ... PY`
  - Result: exit 0; per-fixture status JSON saved under `/tmp/figure-agent-issue92/`.
- `git status --short examples`
  - Result: no output; protected real fixture files were not mutated.

## Fixture Classification

| Fixture | Review action | Release action | Polish action | Classification | Notes |
| --- | --- | --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `host_critique_required` | `critique_stale`; accepted/tracked golden remains human-gated after critique refresh. |
| `fig1_overview_v2` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `host_critique_required` | `critique_stale`; exports are content-fresh but final review must be refreshed. |
| `golden_trap_depth_picture` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `host_critique_required` | `critique_stale`; tracked golden roll-forward remains a later human/release gate. |
| `n3_trial_01_trap_depth` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `host_critique_required` | Stage 3; critique must precede export. |
| `n3_trial_02_actuation_sequence` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `run_critique / host_llm_critique_required` | `host_critique_required` | `critique_stale`; reference aesthetic metrics warning remains non-mutating. |
| `fig3_trapping_concept` | `run_fig_loop / -` | `release_blocked / accepted_or_final_ready_required` | `run_fig_loop / mode_forbidden_action` | `human_gate_required` | No critique required; status now points to acceptance/final-ready decision, not export rerun. |
| `smoke_trap_demo` | `run_fig_loop / -` | `release_blocked / accepted_or_final_ready_required` | `run_fig_loop / mode_forbidden_action` | `human_gate_required` | No critique required; status now points to acceptance/final-ready decision, not export rerun. |
| `fig5_floating_clip_mechanism` | `run_fig_loop / -` | `release_blocked / accepted_or_final_ready_required` | `run_fig_loop / mode_forbidden_action` | `human_gate_required` | Not accepted; QUALITY_AUDIT/accepted state remains human work. |

## Protected Mutation Check

- `git status --short examples`
  - Result: no output.

No `.tex`, export, accepted/golden, publication, build, or SVG polish artifact
was intentionally changed by this migration pass.

## Findings

- Plugin defects:
  - Found and fixed Issue 93: content-fresh exports could still show
    `stale_export` and misleading `/fig_export` next hints due to mtime-only
    drift.
- Host critique refresh queue:
  - Five reference-grounded fixtures require `/fig_critique` refresh after
    Issue 91 because critique generator/rubric/schema contracts changed.
- Human/release gates:
  - Three non-critique fixtures are blocked by acceptance/final-ready decisions,
    not by deterministic plugin defects.
- Mechanical workflow-agent work:
  - No safe source/export mutation was run in this pass.

## Verification

- `uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_loop.py tests/test_status_next_policy.py`
  - Result: 330 passed.
- `uv run pytest -q`
  - Result: 1530 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Review

- Contract/schema/freshness: PASS. Content-hash `EXPORT_FRESH` now suppresses
  mtime-only `stale_export`, while explicit `EXPORT_STALE`, tracked-golden, and
  final-artifact stale routes remain visible.
- Backward compatibility and scope: PASS. No fixture source, export,
  accepted/golden, publication, build, or SVG polish artifact was changed.
- Operator readiness: PASS. Each production fixture has exactly one
  classification and the non-critique fixtures now route to human
  acceptance/final-ready decisions instead of unnecessary export reruns.

## Verdict

Operator-ready after Issue 93 fix. The next real-work action is host-vision
critique refresh for the five stale critique fixtures. No hidden mutation or
release boundary bypass was observed.
