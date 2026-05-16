---
schema: figure-agent.critique.v1
fixture: fig1_overview_v2_pair_001_vault
generated_at: 2026-05-16T02:51:42Z
last_updated_at: 2026-05-16T16:30:00+09:00
verdict: minor_polish_only
author_resolution_at: 2026-05-16T10:40:00+09:00
author_resolution: "linear poly(S-r-DIB) primary microstructure selected; old Panel A network reference is anti-reference topology evidence"
panels: []
findings:
  - id: C001
    severity: MINOR
    category: label_placement
    tex_lines: [728, 733, 735]
    observation: >-
      The compile collision report flags overlap between the two-line
      "Coulomb" / "repulsion" label stack. This does not invert the Panel G
      Coulomb-only physics, but the two labels are tight enough to remain a
      visual-polish risk before manuscript acceptance.
    suggested_fix: >-
      Increase the y separation between the two Panel G Coulomb-repulsion label
      nodes or make the second line slightly smaller while preserving the
      leftward Coulomb arrow.
    status: resolved
    resolution_commit: 49b6af0
    resolution_note: >-
      v8.2 polish — Coulomb / repulsion anchors flipped to south east /
      north east at y=2.04/1.94 so the arrow line at y=1.99 sits BETWEEN
      the labels. IoU=0.157 collision eliminated.
  - id: C002
    severity: MINOR
    category: label_placement
    tex_lines: [199, 205]
    observation: >-
      The compile collision report flags tight spacing between "Sulfur-rich
      polymer" and "poly(S-r-DIB) linear copolymer". The labels preserve the
      resolved linear-topology claim, but the stack is close enough to merit
      final visual polish.
    suggested_fix: >-
      Add a small vertical offset between the Panel A title and subtitle or
      reduce the subtitle size slightly. Do not change the "linear copolymer"
      wording unless manuscript chemistry changes.
    status: resolved
    resolution_commit: 49b6af0
    resolution_note: >-
      v8.2 polish — subtitle 'poly(S-r-DIB) linear copolymer' dropped from
      y=5.55 to y=5.42 to clear descender / ascender intersection. IoU=0.055
      collision eliminated.
  - id: C003
    severity: MINOR
    category: style
    tex_lines: [177, 187, 706, 711]
    observation: >-
      The visual-clash report still flags several text-on-path/text-on-fill
      candidates around sulfur and charge symbols. These are common false
      positives for intentionally embedded atom/charge glyphs, but they should
      remain visible in the acceptance audit because dense symbolic regions are
      where final crop inspection usually fails first.
    suggested_fix: >-
      Treat the flagged glyph regions as manual crop-review targets before any
      accepted:true decision. Patch only if the rendered crop shows actual
      illegibility.
    status: accepted_residual_risk
post_critique_changes:
  - commit: 49b6af0
    label: v8.2 polish — IoU collision closure
    summary: Resolved C001 + C002. Also moved Panel A "inv. vulc." (2.55, 8.00) → (2.15, 7.82) to clear the S8 vertex bump (residual IoU=0.068/0.092 vs chain composition label, below 0.1 visual-defect threshold).
  - commit: 39b5e44
    label: v8.3 audit closure — briefing-grounded gap fixes
    summary: |-
      Full briefing.md (524 lines) ↔ .tex (754 lines) audit identified 4 gaps
      not surfaced by this critique pass:
      - Gap #1 C-R1b shallow Gaussian σ 0.06 → 0.085 (briefing §13.3 spec)
      - Gap #2 C-R5 ΔE_t arrow + label color cGray!70!black → cRed!75!black
        (binds depth scalar to deep trap species per §8.6 / §13.9 Binding-1)
      - Gap #3 G-6 Coulomb/repulsion label coords: briefing §13.8 + §13.10
        updated to record v8.2 anchor flip pattern (briefing predated v8.2).
      - Gap #4 Row2-Caption em-dash: `--` → `---` (rendered – → —)
post_v8_3_metrics:
  collision_candidates: 2
  visual_clash_candidates: 38
  collision_residuals:
    - inv. vulc. × −(S)x− composition label, IoU=0.068/0.092 (below 0.1 threshold; v8.2 polish trade-off — cleared S8 vertex bump at IoU=0.145)
---

# Vision Critique — fig1_overview_v2_pair_001_vault

Verdict: minor_polish_only (post-v8.3). The original critique pass (2026-05-16
02:51 UTC) found no new BLOCKER or MAJOR theory violations; verdict was
`revise` because of 3 MINOR label/glyph polish risks. Two of those (C001 +
C002) were closed by the v8.2 polish (commit 49b6af0). The remaining MINOR
(C003) is accepted residual risk pending manual crop review.

The figure is still not `accepted: true` because publication-compliance
(TG-PUB-001) and human visual crop review (QUALITY_AUDIT.md acceptance check
#3 / #4) remain outstanding. Theory invariants (TG-A-001 .. TG-ROW2-001) all
PASS at source level.

## Theory Adjudication

The previous Panel A topology conflict remains resolved on the linear side.
`authoring_contract.md` and `reference/reference_pack.md` make
`reference/sulfur_polymer_panelA_ref.png` an anti-reference for topology, so
the network-style reference must not drive a structural finding unless new
manuscript evidence changes the chemistry decision.

The main theory guard items pass at source-review level:

- TG-A-001: Panel A comments and labels preserve linear poly(S-r-DIB).
- TG-C-001: Panel C source keeps shallow/deep trap markers in the same polymer
  sheet and the energy diagram as a split view, not phase segregation.
- TG-CFG-001: C/F color semantics stay shallow blue and deep red; G uses red
  charge/force cues for trapped-charge mechanics. v8.3 strengthens this for
  C-R5 ΔE_t (Gap #2 closure: depth scalar now binds to deep red).
- TG-D-001: the Debye reference ends below the long-time power-law traces.
- TG-G-001: no Maxwell-attraction arrow or actuator framing is present.
- TG-ROW2-001: the three spokes remain kinetic, ISPD, and mechanical.

## Visual Adjudication (post-v8.3)

Compile succeeds with report-only warnings: 2 collision candidates (down from
3 at original critique time) and 38 visual-clash candidates (down from 45).

- C001 (Coulomb/repulsion stack): RESOLVED in v8.2 — anchor flip at y=2.04/1.94.
- C002 (Sulfur-rich/subtitle stack): RESOLVED in v8.2 — subtitle y=5.55→5.42.
- C003 (sulfur/charge glyph false positives): ACCEPTED_RESIDUAL_RISK — manual
  crop-review target.
- Residual collisions (inv. vulc. × −(S)x− composition label, IoU 0.068/0.092):
  the v8.2 polish trade-off — moved inv. vulc. from S8-vertex collision
  (IoU=0.145, MINOR) to a chain-composition-label proximity below the 0.1
  visual-defect threshold. Acceptable because (a) IoU below threshold,
  (b) human visual inspection of the rendered PNG shows both labels remain
  individually readable.

## Provenance Notes

Reference usage is bounded by `reference/reference_pack.md`. The figure-level
reference remains style/layout evidence only. The old Panel A network
reference is anti-reference evidence for forbidden topology transfer.

## Method Notes

This critique is report-only. The original critique was generated using the
host `/fig_critique` fallback flow (`scripts/critique_brief.py`, current
rendered artifacts, source review, compile visual-QA reports). The post-v8.3
update is a host-side reconciliation against v8.2 + v8.3 commit evidence; no
automatic edits were applied to the TikZ source by this update. A fresh
`/fig_critique` pass is the next gate before paper submission.
