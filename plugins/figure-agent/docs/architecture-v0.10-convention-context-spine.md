# figure-agent v0.10 — Convention/Context Spine

Status: direction approved 2026-06-20 via `/keelplane` adversarial judgment
(verdict STANDS). **Rev 4 (2026-07-03):** refreshed against current code truth:
semantic assertion tolerance/`indeterminate` and the compile-time convention
receipt substrate now exist; remaining v0.10 work is surfacing that evidence and
proving any new convention-verification primitive before building it. Winner:
**direction D (convention/context engine)** as a hybrid grafting A (substrate),
C (demote-don't-delete), B (frozen advisory). Target: 0.10.x.

---

## 0. The philosophy change (read first)

Change of **identity and investment priority**, not a code rewrite. Nothing is
ripped out on day one.

**KEEP (unchanged trust-boundary tenets):** no vision-AI in the core (no LLM/VLM
gating decision); taste stays with the human; everything deterministic and
report-only (no new AI, no auto-mutation).

**CHANGE (exactly one tenet — the spine):** from "the core is a comprehensive
geometric-detector kernel" → "the spine is **durable authoring memory +
convention propagation + figure-vs-claim assertions**; the detectors are a
**supporting** guardrail set."

**Why the evidence forces this:** every verified win of the session flowed through
the thin convention layer (cantilever-vertical propagation, project-catalog
injection `17aa0b3`, semantic-assertion `da67494`) while all eight detectors
passed a physically wrong figure clean. Value is created in the convention layer;
identity tracks value. The trust-boundary tenets are kept (audit 18-30% + 2026
SOTA; B's counter-number is a missing artifact — §1, §5).

**Honest scope caveat:** the *demonstrated* value of this layer so far is
INJECTION (surfacing conventions into the author's context and now into a build
receipt), not mechanical ENFORCEMENT. Enforcement of the real catalog conventions
(orientation, colour) is new, non-trivial, partly-exploratory work that does not
exist yet (§3). The identity change is adopted **provisionally**, gated on the §5
measurement.

---

## 1. Research and prior art

**Internal (verified):** audit 127→1; 4-figure diagnostic → 6 signals 3/3
(decisive: #2 vision carries quality / detectors blind; #5 relational correctness
= top *invisible* risk; #6 conventions trapped in a pair001-locked catalog →
recurring horizontal-cantilever bias). Shipped this session (5 commits): the spine
components now exist — `docs/authoring-rules-project.md`,
`authoring_context_pack.py` (injects `project_rule_catalog`),
`semantic_assertions.py` (text-anchor spatial relations).

**External SOTA (2026):** reference-grounded VLM critique still fails on the
relational class (PaperBanana connectivity-error escape; ChartHal GPT-5 ≈ 34%) →
"no vision-AI in core" stays. Field converging on spec/memory/convention-driven
authoring for correctness-critical figures.

**Falsified counter-evidence (do not reuse):** B's `grounded_F1_w = 0.981` source
fixture (`examples/golden_trap_depth_picture/...`) **does not exist**; it survives
only as prose AND anchors `critique-evaluation-rubric-v1.md`'s active v0.3 plateau
gate (`≥ 0.9`) → §5 quarantine.

---

## 2. Product position and non-goals

**Position:** an **authoring-memory + convention engine** for paper figures —
carries a project's durable conventions into every figure's authoring context and
(where mechanically possible) verifies declared figure-vs-claim assertions.

**The sharp spine-vs-suite line (resolves §9 R5).** A deterministic check is
**SPINE (may be added)** iff it is **(a) declaration-driven** — fires only because
a catalog rule or a spec assertion declared it, never on an undeclared figure;
**(b) report-only**; **(c) tolerant** (relational, with an indeterminate band,
§3). A check that fires **generically** on any figure with no declaration is
**DETECTOR-SUITE — frozen, no new ones.** This keeps "no new detectors" from being
toothless: 1b's orientation/colour checks qualify as spine only because each is
bound to a declared catalog rule and carries its source quote.

**Non-goals:** NOT a VLM critic / autonomous generator / taste judge; no
auto-mutation; no AI gating; no generic detector-suite growth; no *blind* deletion
of the existing suite (demote, prune on telemetry).

---

## 3. Architecture — honest capability map

**Two distinct fact-sets (the original conflated them — §9 H1):**
- **Text-anchor relations** — what `semantic_assertions.py` checks today: spatial
  relations between *text labels* ("shallow above deep", verified on fig4).
- **Catalog conventions** — what the catalog actually holds: `cantilever-vertical`
  (a drawn-SHAPE orientation) and `shallow-blue/deep-red` (a label↔colour
  binding). **Neither is a text-anchor relation**, so `semantic_assertions` cannot
  verify them; they need **new spine primitives** (§4 1b) that do not exist yet.

**Tolerance (resolves §9 R3; implemented).** `semantic_assertions.py` now has a
default tolerance band and per-assertion `tolerance_pt`: when the relation margin
is below ε, it reports `indeterminate` instead of PASS/WARN. This keeps
text-anchor relational enforcement from pretending a near-tie is stable across
local-native and Docker renders (§5).

**Spine components:** durable memory (catalogs); propagation/injection
(`authoring_context_pack.py` — *the demonstrated-valuable part*); compile-time
convention receipts (`convention_receipt.py` via `compile.sh`, report-only);
assertions (`semantic_assertions.py`, text-relational, with tolerance band);
convention-verification primitives (NEW, §4 1b — orientation, colour).

**Detectors:** demoted to supporting report-only guardrails; candidate/quality/
benchmark apparatus → internal, *pruning candidates* once 0d telemetry proves
which fire on real figures (deletion only after that evidence).

---

## 4. Execution model

### Phase 0 — substrate

- **0a — LICENSE (private repo), public deferred (resolves §9 R1/R4).** Add MIT
  scoped to the project's OWN code. The repo **stays PRIVATE**, so the 82
  third-party reference PNGs in `examples/` (and in git history) are not being
  distributed — adding a LICENSE to a private repo is safe now. **Going public is
  a SEPARATE, out-of-v0.10-scope decision** that requires purging those images
  from git *history* (filter-repo = a history rewrite, its own risk gate) — do not
  conflate it with "add a LICENSE." Known limitation (R4): adopting the 0c pin
  later invalidates fig1's macOS-native byte-identity goldens; until regenerated in
  the pinned env, goldens stay macOS-native and the pin is CI-additive.
- **0b — Merge to main, reviewed by area.** Branch is 0 behind, ~104 ahead (a
  *moving target*). Not a blind merge: re-check 0-behind; confirm branch CI green;
  review the surface BY AREA (authoring-context-pack / MCP / agent-native / this
  session's spine work) for WIP that should not land; reviewed integration merge.
- **0c — Reproducible render (golden regression only).** Dockerfile pinning exact
  TeXLive + tesseract + poppler/dvisvgm + the **exact fonts** (figures use
  macOS-system Arial; Docker Linux must bundle the identical font or geometry
  differs — §9 H3). Gate = **the pinned env reproduces a committed golden pdftotext
  geometry baseline** (NOT "render twice = identical", which only proves within-run
  determinism — §9 H2). Local native stays the fast authoring loop; the pinned env
  is authoritative for goldens; a `doctor` check warns on local drift.
- **0d — Detector telemetry.** No single dispatch (compile.sh runs each checker as
  a separate subprocess — §9 H6) → a tiny shared logging helper each `check_*.py`
  calls once, one JSONL record (name, fired/clean, duration, finding-count) to
  `build/detector_log.jsonl`. Governs later demotion/pruning.

### Phase 1 — spine slice

- **1a — Injection receipt (implemented; no new detection; does not need 0c).**
  At compile time `scripts/compile.sh` invokes `convention_receipt.py --write` to
  emit `build/convention_receipt.{json,md}` listing which `use_as_constraint`
  rules were injected, each with its source quote — so the author sees, on every
  figure, "cantilever = vertical (clip on top); source: …". This is the part that
  demonstrably closed the cantilever bias. Report-only.
- **1b — Mechanical convention verification (NEW spine primitives; later; partly
  exploratory).** Orientation primitive (read the cantilever/beam path orientation
  from geometry) → declaration-driven, tolerant, source-quoted. Colour primitive
  (sample the rendered raster near a label to check shallow=blue/deep=red) is
  **EXPLORATORY and may prove infeasible** (§9 R6: the coloured element is a nearby
  non-label shape at variable distance); if infeasible, the colour convention stays
  injection-only. Both qualify as spine by the §2 line (declaration-driven +
  report-only + tolerant). Attempted only after 1a clears its gate.

---

## 5. Safety, verification, and measurement

**Two reproducibility concerns, separated:** *exact-geometry* (golden regression,
needs 0c pin + committed baseline) vs *relational enforcement*
(`semantic_assertions` + 1b, tolerant with the §3 indeterminate band, env-robust)
→ Phase-1 enforcement does **not** require 0c first; only golden regression does.

**Risk gates (safe default in parens):** philosophy change (KEEP) — approved
provisionally; LICENSE (none) — user picks MIT, private only; public exposure
(stay private) — out of scope, needs history scrub; merge (don't) — reviewed by
area; Dockerfile/CI (don't) — reviewed. No destructive ops, no force-push, no
history rewrite in v0.10.

**Verification gates:** 0a LICENSE present (own-code scope), repo stays private;
0b main 0-behind + CI green + no WIP landed unreviewed; 0c pinned env reproduces
the committed golden geometry + `doctor` flags drift; 0d one JSONL record per
checker run; 1a receipt lists each injected rule + source quote and is surfaced in
operator status/queue evidence; 1b paired hold/violate fixtures per primitive,
tolerant to local-vs-Docker.

**Measurement — the direction-deciding signal (redesigned, resolves §9 R2).**
Naïvely measuring "did figure #2's cantilever come out vertical" is confounded by
priming (we just spent a session on it) and is N=1. Instead:
- **Metric: catalogued-rule re-violation rate, longitudinal.** Baseline is already
  recorded and painful — the horizontal-cantilever convention was re-violated
  across fig1 + fig2/3/4 (a real N=4 baseline, not a hypothetical). The test is
  whether, with injection (1a) live, the *next* batch of figures shows ~0
  re-violations of catalogued rules **before a human catches them**.
- **Priming control:** weight the signal toward conventions the author would
  plausibly get wrong by default and that were NOT the focus of recent work — i.e.
  grow the catalog with a few genuinely non-obvious project conventions and watch
  whether the receipt prevents *their* violation, not just the heavily-primed
  cantilever. A clean attributable hit = the receipt surfaces a rule the author
  confirms they would have missed unprompted.
- **N and honesty:** this requires real figures, so it **partially un-defers
  figure work** — which aligns with the audit's standing mandate to produce
  figures #2/#3. Treat the signal as qualitative until K ≥ 2–3 new figures; the
  identity change stays provisional until then.
- **Secondary:** figure #2 accepted in fewer iterations than fig1's 5–10.

**Reversion trigger:** if injection (1a) does not drive catalogued-rule
re-violations toward ~0 across K ≥ 2–3 figures, the enforcement thesis is weakened
and the direction reverts to "injection-as-context only + A hygiene" — still better
than A-only, since injection is what closed the bias. 1b is attempted only if 1a
clears its gate.

**Quarantine:** mark `critique-evaluation-rubric-v1.md` v0.3 plateau gate
(`grounded_F1_w ≥ 0.9`) **UNVERIFIED** (missing fixture); never cite `0.981`.

---

## 6. Evaluation fixtures

- 0c: a committed golden pdftotext-geometry baseline for one bundled smoke
  fixture; CI asserts the pinned container reproduces it.
- 1a: the next K ≥ 2–3 real figures; measure the longitudinal re-violation rate
  and iteration-count-to-acceptance.
- 1b: paired hold/violate fixtures for the orientation primitive (and colour, if it
  proves feasible).

---

## 7. Implementation plan (smallest first; honest dependencies)

1. **`semantic_assertions` tolerance band + `indeterminate` — DONE.** Keep it
   covered by regression tests; do not re-open it as new substrate work.
2. **1a injection receipt — DONE as build artifacts.** Remaining work is
   operator surfacing/status evidence, not rebuilding receipt generation.
3. **0a LICENSE (MIT, private-scoped)** + record the public-exposure/history-scrub
   decision as out of scope.
4. **0d logging helper** — additive; demote/prune evidence.
5. **0c Docker pin + committed golden-geometry baseline** (budget macOS-Arial-vs-
   Linux font nondeterminism; entails regenerating goldens — R4); golden regression
   only.
6. **0b reviewed-by-area merge to main** — after substrate green + scrub decision.
7. **1b orientation primitive** — only after a declaration-driven feasibility
   proof shows the geometry can be read reliably from authored source/render
   evidence. **Colour binding remains exploratory** and falls back to
   injection-only if the label-to-nearby-shape sampling model is fragile.

Do NOT: rebuild the tolerance band or receipt generator as if absent; build 1b
before receipt evidence is surfaced and feasibility-proven; conflate "add
LICENSE" with "go public"; blanket-merge unreviewed; treat 0c "render twice" as
reproducibility; claim `semantic_assertions` verifies the catalog conventions;
cite `0.981`.

---

## 9. Adversarial review log

**Rev 1 → rev 2 (first pass):** H1 Phase-1 enforcement not buildable
(text-anchor-only) → split 1a/1b + §3 fact-map. H2 "render twice" mis-targeted →
golden-baseline gate. H3 local/Docker geometry mismatch → separate exact-geometry
(golden) from tolerant relational enforcement. H4 82 third-party PNGs → scrub-first.
H5 104-ahead blind merge → reviewed-by-area. H6 no single dispatch → per-script
JSONL. H7 byte/geometry conflation → geometry. H8 throughput N≈1 → provisional +
reversion trigger.

**Rev 2 → rev 3 (second pass):** R1 working-tree scrub ≠ public-safe (history) and
contradicted "no history rewrite" → separate LICENSE-private (now) from go-public
(history scrub, out of scope). R2 the 1a gate was confounded (priming) + N=1 +
blocked on deferred figure work → longitudinal re-violation metric off the real
N=4 baseline, priming-controlled by non-obvious conventions, partial un-defer,
K≥2-3, provisional. R3 `semantic_assertions` had no tolerance band so "env-robust"
was overstated → add tolerance band + `indeterminate`. R4 Docker pin invalidates
macOS-native goldens → known limitation, regenerate in pinned env. R5 spine-vs-
suite line was fuzzy → sharp criterion (declaration-driven + report-only + tolerant
= spine; generic = suite, frozen). R6 colour primitive under-specified/fragile →
marked exploratory, may be infeasible, falls back to injection-only.

**Rev 3 → rev 4 (current-code refresh):** tolerance/`indeterminate` and 1a
convention receipt are no longer future tasks. `compile.sh` writes the receipt
opportunistically during compile, and tests cover the receipt payload plus
semantic near-tie behavior. Remaining work is evidence surfacing in status/queue
outputs and feasibility-gated convention primitives, not generic detector growth
or autonomous taste/mutation.

**Residual known limitations (accepted):** R4 golden migration cost; R6 colour
primitive feasibility; the throughput thesis remains N-small until K≥2-3 figures.
