# Architecture v0.3 — L3 Snippet Library (active direction)

**Status:** PLAN + branch implementation in progress (2026-05-04)
**Supersedes:** `architecture-v0.3-briefing-semantic-grounding.md` and `briefing-semantic-schema-v1.md` as the *active* v0.3 direction. Those documents remain in the repo as design reference but are demoted to **secondary tracks**.
**Derived from:** N=1 dogfood failure (single-rater F1_w 0.244 → predicted 0.981 with prose grounding) + user real-quality assessment ("달라지는 게 없는데… 우리 피겨 에이전트 개선했냐?") + `/compass` STOP verdict (drift + rot SUSPICIOUS).
**One-line goal:** stop authoring scientific-figure TikZ from scratch; vendor and curate battle-tested community packages and snippets so paper-grade reach becomes a composition problem, not an authoring problem.

---

## 1. Why this displaces the schema-layer plan

The v0.2 dogfood + cheap-experiment + advisor + compass loop produced two converging signals:

1. **Critique-side:** prose `briefing.md §7` already lifts the grounded run from F1_w 0.24 to predicted 0.98 (single-rater, brief-overfit caveat acknowledged). A formal `briefing_semantic.yaml` schema would be additional infrastructure for marginal benefit at this stage.

2. **Author-side:** even with grounded findings, the rendered figure remains visibly sub-paper-grade. Polymer chains read as "지렁이," log-axis tick logic is hand-rolled and irregular, lobe Bézier control points are arbitrary. **The bottleneck is L3 authoring depth, not L1 brief expressiveness or L4.5 critique grounding.**

Schema work tries to make critique smarter. Snippet work makes the underlying figure better. Per the dogfood evidence, the second is the lever.

This document does not delete the schema work — it ranks it lower until snippet adoption either succeeds (in which case schema may be unnecessary) or plateaus (at which case schema returns).

## 2. Concrete v0.3 deliverables

### 2.1 New directory

```
plugins/figure-agent/styles/snippets/
├── polymer_chain.snippet.tex      # chemfig-based, S-rich polymer
├── log_plot.snippet.tex           # PGFPlots loglogaxis with proper minor grids
├── band_diagram.snippet.tex       # bandplot or curated TikZ for CB/VB/trap levels
├── dos_lobes.snippet.tex          # PGFPlots fillbetween or curated TikZ for sideways g(E)
└── README.md                      # snippet catalog, parameter docs, attribution
```

Each snippet is a `\input`-able .tex chunk with `\providecommand` parameters. Reproducible by design — no closed-source GUIs in the authoring chain.

### 2.2 Briefing convention update

`briefing.md §7 Author Intent` adds a `### Snippets` subsection:

```markdown
### Snippets to use
- Row 3 polymer: `polymer_chain.snippet.tex` with monomers=14, S_pattern="rich-cluster-x4-x12"
- Row 1 plots: `log_plot.snippet.tex` with x_decades=6, y_decades=5
- Right panel band: `band_diagram.snippet.tex` with shallow_levels=4, deep_levels=2+continuation
- Right panel DOS: `dos_lobes.snippet.tex` with deep_to_shallow_ratio=2.5
```

L3 author (human or LLM) consumes the snippet refs and `\input`s them. L4.5 critique verifies snippet ref matches what's rendered (via `verify_by: structural` against the .tex AST + visual sanity check).

### 2.3 polymer-paper-preamble.sty additions

Vendor required packages:
- `\RequirePackage{chemfig}` — polymer chemistry
- `\RequirePackage{pgfplots}` and `\pgfplotsset{compat=1.18}` — log axes
- `\RequirePackage{tikz-3dplot}` if 3D arises (defer until needed)

`bandplot` is heavier; defer to v0.3.1 unless `band_diagram.snippet.tex` clearly needs it (likely we can hand-curate from references for now).

### 2.3.1 Post-review annotation primitive

The Row 1 label-on-line regression exposed a gap that is adjacent to A2 but not
part of the log-axis snippet itself: authors were using bare inline `\node`
annotations inside plots. v0.3 now includes `\PlotCallout` in
`polymer-paper-preamble.sty` as the safe pattern for labels that point to a data
trace, dashed guide, or reference marker.

