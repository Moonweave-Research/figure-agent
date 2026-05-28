# Issue 63A - Reference Learning Contract

Status: proposed

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

- Valid contracts are parsed and emitted in the critique brief.
- Missing contracts preserve current behavior.
- Malformed contracts fail with controlled errors or visible warnings.
- Unknown roles or empty transfer lists cannot silently pass as authoritative.
- The brief explicitly distinguishes "learn from this" from "copy this".
- Tests cover valid, missing, malformed, unknown-role, and forbidden-transfer
  cases.

## Review Questions

1. Is the contract strict enough to prevent wrong-reference lock-in?
2. Does it avoid requiring every fixture to author a heavy reference taxonomy?
3. Does it keep `briefing.md` and theory guards above visual reference style?
4. Can future metrics consume the same allowed-transfer fields without changing
   their meaning?
