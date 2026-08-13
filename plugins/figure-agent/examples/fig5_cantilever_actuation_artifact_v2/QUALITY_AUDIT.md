# Quality Audit

fixture: fig5_cantilever_actuation_artifact_v2

## Automated Gate Snapshot

generated-at: 2026-08-13T01:25:00Z
scope: First-pass acceptance after a four-defect repair round on the Panel D
recovery label lane, the Panel C subtitle redundancy, the Panel B residual
force vector encoding, and the Panel C Coulomb label clearance.

compile-command: `./bin/fig-agent compile fig5_cantilever_actuation_artifact_v2`
export-command: `./bin/fig-agent export fig5_cantilever_actuation_artifact_v2`
status-command: `./bin/fig-agent status fig5_cantilever_actuation_artifact_v2`

render-state: FRESH
critique-state: FRESH
export-state: FRESH
acceptance-state: ACCEPTED
acceptance-freshness-state: accepted_current

0 collision(s)
6 visual clash candidate(s), 0 unresolved (all six are glyph-level false
positives on `q_tr` subscripts and the `|F|` absolute-value bars; each is
recorded in critique.md with an explicit accept_simplification rationale)
7 label-path proximity check(s), 0 candidate(s)
4 text-boundary check(s), 0 candidate(s)
2 semantic assertion(s) hold
6 tex-geometry assertion(s), 0 issue(s)
physics-grounding: grounded

## Measured Clearances

Coulomb label to film body, ink to ink: 25 px at 600 dpi = 1.04 mm at the
178 mm working width. Measured on the rendered raster, not inferred from
source coordinates.

## Provenance and Publication Compliance

target-venue: Nature Communications (double-column, 180 mm working width)
final-artifact-scope: mechanism schematic only; the assembled paper figure and
  any measured deflection panel remain external and are not covered here
ai-generated-image-in-submitted-artifact: no
  (the artifact is authored TikZ compiled by lualatex; no raster generation)
ai-generated-images-used-as-internal-reference: no
ai-tools-used: Claude Code (figure-agent plugin) for TikZ authoring, gate
  execution, and report-only vision critique; no external image or vision API
disclosure-needed: unresolved
  (depends on the venue policy reading for AI-assisted vector authoring; the
  author has not yet made this determination)
disclosure-draft: unresolved
human-reviewer: unresolved
  (the author accepted the figure content on 2026-08-13; the unforgeable
  attestation binding that decision to this source hash has not been created —
  run `fig-agent attest fig5_cantilever_actuation_artifact_v2`)
human-visual-acceptance: true
  (author reviewed the rendered figure on screen at full size and at the
  178 mm print-scale proxy, requested four specific repairs, and accepted the
  result as the first-pass figure)
submission-safe: false
  (deliberately false: acceptance was declared as a first pass with further
  revision rounds expected. Submission safety is a separate decision the
  author has not made, and it also depends on the unresolved disclosure
  question above.)
