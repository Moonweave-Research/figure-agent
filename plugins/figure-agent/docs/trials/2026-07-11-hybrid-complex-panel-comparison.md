---
schema: figure-agent.hybrid-comparison.v1
trial_id: fig1-complex-panel-tikz-vs-hybrid
protocol:
  predeclared: true
  same_clean_environment: true
  clean_archive_commit: e3a61a1b
  task_boundary: render and diagnose the declared Panel C geometry
  accounting_categories:
    - preparation
    - failed_attempts
    - detector_diagnosis
    - rendering
    - repair
variants:
  tikz_only:
    fixture: fig1_overview_v2_pair_001_vault
    source_sha256: sha256:80e5d3fc5c69b2c6abe631cf9d2a8d33526b4d2473ec2c288bc42df3a3210c05
    compile_exit: 0
    output_sha256: sha256:e97c16a47561d9e12eb0227a7bd992c1a12c7ff05dc5776fae408c40eb3be9eb
    repeated_output_sha256: sha256:e97c16a47561d9e12eb0227a7bd992c1a12c7ff05dc5776fae408c40eb3be9eb
    pdf_bytes_repeatable: false
    compile_seconds: [28.525, 22.242]
  hybrid:
    fixture: fig1_hybrid_complex_panel_pilot
    source_sha256: sha256:73108900d08bfc4e8f10b92c5bf78a979a63d6f6c98a2d1c885660683019e933
    fragment_manifest_sha256: sha256:a4ee6412a6dafbf034d392a48fb3135cf31616cdd8e49aee06ba046ec19281e4
    compile_exit: 0
    output_sha256: sha256:f03848fd7c20f2665a1a4e3ea6905e87d97ffbc2c573786a4172c12765fba865
    repeated_output_sha256: sha256:f03848fd7c20f2665a1a4e3ea6905e87d97ffbc2c573786a4172c12765fba865
    pdf_bytes_repeatable: false
    compile_seconds: [21.028, 21.030]
measurements:
  visual_quality:
    value: null
    missing_reason: pending bound human artifact verdict
  scientific_fidelity:
    value: null
    missing_reason: pending bound human scaffold verdict
  source_edit_size:
    tikz_only: {tex_lines: 2034, tex_bytes: 127405}
    hybrid: {tex_lines: 2071, generator_lines: 78, combined_bytes: 132987}
    hybrid_delta: {tex_insertions: 39, tex_deletions: 2, generator_lines: 78}
  correction_minutes:
    tikz_only: null
    hybrid: null
    missing_reason: no predeclared timed correction run was captured; compile duration is not correction time
    category_accounting:
      preparation: {tikz_only: null, hybrid: null, missing_reason: not separately timed}
      failed_attempts: {tikz_only: null, hybrid: null, missing_reason: no equivalent correction run}
      detector_diagnosis: {tikz_only: null, hybrid: null, missing_reason: not separately timed}
      rendering: {tikz_only_seconds: 50.767, hybrid_seconds: 42.058, runs_each: 2}
      repair: {tikz_only: null, hybrid: null, missing_reason: no equivalent correction run}
  detector_findings:
    tikz_only: {visual_clash: 38, label_path: 0, text_boundary: 0, undeclared_geometry: 95}
    hybrid: {visual_clash: 39, label_path: 0, text_boundary: 0, undeclared_geometry: 95}
  actionable_attribution_rate:
    value: null
    missing_reason: current machine candidates have not received bound human adjudication
  artifact_reproducibility:
    tikz_only: true
    hybrid: true
    evidence: fixed-raster SHA-256 repeated exactly twice; PDF bytes varied for both
verdicts:
  scaffold:
    status: pending
    path: examples/fig1_hybrid_complex_panel_pilot/review/human_scaffold_verdict.yaml
    review_input_hash: sha256:bdd10c1e5735aa24aff9431830122f9bebc4e910bd8647547c3084263844c207
  artifact:
    status: pending
    path: examples/fig1_hybrid_complex_panel_pilot/review/human_scaffold_verdict.yaml
    review_input_hash: sha256:bdd10c1e5735aa24aff9431830122f9bebc4e910bd8647547c3084263844c207
review_state: review-ready
publication_acceptance: not_claimed
---

# TikZ-only versus hybrid complex-panel comparison

Both variants were compiled twice from the same clean `git archive` of
`e3a61a1b`, with the mandated plugin-root command. Their fixed raster outputs
were byte-identical across repeats; their PDF bytes were not deterministic.

The machine evidence does not show a quality win. Hybrid normal compile was
slightly faster in this two-run sample and added one visual-clash candidate,
while the other recorded detector counts were unchanged. The sample is too
small for a performance claim, and candidate count is not a quality metric.

Correction minutes and actionable attribution rate remain explicitly missing.
Retrospectively trimming the successful Task 6 edits into a synthetic timing
would violate the protocol. The two bound human verdicts are still pending, so
this package is review-ready only and cannot close Task 7 or claim publication
acceptance.
