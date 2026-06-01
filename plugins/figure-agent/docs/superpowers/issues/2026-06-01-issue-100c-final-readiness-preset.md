# Issue 100C - Final-Readiness Preset

Status: implemented

Type: final review, release readiness, non-mutating command UX

## Problem

Final confidence was spread across compile strict mode, critique freshness,
adjudication, loop checkpoints, export state, publication gates, and
accepted/golden boundaries. A user could know that each piece exists and still
not know the one safe final command to run.

## Decision

Add `/fig_drive --mode final --goal "final readiness" --dry-run` as the single
non-mutating final-readiness preset.

This mode reuses release-mode gates and adds an additive
`final_readiness_profile`. It does not create a separate executor and does not
turn noisy strict warnings into unconditional release blockers.

## Implemented Contract

- `fig_driver.MODES` includes `final`.
- `final_readiness_profile.schema`: `figure-agent.final-readiness.v1`
- The profile includes:
  - `strict_compile`
  - `critique`
  - `loop_checkpoint`
  - `export`
  - `publication_gate`
  - `release_gate`
  - `overall_state`
  - `non_mutating_driver: true`
- The strict compile row always shows:

```bash
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/<name>/<name>.tex
```

- If render is missing or stale, final mode selects that strict compile command
  as the next `safe_command`.
- If render is already fresh, strict compile remains visible as the final manual
  render check while the driver continues to route release/golden/publication
  boundaries as human-only.
- Final mode requires a current verify-only `/fig_loop` checkpoint before it
  can report `complete`, even when `release_ready` is already true.

## Safety Rules

- Final mode is dry-run only because `fig_driver.py` still requires
  `--dry-run`.
- `/fig_run` rejects `mode: final`; final readiness is a driver explanation
  preset, not a new automation lane.
- Final mode does not force golden, set accepted state, edit SVG, mutate source,
  or write publication evidence.
- Aesthetic scores remain advisory; final mode does not make taste alone a
  release gate.
- Known detector false positives still require the normal critique/adjudication
  or warning-budget paths before becoming hard release blockers.

## Tests

Covered in `tests/test_fig_driver.py`:

- stale render routes to strict compile;
- tracked golden routes to release-operator approval, not an executable
  mutation;
- fully release-ready state reports `overall_state: pass`.

## Follow-Up

Issue 100S should define stricter warning-budget semantics before final mode
auto-fails every report-only detector candidate.
