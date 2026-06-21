# Iteration-First Figure-Agent — Direction & Implementation Spec

> **Status:** canonical direction as of 2026-06-21. **Corrects the premise** of `2026-06-21-figure-agent-v2-svg-illustrator-design.md` (the "safety-scaffold-first / SVG-illustrator" line), which this session's research + architecture audit demoted as over-built for the actual lever.
> **Provenance (read these for full evidence):** `../2026-06-21-techstack-direction-decision.md`, `../2026-06-21-architecture-audit-decision.md`. Memory: `project_techstack_direction_2026_06_21`, `project_architecture_audit_2026_06_21`, `project_tool_value_dogfood_2026_06_21`, `feedback_element_iteration_workflow`.
> **One-line:** premium comes from the *volume* of cheap human element-iteration (not skill, not money, not autonomous AI); the tool's job is to amplify that loop and bank its output as reusable components — and the agent-driven loop must first be made to actually run-and-apply on real figures.

---

## 1. Research & prior art (what is settled — do not relitigate)

**2026 SOTA (web-researched, triangulated):** No system — research or production — autonomously produces Nature-grade *physics/materials* schematics; all "publication-ready" claims come from easier domains (bio / charts / ML-flow). Established, load-bearing facts:
- Topology hallucination is a measured field-wide failure (SciFlow-Bench) → a geometry truth-lock is conceptually right.
- Reference-grounded + *pairwise* MLLM judging works (SciVisAgentBench r≈0.80); ungrounded collapses (~0.38; our own ~18%); self-revision is structurally dead (Revision Matters). → AI can *rank* with grounding, cannot *generate or certify* premium.
- Generative image/SVG as the *renderer* violates the truth constraint. Permitted only as ideation / scoring / non-topology style.
- BioRender is the one production existence-proof of Nature-grade-zero-hallucination — by **asset composition** (humans pre-draw components) — but bio-only; physics coverage ≈ 0.

**Falsified by this team (never loop back):** TikZ-discipline-alone (clean ≠ premium); TikZ-synthesis LLMs (same path + hallucination); Python+SVG mixed libraries ("typography Frankenstein"); ungrounded / single-pass / absolute-scoring critique→patch loop (inert, ~18%); snippet/macro **idiomatic** libraries (idiom lock-in); generative-image-as-renderer; **native element-ID survival through `dvisvgm --pdf`** (Probe A: 0 ids; TikZ node-names + `dvisvgm:raw` both vanish; DVI-mode escape blocked by fontspec/Arial → PDF-only). Useful side-fact from Probe A: **dvisvgm path geometry is byte-stable across recompiles** (deterministic post-processing is reliable).

---

## 2. Goal, the core contradiction, and its resolution

**Ultimate goal:** Nature-grade physics/materials figures for publication with the human hand **minimized** (not eliminated — zero-hand does not exist in 2026).

**The core contradiction (named by the user):** *"I'm not a skilled illustrator — so how can premium come from my hand?"* Every "hand-once" path secretly assumed premium flows from the *user's* skilled hand. False.

**Resolution (the spec's foundation):** premium taste need not come from skill. It comes from the **volume of cheap, tool-assisted element-iteration** — `eye → 1-line patch → recompile → eye → …` — repeated per element until premium. **Iteration substitutes for innate skill.** What the user has (time, eye/judgment, domain knowledge) is exactly the input this loop needs; what they lack (illustration skill, budget) it does not require. Evidence: fig1 reached near-Nature via **20+ human sub-region iterations**; "engine is not the ceiling" (drop-shadow/specular/ambient-occlusion all closed via TikZ iteration). The premium primitive, built once via iteration, is then **banked and reused (composed)** across figures — so the hand amortizes (the user's figures reuse primitives: electrode, polymer chain, MIM stack, band diagram, cantilever, field lines recur across fig1–5).

---

## 3. Product position & non-goals

**The tool is NOT:** a premium-drawer (AI can't generate premium; the user can't one-shot it); an auto-improver (the auto-loop is empirically inert — see audit). 

**The tool IS:** an **iteration amplifier + component bank**. Its job, precisely:
1. Make each element-iteration **cheap, fast, safe, well-judged** (fast recompile, concrete `file:line` targets, micro-crops, safe apply, correctness locks).
2. Feed the human eye exactly what to look at (per-sub-region crops + adjudicated detector findings).
3. Apply human-approved 1-line patches safely and recompile.
4. **Bank** completed premium elements as **parameterized reusable components**; compose them into new figures.
5. Lock correctness (no silent scientific lie) — on substrates where the locks are non-vacuous.

