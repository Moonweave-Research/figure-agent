---
description: Ground a figure's physics intent — read the briefing §6/§7 + research docs, author tex/semantic assertions, and verify they hold. Formalizes Layer 2 of the physics-correctness loop.
---

Connect a figure's documented physics intent to machine-checkable assertions, so a
reversed force/bend direction — which no render detector and no visual pass catches
(see fig5: attraction drawn where the novelty was repulsion) — becomes a fail-loud
failure.

**Usage**: `/fig_ground <name>`

`<name>` maps to `examples/<name>/`. The two checks run automatically inside
`fig-agent compile`, which emits `examples/<name>/build/physics_grounding.json`
(meta-check) and `examples/<name>/build/tex_assertions.json` (enforcement).

Steps:

1. **Surface the grounding status.** Run `fig-agent compile <name>` and read
   `examples/<name>/build/physics_grounding.json`:
   - `grounded` — the intent is already enforced; stop.
   - `undeclared` — the briefing has no "Physics invariants" section; the figure
     leans on general physics. If it has directional physics worth guarding, add a
     briefing §6, then continue.
   - `declared_unenforced` — invariants are declared in prose but unguarded; continue.

2. **Read the intent.** Open `examples/<name>/briefing.md` §6 "Physics invariants" /
   §7 "Author intent", and the research plan it links (e.g. the manuscript figure
   plan). Extract the invariants that are mechanizable:
   - **directional** — a force/bend arrow points a specific way (repulsion = away
     from the electrode; capture = toward the deep trap).
   - **label-relational** — one labelled element sits above / left-of another
     (shallow above deep).
   With no docs, fall back to general physics for the same facts.

3. **Author the assertions** in `examples/<name>/spec.yaml`:
   - directional draw facts → `tex_assertions` (read the `.tex` to find the draw;
     anchor by `anchor_style` if it has a named style, else by `near: [x, y]`;
     give `axis` + `direction`).
   - label-relational facts → `semantic_assertions` (`relation` above/below/
     left_of/right_of + `subject` + `reference` label tokens).

4. **Verify.** Re-run `fig-agent compile <name>` and read the two JSON artifacts:
   `tex_assertions.json` must show no `violated` / `anchor_missing` /
   `anchor_ambiguous`, and `physics_grounding.json` `status` must read `grounded`.

5. **Stay honest.** Not every invariant is mechanizable (slope steepness, cluster
   separation, structural layout). Encode what is; leave the rest to human review —
   never force a fake assertion just to flip the status.
