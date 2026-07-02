# Wave C Dogfood Target Selection

Date: 2026-06-30

Scope: choose the next dogfood figures after the human-decision record and
digest plumbing landed. This is a selection and record-hardening step only; it
does not edit figure sources, accepted state, final artifacts, exports, or
tracked golden baselines.

## Selected fixtures

| Fixture | Role | Decision record | Why this one |
| --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | Protected release/golden policy anchor | `defer_for_dogfood` | Review mode still exposes the protected tracked-golden boundary. It is the right fixture for proving the agent can recommend a narrow decision packet before any irreversible release/golden mutation. |
| `fig3_trapping_concept` | Real manuscript accept-current candidate | `accept_current_generated_export` | Current evidence classifies it as review-complete and release-digest accept-current. It tests whether the agent can propose acceptance with evidence instead of asking the human to inspect from scratch. |
| `smoke_panel_spacing_demo` | Demo bounded-polish lane | `request_bounded_tikz_polish` | It exercises spacing/style rules without putting manuscript figures or protected release state at risk. |

## Excluded fixture

- `fig5_actuation_mechanism` remains excluded from this wave because the current
  source is dirty/stale relative to the release digest. That dirty source is
  user-owned and was not touched.

## Evidence commands

Release digest:

```bash
cd plugins/figure-agent
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode release --goal wave-c-target-selection \
  --human-decision-digest \
  fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo \
  --json
```

Review queue:

```bash
cd plugins/figure-agent
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode review --goal wave-c-target-selection \
  fig1_overview_v2_pair_001_vault fig3_trapping_concept smoke_panel_spacing_demo \
  --json
```

Observed selection facts:

- Release digest grouped all three selected fixtures under
  `accept_current_candidates`.
- Review queue grouped `fig3_trapping_concept` and
  `smoke_panel_spacing_demo` as complete rows with style-direction packets.
- Review queue grouped `fig1_overview_v2_pair_001_vault` as a protected
  redesign/benchmark decision candidate because its review-mode packet is the
  tracked-golden boundary packet.

## Next implementation wave

1. Build a comparison packet for `fig1_overview_v2_pair_001_vault` before any
   future `--force-golden` or release-state mutation.
2. Build an accept-current packet for `fig3_trapping_concept` that states the
   agent recommendation, evidence, risk, and exact follow-up action.
3. Build a bounded spacing/style packet for `smoke_panel_spacing_demo` and keep
   it separate from manuscript release acceptance.

