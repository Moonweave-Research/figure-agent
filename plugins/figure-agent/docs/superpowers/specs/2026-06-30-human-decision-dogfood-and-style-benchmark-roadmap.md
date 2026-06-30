# Human Decision Dogfood and Style Benchmark Roadmap

Date: 2026-06-30

Status: next-major-work planning document

## Executive Decision

The next major work should not be another automatic figure patch loop.

The next major work is to close the human decision loop around the style and
release packets that now exist:

1. turn queue packets into fixture-specific human decision records;
2. separate "accept current style" from "bounded TikZ polish", "SVG polish",
   and "full visual-language redesign";
3. use one benchmark fixture to judge whether a redesign is better rather than
   relying on vague taste language;
4. only then open source edits, SVG polish, or redesign prototypes.

The product problem has shifted from "the agent cannot explain the blocker" to
"the agent needs to make a concrete recommendation, let the human judge it, and
record that judgment as durable project state."

## Current Baseline

Baseline command shape:

```bash
cd plugins/figure-agent
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode review --goal next-big-work-baseline --json
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode release --goal next-big-work-baseline --json
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode polish --goal next-big-work-baseline --json
```

Observed baseline on 2026-06-30:

| Mode | Total | Complete | Executable | Blocked | Dominant blocker |
| --- | ---: | ---: | ---: | ---: | --- |
| review | 14 | 12 | 1 | 1 | one `force_golden_required`, one `render_stale` |
| release | 14 | 0 | 1 | 13 | `accepted_or_final_ready_required` |
| polish | 14 | 0 | 1 | 13 | `mode_forbidden_action` |

Important details:

- `release` has 13 human acceptance/final-artifact boundaries.
- `release` rows now carry `release_decision_packet`.
- review-complete or release-policy-blocked rows carry `style_direction_packet`.
- `polish` rows now split the blocker reason:
  - `continue_tikz_recommended`: 5
  - `ready_for_svg_polish_evidence_missing`: 8
- `fig5_actuation_mechanism` is the one executable/stale fixture in the current
  baseline. It is also the only dirty source file in the worktree, so it must
  remain outside the strategy work unless explicitly assigned.

## Product Diagnosis

The weak point is not one missing template, one missing SVG editor, or one
missing critique pass.

The current weak point is the absence of a durable decision layer that turns
agent recommendations into human-approved project state.

The system can now say:

- the current artifact has no queue-visible review blocker;
- release is blocked only by policy;
- SVG polish is not currently justified for most fixtures;
- a style packet can list viable choices.

But the system still needs to close:

- which fixture is acceptable as-is;
- which fixture deserves one bounded TikZ polish pass;
- which fixture is a true SVG-polish candidate;
- which fixture should become a full redesign benchmark;
- how the human's decision is recorded without mutating release state
  implicitly.

## Operating Principles

### Human gate means guided judgment

A human gate must not mean:

- "inspect everything from scratch";
- "tell the agent what to do with no recommendation";
- "acceptance not declared" with no concrete candidate.

A human gate must mean:

- current state;
- evidence;
- agent recommendation;
- alternatives;
- risks;
- exact follow-up action after the human chooses.

### Quality kernel boundary

`figure-agent` remains a quality kernel. This roadmap should not turn it into:

- a hidden prompt-loop generator;
- an automatic SVG editor;
- an image-generation service;
- an automatic acceptance or golden-baseline mutator;
- a broad visual redesign engine without benchmark constraints.

### Style work is evidence-gated

Full redesign is allowed as a direction, but not as the default response to
style discomfort. It must be benchmarked against fixture-specific semantics,
style-lock constraints, and human-selected art direction.

## Priority Stack

### P0. Decision Record Contract

Create a durable, repo-local contract for human decisions produced from
`release_decision_packet` and `style_direction_packet`.

Required fields:

- fixture id;
- packet schema and packet timestamp or queue run id;
- decision kind:
  - accept current generated export;
  - declare final artifact;
  - reject current artifact;
  - defer for dogfood;
  - request bounded TikZ polish;
  - request SVG polish candidate evidence;
  - request full style redesign;
