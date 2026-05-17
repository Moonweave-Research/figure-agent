---
schema: figure-agent.critique.v1
fixture: fig1_overview_v2_pair_001_vault
generated_at: 2026-05-17T03:15:00+09:00
last_updated_at: 2026-05-17T04:30:00+09:00
verdict: revise
verdict_post_tier1_tier2: minor_polish_only
panels: []
findings:
  - id: C001
    severity: MAJOR
    category: hierarchy
    tex_lines: [382, 397]
    observation: >-
      Panel C-R1b Gaussian DOS overlay (shallow cBlue!18 fill σ=0.085 + deep
      cRed!18 fill σ=0.18) is present in source but barely registers in the
      rendered PNG — the bell-curve fills sit immediately right of the Energy
      axis at x=10.55 with only ~0.28–0.32 cm horizontal extent and opacity 0.55.
      At 178 mm full-width render they read as thin colored slivers rather than
      visible distribution shapes. The Q8 LOCKED narrative ("continuous Gaussian
      DOS = Mott-CFO + Bässler disorder") is not delivered to the reader; the
      panel reads as discrete 2-level traps.
    suggested_fix: >-
      Increase Gaussian fill horizontal scale from 0.28/0.32 → ~0.45/0.55 so the
      bell shape is visually recognizable as a distribution. Optionally lift
      fill opacity 0.55 → 0.70 to register against white background. Keep
      outline 0.50/0.55pt.
    status: resolved
    resolution_iteration: v8.7+tier1
    resolution_note: >-
      Applied scale 0.28/0.32 → 0.45/0.55 + opacity 0.55 → 0.70. Deep red
      Gaussian now clearly visible as bell shape; shallow blue Gaussian visible
      but lighter (consistent with cBlue!18 vs cRed!18 inherent contrast). Q8
      "continuous DOS" narrative now delivered.
  - id: C002
    severity: MAJOR
    category: hierarchy
    tex_lines: [240, 245]
    observation: >-
      Panel B-4 sample-boundary dividers (cGray!25, 0.18pt, densely dotted, at
      y=7.60/7.00/6.40 spanning x=3.85..6.30) are rendered but visually
      invisible at 178 mm width — the 4 zigzag chains read as a single bundled
      column rather than 4 distinct samples. This is exactly the failure mode
      §13.2 B-4 was added to prevent ("pre-v8.4 chain bundle risk"). Acceptance
      criterion #1 in panel_goals.md Panel B fails.
    suggested_fix: >-
      Lift divider tone from cGray!25 → cGray!40 while holding line width at
      0.18pt (width >0.20pt is §13.2 forbidden cap). cGray!40 at 0.18pt should
      register at print scale without crossing into data-axis weight.
    status: resolved
    resolution_iteration: v8.7+tier1
    resolution_note: >-
      Applied cGray!25 → cGray!40. Dividers now register as 4 distinct sample
      boundaries; chain-bundle misread risk eliminated. Width held at 0.18pt
      per §13.2 cap.
  - id: C003
    severity: MAJOR
    category: hierarchy
    tex_lines: [754, 756]
    observation: >-
      Column F apparatus-zone PSU pulse trace (3-segment square wave on PSU
      display, cGray!60!black at line width 0.20pt) is invisible at print scale —
      the "pulsed-bias protocol" signal is lost, undermining the narrative that
      V_active is a pulse train (not DC). Known issue from HANDOFF_v8.7.md §5.
    suggested_fix: >-
      Increase pulse-trace line width 0.20pt → 0.40pt (annotation tier) and
      darken cGray!60 → cGray!75 to match SMU / electrode stroke tone.
    status: partial
    resolution_iteration: v8.7+tier1+tier2
    resolution_note: >-
      Applied (a) width 0.20pt → 0.40pt → 0.60pt + tone cGray!60 → cGray!75.
      Trace marginally more visible but PSU box is small (~5mm × 4.5mm at
      178mm width) so 0.10cm-wide square-wave segments don't register
      strongly. Defer to (b) widen trace horizontally (requires PSU box
      widen — coordination with leads + V_active label) OR (c) accept and
      rely on V_active label for pulse-protocol identity. Recommend (c) for
      next session — diminishing returns on weight-only tuning.
  - id: C004
    severity: MINOR
    category: label_placement
    tex_lines: [167, 172]
    observation: >-
      Panel A `-(S)_x-` composition label anchored at (1.90, 7.55) sits over the
      polymer-row geometric center (ring row spans x=0.75..3.00, center
      x≈1.875). However the wash ellipse (centered x=1.85) and S₈ inset at
      (3.05, 8.45) pull the panel's visual center rightward, making the label
      read as offset toward the LEFT half of the row. Acceptance criterion #3
      (panel_goals.md Panel A) partial pass.
    suggested_fix: >-
      Shift label anchor x: 1.90 → 2.10 to compensate for S₈-inset visual pull.
      Keep y=7.55. Alternative: accept current placement as anchored on the
      polymer-row geometric center (not the panel-wide visual center).
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: Applied x 1.90 → 2.10. Label centers more naturally over polymer row.
  - id: C005
    severity: MINOR
    category: hierarchy
    tex_lines: [436, 442]
    observation: >-
      Panel C-R4 escape arrows (shallow short from y=7.55→7.82 / deep long from
      y=6.20→7.82) share line width 0.35pt and Stealth tips with only ~0.4pt
      difference in head dimensions (3pt vs 2.6pt length / 2.4pt vs 2pt width).
      The "shallow easy escape vs deep hard escape" asymmetry is not
      perceptually distinct at 178 mm render. Acceptance criterion #7
      (panel_goals.md Panel C) partial pass.
    suggested_fix: >-
      Either (a) lift shallow arrow line width 0.35 → 0.50pt while keeping deep
      at 0.35pt (weight = ease), OR (b) widen shallow head 2.4 → 3.2pt and
      shrink deep head 2.0 → 1.6pt (visible head-size delta). Do not change
      colors or dashed pattern (§9 dashed semantic preservation).
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: Applied option (a) shallow 0.35 → 0.50pt. Weight asymmetry visible — shallow reads as "easier escape".
  - id: C006
    severity: MINOR
    category: hierarchy
    tex_lines: [820, 830]
    observation: >-
      Column F apparatus-zone neutral polymer cantilever (cAmber!18 opacity 0.6
      at x=12.40..12.50 spanning y=2.90..4.10) is so pale that the reader cannot
      easily distinguish it from background. The apparatus narrative "neutral
      polymer + Maxwell baseline attraction" loses its subject — Maxwell arrow
      and F_Maxwell label are prominent but what they act on is not clearly
      visible. Acceptance criteria #1 and #3 (panel_goals.md Column F) partial
      pass.
    suggested_fix: >-
      Lift opacity 0.6 → 0.75 OR shade cAmber!18 → cAmber!25. Keep "pale"
      register relative to result-zone polymer (cAmber!22→cAmber!42 saturated
      gradient) but make the apparatus polymer perceptible as a distinct object.
    status: partial
    resolution_iteration: v8.7+tier2
    resolution_note: >-
      Applied opacity 0.6 → 0.75. Polymer slightly more visible but the 0.10cm
      thin rectangle width limits perceptibility regardless of opacity. Next
      iteration could widen polymer (12.40..12.50 → 12.35..12.55, 0.10 →
      0.20cm) — but this may misalign with result-zone cantilever root (11.625).
  - id: C007
    severity: MINOR
    category: hierarchy
    tex_lines: [549, 553]
    observation: >-
      Column D SMU box readout indicator (small rectangle at (0.85, 3.50)..
      (1.20, 3.62) at line width 0.18pt) is barely visible at print scale. Less
      critical than the pulse trace (C003) — SMU box is already clear via V/A
      symbols and SMU italic label — but the readout cue is decorative dead
      weight at current visibility.
    suggested_fix: >-
      Either lift line width 0.18 → 0.30pt OR delete the readout indicator
      entirely. Recommend delete: V/A + SMU label already carry source-meter
      identity, less apparatus-zone visual noise.
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: Deleted readout rectangle. SMU box cleaner; V/A + SMU label carry identity.
  - id: C008
    severity: MINOR
    category: hierarchy
    tex_lines: [663, 666]
    observation: >-
      Column E V_s meter mini-readout indicator (horizontal line at (8.30, 3.75)..
      (8.85, 3.75) at line width 0.15pt) is essentially invisible at 178 mm
      render. Known issue from HANDOFF_v8.7.md §5. The "V_s meter" italic label
      inside the box already communicates the function.
    suggested_fix: >-
      Same pattern as C007: lift line width 0.15 → 0.30pt OR delete. Recommend
      delete for consistency with C007 apparatus-zone cleanup.
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: Deleted readout line. V_s meter label carries function.
  - id: C009
    severity: MINOR
    category: label_placement
    tex_lines: [817, 825]
    observation: >-
      Column F apparatus-zone 'F_Maxwell (baseline)' inline label sits in the
      narrow gap between the pale neutral polymer (x=12.40..12.50) and the
      cross-hatched electrode (x=13.55..13.80) at y≈3.10. The label compresses
      against the air-gap dimension cue and the Maxwell arrow itself. Known
      issue from HANDOFF_v8.7.md §5 — visual crowding.
    suggested_fix: >-
      Move label outside the arrow path: anchor below at y≈2.75 with a skinny
      leader (0.20pt cGray!60 line) up to the Maxwell arrow midpoint. Frees the
      apparatus-electrode gap for the Maxwell arrow + air-gap dimension only.
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: >-
      Applied simpler fix: anchor south → north + y 3.52 → 3.45 so label sits
      directly below arrow line (no leader needed). Arrow path now clear.
  - id: C010
    severity: NIT
    category: style
    tex_lines: [583, 587]
    observation: >-
      Column D ground symbol (RIGHT side of bottom electrode, x=3.65..3.73,
      three horizontal bars at y=3.21/3.18/3.15) is correct topology but renders
      as a tiny stack of thin dashes at print scale. The '+' polarity sign in
      Column E corona is larger and could be misread as carrying more semantic
      weight than the ground.
    suggested_fix: >-
      No fix required if convention is recognized. If reader confusion observed
      in N≥2 future dogfood, lift ground-bar widths 0.30/0.25/0.22 → uniform
      0.32pt.
    status: open
  - id: C011
    severity: NIT
    category: style
    tex_lines: [765, 773]
    observation: >-
      Column F clip-mount stipple (Conrad 2016 small-triangle pattern above the
      clip block, 4 triangles at line width 0.18pt) is hard to identify as
      "fixed mount" indicator at 178 mm. The clip block plus implicit fixed
      support from x-alignment with the result clip carries most of the weight.
    suggested_fix: >-
      No urgent fix. If clip-FIXED narrative needs reinforcement, lift triangle
      line width 0.18 → 0.28pt OR add a single horizontal hatch below clip block
      as alternative fix-cue.
    status: open
  - id: C012
    severity: MINOR
    category: hierarchy
    tex_lines: [560, 580]
    observation: >-
      Column D MIM sample stack: top hatched electrode (y=3.85..3.95, 0.10 cm
      thick) + cAmber polymer film (y=3.40..3.85, 0.45 cm thick) + bottom
      hatched electrode (y=3.30..3.40, 0.10 cm thick). The polymer film
      dominates visually (~4.5× the height of each electrode); electrodes read
      as thin hatched lines rather than as part of a Metal/Insulator/Metal
      sandwich. The MIM terminology in the apparatus narrative implies three
      layers of comparable visual weight.
    suggested_fix: >-
      Either (a) increase electrode thickness 0.10 → 0.15 cm (compress polymer
      to 0.35 cm to fit zone), OR (b) add explicit 'top electrode' / 'polymer
      film' / 'bottom electrode' inline 5pt labels at the right edge so the
      3-layer architecture is named even if visual weight is asymmetric.
      Recommend (b) — preserves polymer-film emphasis while clarifying
      structure.
    status: resolved
    resolution_iteration: v8.7+tier2
    resolution_note: >-
      Applied simpler variant: added single 'MIM stack' label at apparatus-zone
      top-left (0.10, 4.20) instead of 3 per-layer labels. Names the
      architecture without disturbing the lead routing or ground placement.
      If domain-reader confusion persists, escalate to option (b) with
      per-layer labels in next iteration.
---

# Vision Critique — fig1_overview_v2_pair_001_vault

**Verdict: revise.** All six BLOCKER theory invariants in the authoring contract pass at visual inspection — linear Panel A topology, Panel C mixed traps, shallow=blue / deep=red color convention, Panel D power-law above Debye, Column F apparatus-Maxwell vs result-Coulomb tier (color asymmetry reads correctly), and Row 2 three independent spokes (clear fan-out from Panel C, not a D→E→F chain). TG-G-002 (Maxwell vs Coulomb discrimination) passes: Maxwell light-pink dashed thin in apparatus zone, Coulomb bold red solid in result zone — weight and color tier difference perceptible at peripheral vision.

The figure is scientifically and narratively correct. Twelve findings flag visibility and hierarchy gaps where intended elements either fail to register at 178 mm print scale (Gaussian DOS overlay, B-4 dividers, PSU pulse trace, V_s meter readout, apparatus polymer cantilever, clip-mount stipple) or where label placement compresses against neighbors (F_Maxwell label, A-3 (S)_x composition tag). None of these alter the physics or narrative; all are revisable via line-width / opacity / position deltas without structural changes.

## Priority groupings for author triage

**Tier 1 (MAJOR, fix before next critique):** C001 Gaussian DOS overlay, C002 B-4 dividers, C003 PSU pulse trace. All three involve elements that are *present in source* but *invisible at render scale* — highest-value fixes because the spec narrative breaks without them.

**Tier 2 (MINOR, fix this session or accept):** C004 (S)_x label centering, C005 escape-arrow asymmetry, C006 apparatus polymer opacity, C007 SMU readout, C008 V_s meter readout, C009 F_Maxwell label crowding, C012 MIM stack layer hierarchy.

**Tier 3 (NIT, accept):** C010 ground symbol weight, C011 clip-mount stipple — both pass at desktop view, marginal at print.

## What this critique cannot verify

- **Reference-grounded panel comparison**: `spec.yaml` panels A–G declare `bbox_pdf_cm` but no per-panel `reference_image`, so the brief skipped panel-level comparison. Only the figure-level style anchor (`reference/codex_gen_overview_v1.png`) was implicitly available — not formally diffed in this pass.
- **Quantitative ratios**: E-7 vs E-8 Gaussian peak ratio target 1.86× (Q4 LOCKED) is visually plausible (~2×) but not measured against spec.
- **Print-scale absolutes**: "invisible at 178 mm" findings are based on the embedded PNG resolution; actual TIFF 600 DPI print may register some elements that this critique flagged.

## Cross-binding sanity (§13.9)

- **Binding-1 (color)**: shallow=blue / deep=red consistent across Panels C, E, F. No drift detected.
- **Binding-2 (● marker)**: same circle glyph in Panel C matrix + C-R energy levels + F q_tr. Consistent.
- **Binding-3 (E↔F derivation)**: V_s decay → 'derive' inter-arrow → g(E_t) Gaussians chain reads as paired ISPD view. Note: the inter-arrow label says 'derive' not 'ISPD' (per v8.7 iter 2 fix replacing redundant ISPD). Briefing §13.6 E-5 spec is stale.
- **Binding-4 (D↔F kinetic↔density)**: 'deep-rich' D-5 curve label + deep Gaussian dominant E-8 + q_tr cRed in F-6 — same trap-species story holds.

## Recommended next loop

Apply Tier 1 fixes (C001 / C002 / C003), recompile, re-critique. Tier 2 can batch with caption.md update. Tier 3 deferred unless flagged in subsequent dogfood. After Tier 1 + Tier 2 closure, run N≥3 dogfood gate before any `accepted: true` claim.

## Prior critique history

Pre-v8.6 findings (C001 Coulomb-repulsion label collision, C002 dashed-leader pre-resolution, C003 Panel A topology decision) were all closed in earlier loops (commits `49b6af0`, `b2f3...`, et al.). Status preserved in git history at parent commits of `b9840fc`. This v8.7 critique resets finding IDs starting from C001 since the figure has been structurally rebuilt (Row 2 4-panel → 3-column restructure + apparatus zones upgrade).
