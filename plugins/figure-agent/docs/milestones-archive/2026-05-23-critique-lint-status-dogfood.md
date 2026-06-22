# Critique Lint Status Dogfood

**Date:** 2026-05-23 KST
**Status:** evidence captured; next UX follow-up identified

## Scope

This dogfood pass checks how the Issue 35-37 aesthetic-intent and critique-lint
status chain behaves on the real fixture
`fig1_overview_v2_pair_001_vault`.

No figure source, critique, adjudication, export, accepted, golden, or generated
build artifact was edited.

## Commands

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
```

Observed:

```text
critique: stale
Next: tracked golden artifact is stale and reference-grounded critique is missing or stale; run /fig_critique fig1_overview_v2_pair_001_vault, then /fig_export fig1_overview_v2_pair_001_vault --force-golden.
States: render=FRESH critique=STALE export=TRACKED_GOLDEN acceptance=NOT_ACCEPTED workflow_ready=false golden_ready=false release_ready=false final_ready=false
Explanation: critique_stale — critique.md is stale against the current critique input hash. next=/fig_critique fig1_overview_v2_pair_001_vault manual=true
Notes: coordinate_hints_missing, critique_stale, stale_export
```

```bash
uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault \
  --mode review \
  --goal "dogfood aesthetic intent and critique lint surfacing" \
  --dry-run
```

Observed compact fields:

```text
action: run_critique
safe_command: /fig_critique fig1_overview_v2_pair_001_vault
stop_boundary: host_llm_critique_required
first_blocker: critique_stale
```

```bash
uv run python3 scripts/critique_brief.py \
  examples/fig1_overview_v2_pair_001_vault \
  | rg -n "Aesthetic Intent Calibration|exact aesthetic intent anchor|critique_input_hash|schema: figure-agent.critique|rubric_version"
```

Observed:

```text
## Aesthetic Intent Calibration
Each of those four critique slots must cite at least one exact aesthetic intent anchor from the target fields or item ids below; generic style prose is invalid.
schema: figure-agent.critique.v1.10
rubric_version: figure-agent.critique-rubric.v1.10
critique_input_hash: sha256:24bf7b615b580ce750985178586f00a9c8aac056f8539a41f0115afbed758481
```

```bash
uv run python3 scripts/critique_lint.py examples/fig1_overview_v2_pair_001_vault
```

Observed:

```text
BLOCKER: aesthetic_intent_accounting: aesthetic intent pack exists; critique slots must cite at least one exact aesthetic-intent anchor from target fields or item ids: top_tier_audit.aesthetic_coherence, editorial_art_direction.visual_identity, editorial_art_direction.aesthetic_risk, editorial_art_direction.tikz_vs_svg_polish_trigger
```

## Judgment

The current workflow stops at the correct first boundary:

1. `/fig_status` and `/fig_driver` route to `/fig_critique` because the existing
   `critique.md` is stale against the current v1.10 critique input hash.
2. The regenerated brief would require exact aesthetic-intent anchor citations.
3. Direct lint confirms the old critique also fails the new
   `aesthetic_intent_accounting` rule, but this is correctly secondary while
   the critique is already stale.

This means Issue 37 is behaving conservatively: status does not run lint as a
replacement for freshness. It surfaces lint blockers only after the critique is
hash-fresh.

## Follow-Up Candidate

The dogfood pass suggests an optional Issue 38:

- expose a compact `critique_lint_summary` in status/driver JSON when a user
  explicitly asks for deep diagnostics, or when critique is fresh and lint is
  blocked;
- do not replace the current first-blocker ordering, because stale critique
  should still route to `/fig_critique` before lint details are treated as
  actionable.

This is a UX improvement, not a correctness blocker.
