# Bound authoring execution: fig1_composition_comparison_v1

## Output and attempt boundary
- Resolve every repository path from the repository root.
- Do not change directory before resolving paths.
- Write exactly one new source to [examples/fig1_composition_comparison_v1/review/failure-first/comparable-v1/free_composition_generated.tex].
- Do not create an intermediate subdirectory beneath [examples/fig1_composition_comparison_v1/review/failure-first/comparable-v1].
- Start from the declared blank artifact; perform one attempt only.
- Do not inspect or repair historical generated sources.
- Read repository file content only from [AGENTS.md] and [styles/polymer-paper-preamble.sty] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.tex] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.contract.yaml] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.transfer.yaml]; all other required authoring context is already bound below.

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
  - [A] sulfur-rich polymer identity
  - [B] sulfur-content composition series
  - [C] localized shallow and deep trap landscape
  - [D] transient-current kinetic evidence
  - [E] ISPD-derived trap distribution evidence
  - [F] floating cantilever Coulomb response
- Binding fixture briefing (verbatim):

# Fig1 composition comparison v1

Create one standalone scientific figure explaining charge trapping in a
sulfur-rich polymer. The figure must cover six scientific obligations: material
identity, sulfur-composition variation, shallow/deep localized traps,
transient-current decay, noncontact surface-potential evidence, and the floating
cantilever Coulomb response.

The obligations may be grouped, scaled, or sequenced as the author judges best.
No grid, hero panel, panel rectangle, coordinate, or fixed reading path is
prescribed. Panel letters A--F may be used only when they improve manuscript
readability. Preserve the declared scientific relations and distinguish
qualitative concepts from measured data.

The grounded voltage-source return in the mechanical scene must not imply that
the sample or cantilever is grounded. Machine checks are diagnostic only; a
named human review is required for any quality or publication judgment.

- Semantic claim [C:trap-landscape]: shallow and deep trapping states coexist in a sulfur-rich polymer.
- Semantic claim [D:current-decay]: under constant voltage, trap-mediated transient current decays with time.
- Semantic claim [F:floating-topology]: the grounded source return does not ground the sample or cantilever.
- Locked invariant [C:energy-orientation]: energy increases upward; deeper wells are lower in the diagram.
- Locked invariant [F:force-direction]: the Coulomb-force arrow points away from the active electrode.
- Do not imply physics or quantitative relations absent from the declared contracts.

## Curated visual assets
- Curated asset [panel_f_floating_cantilever]: [styles/snippets/panel-f-floating-cantilever.tex]
  - Reuse curated visual asset [panel_f_floating_cantilever] from [styles/snippets/panel-f-floating-cantilever.tex]. Do not redraw its owned geometry.
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
- Declared model: gpt-5.5
- feedback_rounds: 0
- manual_repairs: 0
- filesystem_read_isolation: unavailable
- publication_acceptance: not_claimed
