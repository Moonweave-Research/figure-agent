# Issue 100CV - JSON/dry-run CLI compatibility aliases

Status: implemented in this slice

Type: operator workflow, CLI compatibility, queue runner UX

## Problem

Several figure-agent commands emit JSON by default, but their CLI surfaces were
not consistent about accepting the common `--json` flag. During the Issue 100
SVG-polish evidence pass, `fig_driver.py --dry-run --json` and
`fig_queue_run.py --dry-run --json` failed at argparse even though both commands
already produce JSON output and the queue runner is plan-only unless `--execute`
is provided.

This is not a state-selection bug, but it is an operator-footgun: users and
agents moving between `/fig_queue`, `/fig_drive`, and `/fig_queue_run` can add a
reasonable explicit output/dry-run flag and get a hard error before reaching the
actual plugin evidence.

## Scope

Implement compatibility aliases only:

- `fig_driver.py --json` is accepted as a no-op because driver output is always
  JSON.
- `fig_queue_run.py --json` is accepted as a no-op because queue-run output is
  always JSON.
- `fig_queue_run.py --dry-run` is accepted as a no-op because plan-only is the
  default; only `--execute` opts into bounded execution.

## Non-goals

- Do not change output schemas.
- Do not make either command execute by default.
- Do not add hidden mutation behavior.
- Do not change queue selection, driver policy, or SVG polish gate semantics.

## Verification

- `uv run pytest -q tests/test_fig_driver.py::test_main_accepts_json_flag_as_output_compatibility_noop tests/test_fig_queue_run.py::test_main_accepts_json_and_dry_run_flags_as_plan_only_noops`
- `uv run python3 scripts/fig_driver.py fig3_trapping_concept --mode polish --goal 'svg polish readiness audit' --dry-run --json`
- `uv run python3 scripts/fig_queue_run.py --mode polish --goal 'svg polish readiness audit' --can-start-svg-polish true --dry-run --json`

## Review Notes

1. **Safety** - The aliases are no-op parser compatibility only. They do not
   alter execution, command planning, or mutation boundaries.
2. **Architecture fit** - The change keeps `/fig_drive` as a dry-run advisory
   JSON producer and `/fig_queue_run` as a plan-only runner unless `--execute`
   is explicitly supplied.
3. **Operator reality** - This closes a real confusion observed while using the
   current post-100CU SVG polish evidence path.
