# Top-Tier Audit v1.3 Dogfood Evidence

**Status:** 3-run initial dogfood complete
**Scope:** Validate that `figure-agent.critique.v1.3` / `top_tier_audit` produces useful high-impact journal audit signal without changing source, export, golden, or accepted state.

## Purpose

Issue 9's numeric and journal-grade assessment contract caught broad quality levels, but the host critique could still miss top-tier figure concerns: first-glance message, high-impact journal fit, novelty support, caption coupling, visual economy, cross-panel semantic grammar, reader misinterpretation risk, reduction/print readability, accessibility, and aesthetic coherence.

Rubric v1.3 adds `top_tier_audit` so each `/fig_critique` run must enumerate those ten slots before assigning `journal_grade_assessment`.

## Preconditions

- `critique_brief.py` emits `schema: figure-agent.critique.v1.3`.
- `rubric_version` is `figure-agent.critique-rubric.v1.3`.
- `critique_adjudication.py scaffold` rejects malformed/missing `top_tier_audit`.
- Existing v1.2 critiques are expected to become stale after the rubric bump.

## Runs

| Run | Fixture | Start driver action | v1.3 critique result | Useful v1.3 signal | Final driver action |
| --- | --- | --- | --- | --- | --- |
| 1 | `golden_trap_depth_picture` | `run_critique` | `verdict: ready`, no findings, `top_tier_audit` has pass/weak slots | Separated "solid manuscript" from "high-impact hero" using target-journal fit, visual economy, reduction readability, and aesthetic coherence without inventing a release blocker | `release_blocked`, `force_golden_required` |
| 2 | `fig1_overview_v2` | `run_critique` | `verdict: revise`, findings F001/F002/F003 preserved | Surfaced top-tier failure modes beyond numeric score: color grammar contradiction, reader misinterpretation risk, caption-dependence, visual economy, accessibility/color robustness | `human_gate_stop`, `human_gate_required` |
| 3 | `n3_trial_02_actuation_sequence` | `run_critique` | `verdict: ready`, no findings, `top_tier_audit` has pass/weak slots | Confirmed ready functional sequence still has non-blocking top-tier polish ceilings: utilitarian three-card layout, missing phase index/time axis, plain charge glyphs | `run_fig_loop`, no stop boundary |

## Run 1: `golden_trap_depth_picture`

Sequence:

1. `uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`
2. `uv run python3 scripts/critique_brief.py examples/golden_trap_depth_picture`
3. Codex visual audit against `build/golden_trap_depth_picture.png` and `reference/golden_target_001.png`.
4. `uv run python3 scripts/critique_adjudication.py scaffold examples/golden_trap_depth_picture --force`
5. `uv run python3 scripts/fig_loop.py golden_trap_depth_picture --goal "dogfood v1.3 top-tier audit" --json`
6. `uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`

Evidence:

- `critique_input_hash`: `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba`
- `schema`: `figure-agent.critique.v1.3`
- `top_tier_audit`: complete 10/10 slots
- `critique_adjudication.py scaffold`: passed, 0 decisions
- `/fig_loop`: `escalation_level: manual_approval_required`, `final_stop_reason: status_action_required`
- Final `/fig_driver`: `action: release_blocked`, `stop_boundary: force_golden_required`

Reviewer verdict: useful. The v1.3 audit did not fabricate a release blocker, but it articulated why the figure is solid manuscript quality rather than a high-impact hero figure: row-rule grid, utilitarian plot balance, reduction-risk around small subcaptions, and uneven visual richness.

## Run 2: `fig1_overview_v2`

Sequence:

1. `uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`
2. `uv run python3 scripts/critique_brief.py examples/fig1_overview_v2`
3. Codex visual audit against `build/fig1_overview_v2.png` and `reference/codex_gen_overview_v1.png`.
4. `uv run python3 scripts/critique_adjudication.py scaffold examples/fig1_overview_v2 --force`
5. `uv run python3 scripts/fig_loop.py fig1_overview_v2 --goal "dogfood v1.3 top-tier audit" --json`
6. `uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`

