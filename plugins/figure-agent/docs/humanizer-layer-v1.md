# Humanizer / Narrative Context Layer v1

Status: implemented first slice for read-only context, critique, candidate review,
ranking guard, and loop checkpoint surfacing.

## Research And Prior Art

The active product direction in `quality-kernel-goal.md` rejects hidden prompt
loops, auto-designers, external image generation, and API-backed vision calls.
The existing system already has partial narrative pieces in briefing files,
authoring contracts, aesthetic intent, paper aesthetic context, critique quality
axes, candidate review packets, and verify-only loop checkpoints.

The gap was not another generator. The gap was a durable compiler for the way a
human reader or illustrator asks whether the figure has a clear story, a visual
hero, a sane panel role order, and safe boundaries for hand edits.

## Product Position And Non-Goals

The machine payload is named `narrative_context`; the user-facing concept may be
called the humanizer or editorial layer.

It is allowed to:

- compile source-anchored reader and panel-story context;
- ask human-perspective critique questions;
- appear in `context-pack`, `/fig_critique`, candidate review packets, and
  verify-only loop evidence;
- remind downstream reviewers that narrative guidance is advisory.

It is not allowed to:

- call models or external APIs;
- rewrite prompts behind the user's back;
- generate or mutate TikZ, SVG, build artifacts, or exports;
- select, accept, apply, or rank candidates by itself;
- certify acceptance, journal fit, or scientific truth.

## Workflow Architecture

The first implemented slice is `scripts/narrative_context.py`:

```text
briefing.md / spec.yaml / design.md / authoring_plan.md / authoring_contract.md / panel_goals.md
  -> narrative_context.build_narrative_context(...)
  -> context-pack JSON
  -> critique brief section
  -> candidate review packet advisory context
  -> fig_loop advisory summary
```

The schema is `figure-agent.narrative-context.v1`. The important contract fields
are:

- `read_only: true`
- `mode: human_perspective_compiler`
- `sources`
- `reader_contract.first_takeaway_source`
- `reader_contract.panel_story_inputs`
- `reader_contract.human_review_questions`
- `stop_boundaries.model_calls: false`
- `stop_boundaries.prompt_loop: false`
- `stop_boundaries.generation_executor: false`
- `stop_boundaries.source_mutation: false`
- `stop_boundaries.rank_scoring: false`
- `stop_boundaries.autonomous_patch_selection: false`

## Execution Model

The layer is recomputed on demand from existing fixture files. It writes no
fixture-local cache in the first slice, so freshness is inherited from the
caller: `context-pack`, critique brief generation, candidate review packet
construction, or `fig_loop` checkpoint creation.

Candidate review packets wrap it as `narrative_review_context` with
`rank_eligible: false` and `blocking_allowed: false`. Candidate rank tests prove
the presence of narrative fields cannot change `rank_score`, `scores`, or score
evidence.

`fig_loop` stores only a compact `narrative_context_summary` so the verify-only
checkpoint can report reader-story availability without changing stop reasons,
patch targets, or human gate state.

## Safety And Verification Gates

Required gates for future slices:

- Any source mutation must stop and ask for approval.
- Any model call or network dependency must stop and ask for approval.
- Any ranking score influence must be rejected unless explicitly promoted by a
  separate design and test plan.
- Any loop decision change must be tested as a behavior change, not hidden inside
  narrative plumbing.
- Narrative fields must remain source-anchored; unsupported scientific claims
  stay in human review.

## Evaluation Fixtures

Current test surfaces:

- `tests/test_authoring_context_pack.py`
- `tests/test_critique_brief.py`
- `tests/test_candidate_review_packet.py`
- `tests/test_candidate_rank.py`
- `tests/test_fig_loop.py`

Useful real fixture for dogfood: `examples/fig1_overview_v2_pair_001_vault`.

## Release Or Implementation Plan

Wave 1 is implemented: context-pack compiler plus tests.

Wave 2 is implemented: critique brief and candidate review packet advisory
surfacing.

Wave 3 is implemented: ranking non-influence guard and fig-loop advisory
summary.

Future waves should be conservative:

1. Add richer source extraction only when two or more real fixtures need it.
2. Add UI/operator summaries only after loop-health evidence shows a repeated
   bottleneck.
3. Keep all candidate scoring changes behind explicit tests proving no hidden
   acceptance authority was introduced.
