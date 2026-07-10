# 2026-07-03 Forward Execution Plan and Status

**Status:** Historical evidence — non-authoritative.
**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

## Purpose

Move figure-agent beyond the v0.9.3 baseline by making the operational truth
surfaces consistent first, then using the tool to improve manuscript figure
quality without turning it into an autonomous taste judge or hidden source
mutator.

This note is the durable handoff for future agents. The runtime-only plan was
created under `.omx/plans/2026-07-03-figure-agent-forward-execution-plan.md`,
but `.omx/` is intentionally not tracked by git.

## Current Result

P0, P1, and the first P2 candidate-lane/comparison-handoff slices are
complete.

- P0 unified the executable next-action surface for `status`, `drive`, and
  `queue`.
- P1 refreshed operator-facing docs so implemented v0.10 substrate is not
  described as future work.
- P2 created `fig1_overview_v3_pair_001_vault` as a non-golden candidate lane
  with a restrained Panel C readability patch and explicit human boundary.
- P2 also created a v2-versus-v3 visual comparison packet for the host critique
  boundary; this packet is intentionally non-authorizing and does not approve
  accepted-state, export, publication, or golden mutation.
- The fig1 accepted/golden fixture now reports `run_adjudicate` as the
  executable workflow step while preserving the human-only release blockers
  separately.

The important distinction is:

- workflow-agent executable step: `run_adjudicate`
- release blocker: tracked golden export roll-forward / publication provenance
- release actor: `release_operator`

Agents may run the deterministic adjudication step. They must not force golden,
accept, attest, or mutate release state without explicit human approval.

## Verified Evidence

From `plugins/figure-agent`:

```bash
uv run pytest tests/test_fig_driver.py tests/test_fig_queue.py tests/test_release_contract.py
uv run ruff check .
uv run mypy scripts/next_action_summary.py scripts/status_explanation.py
./bin/fig-agent status fig1_overview_v2_pair_001_vault --json
./bin/fig-agent drive fig1_overview_v2_pair_001_vault --mode review --goal final-verification --dry-run --json
./bin/fig-agent queue --mode review --goal final-verification --json
```

Expected smoke result:

- `status.next_action_summary.action == "run_adjudicate"`
- `drive.action == "run_adjudicate"`
- `drive.next_action_summary.action == "run_adjudicate"`
- fig1 queue row `action == "run_adjudicate"`
- fig1 queue row `release_blocking_source == "export_tracked_golden"`
- queue has 13 rows and 0 errors at the current baseline

## Current P2 Evidence

The v3 candidate lane is intentionally not accepted and not golden.

From `plugins/figure-agent`:

```bash
./bin/fig-agent compile fig1_overview_v3_pair_001_vault
./bin/fig-agent status fig1_overview_v3_pair_001_vault --json
./bin/fig-agent drive fig1_overview_v3_pair_001_vault --mode review --goal fig1-v3-candidate --dry-run --json
./bin/fig-agent queue --mode review --goal fig1-v3-candidate --json
uv run pytest tests/test_style_benchmark_pack_loader.py tests/test_style_benchmark_comparison.py tests/test_human_decision_record_examples.py tests/test_fig_queue.py
```

Expected smoke result:

- v3 render is fresh after compile
- v3 next executable action is `run_critique`
- v3 style benchmark pack and comparison are present
- v3 design direction state is ready for human choice
- v3 visual comparison packet exists at
  `docs/decision-packets/2026-07-03-fig1-v3/fig1_overview_v3_pair_001_vault_visual_comparison.json`
- label-path proximity and text-boundary checks report 0 candidates after
  compile
- the next boundary remains `/fig_critique fig1_overview_v3_pair_001_vault`
  with required actor `host_llm`

## Remaining Plan

### P2 - Fig1 Overview v3 Candidate Lane

First slice complete: `examples/fig1_overview_v3_pair_001_vault/` exists as a
non-golden candidate fixture, and the accepted v2 fixture remains the
benchmark/reference.

Allowed directions:

- current-style repair candidate
- restrained TikZ refinement
- editorial redesign within existing science claims
- SVG-polish handoff only as a human-reviewed artifact path, not as retired
  gate plumbing

Required outputs:

- compile success: complete
- status/drive smoke: complete
- style benchmark packet: complete
- design decision packet: complete
- visual comparison packet for host critique: complete
- explicit human choice boundary before acceptance or golden roll-forward:
  complete

Remaining P2 work is host visual critique and, only after that, a human choice.
Do not accept v3, copy v3 over v2, export it as golden, attest it, publish it,
or hand-edit generated artifacts without explicit human approval.

### P3 - Mechanical Queue Execution

After P0, rerun queue and execute only rows where:

- `required_actor == "workflow_agent"`
- the safe command is deterministic
- no source-drawing, human, golden, release, or attestation boundary is crossed

For host-critique rows, prepare evidence only. For human rows, prepare decision
packets only.

### P4 - Spine Evidence Surfacing

The compile path already writes semantic assertion and convention receipt
artifacts. The remaining work is to surface that evidence through status,
drive, queue, and closeout reports so agents do not need to inspect build files
manually.

Do not add broad visual detectors here. Keep the work declaration-driven,
report-only, and tolerance-aware.

### P5 - Package Hygiene

Only after P2-P4 are either complete or explicitly deferred:

- check local commits against `origin/main`
- run release contract tests
- run secret scan before push
- push only plugin/tooling changes, not manuscript source or private figure
  assets

## Boundaries

- Do not mutate accepted/golden state without explicit human approval.
- Do not edit generated exports by hand as a substitute for source-level repair.
- Do not revive retired SVG-polish proof plumbing.
- Do not add a generic detector unless it is declaration-driven, report-only,
  and tolerance-aware.
- Do not create a hidden auto-designer. Taste remains human-owned.
- Keep changes small, reversible, and covered by targeted tests.
