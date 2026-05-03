# BandDiagram Caller-pgfkeys Pilot — Design Spec

**Date**: 2026-05-03
**Status**: brainstorm-complete, awaiting user review before implementation plan
**Pilot scope**: `\BandDiagram` only. Composite per-sub-element fan-out (β pattern) deferred to follow-up spec pending pilot validation.

## Goal

Add a single optional pgfkeys slot to `\BandDiagram` (a composite macro) so callers can override style at the call site without rewriting the figure-wide `\tikzset{bandFrame/...}` between calls. All existing sub-element default styles (color, line width, dash, rounded corners) remain unchanged. This pilot adds the *single-key α* path to a composite macro; it does **not** answer whether per-sub-element fan-out (β) is needed or how it should look — that question is held open by §"Out of scope".

## Why

### Original macro intent (user, 2026-05-03)

> "복잡한 형상, LLM이 바로 하기 어려운 거는 매크로. 스타일·색상은 나중에 언제든 바꾸는 게 처음 의도였다."

`\BandDiagram` currently encodes **shape + style** in one definition: 5 sub-element styles (`bandFrame`, `bandbox`, `bandAxis`, `bandEt`, `trapShallow`/`trapDeep`) live in `\tikzset` blocks but the macro itself provides no per-call override surface. Callers must edit the figure-wide tikzset between calls — a workflow that breaks the original "style is caller's job" intent.

### Style-responsibility carving rule

Three categories of "style" exist in this codebase (decision recorded 2026-05-03 brainstorm):

1. **Geometric parameters** — positions, dimensions, arrow tip lengths, rounded-corner radii. These are *part of the shape*; belong in macro.
2. **Semantic encoding** — `bandEt` dashed (Et = reference level convention), `trapShallow=cAmber`/`trapDeep=cBlue!45!cRed` (shallow vs deep classification). These *encode meaning*; smart default in macro, caller may override.
3. **Decoration** — pure aesthetic (frame color, fill opacity, non-semantic line widths). Belongs to caller; macro provides default only as convenience.

