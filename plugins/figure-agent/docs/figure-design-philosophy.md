# Figure Design Philosophy — poly(S-r-DIB) manuscript

The cross-figure **기준점** (reference point) for the 4-5 remaining figures.
Extracted from fig1's proven conventions + figure-agent's codified anti-patterns +
the published canon. **Lean by design — grow it per-figure, do not front-load.**

## The fence (read first)
- This codifies **CONVENTIONS** (checkable: palette, sizes, weights, layout, anti-patterns),
  **NOT TASTE**. Autonomous taste judgment is falsified (reference-free LLM critique ~18% vs author).
- It is a reference + checklist for **you (user-as-master)** and the **deterministic linter** —
  NOT an LLM auto-judge or a release gate. Taste calls stay human.
- Current deterministic convention-spine evidence includes Style Lock,
  text-anchor `semantic_assertions` with tolerance/`indeterminate`, and
  compile-time `convention_receipt` files for injected project rules. These
  surface convention evidence; they do not score aesthetics or mutate source.
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
| `cBlue` | `#4477AA` | shallow / cool data (Paul Tol **bright**-scheme blue — NOT muted) |
| `cRed` | `#CC6677` | deep / charge / warm data (Paul Tol muted rose) |
| `cTeal` | `#44AA99` | third categorical (Paul Tol muted teal) |
| `cAmberSphere` | `#DDCC77` | light highlight (Paul Tol muted sand) |
| `cAmber` | `#997A1E` | sulfur/polymer backbone (warm gold) |
| `cBrown` | `#5D4820` | polymer secondary warm |
| `cGray` | `rgb(70,70,70)` | structure outlines, neutral text |
| `cLGray` | `rgb(200,200,200)` | faint reference lines |

Rule: **~4 base chromatic hues** (amber, blue, red, teal). Add hue only with a semantic reason.
Backgrounds are **clean white** (NC main-text convention) — no washes, no tinted bands.

