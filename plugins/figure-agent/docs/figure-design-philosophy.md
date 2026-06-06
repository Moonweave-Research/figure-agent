# Figure Design Philosophy — poly(S-r-DIB) manuscript

The cross-figure **기준점** (reference point) for the 4-5 remaining figures.
Extracted from fig1's proven conventions + figure-agent's codified anti-patterns +
the published canon. **Lean by design — grow it per-figure, do not front-load.**

## The fence (read first)
- This codifies **CONVENTIONS** (checkable: palette, sizes, weights, layout, anti-patterns),
  **NOT TASTE**. Autonomous taste judgment is falsified (reference-free LLM critique ~18% vs author).
- It is a reference + checklist for **you (user-as-master)** and the **deterministic linter** —
  NOT an LLM auto-judge or a release gate. Taste calls stay human.
- Test every line you add against: *"would this have changed a call we actually made?"*
  If it is taste guidance dressed as a rule, delete it.
- Its ONE job is **cross-figure CONSISTENCY**. fig1 reached Nature-tier through 20+ human-judged
  iterations, not through codified principles — so this doc keeps the *next* figures consistent
  with fig1, it does not make any single figure "good".
- **fig1 is the FROZEN reference**: conventions are read FROM it, never retrofitted INTO it.

## 1. Palette (Paul Tol muted + polymer warm; colorblind-safe)
Defined once in `styles/polymer-paper-preamble.sty` — every figure imports it, never redefines.

| token | hex | role |
|---|---|---|
| `cBlue` | `#4477AA` | shallow / cool data (Paul Tol muted blue) |
| `cRed` | `#CC6677` | deep / charge / warm data (Paul Tol muted rose) |
| `cTeal` | `#44AA99` | third categorical (Paul Tol muted teal) |
| `cAmberSphere` | `#DDCC77` | light highlight (Paul Tol light yellow) |
| `cAmber` | `#997A1E` | sulfur/polymer backbone (warm gold) |
| `cBrown` | `#5D4820` | polymer secondary warm |
| `cGray` | `rgb(70,70,70)` | structure outlines, neutral text |
| `cLGray` | `rgb(200,200,200)` | faint reference lines |

Rule: **~4 base chromatic hues** (amber, blue, red, teal). Add hue only with a semantic reason.
Backgrounds are **clean white** (NC main-text convention) — no washes, no tinted bands.

## 2. Typography (sans-serif, Nature size discipline)
- Family: **sans-serif** (`\sffamily`; Helvetica/Arial family).
- **Max 7 pt** for all non-panel-letter text (Nature/Nat Comm rule; figure-wide default capped at 7pt).
- Tiers: panel letters **8 pt bold, upright, lowercase** (`a b c`); apparatus/axis labels **5.5-7 pt**;
  italic only for variables/quantities (ISO 80000-2), upright for verbs/units.
- Anti-pattern to avoid: `low_authority_typography`, `annotation_noise_competes_with_science`.

## 3. Line-weight tiers (to be ENFORCED by the shared `.sty` in Phase 1.2)
Intended 3-tier hierarchy (currently aspirational in fig1; **fig1 has 25 inlined weights with no tier
system** — that is the `uniform_line_weight_monotony` / inconsistency problem 1.2 fixes for fig2-N):
- **primary ~0.9 pt** — narrative paths (polymer chain, well curves, hero outlines)
- **annotation ~0.7 pt** — schematic outlines that are not the narrative (rings, S8, strips)
- **secondary ~0.55 pt** — axes, spines, faint reference lines
Ratio primary:secondary ≈ 1.6-2:1. **Do NOT retrofit fig1**; tier the NEW figures from the start via the shared style file.

## 4. Layout
- Canvas: **178 mm** double-column width, `standalone`, real cm coordinates, **no global `scale=`**.
- Multi-panel: explicit grid; panel letters at NW of each panel/column bbox.
- **Whitespace breathing** — avoid `cramped_or_dead_whitespace`. Negative space is a tool, not waste.
- One clear **hero** per figure (avoid `weak_hero_anchor`); supporting panels stay subordinate.

## 5. Anti-pattern checklist (the codified 13 — `aesthetic_antipattern_audit`)
Run these as a checklist; the critique rubric already audits them per figure.
1. `childish_shape_language` — oversized arrows, rounded generic boxes, cartoon emphasis
2. `poster_gradient_decoration` — decorative gradients / poster-like flat color
3. `generic_template_look` — looks templated, not editorially composed
4. `dead_flat_vector_finish` — no material depth where the object implies it (see instrument lesson)
5. `uniform_line_weight_monotony` — no weight hierarchy (see §3)
6. `weak_hero_anchor` — no clear visual focus
7. `cramped_or_dead_whitespace` — spacing too tight or too empty
8. `low_authority_typography` — weak/inconsistent type
9. `annotation_noise_competes_with_science` — labels fight the data
10. `panel_style_mismatch` — panels inconsistent with each other (THIS doc's main defense)
11. `reference_overcopying` — copied a single reference's idiom (lock-in)
12. `reference_underlearning` — ignored what good references teach
13. `decorative_detail_without_explanatory_value` — gizmos that carry no meaning

## 6. Hard-won lessons (this manuscript)
- **Instrument-substance**: apparatus boxes earn weight via the figure's own instrument standard
  (dark-glass display + faceplate bezel), NOT gizmos/gloss. Over-minimalism reads as flimsy.
- **Reference = STYLE anchor only**: borrow line weights / palette / fonts; keep content from the
  science. no-ref → taste-blind; single-ref → lock-in; prefer 2-3 ref compose, human-supervised.
- **Levers can be binary or structurally blocked** — once a figure is at convention, stop iterating
  (diminishing returns); not every element has a "better" state.
- **Element-iteration is the loop**: name a concrete sub-region defect → 1-line patch → recompile →
  confirm. User-as-master. (Sub-region, not whole panel, is the iteration unit.)

## 7. Published canon (pointers, not gospel)
- **Bang Wong, "Points of View"** (Nature Methods, 2010-2013) — closest to a Nature figure philosophy; the Wong/Tol colorblind palettes.
- **Edward Tufte** — data-ink, chartjunk, small multiples.
- **Rougier, Droettboom & Bourne, "Ten Simple Rules for Better Figures"** (PLOS Comp Biol, 2014).
- **Claus Wilke, "Fundamentals of Data Visualization"** (free online).
- **Paul Tol colour schemes** — the muted palette fig1 already uses.

## Non-goals
- NOT a taste-oracle, NOT a release gate, NOT a substitute for human art-direction.
- Does not author figures. Does not score "is this good".
- Grows per-figure under real pressure; it is a living consistency anchor, not a finished spec.
