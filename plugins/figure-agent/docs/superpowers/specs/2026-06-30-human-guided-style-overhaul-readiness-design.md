# Human-Guided Style Overhaul Readiness Design

Date: 2026-06-30

Status: planning document before implementation

## Current State

The current dogfood result is not "there is one more local visual defect to
patch." The review queue is mostly closed:

- review mode has `executable_count: 0`;
- review mode has `complete_count: 13`;
- the only review blocker is `fig1_overview_v2_pair_001_vault` at
  `force_golden_required`;
- release mode blocks all fixtures at `accepted_or_final_ready_required`;
- polish mode blocks all fixtures at `mode_forbidden_action`;
- the live queue now emits `decision_packet` for human/release handoffs.

This means the next product problem is not local figure repair. The next product
problem is how the system helps a human decide among:

- accept current solid-manuscript style;
- run one bounded TikZ polish pass;
- prepare an SVG-polish handoff;
- stop patching and explore a full style redesign.

## Product Constraint

`figure-agent` is a quality kernel, not a figure-generation orchestrator.

The plugin should strengthen durable contracts:

- style consistency;
- compile/export reliability;
- visual QA;
- reproducible state;
- explicit human/release decision boundaries.

It must not become:

- an external vision or image-generation API caller;
- a hidden prompt-loop system;
- an automatic PNG-to-SVG/TikZ converter;
- an automatic SVG editor;
- a system that asks the human to inspect raw artifacts without an agent
  recommendation.

## Problem Statement

When a figure has no current defect blockers, the system still does not answer
the most important operator question:

> Is the current style good enough, or should we change the visual language?

The current surfaces can say "complete", "release blocked", or "polish
mode-forbidden", but they do not yet provide a unified style-direction packet
that compares the viable routes and explains why one is recommended.

## Design Goal

Build a read-only, evidence-grounded decision layer for style and release
boundaries before adding more automatic editing.

The user-facing outcome should be:

> The figure has no known defect blocker. Here are the viable next style/release
> directions, the agent's recommendation, the risk of each direction, and the
> exact follow-up command or implementation slice.

## Non-Goals

- Do not edit any figure source in this readiness work.
- Do not declare acceptance automatically.
- Do not force golden automatically.
- Do not start automatic SVG polish.
- Do not use numeric journal scores as release authority.
- Do not ask the human to perform open-ended visual inspection.
- Do not introduce new dependencies.
- Do not mutate generated exports except through existing explicit export
  commands in later implementation slices.

## Priority Stack

### P0. Release / Acceptance Decision Packet

Current release-mode output correctly blocks at
`accepted_or_final_ready_required`, but every fixture receives the same broad
release boundary. The operator still needs a fixture-specific decision packet.

Required behavior:

- For each release-blocked fixture, emit a packet with:
  - current render/critique/export/final-artifact state;
  - recommended decision;
  - choices: accept current generated export, declare final artifact, reject,
    defer for dogfood;
  - risk of each choice;
  - exact follow-up command or no-command manual record path.
- Keep accepted/golden/publication mutation human-only.
- Keep release boundary blocking until an explicit accepted/final-ready state
  exists.

Acceptance criteria:

- Release queue rows include a fixture-specific `decision_packet`.
- The packet distinguishes `force_golden_required` from
  `accepted_or_final_ready_required`.
- Tests cover at least:
  - generated export but no acceptance;
  - tracked golden force-golden boundary;
  - declared polished SVG final artifact missing/stale/fresh.

### P0. Style Overhaul Alternatives Packet

The system needs a separate style-direction packet for defect-free figures.
This is the main missing surface before any redesign work.

Required behavior:

- Emit a read-only `style_direction_packet` when a fixture is review-complete or
  release-blocked only by human acceptance/final-artifact policy.
- Compare these choices:
  - keep current style;
  - bounded TikZ source polish;
  - SVG polish handoff;
  - full style redesign / new visual language.
- Include:
  - agent recommendation;
  - why the current style is or is not enough;
  - what evidence supports the recommendation;
  - which direction would be scope-changing;
  - what the next concrete implementation slice would be.

Acceptance criteria:

- Review-complete fixtures can return a style packet without changing action
  semantics.
- The packet never blocks release by itself.
- The packet uses structured fields, not prose-only critique text.
- Tests prove that a clean fixture can still surface "redesign direction" as an
  option without becoming an executable source patch.

### P1. Polish Mode Blocker Explanation

Polish mode currently reports all fixtures as blocked by `mode_forbidden_action`.
That is safe but not sufficiently diagnostic for deciding what to do next.

Required behavior:

- Decompose polish blockers into concrete reasons:
  - review loop prerequisite not closed;
  - accepted/final-ready release boundary missing;
  - `tikz_vs_svg_polish_trigger` says `continue_tikz`;
  - no positive `ready_for_svg_polish` evidence;
  - SVG polish manifest/delta/semantic-diff missing or stale.
- Surface the reason in queue summaries, command plans, and operator handoffs.
- Point back to review/style-direction packets when SVG polish is not yet the
  right path.

Acceptance criteria:

- Polish queue no longer leaves the operator with only
  `mode_forbidden_action`.
- Existing non-executable safety is preserved.
- Tests cover blocked-by-review, blocked-by-release-boundary, and
  ready-for-svg-polish cases.

### P1. Style Lock Policy Hardening

