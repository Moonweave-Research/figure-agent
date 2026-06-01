# Issue 100S - Final Strict Profile And Warning Budgets

Status: completed

Type: final readiness, warning budget, operator safety

## Problem

Final mode should not be equivalent to raw `FIGURE_AGENT_STRICT=1`. Strict
compile can be too blunt because several deterministic detectors intentionally
produce conservative warning candidates during normal figure iteration.

The plugin already has a concrete budget contract for visual-clash warnings:
`spec.yaml.visual_clash_cap`, defaulting to 0. The remaining gap was that
`/fig_drive --mode final` could report a complete final-readiness profile while
ignoring that budget report.

## Scope

Use the existing `build/visual_clash.json` plus `spec.yaml.visual_clash_cap` as
the first final warning budget. This is a read-only final-mode check.

In scope:

- add a structured `figure-agent.warning-budget.v1` summary helper to
  `check_visual_clash_budget.py`;
- attach `final_readiness_profile.warning_budget` in `/fig_drive --mode final`;
- route final mode back to strict compile when `build/visual_clash.json` is
  missing;
- stop final completion at a human gate when the warning total exceeds the
  declared cap.

Out of scope:

- no new detector thresholds;
- no automatic cap edits;
- no critique/adjudication mutation;
- no accepted/golden/export/SVG/publication mutation;
- no global strict-mode default change.

## Public Behavior

When render is fresh and final mode runs:

- missing `build/visual_clash.json` returns `run_compile` with the strict
  compile command;
- `total <= visual_clash_cap` records `warning_budget.state: pass`;
- `total > visual_clash_cap` returns `human_gate_stop`, because a human or
  operator must either fix warnings or explicitly raise the reviewed fixture
  cap.

The warning budget appears in `final_readiness_profile`:

```yaml
warning_budget:
  state: pass | needs_action | not_applicable
  budget_state: pass | needs_action | missing_input | invalid
  reason: <one-line reason>
  visual_clash:
    present: true | false
    total: <int|null>
    cap: <int|null>
    over_by: <int|null>
    status: within_budget | over_budget | missing_report | invalid_report | invalid_cap | missing_spec | invalid_spec
```

## Review Notes

Review 1 - scope:

- Reused existing `visual_clash_cap`; no new policy file or detector threshold
  was introduced.

Review 2 - operator behavior:

- Missing budget input means "rerun strict compile" rather than "final is
  complete".
- Over-budget means "human gate" rather than hidden cap mutation.

Review 3 - backward compatibility:

- Normal compile and non-final driver modes keep existing behavior.
- `check_visual_clash_budget.py check_fixture()` keeps its previous raising
  CLI contract while sharing the new summary helper.
