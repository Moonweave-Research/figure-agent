# Iteration-First Figure-Agent — Direction & Implementation Spec

> **Status:** canonical direction as of 2026-06-21 (rev 2 — hole-reviewed by 3 adversarial passes, all code refs verified live). **Corrects the premise** of `2026-06-21-figure-agent-v2-svg-illustrator-design.md` (the "safety-scaffold-first / SVG-illustrator" line), which this session's research + architecture audit demoted as over-built for the actual lever.
> **Provenance (full evidence):** `../2026-06-21-techstack-direction-decision.md`, `../2026-06-21-architecture-audit-decision.md`. Memory: `project_techstack_direction_2026_06_21`, `project_architecture_audit_2026_06_21`, `project_tool_value_dogfood_2026_06_21`, `feedback_element_iteration_workflow`.
> **One-line:** premium comes from the *volume* of cheap human element-iteration (not skill, not money, not autonomous AI); the tool's job is to amplify that loop and bank its output as reusable components — and the agent-driven loop must first be made to actually run-and-apply on real figures.

---

## 0. Entry point (read this first; for the agent executing this spec)

- **This file is the canonical direction.** If multiple specs exist in `docs/superpowers/specs/`, this one (rev 2026-06-21) supersedes the v2-svg-illustrator spec's premise. Start here.
- **Start work at §8 Slice 0.** Slice 1+ are **blocked** until the §8 gates pass (see "Slice gates"). Do not begin Slice 1/2 first.
- **Working method (applies to every step):** superpowers:test-driven-development (write the failing test first) + superpowers:subagent-driven-development (fresh implementer per task + spec-compliance then code-quality review) + a clean-checkout proof before declaring a slice done.
- **Runtime rule:** ALL python/tool invocations use `uv run` (a repo hook blocks bare `python3`). Run from `plugins/figure-agent/`. Tests: `uv run pytest tests/ -q`. Clean-checkout proof: `git worktree add --detach /tmp/<new> <HEAD> && cd /tmp/<new>/plugins/figure-agent && uv sync && uv run pytest tests/ -q` (expect 0 failed in a clean checkout), then `git worktree remove --force`.
- **"Slice 0 done" is this exact command sequence (the acceptance bar), not prose:** see §7 "Slice-0 exit probe". It runs on **fig2_trap_design_space** and requires B3 (below) to have landed.
- **Code refs in this spec were verified live 2026-06-21**; if a line number drifted, grep the named symbol (line numbers are hints, symbol names are truth).

---

## 1. Research & prior art (settled — do not relitigate)

**2026 SOTA (web-researched, triangulated):** No system — research or production — autonomously produces Nature-grade *physics/materials* schematics; all "publication-ready" claims come from easier domains (bio / charts / ML-flow). Load-bearing facts:
- Topology hallucination is a measured field-wide failure (SciFlow-Bench) → a geometry truth-lock is conceptually right.
- Reference-grounded + *pairwise* MLLM judging works (SciVisAgentBench r≈0.80); ungrounded collapses (~0.38; our own ~18%); self-revision is structurally dead (Revision Matters). → AI can *rank* with grounding, cannot *generate or certify* premium.
- Generative image/SVG as the *renderer* violates the truth constraint. Permitted only as ideation / scoring / non-topology style.
- BioRender is the one production existence-proof of Nature-grade-zero-hallucination — by **asset composition** (humans pre-draw components) — bio-only; physics coverage ≈ 0.

**Falsified by this team (never loop back):** TikZ-discipline-alone; TikZ-synthesis LLMs; Python+SVG mixed libraries ("typography Frankenstein"); ungrounded/single-pass/absolute-scoring critique→patch loop (~18%); snippet/macro **idiomatic** libraries (idiom lock-in); generative-image-as-renderer; **authored element-ID survival through `dvisvgm --pdf`** (Probe A: 0 authored ids — dvisvgm emits only a content-free `page1` wrapper `<g>`; TikZ node-names + `\special{dvisvgm:raw}` both vanish; the DVI-mode escape is blocked by `fontspec`/`\setmainfont{Arial}` → PDF-only). Probe A side-fact: **dvisvgm path geometry is byte-stable across recompiles** (deterministic post-processing is reliable).