- agent recommendation;
- human decision;
- human note;
- follow-up command or implementation slice;
- mutation boundary:
  - no source mutation;
  - source mutation allowed;
  - release-state mutation allowed;
  - golden mutation allowed.

Acceptance criteria:

- A decision can be recorded without editing figure source.
- Recording a style decision does not equal release acceptance.
- Recording release acceptance remains explicit and distinguishable from style
  preference.
- Tests or schema validation reject unknown decision kinds.

### P0. Human Decision Digest

Produce a compact digest over current queue packets so the human can judge a
small set of concrete proposals instead of reviewing raw JSON.

Required behavior:

- summarize each release-blocked fixture as one recommendation row;
- include the packet's recommended choice and one-line risk;
- group rows into:
  - accept-current candidates;
  - bounded TikZ polish candidates;
  - redesign benchmark candidates;
  - SVG-polish evidence missing;
  - dirty/stale fixtures excluded from strategy work;
- name the exact next action for each group.

Acceptance criteria:

- The digest is generated from live queue rows, not hand-written prose.
- The digest can be produced without source mutation.
- `fig5_actuation_mechanism` is called out as stale/dirty and excluded unless
  explicitly targeted.
- The digest output is short enough to paste into a human decision turn.

### P1. Dogfood Decision Pass

Run the digest against a small, representative set before trying to close all
fixtures.

Initial target set:

- `fig1_overview_v2_pair_001_vault`: release/golden/policy boundary and style
  benchmark anchor.
- `fig3_trapping_concept` or `fig3_resistance_mechanism`: real manuscript
  figure with bounded TikZ/style-decision history.
- one smoke/demo fixture: validates that demo rows do not distort the main
  manuscript workflow.

Required output for each target:

- packet summary;
- agent recommendation;
- human-facing question;
- selected decision;
- follow-up slice.

Acceptance criteria:

- At least three decisions are recorded.
- At least one decision chooses "keep current style".
- At least one decision chooses either "bounded TikZ polish" or "full redesign
  benchmark".
- No decision silently mutates acceptance, final artifact, source, or golden
  state.

### P1. Style Benchmark Candidate Pack

Use the selected flagship benchmark to compare style directions.

Existing benchmark anchor:

- `fig1_overview_v2_pair_001_vault`

The candidate pack should define:

- current style strengths;
- current style weaknesses;
- forbidden semantic changes;
- target style class;
- measurable checks;
- human-only art-direction questions;
- candidate family slots:
  - current style;
  - restrained TikZ refinement;
  - editorial redesign;
  - SVG polish handoff only if evidence-gated.

Acceptance criteria:

- The pack can reject a prettier candidate that changes semantics.
- The pack can accept "keep current style" when the redesign does not clearly
  improve manuscript value.
- Future redesign work has a comparison target before any source mutation.

### P2. Style Lock Expansion From Dogfood

Only expand style lint rules after the dogfood pass exposes repeated style
failure classes.

Candidate rule families:

- local font-size override bans and hierarchy limits;
- stroke and arrow weight consistency;
- panel whitespace and title/caption density;
- semantic color economy;
- print-scale label readability.

Acceptance criteria:

- Add rules only for failures observed in real fixtures or benchmark packets.
- Every new rule has a fixture-backed or synthetic regression test.
- Non-measurable art direction remains in the decision packet, not in fake
  deterministic scoring.

### P2. SVG Polish Positive Path

Do not promote SVG polish as the next major default path.

Current evidence says SVG polish is mostly not ready:

- 5 rows route to `continue_tikz_recommended`;
- 8 rows lack positive `ready_for_svg_polish` evidence.

Required behavior:

- find or create a true positive SVG-polish candidate only after the decision
  pass asks for it;
- preserve SVG polish as a handoff path, not a general repair engine;
- keep scientific, semantic, and label-target errors in TikZ/source review.

Acceptance criteria:

- At least one true positive candidate has explicit readiness evidence before
  SVG polish automation expands.
- Negative cases explain the missing evidence.

### P3. Dirty Fig5 Hygiene Slice

`fig5_actuation_mechanism` is not part of the strategic decision-loop work
unless explicitly assigned.

If assigned, handle it as a separate slice:

