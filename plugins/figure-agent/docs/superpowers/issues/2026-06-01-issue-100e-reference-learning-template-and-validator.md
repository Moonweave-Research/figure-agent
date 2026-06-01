# Issue 100E - Reference-Learning Template And Anti-Copy Validator

Status: completed on main in commit `99a440e`

Depends on:

- Issue 63 reference-learning contract and aesthetic metrics
- Issue 100 comprehensive plugin gap inventory

## Problem

`critique_reference_pack.yaml` lets a fixture learn editorial principles from
reference figures without treating those references as copy targets. The
mechanism exists, but pack authoring was still too operator-dependent:

- a pack could say "make it look nicer" without naming concrete transferable
  design axes;
- anti-copy constraints could mention only topology while omitting exact
  geometry, label text, claim payload, or panel semantics;
- new operators had no command-level starter template.

This makes reference use drift toward one of two unsafe extremes: under-learning
generic prose, or over-learning a mismatched reference drawing.

## Goal

Make reference-learning packs easier to author and harder to misuse, without
making references mandatory and without changing release authority.

## Implemented Contract

`scripts/critique_reference_pack.py` now exposes a
`figure-agent.critique-reference-pack.v1.1` starter template:

```bash
uv run python3 scripts/critique_reference_pack.py --template <fixture>
```

The template includes:

- target journal, reference class, and visual ambition;
- comparison reference and calibration questions;
- reference-learning roles;
- allowed transfer axes:
  - palette family;
  - density;
  - typography hierarchy;
  - abstraction level;
  - line language;
  - composition rhythm;
- forbidden transfer guards:
  - component topology;
  - exact geometry or coordinates;
  - label text;
  - claim payload;
  - panel semantics.

The v1.1 validator now checks the reference-learning section at pack level.
Multiple references may divide the learning axes, but the combined pack must
cover every required allowed-transfer axis and every anti-copy guard. Missing
packs remain backward compatible, and legacy v1 packs remain parseable under
the older non-empty-list contract. Malformed packs fail with controlled
`CritiqueReferencePackError` errors and are surfaced by `/fig_critique` as
controlled brief-generation failures.

## Scope Boundaries

In scope:

- template emission;
- stronger validation for opt-in `reference_learning`;
- preserving legacy `figure-agent.critique-reference-pack.v1`;
- keeping existing hash/freshness behavior because `critique_reference_pack.yaml`
  already participates in critique inputs;
- leaving existing real-fixture v1 packs untouched so current critiques are not
  made stale by this authoring-tool slice.

Out of scope:

- web/reference scraping;
- external vision/model calls;
- pixel-copy or SSIM targets;
- hidden source edits;
- release, accepted, golden, or SVG mutation;
- making reference learning mandatory for all fixtures.

## Review Questions

1. Does the pack name concrete transferable editorial lessons rather than generic
   "better style" prose?
2. Does it explicitly block copying topology, exact geometry, label text, claim
   payload, and panel semantics?
3. Can multiple references divide roles without requiring every reference to
   cover every axis?
4. Does validation fail before the host critique can use a misleading pack?
5. Does missing `critique_reference_pack.yaml` preserve current behavior?

## Verification

Final verification:

- `uv run pytest -q tests/test_critique_reference_pack.py tests/test_critique_brief.py tests/test_reference_aesthetic_metrics.py tests/test_real_fixture_audit_adoption.py`
  - `98 passed`
- `uv run pytest -q`
  - `1610 passed, 3 skipped, 1 xfailed, 6 warnings`
- `uv run ruff check .`
  - `All checks passed`
- `git diff --check`
  - clean
- `claude plugin validate .claude-plugin/plugin.json`
  - passed
- `claude plugin validate .`
  - passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - passed

Review fixes made before closeout:

- Changed the stricter contract from silent v1 mutation to explicit
  `figure-agent.critique-reference-pack.v1.1`, with legacy v1 parseability
  preserved.
- Fixed `--template ""` so blank fixture names emit a reloadable placeholder
  template instead of falling through to usage error.
- Avoided touching real fixture packs, because changing a real pack would make
  existing critiques stale in a slice that is only about authoring support.
- Added brief-path coverage for v1.1 packs so the new template contract is
  tested through `/fig_critique` input generation.