---

## 2. Goal, the core contradiction, and its resolution

**Ultimate goal:** Nature-grade physics/materials figures for publication with the human hand **minimized** (not eliminated — zero-hand does not exist in 2026).

**The core contradiction (named by the user):** *"I'm not a skilled illustrator — so how can premium come from my hand?"* Every "hand-once" path secretly assumed premium flows from the *user's* skilled hand. False.

**Resolution (the foundation):** premium need not come from skill. It comes from the **volume of cheap, tool-assisted element-iteration** — `eye → 1-line patch → recompile → eye → …` — repeated per sub-region until premium. **Iteration substitutes for innate skill.** The user supplies time + eye/judgment + domain knowledge (which the loop needs); not illustration skill or budget (which it does not). Evidence: fig1 reached near-Nature via **20+ human sub-region iterations**; "engine is not the ceiling." The premium primitive, built once via iteration, is then **banked and reused (composed)** across figures (electrode, polymer chain, MIM stack, band diagram, cantilever, field lines recur across fig1–5) — so the hand amortizes.

---

## 3. Product position & non-goals

**The tool is NOT:** a premium-drawer (AI can't generate premium; the user can't one-shot it); an auto-improver (the auto-loop is empirically inert — audit). 

**The tool IS** an **iteration amplifier + component bank**: (1) make each element-iteration cheap/fast/safe/well-judged; (2) feed the human eye exactly what to look at (per-sub-region crops + adjudicated detector findings); (3) apply human-approved bounded `.tex` patches safely + recompile; (4) bank completed premium elements as **parameterized** reusable components and compose them; (5) enforce correctness by the means that actually work on real figures (render-detectors + `semantic_assertions` + human review — NOT the id-gated SVG locks; see §6).

**Non-goals:** zero-hand autonomy; generative-image renderer; the SVG-post-process polish workflow + its id-gated safety half (quarantined — never ran on a real figure, and cannot, per Probe A); autonomous taste generation; paid-illustrator dependency; broad orchestration expansion before Slice 0 is robust.

---

## 4. Architecture (corrected by the 2026-06-21 audit; line refs verified live)

**Build ON (genuinely solid, works on real figures):**
- Base `scripts/compile.sh` → lualatex → PDF → `scripts/export_svg.sh:44` (`dvisvgm --pdf`) → 7 detectors. Reliable.
- **`candidate_apply` engine + CLI** — `bin/fig-agent:876` (`_apply_candidate`) → call at `:892` → `scripts/candidate_apply.py:341` (`apply_candidate`). **Supports ONLY `replace_text` on `.tex`** (`candidate_apply.py` ~:239, "only replace_text is supported"), with sha256 source-drift guard + `O_EXCL` mutation lock + rollback patch + exactly-once + post-apply compile/export. Provably mutated `fig1.tex` + recompiled rc=0. **This is the element-iteration lever, already built — and it is a `.tex`/`replace_text` engine, NOT an SVG engine.**
- Render-based detectors (`visual_clash` via pdftoppm, `undeclared_geometry` via pdfplumber) — fire on all 5 real figures (no id dependency).
- fig1's 108-crop **hash-bound** audit manifest — the micro-inspection model to generalize.
- `scripts/semantic_assertions.py` — the one real deterministic scientific-validity check (fires on fig4).
- Report-only critique discipline + human-gate boundary.

