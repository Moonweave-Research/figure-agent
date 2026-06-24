# Nature-Grade Scientific Figures Without Hand-Iteration: Decision Report

> Produced 2026-06-21 by a keelplane research+adversarial-synthesis workflow (11 agents, 5 web-research angles → synthesis → 4 adversarial lenses → report). The adversarial pass **verified its claims against the actual repository** and materially changed the conclusion.

## 0. The verified bombshell (read this first)

The four adversarial reviewers independently verified, against the real artifacts:

1. **The safety scaffold is a NO-OP on every real figure.** `svg_semantic_diff` truth protection is gated on `element_id`; the `dvisvgm` exporter emits **no IDs on geometry paths**. Measured: `fig2`=75 `<path>`/**0 IDs**, `fig1`=461/0, `fig3`=50/0, `fig4`=43/0. The Fréchet bound, shape-signature check, occlusion guard, and render-ship divergence detector all **iterate an empty set and pass vacuously**. The ONLY truth-bearing SVG in the tree is the synthetic `_volume_shading_demo` (one hand-authored `<path id="electrode">` on an 80×80 canvas). **The locks have never run on a real figure.**
2. **The render-ship gate no-ops on real figures.** `_ship_svg_path` returns None unless `spec.final_artifact.kind == polished_svg`; no real fixture declares it → `render_ship_gate_failures` returns `[]` by structure, not by verification.
3. **The reference grounding assets don't exist.** `fig2/fig4 reference/` dirs contain only `.gitkeep`; `REFERENCE_GAP.md` says the most-relevant angle is "EMPTY. 0 PNGs."

Net: the months of safety-scaffold work (truth lock, occlusion guard, render-ship gate) only ever executed on hand-authored toy fixtures. This does not make the work wrong — a geometry truth-lock is *conceptually ahead of the literature* — but it is **not yet engaged on anything real**, and any claim that it makes a style layer "SAFE on real figures" is currently false.

## 1. Bottom line up front

**No fully-autonomous stack exists that produces Nature-grade materials/polymer/electrostatic-physics schematics today — not in research, not in production.** The realistic target is a **hybrid with a per-figure human gate**. The direction we were leaning toward (drive Inkscape on the "truth-locked" SVG, gated by a grounded MLLM taste-oracle) does **not** survive contact with our artifacts as written (truth-lock vacuous; Inkscape `--actions` is an unbounded mutator outside the audited op-set; probe presupposes IDs + reference images that don't exist).

**Recommended direction (adjusted):** pursue a **style-layer-on-correct-base hybrid**, but gate the entire investment behind a **disqualifying prerequisite probe** (do stable, geometry-level element IDs survive the TikZ→dvisvgm export across recompiles? today: no IDs at all). Reframe honestly: this is a **throughput/consistency aid for NEW, early-stage figures with real taste headroom** — NOT a hand-removing path to premium on figures whose physics/geometry defects (the cantilever case) live **inside** the topology fence a style layer is forbidden to touch. The human stays a **per-figure gate**, not a "rare" one.

## 2. The 2026 landscape

Every "publication-ready" claim in the field comes from an *easier* domain — biology, business/analytics charts, or AI/ML method flow-diagrams. Physics schematics (band diagrams, actuator cross-sections, trap-electrode geometry, polymer chains, field lines) are **out-of-distribution for the entire field**. Treat any "publication-ready" claim without a top-journal *physics* comparison as marketing (SciFig is the one honest measurement: 57.1% of human quality, a 13-pt gap).

**Solid (use it):**
- **Topology hallucination is a measured, field-wide failure**, worsening with complexity — SciFlow-Bench inverse-parses generated diagrams to graphs, shows "visually plausible but structurally incorrect" output (arXiv:2602.09809). Bedrock under the hard constraint; confirms a geometry truth-lock is conceptually ahead.
- **Reference-grounded MLLM judging works; ungrounded does not.** SciVisAgentBench: Pearson r≈0.80–0.81 vs experts **only with reference + rubric** (arXiv:2603.29139). Ungrounded collapses to 0.3–0.4 (VisJudge-Bench GPT-5 = 0.383 on aesthetics); critique ~40% wrong (ClaimCheck, EMNLP 2025). Triangulates our ~18% result three ways.
- **Pairwise beats absolute scoring** (MLLM-as-a-Judge ICML 2024; Chart-to-Experience; VisJudge): "which is more premium?" ≈78% human agreement; "rate 1–10" unreliable.
- **Self-revision is structurally dead** ("Revision Matters" arXiv:2406.18559): self-critique → echo chamber; expert *revision traces* (FID ~10 vs human ~6) move quality. External confirmation our critique→patch loop was not a prompt problem.

**Hype / research-only:** TikZ-synthesis LLMs (AutomaTikZ/DeTikZify/TikZero/TikZilla, +0.5–2/5 on reconstruction, never novel premium physics — re-skin of a falsified path); generative SVG + gen-image figure harnesses (VectorFusion, StarVector, OmniSVG, Recraft, FigureLabs, PaperBanana, Crafter ~50% win-rate, FigAgent 32.6% F1 — generate topology → violate the hard constraint). The one production existence-proof of Nature-grade-with-zero-topology-hallucination is **BioRender** (by construction; live MCP API) — but its 50,000 icons are all life-science; **physics coverage ≈ 0**.

## 3. Tech-stack families scored (adversarial-adjusted)

| Family | Works? | Truth-safety on OUR real artifacts | Hidden hand-cost | Domain fit | Leverages our scaffold? |
|---|---|---|---|---|---|
| **#1 Asset-composition (BioRender)** | Strongest production proof | Lowest by construction | High + recurring (build a physics library from scratch; re-risks idiom lock-in) | Coverage = 0 today | Partial; library-building is new |
| **#2 Imitation from expert edit-ops** | PSDesigner (CVPR 2026) + Revision Matters = highest-signal taste path | Medium; lock could fence to style-only *once it engages* | Highest (50–200 illustrator sessions; no sci-figure trace dataset) | Unvalidated; would be a real contribution | High in principle |
| **#3 Multimodal taste-oracle (grounded, pairwise, style-only)** | SciVisAgentBench r≈0.80 *grounded* | Lowest (judge never touches topology) | Low tooling, but recurring per-figure reference-pack tax (our ref dirs are empty) | Cross-domain transfer unproven; cheapest to test | Needs the reference+candidate the scaffold is supposed to produce |
| **#4 Drive pro vector tooling (Inkscape/Illustrator)** | Production tooling; style attrs orthogonal to path-d | **Zero only if scoped to in-process bounded ops by element ID — but fig2 has 0 IDs → ID-scoping structurally impossible today**; Inkscape `--actions` is an unbounded external mutator the scaffold never inspects | Per-op style library hand-built (today: exactly 1 op, `add_volume_shading`, next to *banned* `poster_gradient_decoration`) | High *if* it runs on a correct SVG base | Claimed, not real — locks only ran on the 80×80 demo |
| **#5 (new) StyleID / encode-once-propagate** (Adobe Firefly) | Production | N/A (no sci lock) | Medium | Concept transfers, tool doesn't | Conceptual only — informs #4's deliverable shape (a reusable style-spec) |
| **#6 (new) VFIG raster→SVG vectorizer** (arXiv:2603.24575) | VLM-Judge 0.829, RL on 66k arXiv pairs | Medium; novel-connectivity hallucination unquantified, no code | Low | Ingestion plumbing, not a quality ratchet | Neutral |

## 4. What we already falsified (do not loop back)
1. TikZ discipline alone → clean, not premium. (TikZ-synthesis LLMs = same path + hallucination risk.)
2. Python+SVG mixed libraries → "typography Frankenstein." (#4 is NOT this — it mutates presentation on an already-typeset base — but still isn't ready; see §0.)
3. Ungrounded LLM auto-critique→patch loop → inert + generic-drift (~18%, zero candidates). Confirmed structural by Revision Matters + ClaimCheck + VisJudge. The *grounded-pairwise-style-only* variant is a genuinely different mechanism, but its grounding asset doesn't exist for us yet.
4. Snippet/macro libraries → idiom lock-in. (#1 and any fixed primitive library re-risk this; primitives must be *parameterized, not idiomatic*.)
5. Generative-image-as-renderer → violates the hard topology constraint. Not a candidate in any form.

## 5. The recommended direction — adjusted to survive the adversarial pass

The original lead ("#4 on the truth-locked SVG, gated by #3; leverages your scaffold; provably zero topology risk; buildable today; no upfront cost") **does not survive** — every pillar is verified false on real artifacts (§0). What survives:

> **Build a style-layer-on-correct-base hybrid, gate the entire investment behind one disqualifying prerequisite, and reframe its purpose honestly.**

1. It is a **throughput/consistency aid for NEW, early-stage figures** — strictly additive polish on already-hand-correct geometry, never a finishing tool for ceiling figures, never a substitute for the element-iteration (sub-region) loop on physics/geometry.
2. The **human gate stays per-figure, not "rare."** LLM judges inflate absolute quality (~13 pts); they can *rank* but not *certify* Nature-grade.
3. **Three prerequisites, none met today, before any build:**
   - **(P1) Make the truth-lock actually engage:** a TikZ→semantic-SVG bridge emitting stable geometry-level element IDs + truth-bearing markers on the real figures (named TikZ nodes/scopes through dvisvgm, or a topology-correct re-ID post-processor, *without hand labeling*). Add a release gate asserting `truth_geometry` is **non-empty** for any figure entering the style layer (so vacuous passes become hard failures).
   - **(P2) Fence the executor:** forbid raw Inkscape `--actions`; route all style mutations through the bounded audited in-process op-set (translate ≤10px, stroke ratio 0.5–2.0, opacity ∈ [0,1]).
   - **(P3) Guard physics-encoding presentation attributes:** gradient/opacity/stroke-weight changes on field/charge/depth-bearing elements are **MAJOR** (a white→black Lambert ramp or per-element opacity can fabricate a depth/charge-density field or invented electrode asymmetry **without touching path-d** — the silent-lie surface the geometry lock is blind to). The oracle rubric must ask: *"does this style change imply a physical quantity not in the model?"*
4. **Family #2 (imitation learning) is the higher-ceiling long game** and the natural next investment once the style-layer hypothesis is proven; its 50–200-session data tax keeps it off the first bet.
5. **Family #1 only if** the probe shows parameterized style ops cannot reach premium AND you genuinely need pre-illustrated components (accepting idiom-lock-in re-risk).

**Hidden hand-work that remains:** per-op style library (recurring per lever, amortizes — acceptable); per-figure reference/§7 grounding (recurring per figure — acceptable **only if** principle-level grounding substitutes for matched images; else cost matches #1/#2 and the direction collapses); geometry/physics sub-region edits (**stays a human hand stream** — the honest concession; the hybrid speeds the first draft + style polish around it, it does not remove the hand).

## 6. Cheap falsification probe (~half a day, run IN ORDER; first is disqualifying)

**Probe A — ID-stability (disqualifying prerequisite; ~1–2h).** Input: one golden fixture (e.g. `fig2_trap_design_space`). Add named TikZ nodes/scopes to topology-bearing elements; export through dvisvgm **3×** (recompile between). Diff for element IDs. **Pass:** same stable geometry-level IDs on the same paths across all 3, mapping 1:1 to truth-bearing elements. **Kill:** IDs absent or drift → "scope style ops by element ID" is infeasible, the truth-lock cannot engage on real figures, **Family #4-by-ID is dead on arrival** → next dollar to **Family #2**.

**Probe B — taste-oracle transfer + addressable-fraction (only if A passes; ~3h).** Input: the **real** fig2/fig4 dvisvgm export end-to-end (a figure the user has NOT finished — fig1 is at ceiling, would confirm not discover). (1) Produce 4–6 style variants of identical topology; report how many of the N paths the style layer could address vs silently skip. (2) Frontier MLLM in **grounded pairwise** mode with **principle-level** grounding (decomposed Nature-convention rubric — hairline 0.25–0.5pt borders, ≤3–4 hue palette, sans-only, generous label margins), **not** a matched physics reference image (none exists). 6 variants = 15 pairwise calls → Bradley-Terry order. (3) User blind-ranks the same 6; compute Kendall's τ. **Pass:** high addressable fraction AND τ ≥ ~0.6 AND user top-1 ∈ oracle top-2, under principle-only grounding. **Kill:** τ < ~0.5 even with rubric → taste-oracle doesn't transfer, #3 dead, fall to #2. *Or* it only reaches r≈0.80 with matched in-domain images (which don't exist) → corpus tax matches #1/#2, cost advantage gone. **Optional same session:** feed the gate an intentionally topology-altering Inkscape action on the real figure; if not caught, #4-via-`--actions` is refuted for truth-safety regardless of taste.

## 7. Explicit non-goals / do-not-do
- Do NOT re-enter TikZ-synthesis LLMs (falsified path + hallucination risk).
- Do NOT use any generative-image/SVG model as the **renderer** of the factual artifact (permitted only as ideation, scoring, or non-topology style refinement).
- Do NOT ship the ungrounded / single-pass / absolute-scoring critique→patch loop (structurally dead, confirmed three ways).
- Do NOT build a fixed **idiomatic** primitive/snippet/macro library expecting premium (idiom lock-in). If #1 pursued, primitives must be **parameterized**.
- Do NOT claim the truth-lock / render-ship gate makes the style layer "SAFE on real figures" until **Probe A passes and `truth_geometry` is asserted non-empty** — today every lock passes **vacuously** on real artifacts (0 IDs on 75 paths).
- Do NOT allow raw Inkscape `--actions` (unbounded mutator) as the executor — only the bounded audited in-process op-set.
- Do NOT market this as **removing hand-iteration** or a **"rare gate"** to premium — premium-defining defects (geometry/physics) live inside the topology fence; the honest claim is **first-draft throughput + additive style polish on already-correct geometry, with a per-figure human gate.**
- Do NOT measure the probe on a ceiling figure (fig1) — it confirms a frozen optimum, tells you nothing about transfer.

**One-line decision:** No autonomous physics-schematic stack exists; commit to the **style-layer-on-correct-base hybrid with a per-figure human gate**, but spend **only one afternoon on Probe A (ID-stability) first** — if IDs don't survive the dvisvgm export, the entire Family-#4-by-ID direction is dead on arrival and the next dollar goes to **Family #2 (imitation from expert edit-ops)** as the sole remaining non-falsified source of taste.
