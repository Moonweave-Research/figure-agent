# Tex-Geometry Semantic Assertions (directional physics verifier)

Status: DESIGN (approved in brainstorm 2026-06-28). Branch:
work/review-auto-fixes-2026-06-25. Backs memory
`project_fig5_physics_semantic_assertions_2026_06_28` and the canonical
`project_techstack_direction_2026_06_21`.

## Problem (dogfood-grounded)

fig5_actuation_mechanism was drawn with the cantilever bending TOWARD the +V
electrode (attraction, F=qE toward electrode). But the paper's novelty is
**polarity-dependent REPULSION** — pure-dielectric Maxwell stress (∝E²) is always
attraction, so observed repulsion is THE macroscopic probe of trapped charge.
Drawing attraction shows the trivial behaviour and kills the message.

**Neither the render detectors, nor visual composition-iteration, nor the existing
label-relational `semantic_assertions` could catch this physics-direction error.**
A dogfood probe (`scratchpad/sem_probe.py`) compiled both variants and ran the real
`check_semantic_assertions`: the natural assertion "force points away from the
electrode" (`qE left_of` the electrode label) is **OK in BOTH** repulsion and
attraction (the electrode is far right, so the force label is left of it either
way) — it does NOT discriminate. Only a fragile proxy ("qE left_of the first charge
dot") flips, and it depends on label placement + first-token matching.

ROOT: directional physics lives in **drawn elements** (the force arrow, the
cantilever bend, the neutral axis), not in text-label positions. The robust source
for these facts is the figure's own **`.tex` coordinates** — the recurring session
lesson (the reverted geometric verifier + Approach 2: tex coords beat pixel/label
detection).

## Design — two layers

**Layer 2 — intent source (process, agent-driven), with a deterministic backstop.**
Physics intent already lives in the project research docs: per-figure `briefing.md`
§6/§7 (physics invariants + author-intent), and the master plan
`02_Surfur_Polymer/docs/figure_set/planning/detailed_figure_composition.md`. The
agent READS those, extracts the directional invariants, and authors them as
assertions; with no docs it falls back to general physics.

Layer 2 is formalized by `scripts/checks/check_physics_grounding.py` (a deterministic
meta-check, TDD'd) — the agent-authoring is irreducibly LLM, but the meta-check is its
fail-loud TRIGGER + backstop. It classifies each figure:
- **grounded** — declares physics invariants (briefing §6/§7) AND has `tex_assertions`.
- **declared_unenforced** — declares invariants but no `tex_assertions` ⇒ WARN: the
  agent must read §6/§7 + the plan and author directional assertions. (A cohort
  survey found fig1/fig2/fig3_trapping/fig4 here — intent declared, never enforced.)
- **undeclared** — no Physics-invariants section (general-physics fallback / trivial).

So the loop is: `check_physics_grounding` surfaces which figures need grounding →
the agent reads the docs and authors `tex_assertions` → `check_tex_assertions`
fail-loud enforces them. (This formalizes exactly what was done by hand for fig5.)

**Layer 1 — deterministic enforcement (this build, TDD).** A new checker evaluates
the agent-authored assertions against the `.tex` — a fail-loud verifier that holds
even when agent/visual judgment drifts ("every autonomy advance rides a fail-loud
verifier").

### Component: `scripts/checks/check_tex_assertions.py`

A figure may declare `tex_assertions` in `spec.yaml` (kept separate from the
rendered-text `semantic_assertions`):

```yaml
tex_assertions:
  - id: force-repels-not-attracts
    anchor_style: forceArr      # the tikz style naming the element to locate
    axis: x                     # x | y
    direction: decreasing       # increasing | decreasing
```

- **`find_styled_draw(tex_text, style) -> tuple | None | "ambiguous"`** — locate
  `\draw[…<style>…] (x1,y1) -- (x2,y2)` (regex over the source; the style token is
  matched word-bounded inside the option brackets). Returns the four coordinates;
  `None` when absent; a distinct ambiguous signal when the style matches more than
  one draw (the agent must then anchor more specifically).
- **`check_direction(coords, axis, direction, *, tol)`** — for `axis=x`,
  `increasing` ⟺ `x2 > x1`, `decreasing` ⟺ `x2 < x1` (symmetric for y); within
  `tol` of zero ⇒ indeterminate.
- **`check_tex_assertions(tex_text, assertions) -> list[issue]`** — per assertion:
  `anchor_missing` / `anchor_ambiguous` / `indeterminate` / `violated` / (silent on
  pass), mirroring `semantic_assertions`' issue contract.
- **`tex_assertions_payload` + `write_tex_assertions_json`** — stable JSON
  (`figure-agent.tex-assertions.v1`), and a `main()` CLI: reads the figure's
  `.tex` + `spec.yaml`, report-only by default, `--strict` exits non-zero on any
  violation, `--json-output`.

The checker reads ONLY the `.tex` (no render, no pdftotext) → robust and
deterministic. The physics MEANING (decreasing-x = away-from-the-right-electrode =
repulsion) is the agent's interpretation, baked into the declared `direction`; the
checker is purely mechanical.

### Anchoring decision

Anchor by **tikz style name** (`forceArr`), which the agent selects by reading the
`.tex`. The minimal version asserts the SIGN of a styled draw's own endpoints (the
arrow's direction) — self-contained, no cross-element reference needed. fig5's
attraction↔repulsion flip is caught exactly: `forceArr` decreasing-x ⟺ repulsion.

### Integration

Emit `build/tex_assertions.json` and a WARN line, alongside the other `build/*.json`
checks. A `compile.sh` hook is optional follow-on; the increment ships the checker
module + CLI + tests first (matching how `semantic_assertions.py` is structured and
tested independently of the compile wiring).

## Scope (YAGNI)

- **In:** direction-sign assertions on a single styled `\draw` (the fig5 force-
  direction class).
- **Out (until a real second case needs it):** cross-element relations (arrow vs a
  `\fill` electrode), multi-panel relations (P3/P4 bend opposite), curved-path
  direction. Add when a figure genuinely requires them.
- **Not reused:** label-relational `semantic_assertions` for directional facts — the
  probe proved it non-robust. (It stays for label-position facts like shallow-above-
  deep.)

## TDD increments

- **1 — primitive.** `find_styled_draw` + `check_direction` (pure, regex + sign;
  RED→GREEN; ambiguous/missing/indeterminate/violated/pass cases).
- **2 — checker + schema.** `parse_tex_assertions` (spec validation) +
  `check_tex_assertions` (issue list) + JSON payload. (RED→GREEN.)
- **3 — fig5 dogfood.** Author fig5's `force-repels-not-attracts` assertion; confirm
  the repulsion `.tex` PASSES and the attraction variant (from the probe) is
  `violated`. Throwaway attraction variant; do not commit it.

## Extension — `near` anchor disambiguation (SHIPPED, the fig3 case)

fig3_floating_clip_protocol's core novelty invariant — the +V-drive (P3) and
-V-drive (P4) Coulomb forces point in OPPOSITE x-directions (polarity-dependent;
same direction = the wrong, Hirai/Tamura-like figure) — was the "real second case"
that needed more than a single styled draw: both forces share the `forceArr` style,
so `find_styled_draws` returns two ⇒ `anchor_ambiguous`.

Resolved minimally by an optional `near: [x, y]` on an assertion. `select_draw`
picks the same-style draw whose START coordinate is within `NEAR_TOLERANCE_CM` (0.5)
of `near` (in tikz coords — no pixel/pdf mapping). Then "P3/P4 opposite" is two
ordinary direction assertions, each near-anchored to its own arrow — no new
cross-element relation primitive needed (YAGNI):

```yaml
tex_assertions:
  - id: p3-plus-drive-force-toward-electrode
    anchor_style: forceArr
    near: [11.05, 3.55]
    axis: x
    direction: increasing
  - id: p4-minus-drive-force-reversed
    anchor_style: forceArr
    near: [14.20, 3.55]
    axis: x
    direction: decreasing
```

Dogfood: correct fig3 = both PASS; a variant where P4's arrow is flipped to +x
(polarity-INDEPENDENT) = `p4-…-reversed` violated.

## Out of scope

- Layer 2's agent-authoring (reads docs → writes assertions) stays LLM; its
  deterministic backstop `check_physics_grounding` IS built (classifies grounded /
  declared_unenforced / undeclared).
- compile.sh / loop-gate wiring — optional follow-on.
- Explicit cross-element relation primitive (arrow vs `\fill`, curved-path
  direction) — still deferred; two near-anchored direction assertions covered the
  P3/P4 case without it.
- No new render-based or pixel-geometric checks (proven fragile).