**Non-goals:** zero-hand autonomy; generative-image renderer; the SVG-post-process polish workflow + its safety half (demote/quarantine — never ran on a real figure); autonomous taste generation; commissioning external illustrators (the user's chosen resolution is *their own* iteration, not paid pros); broad orchestration expansion until the core loop is robust.

---

## 4. Architecture (corrected by the 2026-06-21 audit)

**Build ON (genuinely solid, works on real figures):**
- Base `compile.sh` → lualatex → PDF → `export_svg.sh` (dvisvgm) → 7 detectors. Reliable.
- **`candidate_apply` engine + CLI** (`bin/fig-agent:876` → `candidate_apply.apply_candidate`) — the most robust piece; provably mutated `fig1.tex` + recompiled rc=0, with sha256 drift guard + `O_EXCL` mutation lock + rollback + exactly-once. **This is the element-iteration lever, already built.**
- Render-based detectors (`visual_clash` via pdftoppm, `undeclared_geometry` via pdfplumber) — fire on all 5 real figures.
- fig1's 108-crop **hash-bound** audit manifest — the micro-inspection model to generalize.
- `semantic_assertions` — the one real deterministic scientific-validity check (fig4).
- Report-only critique discipline + human-gate boundary.

**Quarantine / demote (over-built; never runs on a real figure; serves a workflow we're not pursuing):** the SVG-semantic half — `svg_polish_*`, `svg_ship_gate`, `svg_semantic_diff` truth path, occlusion guard, render-ship gate (**incl. this session's Plan 3 + Plan 4**) — vacuous because `dvisvgm --pdf` emits 0 geometry ids. The auto-generation/auto-patch layer (`candidate_generator`, `quality_patch_plan/apply`, SAFE_CLASSES) — toy-bound; automation is not the lever.

**Target architecture — the agent-driven element-iteration loop:**
```
detect (render-detectors fire) → adjudicate/surface (file:line + micro-crop, human-curated) →
human eye judges → propose bounded 1-line patch → human approves →
apply (candidate_apply, via MCP front door) → recompile → re-detect →
… (repeat per sub-region) … → when a primitive reaches premium → extract to component bank →
compose banked components into new figures (correctness locks now non-vacuous: authored components carry ids)
```

---

## 5. Execution model

- **Iteration unit = sub-region** (5–8 per panel), not panel, not whole figure (validated: `feedback_subregion_iteration_unit`).
- **Roles:** the *agent* runs the loop mechanics — detect, surface concrete `file:line` + micro-crops, propose the bounded patch, apply (after approval), recompile, re-surface. The *human* supplies the only thing that can't be automated: the per-sub-region premium judgment ("is this element premium yet?").
- **Premium levers:** each iteration must be able to reach *premium*, not just *clean* — so the bounded-patch/op set must include depth/gradient/line-weight-tier/texture levers (`add_volume_shading` is lever #1, repurposed from "safety demo" to "iteration lever"). Without rich levers the loop plateaus at clean.
- **Component banking:** when a primitive is premium, extract it as a **parameterized** (not idiomatic) reusable component with real element ids → drop into new figures via composition. This is where the correctness locks finally have id-bearing input and stop being vacuous.

---

## 6. Safety & verification gates

- **Apply safety (exists, reuse):** `candidate_apply`'s sha256 source-drift guard + `O_EXCL` mutation lock + rollback patch + exactly-once `replace_text` + post-apply compile/export. The MCP refusal (B1) is redundant with these.
- **Correctness locks made real:** native ids are dead on dvisvgm output (Probe A). The locks become non-vacuous **only on authored/composed components** (which carry ids by construction) — so wire the truth/occlusion checks to run on the component-bank substrate, and add a release assertion that `truth_geometry` is **non-empty** before claiming a figure was lock-checked. Never advertise a gate as "safe on real figures" while it passes vacuously.
- **Scientific validity:** generalize `semantic_assertions` (today fig4-only, hidden) — surface it in `status`, template a block into every multi-panel figure, error on duplicate anchors.
- **Honesty gate:** `propose`/`next` must not return `success:true` envelopes for no-ops (misleads an orchestrating agent into believing it acted).

---

## 7. Evaluation fixtures & probes

- **Probe A — DONE.** Native ID survival through `dvisvgm --pdf` = dead (0 ids; raw-special + node-name vanish; DVI blocked by fontspec). Geometry byte-stable across recompiles. → ID-scoping must come from authored components, not export.
- **B1 acceptance probe (gates "agent-driven ready"):** tell an agent "use the figure-agent" on a real figure → it must `propose → apply → recompile` a candidate end-to-end via the MCP front door, with the diff landing in the `.tex` and a clean recompile. Pass = the acceptance bar is met.
- **#1-amortize probe (gates the component-bank investment):** hand-iterate ONE recurring primitive (polymer chain or electrode) to premium; measure (a) does iteration cross clean→premium, (b) how many iterations (the economics), (c) does it extract to a parameterized component reusable in 2 different figures without redraw. Pass → build the bank. Too expensive → reconsider.

---

## 8. Implementation plan (step-by-step slices; each TDD + subagent-driven + clean-checkout proof)

**Slice 0 — Make the agent-driven loop actually run-and-apply (the audit's blockers).** Highest leverage; this is the acceptance bar.
1. **B1** — wire MCP `figure_agent_apply_candidate` → the existing `candidate_apply` engine, behind the existing acceptance/drift/lock gates. (Converts verify-only → operates+applies.) *Non-negotiable, first.*
2. **B2** — `quality_defect_ledger` ingests the render-detectors (`visual_clash`, `undeclared_geometry`, `label_path`) behind an adjudication gate; normalize via `quality_patch_policy.classify_patchability` so an accepted finding becomes an actionable, addressable defect with a concrete `file:line`.
3. **B4** — decouple micro-crop + critique from reference-gating: fire a "micro/critique required" state whenever `audit_crops/manifest.json` or unadjudicated detector candidates exist; route `next` → `/fig_critique` when `unadjudicated_candidate_count > 0`. (Makes judgment + zoom run on fig2–5.)
4. **B3 / handoff** — have the ledger emit `file:line` + a suggested bounded 1-line patch the human (or agent-after-approval) can apply; stop returning `unsupported_defect` into a void.
5. **Generalize `candidate_families`** — derive panels/families/label-targets from `spec.yaml` + node text (not constants + a 5-string allowlist); parameterize the offset, so the working apply path reaches fig2–5.
6. **Detector noise hygiene** — demote bare `undeclared_*` to INFO corpus-wide; re-tune `_known_false_positives.yaml`; honest per-figure caps. (~90% noise today.)
7. **Resolve the RED `test_real_fixture_audit_adoption` honestly**; add render-behavior regression tests vs committed `build/*.pdf`; add a small labeled TP/FP ground-truth set so detector tuning is measurable.
8. **Surface `semantic_assertions`** in `status`/`next`.

> Slice-0 exit = the **B1 acceptance probe passes** AND on fig2 the agent can: surface adjudicated `file:line` targets + micro-crops → propose a bounded patch → apply → recompile clean.

**Slice 1 — Premium levers for iteration.** Expand the bounded op/lever set so each iteration can reach premium (depth/gradient/line-weight tiers/texture). `add_volume_shading` repurposed as lever #1; add the next 2–3 levers driven by what real fig2/fig1 sub-regions actually need. Each lever = a parameterized, bounded, truth-safe op.

**Slice 2 — Component bank + composition (probe-gated by #1-amortize).** Extract iteration-completed premium primitives as parameterized reusable components (with real ids); composition layer to drop them into new figures; the correctness locks finally engage on this id-bearing substrate. Build only after the #1-amortize probe confirms the economics.

**Slice 3 — Quarantine the dead weight.** Remove/hide the inert SVG-semantic + auto-patch machinery from the agent-facing surface (lowest priority — inert, not harmful, but it misleads about guarantees). Either prove one polish recipe on an id-bearing component or stop advertising geometry truth-lock on real figures.

---

## 9. Open risks (track)
1. **Economics of iteration** (#1-amortize probe): if premium costs too many iterations per element, the whole direction is too expensive — the one quantitative unknown. Run the probe before Slice 2.
2. **Levers may plateau at clean** (Slice 1): if the bounded ops can't reach premium, iteration won't either. Mitigate: "no preemptive engine-ceiling claims — list ≥3 unused techniques before declaring a ceiling."
3. **Adjudication burden** (B2/B4): surfacing 28 candidates of which ~90% are noise risks drowning the human eye — detector hygiene is load-bearing, not optional.
4. **Component genericity** (Slice 2): parameterized-not-idiomatic is the dividing line vs the falsified snippet lock-in; bespoke figure novelty may exceed any library.
5. **Honest scope:** this minimizes the hand; it does not remove it. The premium-defining judgment stays a per-sub-region human stream. Market it as such, never as "rare gate" or "hand-free."

---

## 10. Non-goals (explicit, so we don't loop back)
TikZ-synthesis LLMs · generative-image/SVG as renderer · ungrounded/single-pass/absolute-scoring critique loop · idiomatic snippet/macro libraries · native-id-from-dvisvgm scoping · raw Inkscape `--actions` as executor · claiming vacuous gates are "safe on real figures" · autonomous premium generation · paid-illustrator dependency · broad orchestration expansion before Slice 0 is robust.