Scope boundary:
- `paper loglog/.style` owns axis styling, tick density, and plot-area sizing.
- `\PlotCallout` owns white-backed leader-label rendering.
- The author still chooses coordinates; automatic label placement remains out
  of scope.

### 2.4 Snippet acceptance criteria

A snippet ships only if:
1. **Compiles standalone** (lualatex on the existing CI matrix)
2. **Style Lock compatible** (no clash with `polymer-paper-preamble.sty` color tokens)
3. **Parameter-clean** (all variations exposed as `\providecommand` arguments, no in-snippet hardcoded constants for things authors will want to tune)
4. **Attribution recorded** in `snippets/README.md` (license + source URL — most are LPPL/MIT or free)
5. **One reference figure compiles** that uses the snippet (kept as `examples/_snippet_smoke/<name>/`)

## 3. First spike — chemfig polymer chain

Step A1 of v0.3.0. ~30-60 minutes scoped.

### 3.1 Spike scope
Replace lines 125-131 of `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` (the three `plot[smooth] coordinates` polymer chain definitions + S marker `\foreach`) with a chemfig-based snippet.

### 3.2 Acceptance test
Compile `golden_trap_depth_picture.tex` and visually inspect Row 3:
- Are chains rendered as connected monomers with explicit backbone bonds?
- Are S atoms attached to backbone vertices, not floating?
- Does S-rich vs. S-sparse contrast inside the dashed highlight box become visible?

If any of these is **no**, abort the spike and document why chemfig didn't work for this case before proceeding to other snippets. False starts are cheap; false confidence in chemfig wastes the rest of the snippet plan.

### 3.3 If spike succeeds
- Promote to `polymer_chain.snippet.tex` with parameters extracted
- Update `golden_trap_depth_picture.tex` to `\input` the snippet
- Update `briefing.md §7` to reference the snippet
- Re-run `/fig_critique` and re-adjudicate; expected: G001 (BLOCKER) closes
- Move to Step A2 (log_plot via PGFPlots)

### 3.4 If spike fails
Three documented escape hatches in priority order:
1. **TikZ.net manual snippet** — copy a hand-curated polymer drawing, parameterize
2. **Inkscape + svg2tikz** — draw monomer + S, convert, vendor as snippet
3. **Hand-roll TikZ macro** — explicit `\foreach` zigzag + S placement (last resort, was the original v0.2 approach)

Update this doc with the rejected path and rationale.

## 4. Sequencing

| Step | Snippet | Priority | Trigger |
|------|---------|----------|---------|
| A1 | polymer_chain | BLOCKER | First spike — closes G001 BLOCKER on golden fixture |
| A2 | log_plot | MAJOR | Closes G004 (tick logic) and the FN001-class missed findings on power-law and Debye plots |
| A3 | band_diagram | MAJOR | Closes the right-panel structural drift; also useful for `fig3_trapping_concept` (N=2 fixture, briefing already prepped) |
| A4 | dos_lobes | MINOR | Closes G002 (lobe height ratio) cleanly; deferred until A1-A3 demonstrate the snippet pattern works |

Pause-points after each step: re-run `/fig_critique` + adjudicate against the v0.3 grounded rubric. Track F1_w trajectory; if F1_w drops or stalls, snippet plan needs revision.

## 5. v0.3.0 scope vs. v0.3.1+

### v0.3.0 original ship hypothesis (superseded by the addendum)
- A1 (polymer chain) and A2 (log_plot) both ship and are used by `golden_trap_depth_picture` + `fig3_trapping_concept`
- N=2 dogfood produces F1_w within 0.10 of N=1 (i.e., snippet approach generalizes; not just brief-overfit)
- BLOCKER FN count = 0 on both fixtures
- `briefing.md §7` convention is documented in the SKILL doc

### v0.3.1+ deferred
- A3 + A4 snippets
- Schema layer (`briefing_semantic.yaml`) — re-evaluate after N=3 if friction in §7 prose appears
- `bandplot` package vendoring — only if hand-curated TikZ proves insufficient
- L7 Inkscape post-process polish — separate Gap 2 work, unchanged

### Addendum (2026-05-04 EOD): v0.3.0 ship deferred — option ε

**Decision: defer v0.3.0 ship until a real paper figure naturally exercises A1 (`\PolymerChain`) or A2 (`paper loglog/.style`).**

