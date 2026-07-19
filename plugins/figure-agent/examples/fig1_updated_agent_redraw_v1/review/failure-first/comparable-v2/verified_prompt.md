# Bound authoring execution: fig1_updated_agent_redraw_v1

## Output and attempt boundary
- Resolve every repository path from the repository root.
- Do not change directory before resolving paths.
- Write exactly one new source to [examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v2/verified_generated.tex].
- Do not create an intermediate subdirectory beneath [examples/fig1_updated_agent_redraw_v1/review/failure-first/comparable-v2].
- Start from the declared blank artifact; perform one attempt only.
- Do not inspect or repair historical generated sources.
- Read repository file content only from [AGENTS.md] and [styles/polymer-paper-preamble.sty] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-real-feedback-loop/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.tex] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-real-feedback-loop/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.contract.yaml] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/fig3-real-feedback-loop/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.transfer.yaml]; all other required authoring context is already bound below.

## Mandatory standalone TikZ source requirements
- \documentclass[tikz,border=4pt]{standalone}
- \usepackage{tikz}
- \usepackage{polymer-paper-preamble}

## Style Lock authoring requirements
- Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, white, and gray.
- Keep every explicit line width at or above 0.25pt.
- Do not use local \tiny or \scriptsize font overrides.

## Semantic contracts and forbidden implications
- Required panels:
  - [A] polymer repeat-unit schematic
  - [B] sulfur-content composition series
  - [C] localized trap landscape, visual hero
  - [D] transient-current kinetic evidence
  - [E] ISPD-derived trap distribution evidence
  - [F] floating cantilever Coulomb response
- Binding fixture briefing (verbatim):

# Fig1 updated-agent redraw v1

This is an additive full-figure candidate, not a modification of the historical
v5f source. It must explain one narrative: sulfur-rich poly(S-r-DIB) has a
composition-dependent trap landscape, measured independently by transient
current and ISPD, with a mechanically visible Coulomb response.

`authority.yaml` pins the historical visual/narrative baseline and the
human-reviewed Panel F physics correction. The candidate is deliberately
independent source: it may reuse explicitly selected catalog assets with bound
hashes and contracts, but never historical candidate source blocks or an
unreviewed electrical interpretation. The first render is a structural baseline,
not an aesthetic replacement for v5f; human review must judge whether its visual
language actually improves on the reference.

Panel C is the sole hero. Panels D--F are compact evidence modules: retain
scientific relations, suppress instrument decoration, and keep labels outside
the depicted apparatus. In Panel F, the voltage-source return is grounded;
the sample and cantilever remain electrically floating.

Machine checks support inspection only. A named human review is required before
any development-baseline or publication claim.

- Semantic claim [C:trap-landscape]: shallow and deep trapping states coexist in a sulfur-rich polymer.
- Semantic claim [D:current-decay]: under constant voltage, trap-mediated transient current decays with time.
- Semantic claim [F:floating-topology]: the grounded source return does not ground the sample or cantilever.
- Locked invariant [C:energy-orientation]: energy increases upward; deeper wells are lower in the diagram.
- Locked invariant [F:force-direction]: the Coulomb-force arrow points away from the active electrode.
- Do not imply physics or quantitative relations absent from the declared contracts.

