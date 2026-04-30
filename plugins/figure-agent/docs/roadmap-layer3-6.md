# Roadmap: Layer 3-6 Improvements (Post Layer 2.5 v0.3)

**Status**: planning. Layer 2.5 (vtracer extraction) is at plateau as of commit `e611f1e`. Remaining quality gaps are not in extraction — they are in the **authoring + verification** stack (Layers 3-6).

## Where we are (Layer 2.5 complete)

`structural_regions` v0.3 extracts the following from a reference PNG via vtracer:

| Section | Detected | Generalises across fixtures |
|---|---|---|
| panel_arcs | colored ovals (blue / orange / purple) | yes (returns `[]` if absent) |
| border_boxes | teal rounded rectangle | yes |
| chain_rows | polymer chain y-centers + x-spans | yes (canvas-relative thresholds, validated on `golden_trap_depth_picture`) |
| s_atoms | amber dots assigned to chain rows | yes; absence-of-atoms is the reliable spurious-row signal |
| trap_levels | shallow/deep horizontal dashes inside band diagram | yes |
| plot_boxes | axis backgrounds inside panels | depends on panel_arcs being present |
| plot_curves | power-law line + Debye decay bbox | depends on panel_arcs |
| ispd_lobes | ISPD bell curves | layout-specific |
| right_gaussians | g(Et) sideways Gaussians in band diagram | layout-specific |

`{{structural_regions}}` is wired into `llm_author_prompt.py` so any figure with `coordinate_hints.yaml` automatically receives these coordinates in the authoring prompt.

## What we cannot solve at Layer 2.5

These gaps require either semantic understanding (vision-LLM, deferred per plugin identity) or different layers:

- **Mathematical curve shapes** — vtracer Bezier control points ≠ original curve geometry
- **Curved arrow paths** — fragmented to ~20+ pieces
- **Dashed elements** — each dash is its own segment
- **Annotation bracket vs polymer chain disambiguation** — both are horizontal gray paths

Conclusion: more Layer 2.5 work has diminishing returns. Move to Layers 3-6.

---

## Phase 1 — bbox-driven TikZ macro library (Layer 3)

**Goal**: reduce LLM authoring burden by providing high-level primitives that take bbox/coordinate arguments. LLM stops writing raw Bezier curves; writes `\BellCurve{x1,y1,x2,y2,color}` instead.

**Why first**: foundational for Phase 3 (visual diff loop). Without macros, micro-adjustments require Bezier-level edits which the LLM cannot do reliably.

**Estimated effort**: 1-2 sessions. Highest ROI of remaining work.

### Step 1.1 — Pattern audit (30 min)

Audit these `.tex` files for repeated TikZ patterns:
- `examples/fig3_n2_evidence/fig3_n2_evidence.tex`
- `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex`
- `examples/fig3_trap_schematic_v97/fig3_trap_schematic_v97.tex`

Candidate macros to extract (initial list):
- `\LogLogPlot{x1,y1,x2,y2, x_decades, y_decades}` — axes + tick labels + log-log frame
- `\PowerLawLine{x1,y1,x2,y2, color}` — diagonal line in log-log space
- `\BellCurve{x1,y1,x2,y2, color}` — symmetric Gaussian-like bell shape (already partially in `\SmallLobe`)
- `\WavyChain{x1,x2,y, S_x_list, S_color, trap_x_list, trap_color}` — polymer chain row
- `\BandDiagram{bbox, CB_y, VB_y, trap_levels_list}` — full band diagram skeleton
- `\TrapDash{x,y,role}` — single trap dash with electron marker (already partially in `\TrapLevel`)
- `\PanelArc{cx,cy,rx,ry,color}` — colored oval panel border
- `\PanelArrow{from,to,color,dot}` — convergent arrow with optional endpoint dot

Output: `docs/macro-audit.md` listing each pattern + occurrence count + proposed signature.

### Step 1.2 — Implementation (1-2 hours)

Add macros to `styles/polymer-paper-preamble.sty`. Each must:
- Take bbox or (x1,y1,x2,y2) arguments — no figure-specific hardcoded coordinates
- Use only palette colors (cBlue, cAmber, cTeal, etc.)
- Be testable: at least one fixture exercises each macro

### Step 1.3 — Prompt integration (15 min)

Update `prompts/llm_author_tikz.md` §4 (Flagship Macro Guidance) to register new macros via the existing `_RE_FLAGSHIP_NEWCOMMAND` extraction in `scripts/llm_author_prompt.py`. (Pattern: `% \MacroName{args}: description` comment in `.sty` is the source of truth.)

### Step 1.4 — Validation (30 min)

Re-author `fig3_n2_evidence.tex` using new macros. Verify:
- 12/12 drift gate maintained
- Aspect mismatch < 5%
- Line count reduced (macro abstraction working)

