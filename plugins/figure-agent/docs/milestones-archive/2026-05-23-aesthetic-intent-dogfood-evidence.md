# Aesthetic Intent Dogfood Evidence

**Date:** 2026-05-23 KST
**Status:** fixture metadata adopted; critique freshness gate exercised

## Scope

This dogfood pass applies the optional Issue 35 aesthetic-intent contract to
`fig1_overview_v2_pair_001_vault`.

The pass changes fixture metadata only:

- `examples/fig1_overview_v2_pair_001_vault/aesthetic_intent.yaml`

It does not edit TikZ source, generated export artifacts, accepted state, or
golden state.

## Adopted Intent

The fixture now declares:

- `target_journal: Nature Materials`
- `visual_maturity: editorial`
- `density: balanced`
- `reference_style: multipanel_story`

The active design principles tell host critique to prefer restrained
publication-grade hierarchy, crisp instrument precision, and subtle
component-level texture only when it clarifies mechanism, material identity, or
scale.

The explicit anti-patterns are:

- `toy_diagram` as a MAJOR concern
- `preset_macro_feel` as a MINOR concern

The polish triggers separate two routes:

- `ready_for_svg_polish` when TikZ is semantically correct but print-scale
  optical refinement still limits journal polish
- `semantic_backport_required` when a polish request would change mechanism,
  label meaning, component identity, or panel storyline

## Evidence

Initial critique brief generation was blocked by existing stale render state:

```bash
uv run python3 scripts/critique_brief.py \
  examples/fig1_overview_v2_pair_001_vault
```

Observed:

```text
stale render examples/fig1_overview_v2_pair_001_vault/build/fig1_overview_v2_pair_001_vault.png;
newer source file(s): spec.yaml; run /fig_compile first
```

Compile was rerun:

```bash
bash scripts/compile.sh \
  examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

Observed:

- compile exited 0
- existing Style Lock WARN tier findings remained report-only
- collision check passed
- visual-clash candidates were serialized to `build/visual_clash.json`
- text-boundary check passed

After compile, the critique brief contained the new calibration section:

```bash
uv run python3 scripts/critique_brief.py \
  examples/fig1_overview_v2_pair_001_vault \
  | rg -n "Aesthetic Intent Calibration|Target journal|Visual maturity|mature_restraint|toy_diagram|svg_micro_polish|aesthetic_coherence|visual_identity|critique_input_hash"
```

Observed:

```text
## Aesthetic Intent Calibration
Host LLM MUST apply this fixture-specific aesthetic target when filling `top_tier_audit.aesthetic_coherence`, `editorial_art_direction.visual_identity`, `editorial_art_direction.aesthetic_risk`, and `editorial_art_direction.tikz_vs_svg_polish_trigger`.
- Target journal: Nature Materials
- Visual maturity: editorial
- mature_restraint: Prefer restrained, publication-grade visual hierarchy over decorative or cartoon-like emphasis.
- toy_diagram severity=MAJOR: Oversized arrows, rounded generic boxes, unmodulated flat colors, or poster-like decorative gradients.
- svg_micro_polish path=ready_for_svg_polish: TikZ is semantically correct but print-scale label, stroke, or spacing refinement still limits journal polish.
critique_input_hash: sha256:24bf7b615b580ce750985178586f00a9c8aac056f8539a41f0115afbed758481
```

`/fig_status` then surfaced the expected freshness result:

```bash
uv run python3 scripts/status.py examples/fig1_overview_v2_pair_001_vault
```

Observed:

```text
States: render=FRESH critique=STALE export=TRACKED_GOLDEN acceptance=NOT_ACCEPTED workflow_ready=false golden_ready=false release_ready=false final_ready=false
Explanation: critique_stale — critique.md is stale against the current critique input hash.
```

## Judgment

The dogfood result is useful. The new fixture-specific aesthetic target is
visible to host critique and participates in critique freshness. A stale
pre-intent `critique.md` cannot silently remain fresh after the aesthetic target
changes.

This pass intentionally stops before rerunning host vision critique. The next
real figure-work step is `/fig_critique fig1_overview_v2_pair_001_vault`, then
adjudication and loop rerun.
