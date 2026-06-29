# Multi-lens figure QA — ad-hoc recipe (NOT yet a product)

A pattern, not a feature. Run it by spawning parallel review agents (Agent tool); each
reads the build PNG + .tex + briefing through ONE lens and returns a tight, concrete
review. Then dedupe across lenses — a finding that ≥3 independent lenses raise is
high-confidence. Validated once on fig3_resistance (2026-06-29): it caught a glyph
regression the single eye had introduced (×→○) at 4/4 consensus and converged on an
equal-area fix none of the single passes had named.

**Do NOT productize off this.** It is already free to run ad-hoc. Earn a `/fig_critique
--panel` extension only after it pays off on ≥3 figures, the useful lenses are known
(prune the rest), and an integration point is clear. Lives in figure-agent (extends the
single-lens `/fig_critique`), not figops.

## Lenses (4, run in parallel)

1. **NC publication art-editor** — execution to Nature house style: line weights, glyph
   choice, inset proportion/integration, label placement & hierarchy, whitespace, stroke
   & palette consistency. What separates this from a *published* schematic.
2. **Non-specialist reader** — look at the PNG COLD (before the briefing); can the
   mechanism be grasped unaided? Pinpoint where a reader misreads a glyph or an element.
3. **Alternative-representation designer** — for each key element, propose 1–2 alternative
   representations with pros/cons vs the current choice + a pick. (Use when the author
   doubts the current choices are optimal.)
4. **Physics-honesty skeptic** — does the render convey the physics without over-claiming?
   Flag any element that could mislead (a glyph implying a charge sign, a linear inset
   implying exponential not power-law, height/depth implying magnitude).

## Shared context block (prepend to every lens)

- What the figure IS (genre, which half — schematic vs data — it owns).
- Absolute paths: build PNG, .tex, briefing.md (+ its binding physics rules).
- A one-line statement of what each panel intends to convey.
- CONSTRAINTS: which content is in flux (QA the *representation*, not flux content);
  the binding physics rules the figure must not violate.
- Return format: 3–6 findings as `ELEMENT | ISSUE | SEVERITY | CONCRETE FIX/ALTERNATIVE`
  + a 1-line VERDICT (biggest single lever). "Your final message IS the deliverable."

## Synthesis

Tabulate findings × lenses; sort by how many lenses independently raised each. Apply the
unanimous/settled ones immediately; surface representation *choices* (and anything that
touches flux content) to the author as decisions.