**Quarantine / do NOT resurrect (over-built; vacuous on real figures; cannot engage in this direction):** the id-gated SVG-semantic half — `svg_polish_*`, `svg_ship_gate`, `svg_semantic_diff` truth path (`:305` gate `if d and truth_bearing and element_id:`), occlusion guard, render-ship gate (**incl. this session's Plan 3 + Plan 4 + `add_volume_shading`**). All need authored element-ids that Probe A proved dead on real dvisvgm output. The auto-generation/auto-patch layer (`candidate_generator.py:169`, `quality_patch_plan/_default_patch:42`, `quality_patch_policy.py:65` `may_edit:False`, SAFE_CLASSES) — toy-bound (only single-line-`(0,0)` synthetic fixtures); automation is not the lever.

**Target architecture — the agent-driven element-iteration loop (all on the `.tex`/`replace_text`/render substrate, no ids):**
```
render-detect (works on real figs) → adjudicate/surface (file:line + micro-crop, human-curated) →
human eye judges sub-region → propose bounded replace_text patch on .tex → human approves →
apply (candidate_apply, via MCP front door) → recompile → re-detect →
… repeat per sub-region … → when a primitive is premium → bank it (substrate TBD, §8 Slice 2) → compose
```

---

## 5. Execution model

- **Iteration unit = sub-region** (5–8 per panel), not panel, not whole figure (`feedback_subregion_iteration_unit`).
- **Roles:** the *agent* runs loop mechanics — render-detect, surface concrete `file:line` + micro-crops, propose the bounded `replace_text` patch, apply (after human approval), recompile, re-surface. The *human* supplies the per-sub-region premium judgment.
- **Premium levers (corrected — BLOCKER fix):** `add_volume_shading` is NOT a lever for this loop — it is SVG-substrate machinery (`scripts/add_volume_shading.py:71` takes an SVG string + element-id, emits `.polished.svg`; quarantined per §4). It only proves *conceptually* that "depth is a premium lever." Slice 1 must author **NEW premium levers as `replace_text`-expressible TikZ source ops** (e.g. `\shade`/`\shadedraw` gradients, `\path[...]` depth fills, line-weight tiers, cel bands) that edit the `.tex` and survive `candidate_apply`. Without rich TikZ levers the loop plateaus at clean.
- **Component banking (substrate is an OPEN question — see §8 Slice 2):** in the `.tex` world there are no surviving ids, so a banked component is most likely a **parameterized TikZ macro** reused at source level (composition = macro calls, ids irrelevant). The risk: a TikZ macro bank is exactly the falsified snippet/macro path unless genuinely **parameterized, not idiomatic**. This tension is unresolved and gates Slice 2 (do not build the bank before the #1-amortize probe resolves it).

---

## 6. Safety & verification gates (corrected — BLOCKER fix)

**In the `.tex`/`replace_text` direction there are NO authored element-ids, ever (Probe A). Therefore the id-gated SVG locks (truth-lock / occlusion / render-ship in `svg_semantic_diff`) can NEVER be non-vacuous here.** Drop the earlier "locks made real on composed components" claim. Correctness is enforced by the means that work on the real substrate:
- **Apply safety (exists, reuse):** `candidate_apply`'s sha256 drift guard + `O_EXCL` mutation lock + rollback + exactly-once `replace_text`. The MCP refusal (B1) is redundant with these.
- **Render-detectors** (visual_clash, undeclared_geometry, label_path) — geometry/overlap checks on the rendered PDF/raster, no ids needed. Work on real figures.
- **`semantic_assertions`** (value/relation level) — the deterministic scientific-validity check. Must be generalized (B5/§8) and **gated**: a multi-panel figure entering acceptance without a `semantic_assertions` block is a BLOCKER (acknowledge the per-figure human authoring cost — §9 risk).
- **Human review** at the per-sub-region gate (premium + physics judgment).
- **Honesty gate:** `propose`/`next` must NOT return `success:true` envelopes for no-ops (today they do; this misleads an orchestrating agent into believing it acted — audit D10-08).
- **Do NOT advertise** any id-gated SVG lock as "safe on real figures" — it passes vacuously (`truth_geometry` empty). If the SVG half is ever revived, it must run only on an id-bearing substrate and assert `truth_geometry` non-empty first.

---

## 7. Evaluation fixtures & probes (concrete pass/fail)

- **Probe A — DONE.** Authored-id survival through `dvisvgm --pdf` = dead (0 authored ids; only a `page1` wrapper; raw-special + node-name vanish; DVI blocked by fontspec). Geometry byte-stable across recompiles.
- **B1a probe — engine wired (runs on fig1, no B3 needed):** `fig1_overview_v2_pair_001_vault` already has committed `build/candidates/`. PASS = the MCP `figure_agent_apply_candidate` tool applies an existing fig1 candidate end-to-end (diff lands in `fig1*.tex`, `uv run python bin/fig-agent compile fig1_overview_v2_pair_001_vault --strict` rc=0), running the existing acceptance/drift/lock gates (not bypassing them).
- **Slice-0 exit probe — generalized (runs on fig2; B3 is the gating prerequisite):** PASS = `uv run python bin/fig-agent propose fig2_trap_design_space` yields **≥1 operation** (today it yields `operations:[]` + `unsupported_defect`) → a candidate dir is produced → MCP `figure_agent_apply_candidate` applies it → `uv run python bin/fig-agent compile fig2_trap_design_space --strict` rc=0. This is "Slice 0 done."
  - **B3 RESOLVED-VIA-REPLACEMENT (recorded 2026-06-25):** the live `propose` front door is now `quality_patch_plan.build_quality_patch_plan` (called in `bin/fig-agent`, ~:585), which bypassed `candidate_families` entirely. The live gating concern for this exit probe is therefore whether `quality_patch_plan` yields **≥1 defect-driven operation** on fig2 — NOT whether `candidate_families` is generalized off `SUPPORTED_PANEL="C"`. The engine identity moved off `candidate_families`; Slice 0 is **NOT** done — `propose fig2_trap_design_space` yielding ≥1 defect-driven operation remains the open Slice-0 BLOCKER (review §8.1).
- **#1-amortize probe (gates Slice 2; split to avoid circularity):** (a)+(b) run pre-Slice-2 with NO composition layer — hand-iterate ONE recurring primitive (polymer chain or electrode) to premium; measure (a) does iteration cross clean→premium, (b) how many iterations (the economics). (c) is a Slice-2 *checkpoint* (not gate): the banked component drops into a 2nd figure without redraw. Pass (a)+(b) → build the bank; then (c) validates it.
  - **PROBE RESULT (run 2026-06-22, recorded 2026-06-25):** (a) clean→premium crossing = **YES**; (b) economics = **~4 cheap 1-line edits** on a STANDALONE polymer/polysulfide zigzag-chain primitive (NOT a real figure); (c) cross-figure drop-in checkpoint **still PENDING**. (a)+(b) PASS → unblocks building the bank; (c) remains an open Slice-2 checkpoint. This is a RESULT record, not a waiver.

---

## 8. Implementation plan (step-by-step; each step: TDD + subagent-driven + `uv run` + clean-checkout proof)

### Slice 0 — Make the agent-driven loop run-and-apply (the audit's blockers)

- **B1 — wire MCP apply → `candidate_apply`.** Replace the hard refusal `apply_requires_cli_opt_in` (`mcp/figure_agent_server.py:1368`, in `_apply_candidate` ~:1341) with a call to the same `candidate_apply.apply_candidate` the CLI uses (`bin/fig-agent:892`). **Resolve the input gap (spec-exec finding):** the engine REQUIRES `candidate_set_path` + `acceptance_path`, but the MCP tool's `inputSchema` (`mcp/figure_agent_server.py:1806`) declares only `name`+`candidate_id`. Define how MCP resolves these (e.g. canonical `build/candidates/{candidate_id}/{candidate_set.json,acceptance.json}`) AND require the acceptance gate to actually run (do NOT bypass it). Test-first: an MCP apply on a fig1 candidate mutates the `.tex` + recompiles clean (= B1a probe). 
- **B2 — defect ledger ingests render-detectors.** `quality_defect_ledger.py:81` opens only `text_boundary_clash.json` (0 candidates corpus-wide). Add ingestion of `visual_clash.json` + `undeclared_geometry.json` (+ `label_path_proximity`) behind an **adjudication gate** — reuse `scripts/critique_adjudication.py` (name the exact fn; do not invent a parallel gate) — normalized through `quality_patch_policy.classify_patchability:30`. Acceptance test: an adjudicated fig2 visual_clash becomes a ledger defect carrying a concrete `file:line`.
- **B4 — decouple micro-crop + critique from reference-gating.** The gate is `status.py:116` (`compute_critique_state` returns `NOT_REQUIRED` when no figure/panel reference is declared). Add a state that fires "micro/critique required" whenever `build/audit_crops/manifest.json` exists OR `unadjudicated_candidate_count>0` (`audit_evidence_summary.py:468`), and route `next` → `/fig_critique` there (routing lives in `status_explanation.py:122/131/147`). Acceptance test: fig2 (no reference) routes to critique because its audit_crops manifest / unadjudicated count is non-zero.
- **B3 — generalize `candidate_families` (THE gating prerequisite for the Slice-0 exit).** Today hard-bound: `candidate_families.py:18` `SUPPORTED_PANEL="C"`, `:16` `SUPPORTED_FAMILY="energy-trap-alignment"`, `:17` `KNOWN_UNSUPPORTED_PANEL_FAMILIES={"plot-marker-hierarchy"}` (fig2's family — explicit refusal), `:20` `ENERGY_TERMS` 5-string allowlist; and the patch body `quality_patch_plan._default_patch:42` only edits single-line-`(0,0)` toys. Replace constants with derivation from `spec.yaml` (panels[]) + node text, and the patch body with a **selector-based bounded-coordinate `replace_text`** applicator (node-name / line-range, bounded offset). Define: target fn signature, which `spec.yaml` keys feed it, and a test asserting `propose fig2_trap_design_space` yields **≥1 operation**.
  - **RESOLVED-VIA-REPLACEMENT (recorded 2026-06-25):** the live `propose` engine moved to `quality_patch_plan.build_quality_patch_plan` (in `bin/fig-agent`, ~:585), which bypassed `candidate_families`. B3 as literally written (generalize `candidate_families` off `SUPPORTED_PANEL="C"`) is **superseded** — the live gating concern is now whether `quality_patch_plan` yields **≥1 defect-driven operation** on fig2 (still the open Slice-0 BLOCKER per review §8.1). This records that the engine identity moved off `candidate_families`; it does NOT claim Slice 0 is done.
- **B3-handoff (if auto-apply stays out of scope):** when the ledger can't auto-author a patch, emit a concrete `file:line` + a suggested 1-line `replace_text` patch for the human, instead of `unsupported_defect` into a void.
- **Detector noise hygiene (after the metric exists — reordered):** first add a small labeled TP/FP ground-truth set (moved earlier so hygiene is measurable), then demote bare `undeclared_*` to INFO corpus-wide, re-tune `_known_false_positives.yaml`, set honest per-figure caps; **pass criterion: FP rate below a stated threshold on the labeled set** (~90% noise today).
- **Resolve the RED `test_real_fixture_audit_adoption` honestly (reframed — spec-exec finding):** the failure is **missing `adoption_status` entries** for fig2–5 in `tests/real_fixture_audit_adoption.yaml` (not detector-tuning). Per fixture, make an honest `adoption_status` judgment (the enum's 5 values, each with rationale + conditional reference/check-id requirements). Decision rule: a fixture is `adopted` only if it has a real reference or a declared deterministic check; otherwise the honest status (NOT a blanket `not_applicable_no_reference` to force green — that is the dishonesty the test guards against). Add render-behavior regression tests vs committed `build/*.pdf`.
- **B5 — generalize + surface `semantic_assertions`.** (a) Surface: read `build/semantic_assertions.json` in `status.py`/`next`. (b) Generalize: template a `semantic_assertions` authoring block into every multi-panel figure's spec flow. (c) Enforce the §6 gate: a multi-panel figure entering acceptance without a `semantic_assertions` block = BLOCKER (or adopt the §9-risk-5 downgrade "surface where present"). This is the "B5" referenced by §6.

> **Slice-0 gate (exit):** the **Slice-0 exit probe (§7) passes on fig2** AND B1a passes on fig1. Until then, Slice 1 is blocked.

### Slice 1 — Premium levers for iteration (blocked until Slice-0 gate passes)
Author **exactly the 2–3 `replace_text`-expressible TikZ premium levers that fig2's actual sub-regions demand** (NOT add_volume_shading; NOT an open-ended lever set), then re-evaluate against the #1-amortize economics before adding more. Each lever = a parameterized, bounded, value-preserving TikZ op. Stop-gate: if the levers plateau at "clean" (can't reach premium), list ≥3 unused techniques before declaring a ceiling (`feedback_no_preemptive_engine_ceiling`).

### Slice 2 — Component bank + composition (blocked until #1-amortize (a)+(b) passes)
**PROBE RESULT (run 2026-06-22, recorded 2026-06-25):** (a) clean→premium crossing = **YES**; (b) economics = **~4 cheap 1-line edits** on a STANDALONE polymer/polysulfide zigzag-chain primitive (NOT a real figure); (c) cross-figure drop-in checkpoint **still PENDING**. (a)+(b) PASS → the gate to start building the bank is cleared; (c) stays an open Slice-2 checkpoint to validate the bank once built. This is a RESULT record, not a waiver.
> **Namespace note:** "Slice 2" here is THIS spec's cross-figure component banking / amortization lever, distinct from the composition-search doc's local "Slice 2" (single-fixture creative candidate sandbox). See `2026-06-23-llm-amplifying-composition-search-design.md` — its Slice numbering is local to composition-search and is NOT this spec's Slice 0–3.
**First resolve the substrate open-question (§5):** parameterized TikZ macro (risks idiom lock-in) vs an id-bearing format (re-imports the quarantined SVG path). Pick the one the #1-amortize probe shows is parameterizable-not-idiomatic. Then build extraction (premium sub-region → parameterized component) + composition (drop into new figures) + correctness via render-detectors + semantic_assertions (NOT id-gated SVG locks). Validate with #1-amortize part (c).

### Slice 3 — Quarantine the dead weight (lowest priority)
Hide/remove the inert id-gated SVG-semantic + auto-patch machinery from the agent-facing surface (inert, not harmful, but it misleads about guarantees).

---

## 9. Open risks (track)
1. **Economics of iteration** (#1-amortize (a)+(b)): if premium costs too many iterations per element, the direction is too expensive — the one quantitative unknown; run before Slice 2.
2. **Levers may plateau at clean** (Slice 1): mitigate with the ≥3-unused-techniques rule before any ceiling claim.
3. **Adjudication burden** (B2/B4): ~90% detector noise risks drowning the eye — hygiene + the labeled set are load-bearing, not optional.
4. **Component-bank substrate (Slice 2):** TikZ-macro lock-in vs SVG-id-dead — genuinely unresolved; #1-amortize must settle it; do not build before.
5. **`semantic_assertions` authoring cost:** assertions are human-authored per figure; the "no multi-panel figure without a block" gate (§6) adds real recurring authoring labor — accept it explicitly or downgrade the gate to "surface where present."
6. **Honest scope:** this minimizes the hand; it does not remove it. Premium-defining judgment stays a per-sub-region human stream. Never market it as "rare gate" or "hand-free."

---

## 10. Non-goals (explicit)
TikZ-synthesis LLMs · generative-image/SVG as renderer · ungrounded/single-pass/absolute-scoring critique loop · idiomatic snippet/macro libraries · authored-id-from-dvisvgm scoping · `add_volume_shading`/SVG-polish as a loop lever · raw Inkscape `--actions` as executor · claiming vacuous id-gated locks are "safe on real figures" · autonomous premium generation · paid-illustrator dependency · broad orchestration expansion before Slice 0 is robust.
