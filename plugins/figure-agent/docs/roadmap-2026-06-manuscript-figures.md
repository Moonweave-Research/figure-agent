# Roadmap — poly(S-r-DIB) manuscript figures (2026-06)

Active working plan. Re-orient from here after any /compact.

## North star
Ship the remaining 4-5 manuscript figures at fig1's Nature-tier quality, consistently,
via the validated **human-led element-iteration loop**. Tool work ONLY where it removes
friction for that. No tool-as-product building.

## Where we are (refreshed 2026-07-03)
- figure-agent v0.9.3. The active command surface is the quality kernel:
  status/drive/queue share next-action summaries; safe runners stop at
  host/human/accepted/golden/release boundaries.
- **fig1**: visual quality DONE (Nature-tier, accepted, audit 108/108 clean, critique FRESH v1.17).
  Pipeline TAIL open: exports STALE (golden 05-31 predates 06-04 source), no loop checkpoint,
  no final-artifact. `QUALITY_AUDIT.md` exists, `submission-safe: true`.
- **4-5 more figures** to make for this one manuscript.
- Tool has consolidated design-philosophy anchors plus style-pack and
  paper/context-pack surfaces. Treat these as convention references, not a taste
  oracle.
- v0.10 substrate now includes semantic assertion tolerance/`indeterminate` and
  compile-time convention receipts. Do not rebuild those as future work; the next
  v0.10 task is surfacing receipt evidence in operator status/queue outputs.
- Publication gate (provenance / AI-disclosure / source hash) already BUILT + shipped.
  paper-figure-vault exists (connectable, not wired). SVG-polish plumbing proven on synthetic; FALSIFIED on real (0/8).

## Fences (always on)
- User-as-master for TASTE; LLM/tool for CONVENTIONS + mechanics only. (LLM taste-judge falsified ~18%.)
- Codify conventions, never autonomous taste.
- Do NOT rebuild what exists or was falsified: vault auto-supply, SVG-polish "proof", publication-policy package.
- Build foundation/automation only under REAL pressure from the figures, not speculatively.
- **fig1 is the FROZEN reference**: conventions are extracted FROM it into the shared foundation,
  NEVER retrofitted back INTO it (that re-invalidates its rolled-forward golden + re-opens accepted taste calls like the V0 line weights).

## BLOCKED ON USER INPUT
- **The 4-5 figure list** (what each figure must show). Needed to scope 1.2 and order Phase 2.
  Phase 0 and a 1.1 skeleton do NOT need it; everything after does.

---

## Phase 0 — Close the baseline (cheap, now)
- [x] 0.1 Re-export fig1 golden (rolled stale export forward to 06-04 source). DONE: export PDF md5 == build PDF (a1390f3), `stale_export` note cleared. Commit `4e97afd`.
- [x] 0.2 Freeze new tool feature-building (stance adopted). No more SVG-polish / operator plumbing.
- [x] 0.3 README slice: `/fig_improve <name> --goal` documented as the canonical iterate entry point, `/fig_status` kept as the read-only check. Implemented by Codex (codex exec), reviewed by Claude (only README touched, +6/-0, Core-commands list intact).
- [ ] 0.4 Branch decision: with fig1 fully closed (quality + export), merge `goal1/fig1-overnight` -> main as the stable flagship baseline, OR keep iterating. (Confirm.)

> Codex-builds / Claude-reviews mechanism VALIDATED on 0.3: `command codex --dangerously-bypass-approvals-and-sandbox exec - < task.txt` (headless, ChatGPT auth) implements a bounded spec; Claude reviews the full diff for over-reach + spec compliance before commit. Scale this to Phase 1.2 (shared `.sty`) and mechanical TikZ patches. NOT for Phase 2 figure taste (user-as-master).

