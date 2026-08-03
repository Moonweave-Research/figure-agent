# figure-agent-svg — Status Analysis (2026-05-05)

Audience: Codex (or another LLM coding agent) entering this branch with no
prior session context. Read top to bottom; every claim is grounded in concrete
files in this worktree.

Worktree: `/Users/choemun-yeong/workspace/ResearchOS/figure-agent-svg`
Branch: `experiment/svg-first-figure-agent`
Plugin root: `plugins/figure-agent-svg`

---

## 1. Project intent and prior decisions (do not re-litigate)

The sibling plugin `plugins/figure-agent` (TikZ-first) hit a quality ceiling:
LLM/author cannot reach Nature-grade figures by tuning TikZ macros alone
(see memory `session_strategic_fork_2026_05_03_eod`,
`project_architecture_reset_2026_05_03`). This experiment moves the source of
truth to **editable semantic SVG**, with TikZ demoted to an optional
fragment generator.

Locked design decisions encoded in the worktree:

- **Final source = `examples/<name>/source/<name>.svg`**, schema
  `data-figure-agent-svg="semantic-v1"` (`docs/semantic-svg-schema-v1.md`).
- **vtracer output is locked coordinate evidence only**, never copied into
  source. Stripped at export. Enforced in
  `scripts/svg_export.py:27-40` (`_is_underlay`, `_strip_underlay`) and
  asserted by `scripts/svg_contract.py` schema rules.
- **Generated SVG (Vega-Lite, OpenChemLib) is opaque inside a semantic
  wrapper** with stable `data-object-id` and `data-bbox`; raw internals are
  marked `data-external-svg="true"` and skipped by the contract validator
  (`svg_contract.py:97-103`).
- **Boundary rule**: do not mutate `plugins/figure-agent` from this
  experiment. See `AGENTS.md`.

Deleted/avoided paths (do not reintroduce):

- vtracer SVG → TikZ as final source.
- TikZ as durable manuscript source for this plugin.

---

## 2. Architecture map

```
plugins/figure-agent-svg
├── commands/                 6 slash commands (svgfig_new/underlay/primitives/export/qa/status)
├── docs/                     schema, MVP, dogfood notes, tool survey
├── examples/
│   ├── fig1_charge_trap_overview   dogfood A: passed end-to-end
│   ├── fig1_svg_overview           dogfood B: passed end-to-end
│   └── n3_trial_01_trap_depth      ACTIVE STRESS TEST — gaps surface here
├── scripts/
│   ├── svg_contract.py       399 LOC — schema + style + bbox + margin checks
│   ├── svg_export.py         155 LOC — strip underlay, white-bg, rsvg-convert PDF/PNG, PIL TIFF
│   ├── svg_primitives.py     516 LOC — primitive DSL → semantic SVG fragments
│   ├── svg_qa.py             174 LOC — labels, PDF font, white-bg, visual diff
│   ├── svg_status.py          66 LOC — freshness from mtimes
│   ├── svg_underlay.py       146 LOC — vtracer wrapper
│   └── js/
│       ├── render_vega_loglog_plot.mjs        Vega-Lite log-log plot SVG
│       └── render_openchemlib_molecule.mjs    SMILES → SVG molecule
├── styles/svg_style_tokens.yaml   palette, font_families, text_roles, stroke_widths, layout
├── tests/test_svg_mvp.py     613 LOC pytest
├── package.json              vega, vega-lite, openchemlib (Node deps)
└── pyproject.toml            uv-managed Python (PIL, lxml, pyyaml, vtracer)
```

Primitive registry (`svg_primitives.py:452-458`):

```
RENDERERS = {
    "energy_band":           _render_energy_band,           # pure-Python paths
    "loglog_plot":           _render_loglog_plot,           # pure-Python paths
    "openchemlib_molecule":  _render_openchemlib_molecule,  # Node delegate
    "polymer_chain":         _render_polymer_chain,         # pure-Python paths
    "vega_loglog_plot":      _render_vega_loglog_plot,      # Node delegate
}
```