> Verified vs Paul Tol ([SRON](https://sronpersonalpages.nl/~pault/)): the set mixes **3 muted** (rose/teal/sand) **+ 1 bright** (blue `#4477AA`; muted blue would be indigo `#332288` or cyan `#88CCEE`). Each hue is individually CVD-safe, so the set is not unsafe — but Tol's rule is *use a scheme as given*. Not a defect; just verify the four together under a **deutan/protan simulator** before locking, and reserve a `#DDDDDD`-class grey strictly for inactive/bad-data, never as a category color. For a continuous symbolic gradient, switch to a perceptually-uniform map (viridis / Crameri) — do not interpolate the qualitative palette.

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
Verified floor: minimum stroke ~**0.5 pt** at final size (ACS graphics-prep; SciencePlots `nature` style = 0.5 pt axes / 1.0 pt data lines). Keep `secondary` at/above 0.5 pt so it survives print reduction. (The 0.25 pt floor seen in third-party guides is NOT on a primary Nature page — use 0.5 pt.)

## 4. Layout
- Canvas: **178 mm** double-column width = **ACS double-column max** (7.0 in; poly(S-r-DIB) is ACS-domain
  chemistry). Within the universal full-width band (Cell 174 / NC ~180 / Nature flagship 183 mm) and reduces
  cleanly — but confirm the **exact target journal** before locking `\documentclass` geometry. `standalone`, real cm coords, **no global `scale=`**.
- Multi-panel: explicit grid; align everything to invisible guides — small misalignments are highly visible (Wong); panel letters at NW of each panel/column bbox.
- **Whitespace breathing** — avoid `cramped_or_dead_whitespace`. Consolidate negative space into clean contiguous blocks; give the hero MORE surrounding space (Wong).
- One clear **hero** per figure (avoid `weak_hero_anchor`); supporting panels stay subordinate.

## 4b. Submission output (verified — Nature artwork guide / ACS)
- **Line art / schematics → VECTOR PDF (or EPS)**, text kept editable — **NOT** rasterized TIFF/PNG/JPEG.
  The 300/600 dpi raster rule is for *photographs* only; a TikZ schematic has none. Our golden TIFF/PNG are
  internal/preview artifacts — the **submission deliverable is the vector PDF**.
- **RGB** color mode (the journal converts to CMYK for print); author + export in RGB.
- **Embed fonts; do NOT outline text to curves** (keeps text editable for the art editor, avoids substitution).

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
Design-principle pointers with verified primary sources. **Pointers, not a spec** — the mechanical numbers (mm, pt, weights) live in §2/§3/§4, not here. Filter every line by the fence: *would this have changed a call we actually made?* (Wong's "know your audience" / "message trumps beauty", banking-to-45, and the Lie-Factor formula are deliberately omitted — taste/irrelevant for a static schematic.)

- **Bang Wong, "Points of View"** (Nature Methods 2010-2011) — [collected PDF](https://static1.squarespace.com/static/587e7412be6594f2dc02480f/t/63e0d7f70f60c8044b65b900/1675679747977/Bang_Wong_Point-of-view_collection.pdf). Salience, gestalt grouping, negative space, layout. *Ours:* one hero per panel on one strong channel; group sub-regions by shared treatment + tight proximity, not boxes/leader-lines everywhere.
- **Cleveland-McGill perceptual hierarchy** — [ranking](https://www.informationvisuals.com/information-design-theory/elementary-perceptual-tasks): position > length > angle > area > color saturation (least accurate). *Ours:* encode any quantitative symbolic axis / arrow length / trap-depth bar by position or length scaled linearly, never by hue or area.
- **Claus Wilke, "Fundamentals of Data Visualization"** — [color pitfalls](https://clauswilke.com/dataviz/color-pitfalls.html) + [balance data/context](https://clauswilke.com/dataviz/balance-data-context.html). Cap ~3-5 meaning-bearing colors; never color-only (redundant-code so it survives B/W); direct labels over legends; and the data-ink **rebuttal** — do not strip a schematic bare. *Ours:* every color distinction gets a second cue; explanatory decoration (instrument boxes) is context, not chartjunk (cf. §6 instrument-substance).
- **Rougier, Droettboom & Bourne, "Ten Simple Rules for Better Figures"** ([PLOS Comp Biol 2014, e1003833](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003833)). Survivors: Rule 5 don't-trust-defaults, Rule 6 match-colormap-to-data, Rule 8 avoid-chartjunk (erase only gridlines/fills/redundant labels), Rule 10 endorses **TikZ/PGF**. *Ours:* every style key is a deliberate value (Style-Lock); the programmatic-TikZ workflow is convention-aligned.
- **Tufte small-multiples** (via Wilke) — repeated panels share identical scale, motif size, line weights, label placement, color mapping. *Ours:* this **is** the cross-figure Style-Lock job — keep them byte-consistent across fig2-N.
- **Paul Tol colour schemes** — [SRON](https://sronpersonalpages.nl/~pault/). Use as given, no interpolation; muted=9 (+`#DDDDDD` bad-data grey), bright=7 (Tol's line default). *Ours:* see §1 — `cBlue #4477AA` is the **bright**-scheme blue, not muted.
- **Crameri 2020, "The misuse of colour"** ([Nat Commun, PMC7595127](https://pmc.ncbi.nlm.nih.gov/articles/PMC7595127/)). No rainbow/jet; perceptually-uniform maps for continuous data; greyscale-readable.

**Machine-readable systems (what already exists — answer to "has someone built this?"):** A scientific-figure design system already exists as **code**, not prose — closest is [**SciencePlots**](https://github.com/garrettj403/SciencePlots) (MIT; `.mplstyle` rcParam sheets for science/nature/ieee + Paul-Tol cycles). Its *weights/geometry* port to TikZ as named defaults (`nature.mplstyle`: 7pt fonts, 0.5pt axes, 1.0pt lines, ticks-in); its matplotlib inch sizes do **not** (we are a 178mm TikZ canvas). [khroma](https://cran.r-project.org/web/packages/khroma/vignettes/tol.html) gives exact Tol hex + the "use-as-given" constraint for cross-checking our `.sty`; [ColorBrewer](https://colorbrewer2.org/) has a colorblind-safe filter for any future ramp; [Crameri maps](https://www.fabiocrameri.ch/colourmaps/) for continuous fields only. There is **NO scientific-figure linter** that audits a figure against a journal spec — the enforcement pattern is "apply the style at generation time", which our `.sty` + deterministic checks already do for TikZ. Treat all as **verification references**, not dependencies.

> Sources fetched + adversarially verified 2026-06-07 (workflow `wcl1r5kg8`). Honestly unverified (third-party/blocked-fetch, do not over-trust): exact Nature mm widths (artwork PDFs non-extractable), the 0.25 pt floor (third-party only; ACS 0.5 pt used instead), EMBO/Science/Cell numbers (PDFs 403). Confirm exact specs against the chosen target journal.

## Non-goals
- NOT a taste-oracle, NOT a release gate, NOT a substitute for human art-direction.
- Does not author figures. Does not score "is this good".
- Grows per-figure under real pressure; it is a living consistency anchor, not a finished spec.
