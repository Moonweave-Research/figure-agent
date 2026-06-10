# Authoring Context Pack Design

**Date**: 2026-06-10
**Status**: proposed direction (identity-level)
**Depends on**: figure #2 selection; filed defect "detector silence is a false
clean bill" (P1, 2026-06-10)

## Problem

fig1 (`fig1_overview_v2_pair_001_vault`) carries **241 iteration comments** in
its source — the real cost of one golden figure. External evidence (mid-2026)
shows why: TikZ generation is commoditized at roughly 3.5/5 human-rated quality
(TikZilla-3B-RL ≈ GPT-5 on DaTikZ-V4, arXiv 2603.03072), and no published
system closes the gap from there to publication grade autonomously. That gap is
closed today by expensive human-driven element iteration.

Meanwhile the repo already accumulates exactly the knowledge that closes the
gap — Style Lock, `docs/figure-design-philosophy.md`, per-figure iteration
comments, critique adjudications, reference-learning packs, journal style
packs, and the (currently empty) `panels[].semantic_claims` /
`locked_invariants` spec fields — but uses all of it only **after** compile, as
audit gates. First drafts start blind.

Session evidence for the cost of starting blind: a physics-semantic defect
(Panel F cantilever drawn nearly straight with a horizontal tip, i.e. no
deflection under Coulomb repulsion) survived days of tool-supervised iteration
because nothing declares intended physics at authoring time, and all four
detectors are geometry/typography hygiene only. Fixed by hand in `0a6e308`.

## Direction

figure-agent evolves from "deterministic quality gates regardless of author"
to **dual-use contracts**: the same declared knowledge guides the LLM *before*
compile (authoring context) and gates the result *after* compile (audit). The
target identity:

> A tool that makes an LLM draw paper figures better, by compiling the paper's
> accumulated figure knowledge into authoring-time context — and then holding
> the result to the same contracts.

This requires revising `docs/quality-kernel-goal.md`, which currently disclaims
"teaching an LLM how to create every figure". The disclaimer was aimed at
transient prompt plumbing (v0.1) and stays correct about that; it is wrong
about durable, paper-specific knowledge compilation.

## Non-Goals

- No revival of v0.1 prompt plumbing (normalization, HALT/paste/resume loops).
- No model training or fine-tuning.
- No new generation orchestration surfaces; the freeze stands until N≥3 real
  figures exercise the existing ones.
- No automatic physics detectors (perception auto-detection remains falsified;
  the constructive alternative is human-declared claims below).
- No generic TikZ tutorial content in packs. Snippet policy unchanged:
  paper-specific idiom only (anchoring lock-in lesson, 2026-05-05).

## Scope

Four slices, smallest-first, each consumable by figure #2:

1. **Correction-rule distillation (one-time).** Distill fig1's 241 iteration
   comments + `critique_adjudication.yaml` dismissals into a human-reviewed
   catalog of correction rules (e.g. label-on-curve placement, instrument-box
   bezel standard, panel-proportion footguns). Rules must be paper-specific or
   physics-shaped; generic best practice is excluded. Output:
   `docs/authoring-rules-pair001.md` (or similar), treated as hypotheses until
   a second figure confirms transfer.

2. **Semantic contract authoring.** Populate `spec.yaml panels[].semantic_claims`
   and `locked_invariants` with 3–5 human-declared physics statements per panel
   (e.g. "cantilever deflects away from the biased electrode; tip end-face
   perpendicular to beam tangent"). For new figures these are written **before**
   the `.tex`. This is the constructive half of the P1 defect fix: detector
   silence stops being a clean bill because the claims define what a human or
   host-vision pass must still verify.

3. **Pack compiler.** A read-only `fig-agent context-pack <name>` (CLI +
   MCP preview) that compiles into one authoring artifact: design-philosophy
   summary + Style Lock vocabulary + correction-rule catalog + the fixture's
   semantic claims + relevant paper-specific snippets. No hidden writes; the
   pack is an input the author (human or LLM) reads, not an executor.

4. **Narrow-question critique integration.** Critique consumes semantic claims
   as per-claim verification questions ("does the beam visibly deflect left,
   away from the electrode?") instead of open-ended physics judgment. External
   evidence: vision LLMs are unreliable as absolute judges (GPT-5 vs human
   r=0.428, VisJudge-Bench arXiv 2510.22373; mechanism-diagram blindness,
   MISS-QA arXiv 2507.10787) but usable on concrete artifact + narrow question
   (ReLook arXiv 2510.11498).

## Metric

**iterations-to-golden** is the north star and the falsification test.

- Baseline: fig1 = 241 iteration comments, authored without a pack.
- Validation: figure #2 authored WITH the pack. Success = a material reduction
  in iterations-to-golden. Failure = no significant difference → this
  direction is falsified and the kernel-only identity stands; the pack work is
  then capped at slice 2 (semantic contracts), which is independently justified
  by P1.

## Risks

- **Make-work / scaffolding-ahead-of-payload** (the candidate-family failure
  mode, probed 2026-06-10): mitigated by building only what figure #2 actually
  consumes, in slice order, with no speculative generalization.
- **Context anchoring**: a pack that injects standard idioms reproduces the
  snippet lock-in failure. Mitigation: rule catalog admission test — each rule
  must cite the fig1 iteration comment or adjudication it was distilled from.
- **Single-fixture distillation bias**: fig1 rules may not transfer. The
  catalog ships marked as N=1 hypotheses; promotion to stable guidance requires
  confirmation on a second figure.
- **Identity churn**: revising quality-kernel-goal.md mid-flight can confuse
  agents bootstrapping from docs. Mitigation: revise in the same slice as the
  pack compiler lands, not before.

## Validation Commands

- `fig-agent context-pack <name> --json` emits a deterministic pack manifest
  (hashable, like other read-only surfaces).
- Existing release gate unchanged; slice 2 adds a lint that `semantic_claims`
  entries are non-empty for fixtures opting into the pack workflow.
