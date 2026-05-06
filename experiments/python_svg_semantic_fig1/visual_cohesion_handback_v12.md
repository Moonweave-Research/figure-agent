# v12 Whole-Figure Visual Cohesion Handback

## Scope

`v12_whole_figure_visual_cohesion_and_style_tokens` is the first pass after the panel-by-panel audit. It does not redesign the semantic scene model and does not replace the v10/v11 payload-sampled DOS logic. The reference PNG remains layout/style evidence only, not ground truth or a pixel-tracing target.

## Audit Diagnosis Converted Into Checks

The v12 verifier adds composition checks for problems that were not covered by the v11 DOS-specific contract:

- Hero panel must expose a restrained `hero-caption` role and keep it to at most two rendered text lines.
- Electrical evidence panel must include an `electrical-conclusion` cue that ties P-E and current-decay evidence together.
- Interpretation flow must not revert to four boxed UI step cards; its `trap_model_flow` group can contain at most one visible `#f7f9fc` step frame.

These checks were confirmed RED before the rendering changes:

```text
v12 visual cohesion checks failed:
- electrical evidence panel missing v12 conclusion cue
- hero panel missing v12 restrained caption role
- interpretation flow uses too many boxed UI step frames: 4 > 1
```

## Rendering Changes

- Added shared typography/effect knobs in `engine/style.py` for hero title, support title, subtitle, section labels, annotations, and schematic stroke widths.
- Reduced hero typography and callout dominance while preserving the semantic `DeepTrapHero`, `BandDiagram`, `TrapLevelSet`, and `DOSLobes` payload objects.
- Flattened the hero band-edge badges and trap guide styling so the band/trap/DOS stack reads more like one schematic system instead of layered UI widgets.
- Reworked the interpretation flow from four boxed steps into a lighter inline relation: `I(t) ~ t^-n -> Debye exp(-t/tau) -> tau_d -> g(Et)`.
- Kept the mini-DOS shallow/deep lobe roles and compact trap-depth cue from v11, but reduced surrounding label hierarchy.
- Enlarged the electrical schematic plot footprint slightly and added a compact bottom conclusion cue connecting persistent P-E response and slow decay to deep trapping.

## Remaining Direction

v12 is not a final-quality declaration. The whole-figure audit still points to follow-up passes:

- Origin panel: compress the S8-to-Sx story and reduce checklist-like typography.
- Probe panel: flatten the 3D/clipart effect budget, reduce footer dominance, and make the force story read as one coherent physical scene.
- Global cohesion: normalize repeated labels, arrow styles, and support-card density targets across all five panels.

## Verification

The current v12 output was regenerated through `render_fig1_l1.py` and checked by `verify_fig1_semantics.py`. The final handoff should still include human visual review of `fig1_reference_semantic.png`, because the verifier only blocks known semantic and composition regressions.