## Project and paper authoring rules
- Project rule [polymer_paper_project.cantilever-vertical-clip-top]: Draw the polymer cantilever vertical: clip/clamp on top, polymer hangs down, deflection sideways toward a side electrode. Horizontal cantilever orientation is wrong for this lab and its experiments.
- Project rule [polymer_paper_project.trap-colour-shallow-blue-deep-red]: Shallow traps and shallow states are blue or teal; deep traps and deep states are red. Keep this colour mapping consistent across every figure.
- Project rule [polymer_paper_project.panel-header-and-label-clearance]: Reserve a clear header band inside every panel for the panel letter and title. Keep body geometry and subtitles out of that band. Every label must clear other text, apparatus geometry, semantic paths, and the panel frame; use whitespace or a leader when direct placement does not fit. Do not solve clearance by forcing an equal-cell grid: composition remains author-selected.
- Paper rule [pair001.panel-c-hero-split]: Treat localized traps as the primary semantic hero and preserve the real-space plus energy-diagram split when transferring Fig 1 knowledge.
- Paper rule [pair001.panel-c-reference-gap]: When Panel C-like trap physics is reused, ask whether fresh figure research is needed before deep layout iteration.
- Paper rule [pair001.row2-apparatus-result-grammar]: For convergent evidence columns, keep each column split into apparatus context above and result semantics below.
- Paper rule [pair001.panel-d-do-not-transfer-triboelectric]: Reusing Panel D apparatus grammar must not transfer triboelectric mechanism or breakdown narrative into charge-trap figures.
- Paper rule [pair001.panel-e-side-view-apparatus]: Prefer side-view apparatus geometry for ISPD-style probe and grounded-substrate explanations unless a new source justifies isometric transfer.
- Paper rule [pair001.panel-e-probe-above-sample]: Bind probe, motion stage, sample, grounded substrate, and Vs meter labels to their physical components in ISPD-style apparatus panels.
- Paper rule [pair001.panel-f-cross-section-conventions]: Preserve cross-section conventions for electrode hatching, insulator stipple, parameter labels, and deflection arrows when transferring Panel F visual grammar.
- Paper rule [pair001.mobility-edge-label-clearance]: Keep mobility-edge labels clear of the reference line; a readable label must not sit on top of the semantic line it names.
- Paper rule [pair001.deep-escape-curve-clearance]: Treat trap-escape curves as semantic paths with explicit clearance from neighboring labels unless a panel-specific source overrides it.
- Paper rule [pair001.nc-clean-white-background]: For an NC main-text Fig 1, keep a clean white background; remove wash ellipses, background fills, wavy chain hints, and dotted column dividers.
- Paper rule [pair001.molecule-atoms-and-bonds]: Draw molecules such as S8 as atoms-and-bonds that carry molecular identity, not as a graphic icon, and drop redundant center identity labels.
- Paper rule [pair001.atom-label-adjacent-bond-terminus]: Place atom labels adjacent to the bond terminus rather than on the bond line, and originate reaction arrows from the molecule exterior.
- Paper rule [pair001.energy-reference-levels-horizontal]: Draw energy-diagram reference levels such as vacuum and band edges as band-spanning horizontal lines that read as reference levels, not as quantitative measurements.
- Paper rule [pair001.instrument-faceplate-bezel]: Give instrument boxes a dark-glass display plus an inner faceplate bezel for machined-panel weight; avoid flat or gizmo-style boxes.
- Paper rule [pair001.print-scale-registration]: Size and weight elements so they register at the real print scale (178 mm width), not only on screen; verify thin features and small shapes stay visible at print scale.
- Paper rule [pair001.hero-saturation-hierarchy]: Preserve panel visual hierarchy; the HERO panel must out-saturate secondary panels and the loudest color is reserved for the hero claim. Audit when a non-hero color reads as too prominent.
- Paper rule [pair001.label-tone-and-rotation-legibility]: Keep labels legible; avoid a same-tone label on a same-tone fill, and avoid near-vertical rotated labels because a sloped label on a near-vertical element is unreadable.
- Paper rule [pair001.iconic-register-is-intentional]: Iconic-cartoon abstraction of apparatus references in the evidence panels is briefing intent; do not treat iconic simplification as a defect to fix toward photorealism.
- Paper rule [pair001.no-actuator-framing-transfer]: Do not transfer actuator or MEMS framing into the charge-trap mechanical panel; the apparatus reference is borrowed for grammar only.

## Curated visual assets
- Curated asset [panel_f_floating_cantilever]: [styles/snippets/panel-f-floating-cantilever.tex]
  - Reuse curated visual asset [panel_f_floating_cantilever] from [styles/snippets/panel-f-floating-cantilever.tex]. Do not redraw its owned geometry.
  - Import [panel_f_floating_cantilever] with [\input{snippets/panel-f-floating-cantilever.tex}] so compile.sh can resolve it.
  - Invoke [panel_f_floating_cantilever] through [\PanelFFloatingCantilever{prefix}{(x,y)}] and adapt only [prefix, origin].
  - Preserve its declared role: floating charge-trapping cantilever opposite a driven electrode.
  - Known pitfall: caller owns panel labels, force arrows, and whole-panel composition
  - Known pitfall: do not connect the floating cantilever to the source-return ground
  - Known pitfall: do not reinterpret the fixed mechanical boundary as an electrical contact
  - Do not transfer: grounded sample or grounded cantilever
  - Do not transfer: bidirectional actuation sequence

## Declared layout directives
- No optional layout contract selected.

## Optional shape-profile directives
- No optional shape profile selected.

## Optional composition-profile directives
- No optional composition profile selected.

## Provenance and publication boundary
- Declared model: gpt-5.6-sol
- feedback_rounds: 0
- manual_repairs: 0
- filesystem_read_isolation: unavailable
- publication_acceptance: not_claimed
