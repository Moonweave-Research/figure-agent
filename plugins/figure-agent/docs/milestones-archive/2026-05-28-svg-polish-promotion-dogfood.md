# Issue 59 - SVG Polish Promotion Dogfood

**Status:** evidence closed - polish route withheld behind stale critique gates
**Branch:** `codex/issue59-svg-polish-promotion-dogfood`
**Date:** 2026-05-28

## Goal

Dogfood `/fig_drive --mode polish --dry-run` on real fixtures after the
single-next-action UX landed. The intent is to verify that SVG polish promotion
is conservative, predictable, and subordinate to upstream gates.

This milestone records a negative dogfood result: none of the selected real
fixtures reached `ready_for_svg_polish` because all five were blocked by stale
host-vision critiques. The route did not bypass critique freshness, crop
evidence, export state, human gates, accepted/golden state, or publication
state.

## Selected Fixtures

| Fixture | Why selected |
| --- | --- |
| `fig1_overview_v2_pair_001_vault` | strongest prior SVG-polish candidate, tracked golden, rich audit surface |
| `fig1_overview_v2` | real non-golden overview variant with prior v1.2 critique evidence |
| `golden_trap_depth_picture` | tracked golden fixture with different visual grammar |
| `n3_trial_01_trap_depth` | real trial fixture with human-gated critique history |
| `n3_trial_02_actuation_sequence` | real trial fixture with ready critique history but missing export path |

## Command

From `plugins/figure-agent`:

```bash
uv run python3 scripts/fig_driver.py <fixture> \
  --mode polish \
  --goal "issue59 svg polish promotion dogfood" \
  --dry-run
```

## Evidence

| Fixture | Render | Critique | Export | Publication gate | Action | Stop boundary | Safe command |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `FRESH` | `STALE` | `TRACKED_GOLDEN` | `PASS` | `run_critique` | `host_llm_critique_required` | `/fig_critique fig1_overview_v2_pair_001_vault` |
| `fig1_overview_v2` | `FRESH` | `STALE` | `MISSING` | `HUMAN_ACCEPTANCE_REQUIRED` | `run_critique` | `host_llm_critique_required` | `/fig_critique fig1_overview_v2` |
| `golden_trap_depth_picture` | `FRESH` | `STALE` | `TRACKED_GOLDEN` | `HUMAN_ACCEPTANCE_REQUIRED` | `run_critique` | `host_llm_critique_required` | `/fig_critique golden_trap_depth_picture` |
| `n3_trial_01_trap_depth` | `FRESH` | `STALE` | `MISSING` | `NOT_APPLICABLE` | `run_critique` | `host_llm_critique_required` | `/fig_critique n3_trial_01_trap_depth` |
| `n3_trial_02_actuation_sequence` | `FRESH` | `STALE` | `MISSING` | `NOT_APPLICABLE` | `run_critique` | `host_llm_critique_required` | `/fig_critique n3_trial_02_actuation_sequence` |

All five emitted `next_action_summary.schema:
figure-agent.next-action-summary.v1`.

Allowed scope was limited to the selected fixture's `critique.md` and
`build/audit_crops/`. Forbidden scope consistently included accepted/golden
state without explicit human approval, unrelated examples, hidden source edits,
and generated artifacts outside the selected command.

## Plan Deviation

The implementation plan anticipated that a clean worktree might first return
`run_compile`. In the actual branch, all selected fixtures already had fresh
render state. Compile was therefore not rerun. Recompiling would have generated
build churn without resolving the real blocker, which is host-vision critique
freshness.

`/fig_loop` was not run because the driver selected `run_critique` for every
fixture. Running loop checkpoints after a stale critique gate would not provide
valid SVG promotion evidence.

No `/fig_critique` output was fabricated. The next action requires host vision.

## Policy Judgment

Useful route behavior:

- `ready_for_svg_polish` was not emitted while critiques were stale.
- `polish` mode remained subordinate to the same single next-action contract as
  authoring/review/release modes.
- The route did not skip from a stale critique to polish recipe authoring.
- Tracked golden and publication gates remained visible but did not mask the
  first blocker.
- The safe command was actionable and narrow for all five fixtures.

What this evidence does not prove:

- It does not prove a positive real-fixture `ready_for_svg_polish` route.
- It does not prove `semantic_backport_required` versus optical-only polish on
  a fresh real fixture.
- It does not exercise SVG recipe authoring or polished-SVG manifest checks.

## Follow-Up

Before SVG polish can become routine, at least one real fixture must complete
the host-vision refresh and adjudication sync path, then rerun:

```bash
uv run python3 scripts/fig_driver.py <fixture> \
  --mode polish \
  --goal "issue59 svg polish promotion dogfood" \
  --dry-run
```

If the refreshed critique still says `continue_tikz`, that is not a driver
defect. It means the source-level aesthetic or semantic work is not done.

If a refreshed critique says `ready_for_svg_polish`, the next slice should
record whether the driver points to the bounded SVG polish recipe path without
opening accepted/golden/export mutation.

## Critical Review

### Contract and Freshness

Clean. All five decisions were rooted in `critique_state: STALE`, and the
driver selected the canonical host-LLM boundary.

### Scope Containment

Clean. No source, export, accepted, golden, publication provenance, or
polished-SVG artifact was edited or staged. No host-vision critique was
invented.

### Integration Readiness

Clean for negative dogfood. The evidence is sufficient to close Issue 59 as a
safe-withholding check. It is not sufficient to promote SVG polish as a routine
real-fixture stage.

## Conclusion

Issue 59 did not find a routing defect. It found that the route is conservative
under stale critique conditions. Positive SVG polish promotion still requires a
fresh host-vision critique on a real fixture.