Pipeline state machine (template-based authoring path, optional):

```
spec.yaml + briefing.md
   │
   ├──► reference/<draft|ref>.png          (manual or rsvg-convert from draft.svg)
   │
   ├──► svg_underlay.py --from-spec        ⇒ underlay/<name>.underlay.svg (locked)
   │
   ├──► author source/<name>.template.svg  with <!-- figure-agent-fragment:<id> --> markers
   │     +
   │     primitives.yaml                   ⇒ svg_primitives.py renders source/<name>.svg
   │
   ├──► svg_contract.py source/<name>.svg --spec spec.yaml
   ├──► svg_export.py <name>               ⇒ build/<name>.export.svg, exports/<name>.pdf|png|tif
   ├──► svg_qa.py source/<name>.svg --spec --pdf --png --reference-png --max-diff
   └──► svg_status.py <name>
```

Pure hand-authored SVG path: skip primitives.yaml, write source/<name>.svg
directly. Both n3 (template + primitives) and the two `fig1_*` fixtures
(template + primitives) exercise the template path.

---

## 3. Reproducible verification (run from `plugins/figure-agent-svg`)

```bash
npm install                                           # vega + openchemlib
uv sync
uv run pytest                                         # 613 LOC of tests, all passing on this branch

# stress fixture, full chain
uv run python scripts/svg_primitives.py examples/n3_trial_01_trap_depth
uv run python scripts/svg_contract.py \
  examples/n3_trial_01_trap_depth/source/n3_trial_01_trap_depth.svg \
  --spec examples/n3_trial_01_trap_depth/spec.yaml
uv run python scripts/svg_export.py n3_trial_01_trap_depth
uv run python scripts/svg_qa.py \
  examples/n3_trial_01_trap_depth/source/n3_trial_01_trap_depth.svg \
  --spec examples/n3_trial_01_trap_depth/spec.yaml \
  --pdf  examples/n3_trial_01_trap_depth/exports/n3_trial_01_trap_depth.pdf \
  --png  examples/n3_trial_01_trap_depth/exports/n3_trial_01_trap_depth.png \
  --reference-png examples/n3_trial_01_trap_depth/reference/codex_gen_v1.png \
  --max-diff 0.42
uv run python scripts/svg_status.py n3_trial_01_trap_depth
```

All commands above currently exit 0. **The pipeline is green; the artifact
quality is the problem.**

---

## 4. Dogfood evidence — `n3_trial_01_trap_depth`

Reference: `examples/n3_trial_01_trap_depth/reference/codex_gen_v1.png`
Current export: `examples/n3_trial_01_trap_depth/exports/n3_trial_01_trap_depth.png`
Spec: `examples/n3_trial_01_trap_depth/spec.yaml` (nature-double, 1830×980)
Template: `examples/n3_trial_01_trap_depth/source/n3_trial_01_trap_depth.template.svg` (119 lines)
Primitives: `examples/n3_trial_01_trap_depth/primitives.yaml` (44 lines, 3 fragments)

Side-by-side gap inventory (visual inspection of both PNGs):

