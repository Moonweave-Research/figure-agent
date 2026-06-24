# Closed-Loop Quality Kernel Workflow Blueprint

Source of truth: `workflow.plan.json`.

## Objective

Implement the figure-agent closed-loop quality kernel hardening spec through a
resumable, evidence-gated workflow. The workflow starts with safe artifacts only,
then proceeds phase-by-phase through tests-first implementation, adversarial
verification, and dogfood metrics.

## Scope

In scope:

- hardening spec:
  `plugins/figure-agent/docs/superpowers/specs/2026-06-22-closed-loop-quality-kernel-hardening-design.md`
- DWM artifacts:
  `.omo/workflows/closed-loop-quality-kernel/`
- later approved phase-owned source/tests under `plugins/figure-agent/scripts/`
  and `plugins/figure-agent/tests/`

Out of scope without explicit approval:

- fixture source mutation;
- candidate acceptance or apply;
- golden, release, publication, or final artifact mutation;
- external/cloud calls or dependency installs;
- destructive git, commits, pushes, PRs.

## Activation

Activated because this is a large multi-surface implementation with a downstream
consumer, resumable handoffs, planned fan-out, adversarial verification, and
human gates.

Patterns:

- Sequential for phase order.
- Pipeline for phase artifacts flowing into later work.
- Parallel Fan-Out / Fan-In for implementation plus independent verification.
- Adversarial Verify for every phase claim.
- Human Gate for source/test edits and all risky actions.
- Resume And Cache for phase reports and input hashes.

## Phases

| Phase | Name | Exit Gate |
|---|---|---|
| 0 | Baseline And Spec Lock | `workflow.plan.json`, `blueprint.md`, `baseline.lock.json`, and `phase-1-tdd-design.md` exist under `.omo/workflows/closed-loop-quality-kernel/` |
| 1 | Eyes Actionability Metrics | actionability metrics implemented; stale/unknown-panel safe defects do not produce operations; verifier passes |
| 2 | Multi-Candidate Generation | first-match closed-loop generation removed; candidate/refusal coverage and stable id tests pass |
| 3 | Benchmark Render And Candidate-Specific Ranking | render uses candidate sandbox; `requested_not_implemented` gone; rank basis is candidate-specific where applicable |
| 4 | Apply, Status, Closeout Hardening | apply states truthful; `applied_unverified` cannot close out; stale accepted/PASS not ready |
| 5 | Memory Outcomes | attributed events feed bounded priors only; unknowns excluded; authority invariant holds |
| 6 | Semantic Reviewer | local hash-bound validator; stale review invalid; no authority override or external calls |
| 7 | Dogfood Release Gate | smoke/dogfood metrics satisfy spec and independent verifier has no blocking refutations |

Barrier rules:

- Phase 0 must finish and receive human approval before plugin source/test edits.
- Phase 3 waits for candidate manifest/coverage contracts from Phase 2.
- Phase 5 and Phase 6 wait for apply/status/readiness semantics from Phase 4.
- Phase 7 waits for all subsystem reports.

## Workers

- `workflow_author`: owns DWM artifacts and schema alignment.
- `phase_coder`: implements one approved phase with tests first.
- `adversarial_verifier`: refutes producer claims against source, tests, and artifacts.
- `safety_gatekeeper`: checks path, symlink, hash, write, human-gate, and external-action boundaries.
- `integration_synthesizer`: fans in phase reports and prepares dogfood synthesis.

## Handoffs

| From | To | Artifact |
|---|---|---|
| Phase 0 | Phase 1 | `baseline.lock.json` |
| Phase 1 | Phase 2 | `phase-1-eyes-actionability-report.json` |
| Phase 2 | Phase 3 | `phase-2-candidate-coverage-report.json` |
| Phase 3 | Phase 4 | `phase-3-render-rank-report.json` |
| Phase 4 | Phase 5 | `phase-4-apply-closeout-state-report.json` |
| Phase 4 | Phase 6 | `phase-4-apply-closeout-state-report.json` plus semantic review input contract |
| Phase 5 | Phase 7 | `phase-5-memory-outcome-report.json` |
| Phase 6 | Phase 7 | `phase-6-semantic-review-report.json` |
| Phase 7 | Close | `dogfood-release-gate-report.md` |

## Verification

Every phase has an independent falsifier. A producer report is not accepted until
an adversarial verifier checks it against real source, tests, and artifacts.

Key falsifiers:

- unknown-panel or stale defects still generate candidates;
- multi-defect fixture emits one first-match candidate;
- `benchmark-run --render` returns `requested_not_implemented` or success with
  zero rendered candidates in a render-enabled context;
- rank improves from missing or mismatched render evidence;
- apply records verification failure without executed verification;
- stale accepted/PASS fixture reports ready;
- memory prior changes authority;
- semantic review grants authority or performs external calls.

## Risk Gates

Safe default is block-and-ask for:

- writing outside workflow artifacts during first slice;
- editing plugin source/tests;
- fixture source mutation;
- candidate acceptance/apply;
- golden/release/publication/final artifact mutation;
- dependency install or external/cloud API use;
- destructive git, commits, pushes, PRs;
- LLM/semantic review as primary repair or authority grant.

## Budget

- First slice: 45 minutes, only `.omo/workflows/closed-loop-quality-kernel/`.
- Implementation workers: max 3 concurrent.
- Read-only verifiers: max 2 concurrent.
- Phase retries: 2 implementation retries, then escalate.
- No commits or pushes without explicit approval.

## Resume

Resume from the latest phase whose input hashes and verifier report still match.
Invalidation rules:

- spec hash change invalidates all phases;
- defect schema change invalidates phases 2-7;
- candidate manifest schema change invalidates phases 3-7;
- render/rank schema change invalidates phases 4-7;
- apply/readiness semantics change invalidates phases 5-7;
- benchmark dependency probe change invalidates dogfood gate evidence.

Never replay stale `.scratch` benchmark output as current gate evidence.

## First Slice

Instruction:

> Capture baseline evidence and draft Phase 1 failing-test design under
> `.omo/workflows/closed-loop-quality-kernel/` only; do not modify plugin source,
> tests, fixture source, acceptance, golden, release, external/cloud state, git
> history, or commits.

Completion check:

```text
python -m json.tool .omo/workflows/closed-loop-quality-kernel/workflow.plan.json
python -m json.tool .omo/workflows/closed-loop-quality-kernel/baseline.lock.json
git status --short
```

Expected status after first slice: only `.omo/workflows/closed-loop-quality-kernel/`
is newly added by this workflow, in addition to pre-existing dirty files recorded
in `baseline.lock.json`.

## Next Execution Gate

Before Phase 1 source/test edits, ask for explicit approval because Phase 1 will
modify plugin tests and then plugin source.
