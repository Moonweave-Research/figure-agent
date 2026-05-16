# Theory Guard: fig1_overview_v2_pair_001_vault

## Purpose

This guard catches scientific and narrative violations before visual polish or
publication acceptance. It is a human/host-review acceptance surface, not a
compiler gate.

## Guard Table

| ID | Severity | Claim | Check Method | Pass/Fail Evidence |
|---|---|---|---|---|
| TG-A-001 | BLOCKER | Panel A polymer topology is linear poly(S-r-DIB), not a 2D DIB-polysulfide network. | Source review against `briefing.md`, `design.md`, `critique.md`, and rendered Panel A. | Initial source evidence passes: `critique.md` author resolution selects linear topology; `authoring_contract.md` marks the old network reference as anti-reference. Final visual audit pending. |
| TG-C-001 | BLOCKER | Panel C shallow and deep traps coexist in the same polymer matrix, with same-matrix mixed trap sites. | Source/render review of C-L3 and C-R2/C-R3. | Initial source evidence passes: `briefing.md` invariant 8.3 requires mixed sites; no active patch reopens spatial segregation. Final visual audit pending. |
| TG-CFG-001 | BLOCKER | C/F/G color convention is consistent: shallow = blue, deep = red, trapped charge/Coulomb markers = red charge cue. | Compare Panel C trap levels, Panel F lobes/labels, and Panel G charge/force cue. | Initial source evidence passes from `briefing.md` invariants 8.2 and 8.6 plus v7 C/F notes. Final visual audit pending. |
| TG-D-001 | BLOCKER | Panel D non-Debye power-law tails remain above the Debye reference at long times. | Source coordinate review plus rendered Panel D visual check. | Initial source evidence passes: `subregion_iteration_log.md` records v6 D-2/D-3 fix; final visual audit pending. |
| TG-G-001 | BLOCKER | Panel G is Coulomb-only; Maxwell attraction and actuator framing are absent. | Source/render text and arrow review. | Initial source evidence passes: `briefing.md` invariant 8.5 and contract forbid Maxwell transfer. Final visual audit pending. |
| TG-ROW2-001 | BLOCKER | Row 2 shows three independent evidence spokes from Panel C: kinetic, ISPD, and mechanical. | Source/render review of Row2-BR1/Row2-BR2 labels and geometry. | Initial source evidence passes: `briefing.md` invariant 8.7 and v7 spoke update preserve three modalities. Final visual audit pending. |
| TG-B-001 | MAJOR | Composition labels S60/S70/S75/S85 appear only in Panel B. | Source text search and render review. | Initial source evidence pending final source/render audit. |
| TG-EF-001 | MAJOR | Panel E and F read as one ISPD evidence line, with E raw signal and F derived trap distribution. | Render review of E/F pairing arrow and labels. | Initial source evidence passes from `briefing.md` sections 6 and 13.6-13.7; final visual audit pending. |
| TG-PUB-001 | MAJOR | Publication compliance is not inferred from compile/export; reference provenance and AI-image policy remain separately reviewed. | Quality audit and decision doc. | Pending `QUALITY_AUDIT.md` and milestone decision. |

## Acceptance Rule

- Any BLOCKER fail keeps `accepted: false`.
- `accepted: true` requires all BLOCKER items pass, all MAJOR items either pass
  or have explicit author-accepted residual risk, fresh critique/export
  evidence, and publication-compliance review.
- This guard cannot by itself make the figure submission-safe; it only records
  theory and narrative readiness.