| # | Region | Reference shows | Current export shows | Root cause |
|---|--------|-----------------|----------------------|------------|
| G1 | Math labels everywhere | $I \propto t^{-n}$, $\tau_d = \tau_0 e^{E_t / k_B T}$, $g(E_t)$, $E_t$, $E_g$, italic variables, true subscripts | `tau_d`, `tau_d = tau_0 exp(E_t/kBT)`, `g(E_t)`, `kBT` rendered as plain Arial | **No math typography backend.** `_text()` in `svg_primitives.py:56-79` always emits `<text font-family="Arial" font-size=...>` — there is no MathJax / KaTeX SVG path, no MathML, no italic-by-default for variables. Style tokens file lists no math role. |
| G2 | Sulfur polymer chain | zigzag carbon backbone with multiple gold S atoms, lone-pair dots, hand-drawn highlight circle and dashed ellipse around different S atoms | OpenChemLib SMILES `CCSCCSCCSCCSCC` rendering — chemically correct, visually clean, but generic; orange "chemical origin" circle and purple dashed ellipse are placed at hard-coded fractions of the bbox in `svg_primitives.py:420-434`, ignoring where S atoms actually landed in the rendered molecule | **Coordinate disconnect between generated SVG and overlay.** The OpenChemLib output is opaque (`data-external-svg="true"`); overlays do not query atom coordinates from the renderer. They are bbox-fraction guesses. |
| G3 | g(E_t) mini in panel 2 | clean bell-shaped bimodal curve | two cubic Bezier humps that overlap and look noisy | Manually authored path in template lines 44-47. No `bell_curve` / `gaussian_pair` primitive exists. |
| G4 | Energy band diagram (panel right) | discrete trap levels distributed inside the band gap, shading suggests a continuum, right-side g(E_t) curve has clearly distinct shallow (orange) and deep (purple) lobes registered to the same energy axis | CB and VB are gray rounded rectangles (look like device contacts), trap lines sit outside the gap visually, right-side g(E_t) curves are not registered to the same vertical axis as the trap lines | **Primitive expressivity gap.** `_render_energy_band` in `svg_primitives.py:257-363` hardcodes geometry as fractions of bbox. There is no parameter for trap-level distribution (count, energy positions, line widths) and no shared y-axis contract between the band column and the density column. |
| G5 | Convergence brace | a single sweeping brace tying the three left rows into the right panel (functional, not decorative) | a teal vertical-only brace at x≈968-1030 in template lines 57-63; reads as decoration, not data flow | Template hand-authored. No brace primitive. |
| G6 | Composition / density | reference fills its frame, hierarchy is tight | the 1830×980 export has visible whitespace between panels and between panels and labels; the right panel and `unified-energy-diagram` underuse their bbox | Layout is bbox-based with no auto-pack. nature-double dimensions in `styles/svg_style_tokens.yaml:7-9` are width-only; no panel auto-fit logic exists. |

Spec config knob:

```yaml
visual_diff:
  max_fraction: 0.42      # spec.yaml:33
  tolerance: 8
```

`svg_qa.visual_diff_fraction` (`svg_qa.py:98-116`) is a per-pixel max-channel
difference fraction. With `tolerance=8` and `max_fraction=0.42`, this gate
will pass even when 41 % of pixels differ from the reference. In other words:
**QA is green, 6 out of 6 paper-quality gaps are uncaught.** No category
breakdown, no localization, no semantic comparison.

This matches the lesson recorded in
`project_v0_2_critique_reference_grounding` (memory): single-number visual
diff is structurally insufficient for §7-style 80% gates.

---

## 5. Root-cause categories (in order of leverage)

### R1 — Math typography is missing entirely (blocks paper-final)

`svg_primitives.py:56-79` and every `<text>` in template/primitives go
through `font-family="Arial"`. Both Node renderers also use Arial only:

- `render_vega_loglog_plot.mjs:50-66` — Vega-Lite axis titles and labels are
  Arial strings.
- `render_openchemlib_molecule.mjs` — molecule labels are atom symbols only.

Symptoms: every variable in the figure (`τ_d`, `E_t`, `E_g`, `g(E_t)`,
`I ∝ t^{-n}`, `τ_d = τ_0 e^{E_t/k_BT}`) is displayed in roman-Arial ASCII.
This single defect makes any output non-publishable regardless of layout
quality.

Possible backends to evaluate (in increasing order of integration cost):

1. **MathJax-node SVG output** as a sixth primitive `kind: math` →
   `data-external-svg="true"` wrapper, identical to the Vega path. Output is
   already an SVG fragment with paths, embeds cleanly.
