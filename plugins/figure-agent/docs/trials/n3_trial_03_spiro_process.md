# N=3 Trial: Spiro-OMeTAD Processing Schematic (2026-05-04)

## Input & Ground Truth

**Figure source:** External (Nature Reviews Materials style reference, learning-data leakage caveat)  
**Codex image-gen PNG:** `/Users/choemun-yeong/.codex/generated_images/019dedd6-ae63-76b1-a4d7-9af1864d636e/_image_id_.png`  
**Figure type:** Two-panel process flow + material microstructure (3D isometric + insets)

**Reference figure intent (paraphrased):**
- Panel (a): 3D film slab (spiro-OMeTAD, LiTFSI) under UV/O₂, microstructure inset (rod/sphere composition)
- Panel (b): Solution chemistry (beaker, CO₂, precipitation) → "filter prepare film" → refined film + microstructure inset
- Style: Nature Reviews, 3D isometric, dual-inset semantic

## Channels

### Channel (1): Semantic Understanding (PNG → briefing)
**[CAVEAT: learning-data leakage — Nature figure likely in training set]**

Subagent reading (PNG-only) captured:
- Panel (a) intent (film + UV/O₂ + microstructure)
- Panel (b) intent (beaker + solution + precipitate → refined film)
- Dual-inset semantic
- Vocabulary: spiro-OMeTAD, LiTFSI, precipitate, microstructure

Match vs. reference: ~90% — leakage caveat; measurement weak.

### Channel (2): Paper-Quality Reach (PNG → briefing → TikZ)

**Iteration path:**
- iter 0: 0 collisions (first trial to achieve 0 first-pass), 15 clashes
- iter 1: 0 collisions, 15 clashes (no conflict-driven change attempted; layer structure inert)

**Final render vs. Codex PNG:**
- ✓ Film slabs rendered (via `\IsoBlock` macro — first successful 3D primitive fit)
- ✓ UV/O₂ arrows, beaker, precipitate, process arrow ✓
- ✓ Inset (a) microstructure (molecules rendered)
- ✗ Inset (b) microstructure empty (semantic gap in TikZ author — subagent abstained on complex nested structure)

**Paper-quality reach verdict:** 85% (macro-driven clean render, but panel-b inset underspecified)

### Channel (3): Premium Feel
- Style Lock consistency ✓
- Visual hierarchy: clear (process flow left→right, insets integrated)
- Remaining clashes (15) mostly aesthetic (overlapping small labels, inset connector lines crossing stroke patterns)

## Macro Coverage

| Macro | Used | Notes |
|---|---|---|
| `\IsoBlock` | ✓ YES | First successful use case; renders 3D film slab geometry |
| `\UVArrow` / `\ArrowBundle` | NO | hand-coded |
| `\Beaker` | NO | hand-coded (geometry primitive, candidate macro) |
| `\CircularInset` | NO | hand-coded (semantic structure: centered label + connector line, candidate) |
| `\ProcessArrow` | NO | hand-coded |

**N=3 macro candidates (cross-cutting, not physics-specific):**
1. `\Beaker[<fill>, <label>]` — vessel/container with optional fill pattern and precipitate marker
2. `\CircularInset[<label>, <inner_env>]` — circular frame + connector line + internal content box
3. `\FilmStack[<nLayers>]` — isometric film slab (currently `\IsoBlock`, could generalize to multi-layer)
4. `\UVRayBundle[<angle>, <count>]` — parallel UV arrow bundle
5. `\ProcessArrowStep[<label>]` — process flow connector with text label (e.g., "Filter, prepare film")

## Cross-Trial Pattern

| Dimension | N=1 (trap-depth) | N=2 (actuation) | N=3 (spiro-process) | Pattern |
|---|---|---|---|---|
| **First-pass collisions** | 8 | 4 | **0** | inverse with macro density? |
| **Semantic fit** | physics (5 macro) | mechanism (0) | material process (1 macro + insets) | \IsoBlock fit explains 0-collision |
| **Clash distribution** | complex stacks (39) | simple geometry (13) | moderate insets (15) | table-like < procedural ≈ nested |
| **Iteration-to-clean** | 2 iter | 1 iter | 0 iter | more structured → faster |

**Insight:** Macro-heavy figures produce more first-pass clashes (internal text-on-path conflicts) but smaller delta iter 1→2. Bare-hand code produces fewer clashes but sometimes semantic gaps (N=3 panel-b inset). **Hybrid approach (macro for clean primitives + hand for flex semantics) may balance both.**

## Decision Frame: α vs γ

**Option α (hold L3 at 65%):**
- BandDiagram + BellCurve decouple frozen
- BandDiagram Gap 3/4 (CB/VB label hardcoding) remains unresolved
- Future fixtures must work around gaps (or accept WARN clashes)
- Frees capacity for briefing automation + Inkscape integration

**Option γ (continue L3 macro):**
- Commit to BandDiagram Gap 3 + Gap 4 fix + 4 new cross-cutting macros
- Reduced WARN clashes in physics-heavy figures
- Delays briefing/Inkscape work

**N=3 data:** Gap 3/4 remain pressure points even in non-physics context (e.g., spiro uses `\IsoBlock` cleanly, but BandDiagram issues don't appear here). Cross-cutting macros (Beaker, Inset, UVBundle, ProcessArrow) are **generic leverage** — applicable across domains (materials, biology, chemistry).

**Recommendation (data-informed, not decisive):** `α` (hold) is safer. New cross-cutting macros (5 candidates) are **generic wins**, not physics-locked. Briefing automation is documented as bigger lever (session_handoff_2026_05_03_late). Defer BandDiagram refinement to v0.3 post-briefing.

## Residual Risks / Open Questions

1. **Inset semantic complexity:** When subagent faces nested insets (panel-b microstructure), does it need explicit structure hints? (candidate: coordinate_hints.yaml expansion)
2. **IsoBlock style drift:** Film rendered light gray, not reference dark navy — macro tinting applied, but intent mismatch. Parametrize color or document limitation?
3. **Clash quality:** 15 remaining clashes are small-label overlaps. Acceptable for Nature-style draft, but edge case for high-density schematics.
4. **Learning-data leakage:** N=3 reference is external (high chance LLM saw it in training). For future trials, use figures <2022 or explicitly synthetic prompts.

---

## Session Notes

- Session started fresh (clear + reboot from memory)
- Methodology held across 3 N's (PNG → subagent briefing → TikZ → compile → metric)
- Trial data (fixture paths + PDFs + WARN logs) committed to git; trial docs live in `docs/trials/`
- Next session can extend to N=4 (biological/synthetic domain) or close-loop on α/γ decision via roadmap-layer3-6.md Phase 1.1 macro audit
