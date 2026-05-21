# Historical Visual Clash Regression Preflight

**Date:** 2026-05-21 KST
**Issue:** `docs/superpowers/issues/2026-05-21-issue-21b-historical-visual-clash-regression-dogfood.md`
**Status:** preflight captured; host-vision critique pending

## Scope

This milestone records the automated preflight for Issue 21B. It does not
claim that host vision caught the historical defect; that still requires a
real `/fig_critique` run.

## Disposable Artifact

Scratch path:

```text
.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression/
```

Canonical fixture source was not edited. The scratch copy applied one local
regression-pressure edit:

```text
HV+ label center: (6.55, 4.14) -> (6.55, 4.08)
```

This was intentionally kept out of git and only used to check whether the
plugin evidence surfaces remain available for host review.

## Commands

```bash
uv run bash scripts/compile.sh \
  /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression/fig1_overview_v2_pair_001_vault.tex

uv run python3 scripts/critique_brief.py \
  ../../.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression
```

The first compile attempt without `uv run` failed because system `python3`
could not import `numpy` for `scripts/check_visual_clash.py`. The `uv run`
compile path passed and should be used for this dogfood.

## Observed Evidence

- `build/visual_clash.json` exists in the scratch fixture.
- `visual_clash.json total`: `59`.
- First candidate: `VC001 text_on_path S`.
- Historical-relevant candidates include:
  - `VC050 text_on_path HV+`
  - `VC025 text_on_path V`
  - `VC026 text_on_path V`
  - `VC028 text_on_path V`
  - `VC029 text_on_path V`
  - `VC057 text_on_fill V`
- The generated brief includes:
  - `## High-Zoom Visual Audit Crops`
  - `## Visual Clash Candidates (from check_visual_clash.py)`
  - `visual_clash_ref`
  - `schema: figure-agent.critique.v1.7`

## Judgment

Automated preflight passes: the plugin can provide the evidence needed for a
host-vision regression dogfood without mutating canonical source.

The unresolved part is semantic classification by the host critique. The next
step is to run `/fig_critique` on the scratch artifact and verify that:

- every `VC###` candidate is accounted exactly once;
- `VC050` is either classified as `label_backdrop_overflows_outline` or
  explicitly justified as not an overflow in the rendered scratch artifact;
- the `V` candidates around the meter are either classified as
  `label_glyph_overlaps_internal_drawing` where applicable or explicitly
  justified as benign.

If the host critique passes lint but weakly marks all candidates
`accept_simplification`, the next code issue should lint rationale quality for
visual-clash-linked micro-defects.