1. inspect the dirty source diff;
2. compile;
3. refresh status;
4. decide whether critique/export needs refresh;
5. rerun queue.

Acceptance criteria:

- Strategic decision-loop commits do not include fig5 source changes.
- Any fig5 mutation has separate compile/status evidence.

## Recommended Implementation Waves

### Wave A: Decision Record Schema and Validator

Goal: make human decisions durable without changing figure source.

Likely files:

- `scripts/fig_queue.py`
- new or existing decision-record helper under `scripts/`
- `tests/test_fig_queue.py`
- possibly a docs/schema example under `docs/`

Stop condition:

- a sample decision record validates;
- invalid decision kinds fail;
- no release/source/golden mutation happens from record validation.

### Wave B: Decision Digest CLI Surface

Goal: turn queue packets into a short human-facing digest.

Likely files:

- `scripts/fig_queue.py`
- CLI wrapper or subcommand surface;
- queue tests covering grouping and stale/dirty exclusions.

Stop condition:

- digest groups the 14 current rows into actionable categories;
- release packet and style packet recommendations are both visible;
- `fig5_actuation_mechanism` is explicitly excluded as stale/dirty.

### Wave C: Three-Fixture Dogfood Pass

Goal: prove the decision loop works on real fixture state.

Likely outputs:

- milestone document recording the dogfood decisions;
- validated decision records;
- no source mutation unless a later human decision explicitly authorizes it.

Stop condition:

- three fixture decisions recorded;
- follow-up slices are ranked;
- release/style/SVG/redesign paths are no longer mixed together.

### Wave D: Benchmark Candidate Pack

Goal: prepare for possible style overhaul without starting uncontrolled redesign.

Likely outputs:

- benchmark candidate-pack document;
- optional structured schema for candidate comparison;
- tests only if the schema becomes executable.

Stop condition:

- current style and redesign alternatives can be compared against explicit
  semantic and style criteria.

### Wave E: Rule Extraction

Goal: convert repeated dogfood findings into Style Lock checks.

Stop condition:

- at least one real repeated style issue becomes a deterministic lint/test;
- no broad style scoring system is introduced.

## Team Split

If run with team mode, split the work as follows:

| Lane | Scope | Do not touch |
| --- | --- | --- |
| worker 1 | decision record schema, examples, validation tests | fixture source |
| worker 2 | digest grouping and CLI/table output | release/golden state |
| worker 3 | benchmark candidate-pack doc and style-rule extraction proposal | fig5 source |

Leader responsibilities:

- keep `fig5_actuation_mechanism.tex` out of shared edits;
- reconcile schemas and naming;
- run queue smoke and targeted tests;
- decide whether later waves are implementation or docs-only.

## Verification Plan

Minimum verification for Wave A/B:

```bash
cd plugins/figure-agent
uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py
uv run pytest -q tests/test_fig_queue.py
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode release --goal decision-dogfood --json
```

Additional checks when CLI output changes:

```bash
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode review --goal decision-dogfood --format table
PYTHONPATH=scripts:scripts/driver:scripts/checks:scripts/quality:scripts/svg_polish \
  uv run python scripts/fig_queue.py --mode polish --goal decision-dogfood --json
```

Completion evidence must state:

- changed files;
- tests run;
- current queue summary;
- whether any fixture source, acceptance state, final artifact, or golden export
  changed.

## Stop / Defer Rules

Stop and ask for a human decision when:

- a step would mutate accepted state;
- a step would mutate golden exports;
- a step would choose full redesign over current style;
- a step would treat SVG polish as the release artifact;
- a step would edit `fig5_actuation_mechanism.tex`.

Continue automatically when:

- generating read-only digests;
- validating schemas;
- adding tests for packet grouping;
- writing docs;
- running queue/status smoke checks.

## Definition of Done

This major work is done when:

- the repo has a durable decision-record contract;
- queue packets can be summarized into a human-facing digest;
- at least three representative decisions have been dogfooded and recorded;
- the benchmark path is ready for a future style-overhaul prototype;
- SVG polish remains evidence-gated;
- dirty fig5 source remains isolated unless explicitly assigned.