## Phase 1 — The 기준점 (shared foundation, PRINCIPLE layer)
- [x] 1.1 `figure-design-philosophy.md` — DONE (lean skeleton, grows per-figure). Grounded in fig1's
      EXACT values (palette hex cBlue #4477AA / cRed #CC6677 / cTeal #44AA99 / cAmber #997A1E; 7pt-max
      typography; 0.9/0.7/0.55 weight tiers) + the codified 13 `aesthetic_antipattern_audit` ids +
      hard-won lessons + canon (Bang Wong, Tufte, Ten Rules, Paul Tol). CONVENTIONS not taste; fence stated up front.
   - [x] 1.1a external research pass DONE (workflow wcl1r5kg8, 6 agents, real URLs + adversarial verify). Folded verified canon (Bang Wong/Cleveland-McGill/Wilke/Ten Rules/Tufte small-multiples/Tol/Crameri) + machine-readable systems (SciencePlots/khroma/ColorBrewer) into §7. Caught 2 corrections: (a) cBlue #4477AA is Tol BRIGHT not muted; (b) schematics submit as VECTOR PDF/EPS, not raster TIFF/PNG (new §4b). Confirmed 178mm = ACS double-col max.
- [ ] 1.2 (just-in-time, WITH fig2 — not all upfront) shared style IMPLEMENTATION layer:
      line-weight TIER system (fix the 25-inlined-weights / no-tier problem),
      shared named styles (interArrow, label tiers, panel letters) + reusable macros
      (dibRingAt, zigSChain, band-diagram, ...) -> a shared `.sty` / macro lib that fig2-figN import.
- [x] 1.3 v0.10 substrate already exists: semantic assertion tolerance/`indeterminate`
      and `build/convention_receipt.{json,md}` generation during compile.
- [ ] 1.4 current v0.10 task: expose convention receipt status/evidence in
      operator-facing status/drive/queue surfaces. This is docs/read-only evidence
      routing, not a new detector and not auto-mutation.
- [ ] 1.5 only after 1.4: consider a declaration-driven shape-orientation
      primitive if feasibility is proven on authored/render evidence. Color binding
      remains exploratory; if reliable label-to-shape sampling cannot be proven,
      keep it injection/receipt-only.

## Phase 2 — Make the figures (the DELIVERABLE)
For each remaining figure, in reuse-maximizing order:
- [ ] 2.x.1 scaffold `briefing.md` + `spec.yaml` (science-grounded: what it must show)
- [ ] 2.x.2 first TikZ draft importing the shared foundation (1.2), measured vs `figure-design-philosophy.md` (1.1)
- [ ] 2.x.3 element-iteration loop (name defect -> 1-line patch -> recompile -> confirm; parallel variant renders where spread exists)
- [ ] 2.x.4 reference-grounded `/fig_critique` (hand-author `critique_reference_pack.yaml`, 2-3 refs, ~1-2h) -> adjudicate -> loop
- [ ] 2.x.5 close tail: export + `QUALITY_AUDIT.md`
(The FIRST figure also stands up Phase 1.2 shared `.sty`.)

## Phase 3 — Paper-level closeout (when all figures exist)
- [ ] 3.1 cross-figure consistency audit (should be ~free given the foundation; verify)
- [ ] 3.2 per-figure publication gate (provenance / AI-disclosure — already built) at submission
- [ ] 3.3 (conditional) SDK throughput automation — only if the manual loop is too slow across the batch
- [ ] 3.4 (conditional) SVG polish — reopens ONLY if a TikZ-cannot-do-X defect recurs >=3x across the figures (documented condition)

---

## Explicitly NOT doing (from the 2026-06-06 external-review vetting)
- Rebuild publication-policy package (already exists, shipped, fig1 QUALITY_AUDIT filled).
- Auto-wire paper-figure-vault supply (the gap is human-judgment, not automatable; fig1 already hand-curated).
- "Prove SVG polish once on a real fixture" (falsified; the exact state was made + discarded 48h ago in 1da4810; satisfying it would corrupt the gate).
- Re-architect the command surface (contract-pinned; cheap README slice only).
- New ML sidecars: crop-second-opinion (= falsified vision critique) or draft-alternatives (= off-identity generation).
- Rebuilding v0.10 tolerance or convention receipt generation; those are already
  implemented substrate.
- Adding generic detectors, taste scoring, or autonomous source mutation under
  the convention-spine banner.
