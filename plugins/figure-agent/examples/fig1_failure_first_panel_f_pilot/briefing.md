# Fig1 failure-first Panel F pilot

## §1. Intent

Test whether Figure Agent can turn a reviewed complex-panel defect into exact,
multiscale evidence and one bounded repair without pretending that machine
checks establish publication quality.

## §3. Correctness rules

- Panel F must show one understated fixed mechanical boundary holding the
  cantilever: a restrained support rail, short structural stem, and shallow jaw.
- Panel F must show a compact voltage source driving the right electrode.
- The source return must terminate at ground; the ground belongs to the source
  circuit, not to the sample.
- The sample and cantilever must remain electrically floating, with no
  electrical connector at the mechanical jig.
- The holder's material and conductivity are not established by the reference;
  leave them electrically unmodeled rather than declaring an insulating or
  conducting clip.
- A compact source symbol is sufficient; a detailed instrument display is not required.
- The historical v5f source must remain unchanged.

## §6. Physics invariants

- The cantilever must remain separated from the right electrode by an air gap.
- The Coulomb-force arrow must point away from the right electrode.
- Correcting the source/ground topology must not alter charge, cantilever,
  electrode, air-gap, or force relations.

## §7. Review constraints

- Raw, verified, and repaired states must use the same model/input/budget
  contracts.
- Review must include whole, panel, object/relation, and zoom evidence.
- A named human must supply scientific and visual verdicts separately.
- Machine gates must not claim publication acceptance.