2. **mtex2MML + MathJax** for a pure LaTeX input surface
   (`\tau_d = \tau_0 e^{E_t / k_B T}`).
3. **Pre-baked SVG glyph fragments** for the dozen variables this corpus
   actually uses. Cheapest, but does not generalize.

Recommendation: option 1, treat math as an external-SVG fragment with stable
`data-bbox`, font fallback handled by MathJax font config.

### R2 — Semantic overlays leak coordinate guesses around opaque generators

When a primitive uses an external engine, decorative overlays (highlight
circles, dashed ellipses, leader lines) are placed at hard-coded bbox
fractions of the wrapper, with no contract from the engine about where
features actually are. See:

- `_render_openchemlib_molecule` `svg_primitives.py:420-434`: `chemical_x =
  x + w * 0.39`, etc.
- Overlays in `_render_vega_loglog_plot` `svg_primitives.py:380-390`.

Two possible repairs:

- **Primitive contract returns landmarks**: each renderer returns the SVG
  string AND a `landmarks` dict (e.g. `{"S_atoms": [(cx, cy), ...]}` for
  OpenChemLib, `{"power_law_endpoint": ..., "intersection": ...}` for Vega).
  Overlays consume landmarks instead of bbox fractions.
- **Semantic overlay layer in `primitives.yaml`**: declarative overlay spec
  (`{kind: highlight_circle, anchor: {primitive: polymer-chain, landmark:
  S_atoms[1]}}`) → renderer resolves at render time.

R2 is the gating problem behind G2 specifically and behind any future
"draw a circle around feature X" task.

### R3 — Primitive vocabulary is too thin for actual scientific schematics

Five renderers cover one molecule, one log-log plot, one band diagram, one
polymer chain, one purely Python log-log plot. The corpus needed even for
`n3_trial_01` already exposes:

- Bimodal `g(E_t)` density (G3).
- Trap-level ladder with shared energy axis (G4).
- Sweeping brace from N rows to 1 column (G5).
- Pipeline arrow chain with annotated boxes (visible in panel 2, currently
  drawn as raw paths in template lines 35-43).

Each addition is small (~50-100 LOC of Python paths + tests). The harder
question is whether to build them inside `svg_primitives.py` or extract a
`primitives/` package that can be reused outside this experiment.

### R4 — QA blind spots dominate the §7 80% question

`svg_qa.py` checks: schema validity, required label presence, PDF font
embedding, white background, visual diff fraction. None of these caught
gaps G1-G6. The visual-diff gate is fraction-only, with no
localization, category, or per-region threshold.

Repair direction (see also R5):

- Reference-grounded category critique. Categories: `math_typography`,
  `overlay_landmark_alignment`, `palette`, `panel_density`, `axis_registration`.
- Per-category PASS/FAIL with explicit evidence (bbox of finding).
- Treat single-number visual diff as a smoke check, not a §7 gate.

This needs the host LLM (Claude / Codex) to do vision-style comparison
against the reference; cannot be done with PIL alone. Memory
`project_v0_2_critique_reference_grounding` already tracks this design
direction in the sibling plugin.

### R5 — Runtime sprawl

The plugin now needs Python (`uv`), Node (`npm`), `rsvg-convert` (librsvg),
`vtracer`, `pdffonts`, `pdftotext`. Each adds reproducibility surface area.

This is acceptable cost if R1-R4 land; not acceptable if the experiment
stalls. Worth making `npm install` lazy (only when a fragment kind requires
it) so the pure-Python primitives path stays self-contained.

---

## 6. Open decisions for Codex

D1. **Math backend** — MathJax-node SVG (recommended) vs pre-baked glyphs vs
    deferring math support. Affects every fixture from now on.

D2. **Landmark contract** — make primitive renderers return `(svg,
    landmarks)` and let overlays resolve symbolically? Or keep them opaque
    and accept that "highlight a feature" requires hand authoring?

