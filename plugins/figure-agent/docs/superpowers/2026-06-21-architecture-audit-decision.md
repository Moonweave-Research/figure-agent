# Figure-Agent Architecture & Capability Audit — Decision Grade

> 2026-06-21. keelplane audit: 6 dimension-auditors (read real code, tested on real figures fig1–5) → 16 adversarial re-verifications → synthesis. 50 findings, all load-bearing claims re-verified live against the repo. Branch `design/figure-agent-v2-svg`.

## 1. Bottom line

**No — "tell an agent to use the figure-agent" does NOT run-and-apply end-to-end on real figures today, and it cannot via the agent's own front door.** The MCP surface (the path an agent drives) is deliberately read-only: the one mutation tool `figure_agent_apply_candidate` is a hard-coded refusal (`mcp/figure_agent_server.py:1367–1368` → `apply_requires_cli_opt_in`). The state router `next` terminates at `action:complete, writes:False` on every real figure after a single export. The auto-improvement layer is inert on real figures (`propose` → `operations:[]`; the candidate generator only fires on synthetic single-line `(0,0)` `.tex`; the one real generator is hard-wired to panel C + the literal "mobility edge"). Detectors DO fire (fig2 = 28 unadjudicated candidates) but are structurally orphaned from the patch pipeline. The entire SVG-semantic safety half (truth-lock, occlusion guard, render-ship gate, polish) is **vacuous on every real figure** because `dvisvgm --pdf` emits 0 IDs on geometry paths (fig1 461/0, fig2 75/0, fig4 43/0) and truth-geometry is gated on `element_id` (`svg_semantic_diff.py:305`).

There IS one genuine, robust apply path — the `apply-candidate` CLI, which provably mutated `fig1.tex` and recompiled clean — but it is reachable only by shelling to the CLI with exact panel/family flags, and the only edit it can author is a single +0.10 X-nudge.

