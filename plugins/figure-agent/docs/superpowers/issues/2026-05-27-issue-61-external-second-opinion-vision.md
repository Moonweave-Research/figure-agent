# Issue 61 - External Second-Opinion Vision Evidence

Status: completed on main in commit `e37dc11`

Depends on: Issue 58 single next-action UX and Issue 59 SVG polish promotion
dogfood

## Problem

Host-vision critique is stronger after high-zoom crops, crop-read
accountability, clash candidates, and aesthetic packs, but a single vision
model can still miss small aesthetic or geometry defects. External second
opinions can help, but direct provider automation introduces cost, quota,
privacy, and reproducibility problems.

The missing plugin layer is not an API client. It is a first-class evidence
import contract for independent visual reviews.

## Goal

Define and test an optional external-vision evidence import path that lets a
human or outer agent attach a second-opinion review without letting that review
mutate source, accepted/golden state, export state, or release gates by itself.

## Order

Run after next-action UX and SVG route dogfood. External reviews should clarify
edge cases, not compensate for unclear local state.

## Scope

In scope:

- Design an optional evidence file such as
  `examples/<name>/external_vision_review.yaml`.
- Require provenance fields:
  - reviewer/model/tool name;
  - reviewed artifact hash;
  - reviewed crop ids or image paths;
  - timestamp;
  - findings;
  - confidence;
  - conflicts with host critique if any.
- Include the evidence in critique freshness only when the fixture opts in.
- Surface conflicts as human review, not automatic truth.
- Add lint/schema tests for malformed or stale evidence.

Out of scope:

- Calling Gemini, Claude, OpenAI, or any other provider from the plugin.
- Storing API keys.
- Making external review a required gate for all fixtures.
- Automatically applying external suggestions.
- Treating external review as higher authority than local contracts.

## Acceptance

- The external evidence contract is optional and controlled.
- Stale external evidence cannot silently pass as current.
- Conflicting external vs host critique findings surface as human review.
- Provider-specific details remain outside the plugin core.
- No network dependency is introduced into tests or normal commands.

## Implementation Notes

Implemented as an opt-in local evidence import path:

- `scripts/external_vision_review.py` parses and validates
  `examples/<name>/external_vision_review.yaml`.
- `spec.yaml.external_vision_review: true` is the only opt-in switch.
- `quality_manifest.py` includes the review file in critique input hashing only
  when opted in.
- `critique_brief.py` emits an `External Second-Opinion Vision Review` section
  only for valid opted-in reviews.
- `critique_lint.py` blocks malformed, stale, or missing-artifact external
  review evidence.
- `fig_loop.py` and `fig_loop_assessments.py` surface fresh conflicts as
  `human_gate_required` and stale/missing/invalid evidence as action-required
  state without demoting an existing human gate.
- `fig_loop_records.py` includes `external_vision_review_summary` in JSON
  stdout summaries.

Verification performed during implementation:

- `uv run pytest -q tests/test_external_vision_review.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py tests/test_fig_loop.py`
  -> 257 passed.
- `uv run ruff check ...` on touched Python files -> all checks passed.
- `uv run pytest -q` -> 1328 passed, 3 skipped, 1 xfailed.
- `uv run ruff check .` -> all checks passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> validation passed.
- `claude plugin validate .` -> validation passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> validation
  passed.

Review notes:

- No provider API, network call, or provider-specific client was introduced.
- No global external-review requirement was added; legacy fixtures remain
  unaffected unless they opt in.
- Stale, missing, malformed, or spec-invalid external evidence is surfaced as
  non-pass state.
- Fresh conflicts route to existing human-gate semantics.
- Stale external evidence does not demote an existing human gate.
- Source, export, accepted, golden, and generated artifacts are outside this
  slice.

## Review Questions

1. Does this improve blind-spot coverage without making the plugin provider
   dependent?
2. Can stale or mismatched external evidence affect a current figure?
3. Are conflicts routed to human judgment instead of automatic override?
4. Does the format remain useful for Gemini, Claude, or manual reviewer notes?
