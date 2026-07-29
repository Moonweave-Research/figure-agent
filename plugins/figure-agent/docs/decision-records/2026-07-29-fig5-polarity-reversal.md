# Fig5 polarity-reversal decision

- `outcome`: `confirmed_paper_local`
- `applies_to`: `polymer_paper_project.fig5_cantilever_actuation_artifact_v2`
- `fixture`: `fig5_cantilever_actuation_artifact_v2`
- `reviewer`: `choemun-yeong`
- `reviewed_at`: `2026-07-29`
- `evidence_class`: `human_scientific_direction`
- `publication_acceptance`: `not_claimed`

## Decision

Fig5 may depict a polarity-reversal actuation sequence for the same mounted
cantilever. The sequence is:

1. a two-terminal high-voltage drive bends the cantilever by the initial
   attractive interaction;
2. the source is switched off and the specimen lead is manually isolated so
   the mounted specimen is electrically floating; the OFF/float state does not
   retain a ground symbol or invent a fixed-support electrical reference;
3. the retained charge produces an immediately reversed charge-mediated
   force, so the trace passes through the neutral angle into a reverse bend;
4. the reverse bend relaxes slowly toward the polarity-independent Maxwell
   baseline, and an indefinitely continued experiment is expected eventually
   to return toward attraction as the retained charge relaxes.

The figure is a qualitative mechanism schematic. It must not imply that the
support reference is the disconnected specimen clip, that a grid or earth
ground is present at the charging station, or that the reversal is caused by
Maxwell attraction alone. Maxwell attraction is the `E^2` baseline; the
charge-mediated term follows `q_tr E` and can change sign.

## Scope and provenance

This is a paper-local scientific direction recorded from the author's explicit
Fig5 discussion on 2026-07-29. It is not a generic authoring rule for other
figures, instruments, or experiments, and it does not authorize promotion to
accepted, release, or publication state. The durable implementation contract
is in `docs/current-sulfur-paper-figure-state.md`; visual ownership and
cross-panel safeguards are in `docs/authoring-rules-project.md`.

The exact timing of lead isolation and any quantitative angle or relaxation
constants remain qualitative unless separately bound to measured data. Do not
invent a polarity, duration, or voltage in another fixture from this record
alone.