D3. **Critique gate replacement** — replace `--max-diff` numeric gate with a
    reference-grounded categorical critique driven by the host model
    (mirroring `figure-agent` v0.2 `/fig_critique`)? If yes, command name
    likely `svgfig_critique`, output `critique.md` like the sibling.

D4. **Primitive package extraction** — keep `svg_primitives.py` flat or
    split into `primitives/{plot,band,chain,brace,math}/...`? Extraction
    cost is small now; will compound after 5-10 more primitive kinds.

D5. **Layout / panel auto-fit** — accept manual bbox specs in primitives.yaml
    forever, or add a panel layout pass (e.g. minimal Z-pattern grid solver
    with margin/gap from style tokens)?

D6. **Scope reset check** — re-read `session_handoff_2026_05_03_late` and
    `project_architecture_reset_2026_05_03`. The October decision was that
    L3 macros (TikZ side) were a secondary lever, with the real reach being
    briefing automation + Inkscape post-process. Is the SVG-first experiment
    a third path, or a substitute for one of those? Resolve before adding
    primitives indefinitely.

---

## 7. Out of scope for this branch

- Modifying `plugins/figure-agent` (sibling plugin, TikZ-first).
- Routing vtracer SVG paths back into TikZ.
- Treating `underlay/<name>.underlay.svg` as anything other than locked
  coordinate evidence.
- Marketplace wiring of this plugin into the workspace until the
  human/maintainer says so (per `AGENTS.md`).

---

## 8. Geometry rendering — is SVG the bottleneck?

Short answer: **no**. SVG is geometry — paths, Bezier, transforms, clip,
gradients, patterns are all native. The current pipeline fails at geometry
not because the format is limited, but because **there is no coordinate
algebra layer producing the path data**. Evidence from this worktree:

**Geometry that renders well today** (anything delegated to a real engine):

- `vega_loglog_plot` — Vega-Lite computes log scales, axis ticks, marker
  positions, line interpolation. Output SVG is correct.
- `openchemlib_molecule` — bond angles, atom coordinates, valence layout
  computed by OCL. Output SVG is correct.
- `rsvg-convert` — lossless SVG → PDF / 600 dpi PNG.

**Geometry that renders badly today** (everything authored as raw Bezier):

- `_render_energy_band` (`svg_primitives.py:257-363`) — every coordinate is
  a hard-coded fraction of the wrapper bbox. Trap lines, density curves,
  axis arrows, labels — none share a coordinate system. Output looks
  unregistered (G4).
- `n3_trial_01_trap_depth.template.svg:44-47` — `g(E_t)` mini drawn as
  one cubic path with hand-picked control points. Output is noisy (G3).
- `n3_trial_01_trap_depth.template.svg:57-63` — convergence brace is six
  hand-picked Bezier control points. Reads as decorative, not functional
  (G5).
- OpenChemLib overlays (`svg_primitives.py:420-434`) — highlight circle
  positioned by bbox fraction because the molecule renderer is opaque (G2).

**Diagnosis.** TikZ was deprecated as the *final source* (rendering ceiling
problem), but its **coordinate-algebra system was the load-bearing piece**:

```tex
\node (cb) at (0,4) [band] {CB};
\node (vb) at (0,0) [band] {VB};
\draw[trap] (cb.south) -- ++(0,-0.5);
\draw[brace] (s1.east) to[bend right] (density.west);
```

Named anchors, relative coordinates, automatic curve fitting. SVG-first
threw out this layer too, and now the LLM (or hand-coded Python) computes
every `cx`, `cy`, control point manually. LLMs are weak at this; humans
make mistakes; primitives drift apart.

The format is fine. The missing layer is a **coordinate engine that emits
SVG fragments**.

### Geometry-engine options (cost order)