**Readiness verdict: NOT-READY for agent-driven operation. PARTIALLY-READY for human-driven CLI element-iteration (the user's actual lever), provided the human hand-authors candidate manifests.**

## 2. Capability scorecard

| # | Dimension | Verdict | SCOPE | Load-bearing evidence |
|---|-----------|---------|-------|----------------------|
| 1 | Architecture | Split: solid base + dead SVG half | mixed | base compile chain solid (`compile.sh`); SVG-semantic half vacuous (`svg_semantic_diff.py:305`, dvisvgm 0-ids) |
| 2 | Gaps / wiring | MCP→apply hole; generators toy-bound | not_at_all (apply) | MCP refusal `figure_agent_server.py:1367`; generator gate `candidate_generator.py:169`; family gate `candidate_families.py:16–20` |
| 3 | Dependencies | Healthy, graceful failure | works_on_real | doctor ok; lualatex/dvisvgm/rsvg/pdftoppm present; `fixture_missing` structured not a crash |
| 4 | Detector / audit | Render-detectors fire; spec-detectors fig1-only; ~90% noise | works_on_real (render) / toy_only (spec) | visual_clash + undeclared_geometry fire on all 5 (fig2=28); text_boundary/label_path only in fig1 spec |
| 5 | QA / tests | 2356 pass but synthetic; 1 real gate (RED) | toy_only | benchmark = count-movement not P/R; dogfood = fig1 only; `test_real_fixture_audit_adoption` RED (correct) |
| 6 | Vision judgment | Sophisticated but reference-gated; skipped on 4/5 | toy_only (loop) / works (manual) | `compute_critique_state`→NOT_REQUIRED for fig2/4/5; `next` never routes critique for NOT_REQUIRED |
| 7 | Crop-to-micro | Strongest forcing-function; dormant on 4/5 | works_on_real (fig1) / toy_only (rest) | 108 crops hash-bound on fig1; gate dormant when critique NOT_REQUIRED; hero panel C gets 0 micro crops |
| 8 | Narrative coherence | No deterministic check; LLM-only, inert | not_at_all | story axis = None on every real fig (`fig_loop_axes.py`); cross-panel terms are prompt text only |
| 9 | Scientific validity | 1 real deterministic check (fig4 only), hidden | works_on_real (fig4) / toy_only (rest) | `semantic_assertions` fires live on fig4; declared in 1/5 specs; NOT surfaced in status/next/loop |
| 10 | E2E agent-driven | Read-only by design; cannot apply | not_at_all (apply) | `next`→complete/writes:False; `fig_run` whitelist has no apply; `quality_patch_policy:65` `may_edit:False` |

## 3. The blocker holes (4 confirmed)

**B1 — MCP apply is a hard-coded refusal (the front door cannot mutate).** `mcp/figure_agent_server.py:1367–1368` returns `apply_requires_cli_opt_in` unconditionally; the working CLI it points to (`bin/fig-agent:876–904` → `candidate_apply.apply_candidate`) is never wired in. *Fix:* wire the MCP tool to the same `apply_candidate` the CLI shells, gated by the existing `acceptance.json` + drift-hash + `mutation.lock` safety (which already enforce everything the blanket refusal redundantly blocks). If human-only is intended, make `next.operator_guidance` say "hand off to a human / drop to CLI" instead of silently dead-ending.

**B2 — Quality ledger is blind to every detector that fires.** `quality_defect_ledger.py:162` reads only `build/text_boundary_clash.json` (0 candidates on all 5) and never `visual_clash.json`/`undeclared_geometry.json`/`critique.md`. fig2's 28 real findings produce exactly one generic `acceptance_not_declared` defect. *Fix:* ingest visual_clash/undeclared_geometry/label_path behind an adjudication gate, normalize through `quality_patch_policy.classify_patchability`.

**B3 — The patcher's only edit path cannot touch any real figure.** `quality_patch_plan._default_patch:42–53` returns `''` unless `len(lines)==1 and "(0,0)" in line`; real `.tex` are 63–2028 lines. `quality_patch_policy.py:65` hard-codes `may_edit:False`. *Fix:* if auto-apply stays out of scope (the validated lever is human iteration), have the ledger hand the human a concrete `file:line` + suggested 1-line patch instead of `unsupported_defect`. If auto-apply is wanted, replace `_default_patch` with a selector-based bounded-coordinate applicator.

**B4 — Crop-to-micro forcing-function is dormant on 4/5 figures.** The 108-crop hash-bound BLOCKER gate (solid on fig1) only engages when a `critique.md` exists, which only happens when critique is REQUIRED, which `compute_critique_state` (`status.py:113–116`) returns only for figures declaring a reference. fig2–5 = NOT_REQUIRED, so nothing forces the agent to zoom — even though fig2's `audit_crops/manifest.json` exists with 16 crops. *Fix:* decouple micro-inspection from reference-gating; add a "micro audit required" state whenever `audit_crops/manifest.json` exists; route `next` to `/fig_critique` when `unadjudicated_candidate_count>0`.

(Verifier demoted D6-1 blocker→major: release still requires explicit human `accepted=true`, so bad figures can't silently auto-ship; the gap is that automated judgment never runs, not that bad figures ship.)

## 4. What is genuinely solid
- **Base compile→PDF→SVG→detector chain** (works_on_real): `compile.sh` lint-gate → lualatex → 7 detectors; clean on the 2028-line fig1. Reliable foundation.
- **`candidate_apply` engine + CLI apply path** (works_on_real): `replace_text` exactly-once guard, sha256 drift guard, `O_EXCL` mutation lock, rollback patch, post-apply compile+export. **Provably mutated `fig1.tex`, recompiled rc=0. This is the user's element-iteration lever, already built.**
- **Render-based detectors** (works_on_real): visual_clash (pdftoppm) + undeclared_geometry (pdfplumber) fire on all 5, independent of the dead SVG-id path.
- **Crop-pack + hash-bound manifest on fig1** (works_on_real): 108 deterministic sha256-bound crops; corrupting one → immediate BLOCKER. The model the rest should follow.
- **`semantic_assertions`** (works_on_real): the one real deterministic scientific-validity check; fires on fig4, catches reversed relations.
- **Report-only discipline + human-gate boundary**: critique never auto-mutates; conflicts route to human. Right for a human-supervised lever.
- **`test_real_fixture_audit_adoption` is RED — correctly**: the one test tying detectors to the real corpus caught fig2–5 added without adoption contracts. Resolve honestly; don't silence.

## 5. Toy-only vs real (never ran meaningfully on a real figure)
- SVG truth-lock / occlusion guard / geometry-violation locks — only `_volume_shading_demo` satisfies the gate (real dvisvgm = 0 path-ids).
- SVG render-ship gate + svg_polish + svg_semantic_diff truth half — no real figure has `*.polished.svg` / `svg_polish_recipe.yaml` / `final_artifact.kind==polished_svg`; four no-op early returns guarantee it never runs.
- Auto candidate generator + `_default_patch` — single-line-`(0,0)` precondition matches only the 5 `smoke_*_demo` toys.
- `quality_patch_plan`/`quality_patch_apply` apply path — unreachable for any multi-line real `.tex`.
- Patch-policy SAFE_CLASSES — no upstream ever constructs these on a real figure.
- Benchmark/QA harness — dogfood = fig1 only; contracts measure count-movement not precision/recall; no labeled ground-truth exists.
- **Reference-gated-but-real** (work only when a human supplies references): vision critique, crop-to-micro accounting, reference-grounded adjudication, judge→adjudicate→apply handoff — live on fig1 (STALE), dormant on fig2–5.

## 6. Prioritized remediation roadmap

**HIGHEST-LEVERAGE FIRST FIX → B1 (wire MCP apply to the existing CLI engine). NOT the 0-id locks.** The 0-id/vacuous-SVG-locks problem protects a workflow the user is not pursuing (SVG post-process); fixing it is low-value dead-weight removal. The one change that converts the system from "verify-only demo" to "agent operates and applies" is connecting the *already-built, already-safe* `candidate_apply` engine to the agent's front door. The safety gates already exist, so the refusal is redundant. This single change is what the acceptance bar literally tests.

1. **B1** — wire MCP `apply_candidate` → `candidate_apply` CLI behind acceptance/drift/lock gates.
2. **B2** — ledger ingests render-detectors (visual_clash / undeclared_geometry / label_path) behind an adjudication gate.
3. **B4** — decouple micro-crop + critique from reference-gating; fire a "micro/critique required" state whenever `audit_crops/manifest.json` or detector candidates exist; route `next` to `/fig_critique` on `unadjudicated>0`.
4. **B3** — replace `_default_patch` OR have the ledger emit `file:line` + suggested 1-line patch for human application.
5. **Generalize the panel-family generator** (`candidate_families.py`): derive panels/families/label-targets from spec.yaml + node text instead of constants + a 5-string allowlist; parameterize the offset.
6. **Detector hygiene**: demote bare `undeclared_*` to INFO corpus-wide (`undeclared_geometry_profile: schematic`); re-tune `_known_false_positives.yaml`; honest `visual_clash_cap` per figure. (Stops ~90% noise.)
7. **Resolve the RED adoption test honestly**; add render-behavior regression tests vs committed `build/*.pdf`; add a small labeled TP/FP ground-truth set so detector tuning is measurable.
8. **Surface the one real validity signal**: have `status.py` read `build/semantic_assertions.json`; template a `semantic_assertions` block into every multi-panel figure; make duplicate-anchor an explicit error.
9. **Quarantine/remove the dead SVG-semantic half** from the agent-facing surface (lowest priority — inert, not harmful, but misleads about guarantees). Either prove one polish recipe with injected IDs, or stop advertising geometry truth-lock on real figures.

## 7. Honest verdict on the direction

**"Iteration-built premium primitives via heavy human element-iteration" IS buildable on this system as-is — but only by a human driving the CLI, not by telling an agent to do it.** The validated lever (eye → 1-line patch → recompile → confirm) is real and the engine under it (`candidate_apply`) is the most robust piece in the codebase. The base compile and render-detector chains are solid. The core mechanism the user wants is present and works.

**What must be fixed before an agent can be told "use the figure-agent" and have it actually apply:** B1 (MCP apply wiring) is non-negotiable and is the single highest-leverage change. Without it the agent can only verify — and worse, `propose`/`next` return `success:true` envelopes for no-ops that mislead an orchestrating agent into believing it acted. B2 + B4 are needed for the agent to *know what to fix* (otherwise detectors fire into a void and judgment never runs on 4/5 figures).

**Yes, the system is over-built in places that do not serve the element-iteration lever.** The entire SVG-semantic half (~8+ modules: svg_polish_*, svg_ship_gate, svg_semantic_diff truth path, occlusion guard, render-ship gate) has never run on a real figure and protects a workflow the user is not pursuing. The auto-generation/auto-patch layer is toy-bound and, given automation is explicitly *not* the lever, is effort against the stated goal. The 2356-test suite gives false confidence (greens on synthetic while the one real-corpus gate is RED). The honest path is to **lean into the human-iteration lever**: wire MCP→CLI apply (or document the human-CLI handoff), connect detectors→ledger→suggested-1-line-patch so the human's eye is fed concrete `file:line` targets, and stop maintaining the inert SVG-lock and auto-patch machinery until a real workflow demands them.

Load-bearing files: `mcp/figure_agent_server.py:1367`, `scripts/svg_semantic_diff.py:305`, `scripts/quality_defect_ledger.py:162`, `scripts/quality_patch_plan.py:42`, `scripts/quality_patch_policy.py:65`, `scripts/candidate_generator.py:169`, `scripts/candidate_families.py:16-20`, `scripts/status.py:113`, `scripts/semantic_assertions.py`, `bin/fig-agent:876`, `tests/test_real_fixture_audit_adoption.py:60`.