Context: After A1 + A2 were integrated into `golden_trap_depth_picture` and the BandDiagram Gap 3+5 options were added as a separate macro hardening step, the planned N=2 fixture `fig3_trapping_concept` was found incompatible with the current `\BandDiagram` macro encoding (Gap 1: line-vs-box visual model; Gap 4: hard-coded "CB"/"VB" labels — both out of `/decide` Option B scope). A repo-wide survey found no other fixture exercises A1 or A2:

- `n3_trial_01_trap_depth` uses `\WavyChain` + `\LogLogPlot` (the *sibling* macros of A1/A2, not A1/A2 themselves) — useful as a broad-catalog stability signal but does not directly defend the ship-gate clause "snippet approach generalizes; not just brief-overfit."
- `dogfood_power_law_trap_pipeline` lacks `\BandDiagram` entirely.
- All other fixtures predate the v0.3 deliverables.

Per advisor + the shadcn/Salesforce design-system pattern (ship when N≥2 *real* consumers organically pull the component), synthesizing a fixture purely to satisfy the gate violates the very condition the gate is meant to enforce. The macro Gap 3+5 extension + smoke + golden regression are durable on branch and require no v0.3.0 tag to remain useful.

**Ship gate restated**: v0.3.0 ships when the next real manuscript figure pulls in A1 or A2, that figure compiles cleanly under the existing snippet API, and `/fig_critique` produces a grounded N=2 measurement. Until then v0.3 work continues in-place on `main` without tag.

**Catalog stability signal (separate from ship gate)**: `/fig_critique n3_trial_01_trap_depth` is run as a rubric §4.2 evaluator-stability + library-catalog-stability probe. F1_w from this run is logged but is **not** treated as the §5.1 ship-gate metric.

## 6. Open issues for next session

1. **Real N=2 consumer** — wait for a real manuscript figure to pull A1 or A2; do not synthesize a fixture only to satisfy the ship gate.
2. **A3/A4 pressure** — keep BandDiagram line-vs-box and DOS-lobe improvements deferred until another figure creates direct pressure.
3. **Snippet interface generalization** — keep the first 1-2 snippet interfaces small; later snippets should conform only where the pattern proves useful.
4. **Attribution + license tracking** — chemfig and PGFPlots are LPPL 1.3-compatible; keep `styles/snippets/README.md` as the active catalog.
5. **Reference vs. snippet conflict** — when a reference image shows a feature the snippet does not generate by default, document the override in `briefing.md §7`.

## 7. Status of sibling docs

| Doc | Status | Reason |
|---|---|---|
| `architecture-v0.3-briefing-semantic-grounding.md` | demoted, kept as reference | Schema-layer hypothesis didn't fail per se; it was preempted by cheaper prose convention. Re-evaluate at N=3. |
| `briefing-semantic-schema-v1.md` | demoted, kept as reference | Premature spec; schema may still inform §7 prose structure, not new file format. |
| `critique-evaluation-rubric-v1.md` | active | Used to score v0.3 progress; still primary metric. Add §6 amendment: "applied-fix verification" gap (rubric measures finding-quality, not artifact-quality). |
| `golden_trap_depth_picture/critique_adjudication.yaml` | active | N=1 baseline + iter 4 grounded run; will be augmented with iter 5 after chemfig spike. |
| `golden_trap_depth_picture/critique.md` | active | Iter 4 grounded run record. Replaced when iter 5 is run. |

## 8. Next-session bootstrap checklist

When resuming in a new session:

1. Read this doc and `docs/superpowers/plans/2026-05-04-v0-3-review-blockers.md`.
2. Confirm the branch state: A1 `\PolymerChain`, A2 `paper loglog`, and BandDiagram `[no_et]` / `[traps=none]` should exist.
3. Run the current verification loop before making claims: `uv run pytest -q`, `uv run ruff check .`, and a golden fixture compile.
4. Pick the next real manuscript figure that naturally needs A1/A2; do not create a fake N=2 fixture for metrics.
5. If promoting v0.3.0, rerun critique/adjudication and only tag after artifact gates match the accepted criteria.

---

_Plan written at compass STOP after N=1 dogfood + cheap experiment + advisor pushback + user real-quality assessment. Closes the v0.3 direction question with a concrete spike-first plan that defers heavier infrastructure (schema layer, briefing automation) until snippet evidence either lands or plateaus._