---

## Phase 2 — Author next paper figure (dogfood)

**Goal**: validate Phase 1 in production by drawing the next paper figure with the new macros + auto-wired structural_regions.

**Why second**: real-world friction surfaces remaining gaps faster than synthetic tests. Picks the actual next figure for the user's manuscript.

**Estimated effort**: 1-2 sessions, depends on figure complexity.

### Steps

1. User identifies next figure (or `/fig_new` interview)
2. User saves AI-generated reference PNG to `examples/<name>/reference/`
3. Run `/fig_extract <name> --rebuild` (auto: vtracer → coordinate_hints.yaml)
4. Run `llm_author_prompt.py examples/<name>` → prompt with `{{structural_regions}}` filled
5. LLM authors `<name>.tex` using new bbox macros
6. `/fig_compile <name>` → drift gate + visual checks
7. If gaps remain, document them as Phase 3 input

---

## Phase 3 — Visual diff feedback loop (Layers 4-6)

**Goal**: close the residual gap between LLM output and reference automatically, mimicking how a human designer iterates by eye.

**Why third**: Phase 1 macros must exist first, otherwise visual diff produces Bezier-level micro-edits the LLM can't reliably make.

**Conditional**: only build if Phase 1 + 2 leave visible quality gap on dogfood fixtures.

**Estimated effort**: 2-3 sessions.

### Step 3.1 — Pixel diff tool

`scripts/visual_diff.py`:
- Input: compiled PNG (`build/<name>.png`) + reference PNG (`reference/<name>.png`)
- Tool: ImageMagick `compare -metric RMSE` for global score; Pillow + numpy for per-region diff
- Output: list of `{bbox_cm: [x1,y1,x2,y2], rmse: float, hint: "darker" | "shifted_left" | ...}`

Tests: `tests/test_visual_diff.py` with synthetic before/after fixtures.

### Step 3.2 — Diff → natural-language feedback formatter

Translate per-region diff into prompt-ready instructions:
```
- Region [4.5, 1.5, 6.0, 2.5]: too dark (rmse 0.32) — reduce dashed line
  density or use cGray!50 instead of cGray
- Region [10.5, 2.0, 13.5, 3.5]: gaussian shifted (rmse 0.45) — peak should
  be 0.3 cm to the left
```

This is the part where domain knowledge matters most — what aspects of the diff are actionable to an LLM authoring TikZ?

### Step 3.3 — `/fig_refine` slash command

Iteration loop:
1. compile current `.tex` → PNG
2. visual_diff vs reference
3. format diff as feedback block
4. LLM re-authors `.tex` (only the regions flagged)
5. compile + re-diff
6. converge or hit max-iter (3) → human handoff

Add `/fig_refine <name>` to `commands/` directory.

### Step 3.4 — Integration

- Layer 6 (validation gates): visual_diff RMSE as an optional accepted-mode gate
- Layer 7 (status): show last refine result if present

---

## Phase 4 — Stretch / deferred

These are intentionally not on the critical path:

- **Vision-LLM extraction**: would close all semantic gaps (curve identification, arrow direction, annotation purpose) but conflicts with current plugin identity ("does not call image-gen or vision APIs"). Would require explicit identity revision discussion.

- **Source format alternative**: if user obtains AI-generated references in SVG (not PNG), we can extract semantic structure directly. Out of our control — depends on user's image-gen tool.

- **Auto-vectorizer replacement**: vtracer alternative (potrace, Inkscape autotrace, ML-based). Investigated and rejected — fundamental issue is "raster has no semantic structure," not "vtracer is bad at vectorization."

- **Per-fixture threshold overrides**: if Phase 2 dogfooding shows Layer 2.5 thresholds need fixture-specific tuning, add `coordinate_hints_overrides:` block to spec.yaml. Don't pre-build this; wait for evidence.

---

## Concrete starting point for next session

**First action**: Phase 1.1 — pattern audit.

Command:
```bash
cd /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent
# Read the three .tex files and identify repeated patterns:
# - log-log axes (lines 41-69 of golden_trap_depth_picture.tex)
# - bell curves (\SmallLobe macro already exists)
# - polymer chains (lines 132-138 of golden + lines 195-260 of fig3_n2_evidence)
# - panel arcs (ellipse pattern in fig3_n2_evidence)
# - tick label foreach loops
```

Output: `docs/macro-audit.md` ranked by occurrence count → top 5 candidates for Step 1.2.

## References

- `docs/architecture-overview.md` — current 10-layer model
- `docs/quality-kernel-goal.md` — product direction (NO vision API, NO PNG-to-TikZ auto-conversion)
- `docs/historical/roadmap-v0.1.7-selection-notes.md` — earlier rejected items, may be revisited
- Latest commit: `e611f1e` (Layer 2.5 v0.3 generalisation)