Evidence:

- `critique_input_hash`: `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77`
- `schema`: `figure-agent.critique.v1.3`
- `top_tier_audit`: complete 10/10 slots
- `critique_adjudication.py scaffold`: passed, decisions for F001/F002/F003
- `/fig_loop`: `escalation_level: human_review_required`, `final_stop_reason: human_gate_required`
- Final `/fig_driver`: `action: human_gate_stop`, `stop_boundary: human_gate_required`

Reviewer verdict: useful. The v1.3 audit added signal that the v1.2 score block did not force explicitly: `cross_panel_semantic_grammar: fail`, `reader_misinterpretation_risk: fail`, and `accessibility_color_robustness: fail` all point to the same real root cause, F001's shallow/deep color contradiction. This is the kind of top-tier audit slot that prevents polishing a semantically unstable figure.

## Run 3: `n3_trial_02_actuation_sequence`

Sequence:

1. `uv run python3 scripts/fig_driver.py n3_trial_02_actuation_sequence --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`
2. `uv run python3 scripts/critique_brief.py examples/n3_trial_02_actuation_sequence`
3. Codex visual audit against `build/n3_trial_02_actuation_sequence.png` and `reference/codex_gen_v1.png`.
4. `uv run python3 scripts/critique_adjudication.py scaffold examples/n3_trial_02_actuation_sequence --force`
5. `uv run python3 scripts/fig_loop.py n3_trial_02_actuation_sequence --goal "dogfood v1.3 top-tier audit" --json`
6. `uv run python3 scripts/fig_driver.py n3_trial_02_actuation_sequence --mode review --goal "dogfood v1.3 top-tier audit" --dry-run`

Evidence:

- `critique_input_hash`: `sha256:89c9593862f8997911462db8107621623e25f504e55aecd88e68ea9d882fe7ae`
- `schema`: `figure-agent.critique.v1.3`
- `top_tier_audit`: complete 10/10 slots
- `critique_adjudication.py scaffold`: passed, 0 decisions
- `/fig_loop`: `escalation_level: agent_action_required`, `final_stop_reason: status_action_required`
- Final `/fig_driver`: `action: run_fig_loop`, `stop_boundary: null`

Reviewer verdict: useful. The v1.3 audit captured non-blocking but concrete top-tier polish ceilings: functional three-card layout, missing phase index/time axis, and plain `e^-` charge text. It did not override the existing driver path; export remains the next agent action.

## Initial Judgment

The v1.3 audit is useful enough to keep:

- It catches high-impact figure concerns that numeric scores alone do not force.
- It distinguishes blocking semantic grammar failures from non-blocking art-direction polish.
- It preserves non-score gates: `force_golden_required`, `human_gate_required`, and agent action/export paths were not bypassed.
- It makes the "not high-impact candidate" rationale more inspectable.

Known limitations:

- Runs 1 and 3 used non-blocking weak slots without turning them into findings; this is acceptable for current schema but may need a future summary surface in `/fig_loop`.
- The validator enforces shape and high-impact safety, but it cannot judge whether the prose is deep rather than generic. That still requires dogfood review.
- More runs are needed on genuinely bad/ambiguous figures to verify `top_tier_audit.fail` behavior beyond the F001 color-grammar case.

## Recommended Follow-Up

1. Add `/fig_loop` JSON surfacing for a compact `top_tier_audit_summary` so humans can see fail/weak counts without opening `critique.md`.
2. Add dogfood runs for one intentionally weak fixture and one post-polish fixture to test both tails.
3. Consider a future validator rule: if `top_tier_audit.*.blocks_high_impact: true`, require either a linked finding id or `concrete_fix: accept_simplification | human_review | revise_briefing`.
