# Fig1 failure-first Panel F pilot

## §1. Intent

Test whether Figure Agent can turn a reviewed complex-panel defect into exact,
multiscale evidence and one bounded repair without pretending that machine
checks establish publication quality.

## §3. Correctness rules

- Panel F must show one understated metal contact attached to the cantilever.
- Panel F must not imply that the right electrode is grounded.
- The historical v5f source must remain unchanged.

## §6. Physics invariants

- The cantilever must remain separated from the right electrode by an air gap.
- The Coulomb-force arrow must point away from the right electrode.
- Removing the false ground cue must not alter charge, cantilever, electrode,
  air-gap, or force relations.

## §7. Review constraints

- Raw, verified, and repaired states must use the same model/input/budget
  contracts.
- Review must include whole, panel, object/relation, and zoom evidence.
- A named human must supply scientific and visual verdicts separately.
- Machine gates must not claim publication acceptance.