The current question about "human taste" should be converted into explicit
style contracts where possible.

Required behavior:

- Add or refine policy fields for:
  - typography scale and hierarchy;
  - stroke and arrow weight range;
  - palette and contrast consistency;
  - panel spacing and whitespace;
  - caption/title density;
  - manuscript-scale readability.
- Route measurable violations to lint/checker outputs.
- Route non-measurable art direction to the style-direction packet.

Acceptance criteria:

- At least one new or refined Style Lock rule has tests.
- The rule catches a real class of style drift without requiring host vision.
- Non-measurable style questions remain human-guided, not false-automated.

### P1. Representative Style Benchmark Fixture

Before a full redesign, the repo needs a benchmark fixture or fixture pair that
represents the desired style class.

Required behavior:

- Select one flagship fixture for style benchmarking.
- Record current style strengths and weaknesses.
- Define what a higher-style alternative should improve without changing
  scientific semantics.
- Keep source mutation out of the benchmark selection step.

Acceptance criteria:

- Benchmark document names the fixture, current artifact, target style class,
  forbidden semantic changes, and comparison criteria.
- Future redesign work can be judged against the benchmark instead of against
  vague taste language.

### P2. SVG Polish Gate Refinement

SVG polish should remain a bounded handoff, not the default solution to style
discomfort.

Required behavior:

- Keep `ready_for_svg_polish` as a positive gate.
- Add clearer reasons when SVG polish is not appropriate.
- Avoid letting SVG polish repair scientific, semantic, or label-target issues.

Acceptance criteria:

- SVG polish readiness remains opt-in and evidence-gated.
- Queue/filter output can find true positive SVG-polish candidates.
- Negative cases explain the missing prerequisite.

### P2. Dirty Fixture Hygiene

The only current dirty working-tree file outside this planning work is
`examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`.

Required behavior:

- Treat it as user-owned until explicitly assigned.
- Do not mix it into packet/style/release infrastructure commits.
- If it becomes a target, handle it as a separate slice with status, compile,
  critique, export, and queue evidence.

Acceptance criteria:

- Infrastructure commits do not include fig5 source changes unless explicitly
  requested.

## Implementation Waves

### Wave 1: Release Packet Specificity

Implement fixture-specific release/acceptance decision packets.

Files likely involved:

- `scripts/fig_queue.py`
- `scripts/fig_driver.py`
- `scripts/status.py`
- `tests/test_fig_queue.py`
- `tests/test_fig_driver.py`

Stop condition:

- Release queue still blocks safely, but each blocked row explains the concrete
  decision and options.

### Wave 2: Style Direction Packet

Implement read-only style alternatives for review-complete or release-blocked
fixtures.

Files likely involved:

- new helper under `scripts/`
- `scripts/fig_driver.py`
- `scripts/fig_queue.py`
- tests for clean, polish-needed, and redesign-needed shapes

Stop condition:

- A defect-free fixture can produce a structured comparison of current style,
  TikZ polish, SVG polish, and redesign without mutating source or release
  state.

### Wave 3: Polish Blocker Detail

Improve polish-mode queue/handoff diagnostics.

Files likely involved:

- `scripts/fig_queue.py`
- `scripts/fig_driver_guidance.py`
- `scripts/svg_polish_readiness.py` or existing polish helpers
- tests for polish queue summaries and handoffs

Stop condition:

- `mode_forbidden_action` rows include an actionable blocker reason and a
  recommended upstream packet or mode.

### Wave 4: Style Lock Policy

Convert recurring style discomfort into measurable contracts.

Files likely involved:

- `scripts/lint_tex.py`
- style/preamble files
- critique schema/lint tests if host-vision fields are involved
- representative fixture tests

Stop condition:

- At least one style drift class is caught deterministically before host vision.

### Wave 5: Benchmark And Redesign Readiness

Select benchmark fixture(s) and prepare a redesign decision packet.

Files likely involved:

- docs under `docs/milestones/` or `docs/superpowers/specs/`
- existing fixture evidence
- no source mutation in this wave

Stop condition:

- A future redesign can be evaluated against explicit criteria rather than
  generic "better style" language.

## Recommended Next Step

Start with Wave 1.

Reason:

- It directly addresses the current live release queue state.
- It extends the `decision_packet` work already committed.
- It keeps human authority explicit.
- It reduces operator confusion before broader style redesign decisions.

Wave 2 should follow immediately after Wave 1 because it answers the user's
current strategic question: whether the style itself should be kept, polished,
or replaced.

## Evidence Snapshot

- `AGENTS.md` defines the plugin as a paper-figure quality kernel and lists
  Style Lock, compile/export reliability, visual QA, and reproducibility as its
  responsibilities.
- `docs/quality-kernel-goal.md` says future work should improve Style Lock,
  Macro Library, Compile/Export, Visual QA, Reproducibility, and Authoring
  Context.
- `docs/milestones/2026-06-30-wave12-human-gate-decision-packets.md` records
  the human-gate correction: humans should judge bounded recommendations, not
  inspect from scratch.
- Live review queue: `executable_count=0`, `complete_count=13`,
  `blocked_count=1`, blocker `force_golden_required`.
- Live polish queue: all fixtures blocked at `mode_forbidden_action`.
- Live release queue: all fixtures blocked at `accepted_or_final_ready_required`.