**A. TikZ as a coordinate engine, SVG as final source.**
- New primitive `kind: tikz` in `RENDERERS`. Input: TikZ source string.
  Pipeline: `latexmk` → `dvisvgm` (or `pdf2svg`) → SVG fragment.
- Wrap output with the existing `data-external-svg="true"` envelope, exactly
  like `_render_vega_loglog_plot` already does. Schema and contract code
  already handle this. No boundary-rule violation: TikZ is no longer the
  durable source, only a renderer behind a primitive.
- Cost: ~30 LOC + `dvisvgm` dependency.
- Closes immediately: G3 (bimodal density), G4 (energy band registration),
  G5 (brace), and most future scientific schematic geometry.

**B. Asymptote.**
- Native SVG/PDF output, more programmable than TikZ.
- Cost: extra LaTeX-class toolchain. Strictly dominated by A in this
  workspace because TikZ is already installed and battle-tested.

**C. Custom Python anchor DSL.**
- Build a mini coordinate algebra: `Node("cb", at=(0,4), kind="band")`,
  references like `cb.south + (0,-0.5)`, automatic brace path generation.
- Cost: 200-400 LOC plus debugging. Reinvents what TikZ already does, with
  no guarantee LLMs are better at this DSL than at raw SVG.

**D. Per-domain engine delegation (scattered).**
- bell-curve density via numpy → SVG path; brace via TikZ macro; trap
  ladder via custom Python — each gap solved with a different engine.
- Effectively A but unbundled. Inconsistent, harder to teach the LLM.

### Recommendation

**A first**, single PR. Ship one TikZ-backed primitive (e.g. an
`energy_band_v2` written in TikZ and rendered through `dvisvgm`) that
replaces the current `_render_energy_band` for the n3 fixture. Re-export
and compare against `reference/codex_gen_v1.png`. If A closes G3-G5, the
SVG-first hypothesis survives and primitive expansion is straightforward.
If A does not close them, the bottleneck is upstream of geometry — almost
certainly briefing semantic grounding (memory
`project_v0_2_critique_reference_grounding`), and SVG-first should not
keep accreting primitives until that signal comes back.

Adding more hand-Bezier primitives without A would re-create the
"primitive hand-tuning explosion" pattern recorded in memory
`feedback_macro_vs_snippet_dichotomy`.

---

## 9. Suggested first move for Codex

Two independent gating PRs exist — R1 (math typography, §5) and §8 option A
(TikZ as coordinate engine). They do not block each other; either can land
first. Recommended order based on impact and signal value:

1. **§8 option A first.** Higher-impact single PR (closes G3-G5,
   regression-tests SVG-first viability). If this fails to close geometry
   gaps the SVG-first hypothesis is in trouble — a bigger signal than R1
   would give.
2. **R1 second.** Closes G1 (every math label) but does not by itself
   answer the viability question. Mechanically simpler.

Concrete plan for R1 once §8-A has landed:

1. Add `scripts/js/render_mathjax.mjs` taking
   `{ tex: string, font_size: number, color: string }` over stdin and
   writing a self-contained SVG fragment with embedded font glyph paths.
2. Add `_render_mathjax` to `svg_primitives.py:RENDERERS` as kind `math`.
3. Replace the ASCII labels in
   `examples/n3_trial_01_trap_depth/source/n3_trial_01_trap_depth.template.svg`
   lines 92-106 (`tau_d`, `g(E_t)`, `tau_d = tau_0 exp(E_t/kBT)`, `E_t`)
   with `<!-- figure-agent-fragment:math-tau-d -->` markers backed by
   primitives.yaml entries.
4. Re-export and visually compare against `reference/codex_gen_v1.png`.
5. Update `tests/test_svg_mvp.py` with one math-fragment fixture and one
   PDF-text assertion that `τ` survives `pdftotext`.

This gives a clean signal on whether D1 alone moves the dogfood gap from
"unpublishable" to "tunable", before the larger R2-R5 work begins.
