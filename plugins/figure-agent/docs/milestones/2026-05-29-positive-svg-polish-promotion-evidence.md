# Positive SVG Polish Promotion Evidence

Date: 2026-05-29

Related issue:

- `docs/superpowers/issues/2026-05-29-issue-71d-positive-svg-polish-promotion-evidence.md`

Status: completed - no positive SVG polish promotion found

## Goal

Try to find a real fixture that can safely enter SVG polish mode after the
71A/71B production-readiness pass. If no fixture qualifies, record the no-go
with exact blockers instead of weakening the route.

## Boundaries Observed

- No `.tex`, SVG, export, accepted, golden, or publication state edited.
- No `--force-golden`, accepted flip, source patch, or SVG polish recipe write.
- All evidence came from read-only `/fig_loop` and `/fig_driver --dry-run`
  commands.

## Initial Polish-Mode Sweep

Command shape:

```bash
uv run python3 scripts/fig_driver.py <fixture> \
  --mode polish --goal issue-71d-svg-polish-promotion --dry-run
```

| Fixture | action | stop_boundary | can_start_svg_polish | recommended_path |
| --- | --- | --- | --- | --- |
| `fig1_overview_v2` | `human_gate_stop` | `human_gate_required` | `False` | `continue_tikz` |
| `fig1_overview_v2_pair_001_vault` | `run_fig_loop` | `mode_forbidden_action` | `False` | `continue_tikz` |
| `fig3_trapping_concept` | `run_fig_loop` | `mode_forbidden_action` | `None` | `None` |
| `fig5_floating_clip_mechanism` | `polish_handoff_stop` | `accepted_or_final_ready_required` | `None` | `None` |
| `golden_trap_depth_picture` | `human_gate_stop` | `human_gate_required` | `False` | `continue_tikz` |
| `n3_trial_01_trap_depth` | `run_export` | `None` | `None` | `None` |
| `n3_trial_02_actuation_sequence` | `run_fig_loop` | `mode_forbidden_action` | `False` | `continue_tikz` |
| `smoke_trap_demo` | `run_fig_loop` | `mode_forbidden_action` | `None` | `None` |

No fixture returned `ready_for_svg_polish`.

## Candidate Loop Evidence

Three candidates were re-run through `/fig_loop --json` because they had the
most relevant SVG-polish-adjacent state:

- `fig1_overview_v2_pair_001_vault`: accepted/tracked-golden, cleanest and
  highest-quality candidate.
- `n3_trial_02_actuation_sequence`: fresh critique, no human gate, remaining
  work is polish-shaped.
- `golden_trap_depth_picture`: high-quality golden-style reference fixture with
  a remaining human gate.

Command shape:

```bash
uv run python3 scripts/fig_loop.py <fixture> \
  --goal issue-71d-svg-polish-promotion --json
```

| Fixture | loop_stop | escalation | benchmark | score | editorial_worst | path | readiness | blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `n3_trial_02_actuation_sequence` | `status_action_required` | `agent_action_required` | `solid_manuscript` | `85` | `weak` | `continue_tikz` | `False` | `tikz_vs_svg_polish_trigger` |
| `fig1_overview_v2_pair_001_vault` | `status_action_required` | `manual_approval_required` | `high_impact_candidate` | `88` | `pass` | `continue_tikz` | `False` | `tikz_vs_svg_polish_trigger` |
| `golden_trap_depth_picture` | `human_gate_required` | `human_review_required` | `solid_manuscript` | `None` | `weak` | `continue_tikz` | `False` | `tikz_vs_svg_polish_trigger` |

## Post-Loop Driver Confirmation

After the loop evidence was refreshed, polish-mode driver dry-runs still did
not promote any fixture:

| Fixture | action | stop_boundary | reason |
| --- | --- | --- | --- |
| `n3_trial_02_actuation_sequence` | `run_fig_loop` | `mode_forbidden_action` | latest loop recommends `continue_tikz`; leave polish mode and resolve source-level illustration issues first |
| `fig1_overview_v2_pair_001_vault` | `run_fig_loop` | `mode_forbidden_action` | latest loop recommends `continue_tikz`; first additional blocker is `export_tracked_golden` |
| `golden_trap_depth_picture` | `human_gate_stop` | `human_gate_required` | human review required for C001; first additional blocker is `export_tracked_golden` |

## Judgment

The useful result is a justified no-go:

- `ready_for_svg_polish` did not appear on any real fixture.
- The driver did not mistake a high score (`88`, `high_impact_candidate`) for
  SVG readiness.
- Human gates and tracked-golden gates stayed independent from polish mode.
- SVG polish stayed visual-only; no route treated it as semantic repair.

The smallest blocker is not missing SVG tooling. It is the editorial trigger
contract: even the strongest candidate has
`polish_trigger_verdict: pass` while `polish_recommended_path: continue_tikz`,
so `svg_polish_readiness` blocks on `tikz_vs_svg_polish_trigger`.

This may be correct for a conservative workflow, but it leaves no positive
real-fixture path to rehearse. The follow-up should clarify when a figure has
crossed from "continue TikZ polish" into "bounded SVG optical polish".

Follow-up issue:

- `docs/superpowers/issues/2026-05-29-issue-73-svg-polish-trigger-semantics.md`

## Review Cycles

### Cycle 1 - Evidence-backed route

PASS. The no-go is based on fresh `/fig_loop` checkpoint data and driver
dry-runs, not just visual intuition. The strongest fixture was explicitly
tested and still blocked.

### Cycle 2 - SVG remains visual-only

PASS. No SVG recipe, polish manifest, export, golden, or accepted state was
mutated. The route did not attempt to use SVG polish to fix semantic/human
review findings.

### Cycle 3 - Semantic backport separation

PASS. No fixture was reclassified as `semantic_backport_required`; fixtures
instead stayed in `continue_tikz`, `human_gate_required`, or tracked-golden
release gates. The distinction remains intact.

## Verification

- `uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop.py tests/test_status.py tests/test_svg_polish_manifest.py tests/test_svg_polish_recipe.py` -> 370 passed.
- `uv run pytest -q` -> 1427 passed, 1 skipped, 1 xfailed, 6 warnings.
- `uv run ruff check .` -> All checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> Validation passed.
- `claude plugin validate .` -> Validation passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> Validation passed.

No known Issue 71D blocker remains.
