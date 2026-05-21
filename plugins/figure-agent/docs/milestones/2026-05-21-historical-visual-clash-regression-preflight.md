# Historical Visual Clash Regression Preflight

**Date:** 2026-05-21 KST
**Issue:** `docs/superpowers/issues/2026-05-21-issue-21b-historical-visual-clash-regression-dogfood.md`
**Status:** preflight captured; host-vision dogfood completed 2026-05-21 (see "Host-Vision Dogfood Result")

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

## Host-Vision Handoff Prompt

Use this prompt in Claude after checking out PR #28 or the branch
`codex/historical-visual-clash-regression`.

```markdown
# Task: Complete Issue 21B host-vision dogfood on scratch artifact

Repository:
- `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]`
- Plugin root: `plugins/figure-agent`

Source of truth:
- `plugins/figure-agent/docs/superpowers/issues/2026-05-21-issue-21b-historical-visual-clash-regression-dogfood.md`
- `plugins/figure-agent/docs/milestones/2026-05-21-historical-visual-clash-regression-preflight.md`

Scratch fixture:
- `.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression`

Important:
- Do not edit canonical `plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/*.tex`.
- Do not mutate accepted/golden/export state.
- Ignore the copied old `critique.md` unless you move it aside; it is schema v1.5 and must not be treated as fresh evidence.

Steps:
1. From `plugins/figure-agent`, regenerate the brief if needed:
   `uv run python3 scripts/critique_brief.py ../../.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression`
2. Read the scratch render and audit assets:
   - `.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression/build/fig1_overview_v2_pair_001_vault.png`
   - all listed `build/panel_crops/*`
   - all listed `build/audit_crops/*`, especially Panel E crops
   - `build/visual_clash.json`
3. Write a new schema v1.7+ `critique.md` for the scratch fixture.
4. In `micro_defects`, account for every `VC###` candidate exactly once using `visual_clash_ref`.
5. Pay special attention to:
   - `VC050 text_on_path HV+`
   - `VC057 text_on_fill V`
   - other `V` candidates around the meter/probe area
6. Classify the historical shape if present:
   - `label_backdrop_overflows_outline` for HV+ backdrop/box overflow
   - `label_glyph_overlaps_internal_drawing` for V_s meter same-box display/glyph collision
   If absent, explicitly justify absence in the relevant `micro_defects[].observation`.
7. Run:
   `uv run python3 scripts/critique_lint.py ../../.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression`
8. Append results to the milestone:
   - whether lint passed
   - how `VC050` was classified
   - how `VC057` / meter-area `V` candidates were classified
   - whether another code issue is needed

Completion condition:
- Do not mark Issue 21B complete unless the host-written critique passes lint and the milestone records the semantic classification outcome.
```

## Host-Vision Dogfood Result (2026-05-21)

Host-vision critique pass on the scratch artifact completed by Claude Code main
loop (no external vision API). The schema v1.5 `critique.md` copied into the
scratch directory was moved aside to `critique.md.v1_5_old` so it could not be
mistaken for fresh evidence; a new schema v1.7 `critique.md` was authored from
the high-zoom Panel E crops, the full-quadrant audit crops, and
`build/visual_clash.json`.

### Lint outcome

```bash
uv run python3 scripts/critique_lint.py \
  ../../.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression
```

Result: `OK: critique lint passed for fig1_visual_clash_regression`.

All 59 `VC###` candidates from `build/visual_clash.json` are accounted exactly
once by `micro_defects[].visual_clash_ref`.

### Semantic classification of historical-shape candidates

- **`VC050 text_on_path HV+`** — classified as
  `label_backdrop_overflows_outline` (BLOCKER, micro-defect `M050`, linked to
  top-level finding `C301`). Host vision confirmed that the HV+ label backdrop
  fill protrudes below the corona-source supply-box outline in this scratch
  render, reproducing the historical regression shape that motivated Issue 21B.
  The corona needle path also crosses through the V glyph, but the primary
  defect is the backdrop overflow.
- **`VC026 text_on_path V` and `VC027 text_on_path s`** — classified as
  `label_glyph_overlaps_internal_drawing` (MAJOR, micro-defects `M026` and
  `M027`, both linked to top-level finding `C302`). The `V_s` portion of the
  `V_s meter` label sits on the meter's internal black display fill rather than
  below it, so the black rectangle bites the top of the glyph — the same-box
  display-vs-glyph collision the issue targets.
- **Other `V` candidates around the meter / probe area**:
  - `VC025 V` is the V of `V_s probe` label above the disk-on-shaft probe;
    accepted as intentional apparatus-label position (`M025`,
    `accept_simplification`).
  - `VC028 V` is the V of Panel F `V_active` PSU label sitting on the box
    light fill below the pulse-trace display — no glyph-on-display overlap;
    accepted (`M028`, `accept_simplification`).
  - `VC029 V` is the V of the rotated `V_s(t)` y-axis label in the lower
    Panel E sub-zone; axis-arrow crossing by axis-label convention, accepted
    (`M029`).
- **`VC057 text_on_fill V`** — classified as `floating_semantic_cue`
  (`M057`, `accept_simplification`). This candidate lies in the Panel C upper
  energy-diagram region (likely the `E_V` axis-tick label), distinct from the
  V_s meter glyph-overlap. It is explicitly justified in `M057.observation`
  as not on an internal drawing of an instrument box.

### Quality-axis verdicts

- `label_annotation_semantics`, `journal_polish`, and `publication_readiness`
  all `needs_patch`, with `C301` and `C302` in `blocking_items`.
- `top_tier_audit.reader_misinterpretation_risk` = `fail`,
  `blocks_high_impact: true`, linking `C301` + `C302`.
- `journal_grade_assessment.benchmark_level` = `needs_human_art_direction` with
  `regression_detected: true` against the canonical fixture's prior pass state
  on the same three quality axes.
- Top-level `verdict: revise` (no physics BLOCKER, so not `block`).

### Plugin-contract sufficiency

The current plugin contract is sufficient for this dogfood:

- `check_visual_clash.py` emitted stable `VC050`, `VC026`, `VC027` ids for the
  two historical-shape sites.
- `critique_brief.py` listed the candidates with the historical shape kinds
  (`label_backdrop_overflows_outline`,
  `label_glyph_overlaps_internal_drawing`) named in scope.
- `build/audit_crops/panel_E_q1.png` and Panel E sub-region crops carried
  enough resolution for host vision to classify both regressions without user
  screenshots.
- `critique_lint.py` enforced the one-to-one `VC### -> visual_clash_ref`
  accounting that prevents an accept-everything bypass at the schema level.

### Code-issue recommendation

No new code slice is required to complete Issue 21B. An optional follow-up
issue could add a rationale-quality lint for `accept_simplification`
`micro_defects` linked to visual-clash candidates — to prevent a future
host-vision pass from waving away a real `VC050`-shape regression with a weak
`accept_simplification` rationale. This is the review-question concern at the
bottom of Issue 21B and matches the "stronger `accept_simplification` rationale
lint" follow-up option in the issue's Expected Outcome section.

### Artifacts

- New critique:
  `.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression/critique.md`
  (schema `figure-agent.critique.v1.7`).
- Preserved prior critique (do not treat as fresh evidence):
  `.scratch/issue-21b/preflight-20260521-212042/fig1_visual_clash_regression/critique.md.v1_5_old`.
- Lint command + output recorded above.