This pilot adopts the **seaborn / ggplot2 industry pattern**: macro provides smart semantic defaults (categories 1 + 2), caller may override anything via the new pgfkeys slot. (Industry sources: [Seaborn](https://seaborn.pydata.org/), [ggpubfigs PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8567791/), [ggplot2 vs Seaborn comparison](https://medium.com/@petroschol123/ggplot2-and-seaborn-a-bilingual-guide-to-data-visualization-634d4b30f664).)

The Style Lock layer (`lint_tex.py` palette enforcement at BLOCKER tier) is unaffected — it operates on callsites, and the new override slot still passes through callsite color tokens that `lint_tex.py` scans.

### Why BandDiagram, not another candidate

Decision rationale (2026-05-03 `/decide`):

- BellCurve (PR #1) validated the *primitive* single-key pattern. The next open design question is the *composite* pattern.
- BandDiagram is the most composite of the remaining 4 candidates (already invokes 5 named sub-styles), and has only 2 callsites (both in `_macro_smoke`) → minimal migration noise during the pattern pilot.
- TrapLevel (14 callsites in golden + dogfood) was the alternative; deferred because its callsites are validation fixtures, not in-flight manuscript figures, so "real-fixture exposure" is not a current discriminator.
- Tracer Bullet rationale: validate the structural unknown (composite override) before extending the proven primitive pattern to high-volume callsites.

### Pilot scope honesty

α + (ii) confines this pilot to **adding a single optional pgfkeys slot wrapped in a TikZ scope** — roughly 5–10 LOC delta in the macro. The composite per-sub-element fan-out pattern (β: `\BandDiagram[frame={...}, axis={...}]`) is *not* validated here; it is deferred to a follow-up spec triggered by future fixture pressure (≥ N callsites simultaneously varying ≥ 2 sub-styles).

## Architecture

### Macro definition pattern

```latex
\tikzset{
  band diagram/.style={},   % default empty no-op; caller-supplied keys appended via \BD@opts
}
\makeatletter
\newcommand{\BandDiagram}[2][]{%
  \begingroup
  \def\BD@opts{#1}%
  \BandDiagramDraw#2\relax
}
\def\BandDiagramDraw#1,#2,#3,#4,#5,#6,#7,#8,#9\relax{%
  \begin{scope}[band diagram, \BD@opts]
    %% body unchanged from current macro:
    \pgfmathsetmacro{\BDcx}{(#1+#3)/2}%
    \pgfmathsetmacro{\BDaxX}{#1+0.63}%
    \pgfmathsetmacro{\BDaxYlo}{#6+0.05}%
    \pgfmathsetmacro{\BDaxYhi}{#5-0.43}%
    \pgfmathsetmacro{\BDaxYmid}{(\BDaxYlo+\BDaxYhi)/2}%
    \pgfmathsetmacro{\BDetYlo}{#6-0.35}%
    \pgfmathsetmacro{\BDetYhi}{#5+0.30}%
    \draw[bandFrame] (#1,#2) rectangle (#3,#4);
    \BandBox{\BDcx}{#5}{CB}
    \BandBox{\BDcx}{#6}{VB}
    \draw[bandAxis] (\BDaxX,\BDaxYlo) -- (\BDaxX,\BDaxYhi);
    \node[rotate=90, text=cGray, font=\sffamily\fontsize{6.5}{7.8}\selectfont]
      at (\BDaxX-0.18,\BDaxYmid) {Energy};
    \draw[bandEt] (#7,\BDetYlo) -- (#7,\BDetYhi);
    \node[text=cGray] at (#7+0.20,\BDaxYmid) {$E_t$};
    \foreach \BDy in {#8} { \TrapLevel{\BDcx-0.41}{\BDy}{trapShallow} }%
    \foreach \BDy in {#9} { \TrapLevel{\BDcx-0.25}{\BDy}{trapDeep} }%
  \end{scope}
  \endgroup
}
\makeatother
```

**Scope discipline**: `\begingroup` is opened in `\newcommand{\BandDiagram}` (before `\def\BD@opts`) and closed in `\BandDiagramDraw` after the scope environment. This isolates `\BD@opts` to the call so a future macro that nests `\BandDiagram` (or sequential calls without intervening `\endgroup`) cannot read or clobber a stale outer-call value.

**Why option storage via `\BD@opts` instead of `\BandDiagramDraw[#1]#2,...,#9\relax`:**

LaTeX's `\def` parser supports at most 9 positional arguments (`#1`–`#9`). The current `\BandDiagramDraw` already consumes all 9 slots for the bbox CSV (`x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys`). Prepending an optional `[#1]` slot would push the count to 10 and exceed the limit. The fix: store the optional argument in an outer `\def\BD@opts{#1}` at `\newcommand` level, then reference `\BD@opts` from inside `\BandDiagramDraw` after its 9 CSV slots are consumed. This preserves the existing 9-arg parser shape and adds zero parse-slot pressure to the inner macro.

Key changes vs current macro:
- 1 new outer style key `band diagram/.style={}` (empty default).
- `\newcommand{\BandDiagram}[1]{...}` → `\newcommand{\BandDiagram}[2][]{...}` — one optional leading argument added.
- New `\def\BD@opts{#1}` line in `\newcommand` body to capture the optional arg without consuming an inner-macro slot.
- Body wrapped in `\begin{scope}[band diagram, \BD@opts] ... \end{scope}`. No body-level draw calls modified, all `#1`–`#9` references inside `\BandDiagramDraw` retain their original CSV-arg meaning.
- All 5 sub-style defaults (lines 186–194 of current preamble) untouched.

### Three caller patterns supported simultaneously

```latex
% (1) Default — visually identical to current behaviour. Backwards-compatible.
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}

% (2) Per-call override — single sub-style varied at this call only.
\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]
            {6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}

% (3) Figure-wide tikzset — existing path, still works unchanged.
\tikzset{bandFrame/.append style={draw=cAmber}}
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
```

### Sub-element semantic-encoding defaults (preserved)

Per the carving rule, these defaults remain in the preamble unchanged because they encode meaning, not decoration:

- `bandEt` = dashed (Et = reference-level convention).
- `trapShallow={cAmber, line width=0.72pt}`, `trapDeep={cBlue!45!cRed, line width=0.72pt}` — shallow/deep classification by hue.

Caller may override either via the new `[#1]` slot or via figure-wide tikzset; nothing forbids it. The defaults exist to make the *uncustomized* call produce a meaningfully encoded figure.

### Lint policy: unchanged

`scripts/lint_tex.py` continues to enforce palette membership / no raw hex / no `\definecolor` / no font overrides at the BLOCKER tier. The new `[#1]` slot's contents are scanned at the callsite by the existing scanner — coverage automatic.

## Migration

### Callsite migration

`\BandDiagram` callsites = 2, both in `examples/_macro_smoke/_macro_smoke.tex`:
- line 24: `\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}`
- line 28: `\BandDiagram{6,5.5,9,8.5, 7.8, 6.2, 7.5, {}, {}}`

**Both kept verbatim.** The new signature with `[#1]` empty default makes 1-arg invocation valid; no syntactic migration required.

### `_macro_smoke` augmentation (override demonstration)

Add a 3rd `\BandDiagram` invocation to `_macro_smoke.tex` so the pilot exercises the new override path at smoke-test level:

```latex
% --- BandDiagram: per-call override demo (Layer 3 caller-pgfkeys pilot) ---
\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]
            {6,9,9,11.5, 11, 9.5, 7.5, {}, {}}
\node[font=\sffamily\fontsize{6}{7}\selectfont]
  at (7.5,8.7) {BandDiagram (override demo)};
```

Bbox coordinates chosen to avoid overlap with existing _macro_smoke layout (above the second BandDiagram at y=5.5..8.5).

## Validation

### Drawing-instruction-level criterion (qpdf qdf classifier)

**Baseline selection (decided)**: The classifier test compares the **post-pilot `_macro_smoke.pdf`** (new macro signature + 3rd callsite added) against a **frozen pre-pilot baseline PDF** captured before any code change. The pre-pilot baseline is committed as a binary fixture under `tests/fixtures/banddiagram_pilot/` (qpdf-stripped form, ~few KB). This follows the standard golden-fixture pattern (test asserts diff against a locked-in artifact, not against a regenerated reference).

Why this direction (vs comparing post-pilot against post-pilot-plus-one-more-change): the pilot's claim is "scope wrap + 3rd callsite addition produces *only* (a)–(e) deltas vs the unmodified `_macro_smoke`." That assertion is meaningful only against the pre-pilot baseline. Comparing post-pilot against itself would tautologically pass.

The expected PDF stream delta between **frozen pre-pilot baseline** and post-pilot `_macro_smoke.pdf` is bounded:

- (a) `\begin{scope}[band diagram, ]` with empty `[#1]`: TikZ may emit a `q\nQ\n` graphics-state save/restore pair per existing call (0 or 4 bytes per call, version-dependent). Predicted total: 0 or 8 bytes (2 existing calls).
- (b) The added 3rd callsite emits a complete BandDiagram path stream (frame rectangle + 2 BandBox nodes + axis arrow + Et dashed + 0 trap dashes since shallow_ys/deep_ys are empty) plus the accompanying `\node` label. Length predictable from existing BandDiagram emission size.
- (c) `/CreationDate`, `/ModDate`, `/ID` (lualatex per-build variance).
- (d) Stream length declarations and xref offsets — mechanical consequences of (a) and (b).
- (e) Position-only shifts of pre-existing operators caused by (a)/(b)/(d).

Any line-level qdf diff outside (a)–(e) — particularly inside coordinate values of *pre-existing* paths, path operators (`m`/`l`/`c`/`h`), or final draw/fill colors of pre-existing draws — indicates a real rendering regression.

The exact (a) byte count cannot be predicted in advance because TikZ scope `q...Q` emission is implementation-detail dependent. The plan task that runs the first compile **must measure the actual delta and pin it in the test classifier**.

Implementation:
- Plan Task 1: capture pre-pilot baseline. Compile current `_macro_smoke.tex` (no edits yet), run `qpdf --qdf --object-streams=disable build/_macro_smoke.pdf tests/fixtures/banddiagram_pilot/baseline.qdf`. Commit the baseline as a small binary fixture.
- After macro + 3rd-callsite changes: `qpdf --qdf --object-streams=disable build/_macro_smoke.pdf /tmp/new.qdf`.
- `scripts/diff_pdf_content.py tests/fixtures/banddiagram_pilot/baseline.qdf /tmp/new.qdf` — first run reports `DIFFER` with measured length delta.
- Structural classifier over the qdf diff confirms every difference falls into (a)–(e). Failure → investigate before merge.

### Pixel-level safety net

For the case where qpdf qdf classifier passes but pixel output diverges (e.g., sub-pixel TikZ rounding from scope wrap):

- `magick compare -metric AE _macro_smoke.png _macro_smoke.png.baseline` over both old and new build PNGs (600 dpi rasterize).
- Threshold: AE fraction ≤ 0.001 (essentially 0 tolerance; only the predicted 3rd callsite region should differ from baseline).
- Mechanism reuses Layer B (`scripts/test_export_pipeline_equivalence.py`-style harness). Activation scope: `_macro_smoke` only, opt-in for the duration of the pilot. Decision to keep or retire this opt-in deferred to PR REVIEW.md.

### Tests (4 added)

New file `tests/test_band_diagram_api.py`:

1. **Default render unchanged.** Compile minimal `.tex` with `\BandDiagram{0,0,4,3,2,1,3,{},{}}`; assert PDF stream contains the cTeal frame stroke, cAmber `trapShallow` stroke (when triggered), `bandEt` dashed pattern. (Validates the (2) semantic-encoding defaults survive the scope wrap.)
2. **Per-call override applies.** Compile `\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]{...}`; assert frame outline appears in cAmber at 0.8 pt; default cTeal absent on that frame path.
3. **Figure-wide tikzset path still works.** Compile fixture with `\tikzset{bandFrame/.append style={draw=cAmber}}` *before* the call (no `[#1]` arg); assert cAmber frame emitted. (No-regression for the pre-pilot caller pattern.)
4. **Drawing-instruction classifier.** `tests/test_band_diagram_byte_classifier.py` (separate file). Compile current `_macro_smoke.tex`; qpdf-strip; diff against the **pre-pilot baseline** committed at `tests/fixtures/banddiagram_pilot/baseline.qdf` (captured in plan Task 1 before any code change). Assert every line-level diff matches one of (a)–(e). The baseline fixture is the load-bearing artifact — without it the test cannot detect drift introduced by the pilot itself.

Existing `pytest` suite (currently 226 passed) must remain green after migration. Expected post-pilot total: 230.

### Documentation

New `docs/macros/band-diagram.md`:

- Signature: `\BandDiagram[<style keys>]{x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys}`
- Five sub-style keys with current defaults: `bandFrame`, `bandbox`, `bandAxis`, `bandEt`, `trapShallow`, `trapDeep`.
- Style-responsibility carving rule (1/2/3) with this macro as worked example.
- Three caller usage patterns (default / per-call override / figure-wide tikzset).
- Migration note: existing 1-arg callsites unchanged; option slot is add-only.
- Explicit deferred: sub-element fan-out (`[frame={...}, axis={...}]` β pattern) — separate spec triggered by future fixture pressure.

Update `docs/architecture-overview.md` Layer 3 section: change "BellCurve decoupled (other 7 deferred)" line to "BellCurve + BandDiagram decoupled (composite pilot uses single-key α pattern; sub-element fan-out β deferred)".

## Out of scope

- WavyChain / LogLogPlot / TrapLevel decoupling — separate specs, gated on this pilot's validation outcome.
- β sub-element fan-out (`\BandDiagram[frame={...}, axis={...}]`) — deferred until fixture-side pressure is empirically observed (≥ N callsites simultaneously varying ≥ 2 sub-styles). **This pilot does not answer the question "does the composite per-sub-element fan-out pattern work for figure-agent macros?" That question remains open and must not be marked closed by virtue of this pilot succeeding.**
- BandBox / TrapLevel signature changes — BandDiagram only invokes them, does not re-define.
- Promoting (2) semantic-encoding to BLOCKER lint (e.g., reject `\BandDiagram[bandEt/.append style={solid}]`) — separate analysis; current Style Lock stays at palette-only.
- Layer 5 export-staleness prerequisite from BellCurve spec is **already satisfied** by PR #3 (merged 2026-05-03).

## Implementation order (for downstream writing-plans)

1. Confirm `\BandDiagram` callsite count and exact line numbers via `grep -rn '\\BandDiagram' examples/`.
2. **Capture pre-pilot baseline** (load-bearing for §Tests #4): with no code changes yet, run `bash scripts/compile.sh examples/_macro_smoke/_macro_smoke.tex`, then `qpdf --qdf --object-streams=disable plugins/figure-agent/examples/_macro_smoke/build/_macro_smoke.pdf tests/fixtures/banddiagram_pilot/baseline.qdf`. Commit this fixture in the same atomic commit as the macro/test changes (or in a precursor commit so the baseline is recoverable independently of the pilot).
3. Update `styles/polymer-paper-preamble.sty`:
   - Add `band diagram/.style={}` to a new `\tikzset{...}` block (or merge into existing block above line 195).
   - Wrap macro body in `\begingroup\def\BD@opts{#1}\BandDiagramDraw#2\relax`, with `\endgroup` placed inside `\BandDiagramDraw` after `\end{scope}`. `\begingroup` placement is **load-bearing** — keeping `\BD@opts` outside the group would leak the option value to subsequent `\BandDiagram` calls.
   - `\BandDiagramDraw`'s 9-slot CSV parser is **unchanged** — the optional arg is stored in `\BD@opts` to avoid LaTeX's 9-arg `\def` limit.
   - Wrap body in `\begin{scope}[band diagram, \BD@opts] ... \end{scope}` (use `\BD@opts`, not `#1`, since `#1` inside `\BandDiagramDraw` is still the first CSV arg `x1`).
4. Compile `_macro_smoke.tex` (existing 2 callsites, unchanged) — assert visual no-regression by qpdf qdf classifier against the Step 2 baseline.
5. Add 3rd `\BandDiagram[bandFrame/.append style=...]{...}` callsite to `_macro_smoke.tex` per Migration §2.
6. Add `tests/test_band_diagram_api.py` (3 assertions — default / override / figure-wide).
7. Add `tests/test_band_diagram_byte_classifier.py` (1 classifier test against the Step 2 baseline fixture).
8. Run `uv run pytest -q` — must reach 230 passes.
9. Run `uv run ruff check .` — must be clean.
10. Add `docs/macros/band-diagram.md`.
11. Update `docs/architecture-overview.md` Layer 3 line.
12. Single feature branch, commit message: `refactor(macro): add caller-pgfkeys slot to BandDiagram (composite pilot, single-key α pattern)`.
13. PR with REVIEW.md describing pilot validation outcome (α + (ii) decisions, β fan-out deferred, semantic-encoding defaults preserved).

## Self-review

- **Placeholder scan**: no TBD or TODO. The "exact (a) byte count" is left to plan-time measurement, not a placeholder — qpdf qdf scope-wrap delta is genuinely TikZ-version-dependent.
- **Internal consistency**: α single-key decision, (ii) preserved-default decision, and "(2) semantic-encoding stays in macro" decision all converge on the same outcome — body unchanged, only outer scope wrap added.
- **Scope check**: 1 macro, 1 .sty edit, 1 callsite addition (no migration), 2 new test files, 1 new doc, 1 doc update. Single implementation plan is appropriate.
- **Ambiguity check**: caller pattern (2) `bandFrame/.append style={...}` vs `bandFrame={...}`-style direct override is ambiguous in the §"Three caller patterns" example. The `.append style` form is documented as the recommended idiom; the macro itself does not parse sub-keys so the alternative direct form is *not supported* in this pilot — that's β fan-out's job. Spec must surface this so callers do not assume direct-key syntax works.
- **Drift from original goal**: the brainstorm's stated goal was "validate composite per-sub-element override pattern." α + (ii) confines this pilot to a 5–10 LOC scope wrap, which does **not** validate β fan-out — that validation is explicitly deferred. The pilot's actual contribution is "establish that BellCurve's primitive pattern transfers to a composite macro without regression" + "verify smart-default + override-available framing on a real semantic-encoding case (Et dashed, trap color classification)." This is honest scope, not the originally framed validation.
- **Fact-check fixed inline (post-write)**: initial draft used the BellCurve idiom `\BandDiagramDraw[#1]#2,...,#9\relax` — but `\BandDiagram`'s 9 CSV args already saturate LaTeX's 9-slot `\def` limit, so prepending `[#1]` would push to 10 and fail to compile. Replaced with outer `\def\BD@opts{#1}` storage at `\newcommand` level, referenced as `\BD@opts` inside the scope wrap. Implementation-order Step 3 updated to call this out so plan executors do not regenerate the broken pattern.
- **Advisor pre-commit review (2026-05-03)**: 3 findings folded back in.
  - Classifier baseline ambiguity → §Validation explicitly pins "frozen pre-pilot baseline" + new Step 2 captures it before any code change.
  - `\BD@opts` global-state risk → moved `\def\BD@opts` inside `\begingroup`; §Architecture adds a "Scope discipline" paragraph explaining why placement is load-bearing.
  - §Goal vs §Self-review consistency → §Goal softened from "establishes the primitive single-key pattern" to "adds the single-key α path to a composite macro", §Out-of-scope adds an explicit negative claim "this pilot does not answer 'does fan-out work'".
