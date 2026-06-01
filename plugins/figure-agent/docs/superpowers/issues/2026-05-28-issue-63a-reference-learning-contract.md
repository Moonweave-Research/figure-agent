# Issue 63A - Reference Learning Contract

Status: completed; merged to main

Depends on: Issue 63 reference-learning roadmap

## Problem

The plugin already passes figure-level and panel-level reference context into
the critique brief, but the contract does not clearly say which aspects of a
reference are transferable and which are forbidden. This creates two failure
modes:

- the host vision model treats the reference as a literal target and imports
  unrelated structure, hardware, layout, or physics; or
- the host vision model treats the reference as generic inspiration and fails
  to extract concrete editorial lessons.

The next layer must make reference use explicit enough for a host LLM, a human
reviewer, and future numeric metrics to agree on the same boundaries.

## Goal

Add an optional reference-learning contract that classifies each reference by
role and lists allowed and forbidden transfers. The critique brief must include
that contract and explicitly prohibit literal copying when the reference is only
a style or editorial anchor.

## Scope

In scope:

- Extend the existing reference-pack path or add a compatible
  `reference_learning` section.
- Support reference roles such as:
  - `style_anchor`;
  - `typography_reference`;
  - `density_reference`;
  - `composition_reference`;
  - `apparatus_convention`;
  - `journal_tone_reference`.
- Require per-reference or pack-level `allowed_transfer` and
  `forbidden_transfer` lists.
- Emit a critique-brief section that says what the host LLM may learn and what
  it must not copy.
- Treat malformed contracts as controlled validation errors or visible warnings,
  not silent prompt drift.
- Keep missing reference-learning contracts backward compatible.

Out of scope:

- Numeric aesthetic metrics.
- Provider API calls.
- Automatic patching.
- Replacing `briefing.md` as the semantic source of truth.
- Making references mandatory for every fixture.

## Candidate Contract Shape

```yaml
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
        - density_reference
      allowed_transfer:
        - restrained palette
        - compact label hierarchy
        - editorial whitespace rhythm
      forbidden_transfer:
        - copy component topology
        - introduce unbriefed hardware
        - override physics story
        - force panel layout equality
      rationale: "Use as a journal-tone anchor, not a content authority."
```

## Acceptance

- [x] Valid contracts are parsed and emitted in the critique brief.
- [x] Missing contracts preserve current behavior.
- [x] Malformed contracts fail with controlled errors or visible warnings.
- [x] Unknown roles or empty transfer lists cannot silently pass as
  authoritative.
- [x] The brief explicitly distinguishes "learn from this" from "copy this".
- [x] Tests cover valid, missing, malformed, unknown-role, and
  forbidden-transfer cases.

## Implementation Notes

Implemented as an optional `reference_learning` section inside the existing
`critique_reference_pack.yaml`. This keeps freshness behavior inherited from the
existing critique-reference-pack hash path and avoids introducing a second
reference-learning file before metrics exist.

The implemented contract:

- validates `schema: figure-agent.reference-learning.v1`;
- validates non-empty `references`;
- validates controlled roles:
  - `apparatus_convention`;
  - `composition_reference`;
  - `density_reference`;
  - `journal_tone_reference`;
  - `style_anchor`;
  - `typography_reference`;
- requires non-empty `allowed_transfer`, `forbidden_transfer`, and `rationale`
  for every reference-learning item;
- emits a `Reference Learning Contract` section in `/fig_critique` briefs;
- tells the host LLM that references are learning sources, not copy targets;
- preserves missing-contract compatibility.

Verification performed:

- `uv run pytest -q tests/test_critique_reference_pack.py tests/test_critique_brief.py`
  -> 66 passed.
- `uv run pytest -q tests/test_critique_reference_pack.py tests/test_critique_brief.py tests/test_quality_manifest.py`
  -> 86 passed.
- `uv run ruff check scripts/critique_reference_pack.py scripts/critique_brief.py tests/test_critique_reference_pack.py tests/test_critique_brief.py`
  -> all checks passed.

## Review Questions

1. Is the contract strict enough to prevent wrong-reference lock-in?
2. Does it avoid requiring every fixture to author a heavy reference taxonomy?
3. Does it keep `briefing.md` and theory guards above visual reference style?
4. Can future metrics consume the same allowed-transfer fields without changing
   their meaning?
