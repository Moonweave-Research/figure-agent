# Theory Guard: fig1_overview_v3_pair_001_vault

## Purpose

This guard catches scientific and narrative violations before visual polish or
publication acceptance. It is a human/host-review acceptance surface, not a
compiler gate.

## Guard Table

| ID | Severity | Claim | Check Method | Pass/Fail Evidence |
|---|---|---|---|---|
| TG-A-001 | BLOCKER | Panel A polymer topology is linear poly(S-r-DIB), not a 2D DIB-polysulfide network. | Source review against `briefing.md`, `design.md`, `critique.md`, and rendered Panel A. | Pass for this loop: `critique.md` author resolution selects linear topology; `authoring_contract.md` marks the old network reference as anti-reference; fresh critique found no BLOCKER/MAJOR topology finding. |
| TG-C-001 | BLOCKER | Panel C shallow and deep traps coexist in the same polymer matrix, with same-matrix mixed trap sites. | Source/render review of C-L3 and C-R2/C-R3. | Pass for this loop: `briefing.md` invariant 8.3 requires mixed sites; no active patch reopens spatial segregation; fresh critique found no BLOCKER/MAJOR Panel C finding. |
| TG-CFG-001 | BLOCKER | C/F/G color convention is consistent: shallow = blue, deep = red, trapped charge/Coulomb markers = red charge cue. | Compare Panel C trap levels, Panel F lobes/labels, and Panel G charge/force cue. | Pass for this loop: `briefing.md` invariants 8.2 and 8.6 plus v7 C/F notes preserve the convention; fresh critique found no BLOCKER/MAJOR color finding. |
| TG-D-001 | BLOCKER | Panel D non-Debye power-law tails remain above the Debye reference at long times. | Source coordinate review plus rendered Panel D visual check. | Pass for this loop: `subregion_iteration_log.md` records v6 D-2/D-3 fix; fresh critique found no BLOCKER/MAJOR non-Debye finding. |
| TG-G-001 | BLOCKER | Panel G **result zone** is Coulomb-only; Maxwell attraction and actuator framing are absent from result zone. | Source/render text and arrow review of Column F result zone (post-v8.6) / Panel G (pre-v8.6). | Pass for this loop: scope narrowed to the Column F result zone per §8.5 amendment; the result zone remains Coulomb-only and does not show actuator framing. |
| TG-G-002 | BLOCKER | Column F (v8.6 mechanical column) Maxwell-vs-Coulomb contrast convention: apparatus zone shows baseline Maxwell attraction on neutral polymer (neutral gray dashed, cGray!55!black, 0.45pt); result zone shows Coulomb repulsion winning against this baseline (bold cRed!80 solid, 0.7pt). Color/weight tier asymmetry MUST signal "Coulomb wins." | Source/render review of Column F apparatus + result zone color, weight, dashed/solid discrimination. | Pass for this loop: Column F preserves lower-tier Maxwell baseline styling and stronger Coulomb repulsion styling; Maxwell is not promoted above the Coulomb result cue. |
| TG-ROW2-001 | BLOCKER | Row 2 shows three independent evidence spokes from Panel C: kinetic, ISPD, and mechanical. | Source/render review of Row2-BR1/Row2-BR2 labels and geometry. | Pass for this loop: `briefing.md` invariant 8.7 and v7 spoke update preserve three modalities; fresh critique found no BLOCKER/MAJOR Row 2 finding. |
| TG-B-001 | MAJOR | Composition labels S60/S70/S75/S85 appear only in Panel B. | Source text search and render review. | Pass at source level: composition-label matches are confined to Panel B source/comments and briefed forbidden examples, with no Row 2 composition labels in TikZ. |
| TG-EF-001 | MAJOR | Panel E and F read as one ISPD evidence line, with E raw signal and F derived trap distribution. | Render/source review of E/F pairing arrow and labels. | Pass at source level: `V_s(t)` raw signal, E->F `ISPD` inter-arrow, and `g(E_t)` derived panel are present in TikZ lines 528-606. |
| TG-PUB-001 | ACCEPTANCE | Publication compliance is not inferred from compile/export; reference provenance and AI-image policy remain separately reviewed. | Quality audit and decision doc. | Closed for this loop as `submission-safe: false`; target-journal policy remains a required future input before `accepted: true`. |

## Acceptance Rule

- Any BLOCKER fail keeps `accepted: false`.
- `accepted: true` requires all BLOCKER items pass, all MAJOR items either pass
  or have explicit author-accepted residual risk, fresh critique/export
  evidence, and publication-compliance review.
- This guard cannot by itself make the figure submission-safe; it only records
  theory and narrative readiness.
