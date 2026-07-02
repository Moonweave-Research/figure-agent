# Changelog

All notable changes to figure-agent are documented here.

<!-- Unreleased (stage for the next version bump at release/merge time):
     - Slice 0 defect-driven candidate generation (source_hashes + %Panel
       line->panel fallback + geometry-aware offset); apply stays human-gated.
     - Humanizer capture-only "Why" column in the sub-region iteration log.
     - MCP honesty gate: propose_* report success:false + no_op:true on no-ops.
     - Documented composition_* (architecture L3.7); refreshed drifted paths;
       recorded the #1-amortize probe result + Slice namespace.
     - Quarantined the inert SVG-semantic stack; removed orphaned _handlers_* shims.
     The version bump (0.9.3 -> 0.10.0) is a coordinated release-contract change
     across plugin.json, pyproject.toml, README, the issue-100 inventory,
     closeout status, test_release_contract.EXPECTED_RELEASE_VERSION, and the
     cowork zip names; do it as one deliberate step at release. -->

## [0.9.3] - 2026-06-07

Patch release for Cowork plugin packaging and runtime path separation.

### Added

- `bin/fig-agent` as the Cowork-facing command entrypoint for doctor, status,
  compile, and export.
- Deterministic Cowork ZIP packaging with bundled scripts, styles, docs, and
  smoke fixtures while excluding manuscript fixtures and generated artifacts.

### Changed

- Runtime path resolution now separates installed plugin resources from the
  user workspace containing `examples/`.

## [0.9.2] - 2026-06-02

Patch release for the first Issue 100 hardening wave after v0.9.1.

### Added

- Final warning-budget visibility in release mode, so high-confidence detector
  warning debt remains visible before human roll-forward decisions.
- Optional `inspection_trace.yaml` validation and critique-lint surfacing for
  reviewed crops, commands, verdicts, and outstanding doubts.
- `critique_adjudication.py sync --preview`, which shows the decision diff
  before mutating adjudication state.
- SVG polish positive-route recipe templates via
  `svg_polish_recipe.py --template <fixture> --write-template`, producing a
  hash-bound starter file for conservative polish edits.

### Guardrails

- The new evidence and template surfaces are review aids only. They do not
  execute SVG edits, force golden, set accepted state, bypass release gates, or
  convert optional-improvement findings into blocking release decisions.

## [0.9.1] - 2026-06-01

Patch release for Issue 95 loop-centered improvement orchestration plus the
post-v0.9.0 top-tier critique contract sync.

### Added

- Issue 95 `/fig_improve`, a loop-centered single-fixture entry point for
  "keep improving this figure" requests. It wraps `/fig_run`, surfaces
  host critique, human, patch, SVG polish, release, and optional-improvement
  boundaries, and emits `figure-agent.improve.v1` JSON.
- Official docs and skill routing now prefer `/fig_improve` when the user asks
  to run repeated critique/improvement loops on one fixture.
- Issues 97 and 98 v1.17 grounded critique contract sync. Host critique
  guidance now requires `aesthetic_antipattern_audit`,
  `weakest_panel_coherence`, and `reference_learning_accountability` where the
  grounded v1.17 route applies, and command docs no longer describe those
  paths as v1.14-only.

### Guardrails

- `/fig_improve` is not a hidden auto-designer. It does not author host
  critiques, patch source, edit SVG, force golden, set accepted state, or bypass
  release/human gates.
- Optional-improvement candidates remain advisory. They do not override
  critique lint, adjudication, accepted/golden, publication, SVG-polish, or
  human-review gates.
- v1.17 aesthetic and reference-learning fields are critique evidence, not
  permission to bypass human, release, accepted, golden, or publication gates.

## [0.9.0] - 2026-05-30

Operator-grade release-candidate for the guided autonomy workflow after Issues
70-89.

### Added

- Issue 70 guided autonomy surfaces for bounded runner execution without hidden
  source edits, host critique, SVG polish, accepted, golden, or release
  mutation.
- Issue 71 real-fixture readiness closeout, including refreshed host-vision
  critique/adjudication evidence for the current fixture corpus.
- Issues 77-88 multi-fixture queue and queue-run operator surfaces that group
  work by actor, expose blocked-row `operator_handoff` packets as explicit
  operator handoff records, and delegate only the workflow-agent subset to
  `/fig_run`.
- Issue 88 queue closeout follow-through for fixtures blocked on export or loop
  reruns, with exact follow-up commands instead of ambiguous prose.
- Issue 89 release-candidate docs that freeze `/fig_status`, `/fig_drive`,
  `/fig_run`, `/fig_queue`, and `/fig_queue_run` as the canonical operator
  workflow.

### Changed

- README and architecture docs now present the single-fixture and multi-fixture
  operating paths together, including bounded safe runner behavior and queue
  handoff boundaries.
- Release contract tests now assert the v0.9 operator-grade version surface
  across plugin manifest, `pyproject.toml`, `uv.lock`, README, changelog, and
  closeout status docs.

### Guardrails

- v0.9.0 is still a quality/audit kernel, not a hidden auto-designer.
- Scores, reference-learning metrics, aesthetic signals, and queue summaries are
  routing evidence only; they do not override critique lint, adjudication,
  human review, accepted/golden, publication, or SVG-polish gates.
- No generated build/export/.scratch artifacts, source drawing changes, hidden
  auto-patching, or accepted/golden mutation are part of this release.

## [0.8.2] - 2026-05-29

Patch release for Issue 64 loop-summary and generated-export closeout UX after
v0.8.1.

### Fixed

- `/fig_loop` assessment summaries now surface latest v1.13 critique evidence,
  including journal-grade assessment, top-tier audit, editorial art direction,
  crop audit, reference calibration, aesthetic lever audit, and journal
  art-direction playbook summaries when present.
- Routine generated `exports/<name>.svg` files no longer churn
  `critique_input_hash` for non-polished fixtures. Polished-SVG opt-in and
  existing polish-layer evidence still include the generated SVG in final
  artifact freshness.
- `/fig_status` and `/fig_export` wording now distinguishes reference-grounded
  pre-export critique from optional post-export final-review critique.

### Guardrails

- No source drawing, hidden auto-patching, accepted/golden mutation,
  publication-gate bypass, or automatic SVG polish editing is introduced by
  this patch.

## [0.8.1] - 2026-05-28

Patch release for Issue 63 reference-learning and non-model aesthetic audit
signals after v0.8.0.

### Added

- Optional `reference_learning` contract inside `critique_reference_pack.yaml`
  so references can teach editorial principles without becoming copy targets.
- Deterministic `reference_aesthetic_metrics.py` pack for palette, density,
  silhouette, and line-density divergence against opt-in reference-learning
  anchors.
- `/fig_status`, `/fig_loop`, critique freshness, and `/fig_critique` brief
  surfacing for reference-aesthetic metric summaries.
- Loop basin detection for repeated patch targets, repeated aesthetic
  bottlenecks, and repeated severe reference-aesthetic divergence.
- Critique schema/rubric v1.13 for reference-learning critiques, including
  crop-level unintended-visible-anomaly accounting.

### Fixed

- Scoped `unintended_visible_anomaly` and `anomaly_link` prompt fields to v1.13
  reference-learning critiques so legacy v1.10 critique briefs do not request
  fields their schema does not validate.

### Guardrails

- Reference metrics are suspicion and routing signals, not release authority.
- Reference learning does not override `briefing.md`, theory guards, fixture
  semantics, or author intent.
- No provider API calls, hidden auto-patching, accepted/golden mutation, SVG
  polish editing, or source drawing work is introduced by this release.

## [0.8.0] - 2026-05-28

Release-hardening pass for the v0.8 audit kernel after Issues 57-61. This
release makes the current command surface, opt-in evidence layers, and
quality-claim boundaries explicit before the next plugin release candidate.

### Added

- Issue 57 real-fixture audit adoption matrix for explicit text-boundary,
  label-path, reference, aesthetic, paper-wide, and journal-playbook coverage.
- Issue 58 single next-action summary shared by status, driver, loop, and
  closeout surfaces.
- Issue 59 SVG polish promotion dogfood evidence showing the route stays
  blocked behind stale critique gates until source-level evidence is fresh.
- Issue 60 journal style-pack catalog with opt-in Nature Communications, Nature
  Materials, Science, and graphical-abstract playbook/context packs.
- Issue 61 optional external vision review evidence import for local
  second-opinion reviews without provider API calls.

### Changed

- README and closeout docs now describe the plugin as a quality/audit kernel,
  not a hidden auto-designer.
- Current-state docs distinguish automatic deterministic gates,
  semi-automatic host-vision critique, opt-in style/evidence packs, and manual
  source or SVG editing.

### Guardrails

- v0.8.0 does not claim automatic Nature/Science acceptance.
- External vision review is opt-in evidence only; conflicts route to human
  judgment rather than overriding host critique.
- SVG polish remains bounded finalization/handoff, not semantic repair or
  hidden source mutation.

## [0.7.1] - 2026-05-26

Patch release for post-v0.7.0 SVG-polish readiness and current-truth
documentation sync.

### Added

- `svg_polish_readiness` is now part of the current release surface: `/fig_loop`
  records it when editorial art-direction evidence exists, and
  `/fig_drive --mode polish` surfaces the same readiness object from the latest
  loop checkpoint.
- Release-contract coverage now checks that the plugin-development closeout
  status and Issue 48 docs match the current plugin version and mainline state.

### Changed

- README current-state docs now identify v0.7.1 and describe the explicit SVG
  polish readiness gate instead of only the recipe/executor tools.
- The plugin-development closeout status now reflects the mainline state through
  v0.7.1 / Issue 48 rather than the older Issue 33 / PR #47 checkpoint.
- Issue 48 docs now identify the implementation as landed on main in commit
  `ef1fda9`.

### Fixed

- Removed stale current-priority guidance that still pointed to Issue 34 even
  though phrase-aware text-boundary containment is already complete.

## [0.7.0] - 2026-05-26

SVG-polish route release. This ships the deterministic, non-mutating polish
handoff layer and records the first real-fixture negative dogfood result: a
fixture may be high-quality and still correctly route back to TikZ when the
host critique says `continue_tikz`.

### Added

- `svg_polish_recipe.py`, `svg_polish_executor.py`, and
  `svg_polish_delta.py` for bounded SVG-polish recipes, dry-run/executor
  validation, and before/after/diff aesthetic delta packs.
- `/fig_drive --mode polish` route hints for recipe authoring, executor dry
  runs, delta-pack generation, and handoff review while preserving dry-run
  driver semantics.
- SVG polish command-facing documentation and dogfood milestones for Issues
  44-47, including a clean temporary-fixture proof and a real-fixture preflight.
- Real fig1 aesthetic-upgrade evidence and accepted/golden roll-forward for
  `fig1_overview_v2_pair_001_vault`, including Panel A hand-feel / chemistry
  convention refinements and figure-wide v8.5-v8.6 calibration.

### Changed

- `/fig_critique` and critique freshness now include SVG-polish aesthetic
  delta inputs when present, so polish comparisons can participate in the same
  hash-based audit contract as source/reference/critique inputs.
- The polish driver now refuses to invent a recipe when the latest loop
  checkpoint routes `continue_tikz`, `semantic_backport_required`, or human art
  direction instead of `ready_for_svg_polish`.
- Issue 42 and 42B docs now point to their implemented mainline slices instead
  of stale "pending commit" wording.

### Fixed

- `critique_adjudication.py sync` now shares
  `quality_manifest.expected_critique_rubric_version()` with `/fig_status`,
  so v1.11 aesthetic-intent critiques can be synced instead of failing against
  the legacy v1.10 rubric constant.
- Real-fixture SVG-polish dogfood captured the correct negative route for
  `fig1_overview_v2_pair_001_vault`: audit evidence passed, but
  `editorial_art_direction_summary.polish_recommended_path` remained
  `continue_tikz`, so no polish recipe was authored.

### Tests

- Local release verification: `1209 passed, 1 skipped, 1 xfailed`; ruff clean;
  `git diff --check` clean; Claude plugin validation passed for plugin
  manifest, plugin directory, and marketplace manifest.

## [0.6.0] - 2026-05-25

Aesthetic-lever grammar release. This moves the plugin from broad
aesthetic-intent anchoring toward explicit, auditable figure-polish levers that
host critique, lint, loop, and driver surfaces can enforce without turning the
plugin into an autonomous illustrator.

### Added

- `aesthetic_intent.yaml` schema v2 with bounded `aesthetic_levers[]` for
  maturity, hero hierarchy, whitespace, typography, color harmony, line-weight
  rhythm, component fidelity, hand-craft routing, and cross-panel grammar.
- Critique schema/rubric v1.11 with mandatory `aesthetic_lever_audit` when a
  fixture opts into v2 aesthetic intent.
- Fixture-aware critique lint accountability for missing, duplicate, unknown,
  mismatched, unresolved, or unsafe aesthetic lever routes.
- `/fig_loop` aesthetic lever summary with worst verdict, lever counts, and the
  next aesthetic bottleneck.
- `/fig_drive` and release checkpoint handling for loop-level aesthetic and
  top-tier blockers.
- Real fixture dogfood evidence for `fig1_overview_v2_pair_001_vault`, showing
  `print_typography_authority` surfacing `C004` as a bounded TikZ patch
  bottleneck instead of generic polish prose.

### Changed

- `/fig_critique` now emits the stronger "Aesthetic Lever Grammar" brief
  section and schema v1.11 only for fixtures that explicitly declare
  `figure-agent.aesthetic-intent.v2`; v1 or missing intent keeps the v1.10
  path.
- Critique freshness now expects rubric v1.11 for v2 aesthetic-intent fixtures.
- High-impact candidate claims are blocked when required aesthetic levers remain
  unresolved.
- Polish-driver routing now respects aesthetic/top-tier blockers before
  suggesting SVG handoff.

### Fixed

- Closed the anchor-only aesthetic-intent loophole where a critique could cite
  broad intent while still returning generic "improve polish" guidance.
- Tightened route gates so `tikz_patch`, `svg_polish`, `semantic_backport`, and
  `human_art_direction` cannot be activated by unsupported prose alone.
- Preserved advisory/gate separation: aesthetic critique does not bypass
  adjudication, export/golden, publication, or human-review gates.

### Tests

- Local release verification: `1143 passed, 1 skipped, 1 xfailed`; ruff clean;
  `git diff --check` clean; Claude plugin validation passed for plugin manifest,
  plugin directory, and marketplace manifest.
- PR #64 CI: `figure-agent tests` passed; `figure-agent full render tests`
  skipped by workflow policy.

## [0.5.6] - 2026-05-23

Audit-hardening and workflow-readiness release. This brings the post-0.5.3
loop/driver work up to the current plugin manifest version and documents the
new audit evidence contracts, critique accountability gates, text-boundary
checks, and canonical command order.

Note: `0.5.4` and `0.5.5` existed only as intermediate manifest/version states
without separate public tags. The current shipped plugin version is `0.5.6`.

### Added

- Visual-clash-centered audit crops and a deterministic
  `build/audit_crops/manifest.json` crop pack for `/fig_critique`.
- Crop-read accountability in the critique contract so host critiques must
  explicitly account for required zoom, print-scale, and visual-clash crops.
- Optional `critique_reference_pack.yaml` support for reference-calibrated
  top-tier critique and advisory scoring metadata.
- Audit evidence summary plumbing through `/fig_status`, `/fig_drive`, and
  `/fig_loop`.
- Text-boundary clash detection for labels crossing declared row boxes, column
  rules, panel boundaries, and internal instrument rectangles.
- Helpers for authoring-safe maintenance:
  `text_boundary_spec_helper.py`, `tex_coordinate_shift.py`, and
  `/fig_closeout` text-boundary sync reporting.
- Aesthetic intent packs via `aesthetic_intent.yaml`, with `/fig_critique`
  grounding and freshness participation.
- Workspace dirty-file warnings in `/fig_drive --dry-run`.
- Plugin readiness matrix documentation for real fixture status/driver/loop
  behavior.

### Changed

- `/fig_loop` now forwards the canonical `/fig_status` next action when render
  is missing or stale, so stale renders are compiled before host vision
  critique is requested.
- `/fig_status` now surfaces critique lint blockers and a compact
  `critique_lint_summary` for fresh critiques.
- `/fig_drive` now ingests current `/fig_loop` checkpoints, audit evidence,
  publication gates, and closeout state while remaining dry-run only.
- Critique schema/rubric surfaces were extended through the v1.9/v1.10 family
  for top-tier audit, editorial art direction, micro-defects, crop
  accountability, structured accept-simplification reasons, and
  reference-calibrated scoring.
- Canonical workflow docs now pin the order:
  `/fig_status` or `/fig_drive --dry-run` first, then compile, critique,
  adjudication, loop, export/release/polish only when routed.
- CI was split into fast plugin tests and full render tests with timeout and
  dependency-stall guardrails.

### Fixed

- Historical label/backdrop and glyph/internal-drawing visual-clash blind spots
  are now represented in the micro-defect taxonomy and critique lint path.
- Visual-clash `accept_simplification` entries now require concrete rationale
  instead of vague prose.
- Crop manifest and historical visual-clash regression lint paths were hardened
  against stale or malformed audit evidence.
- Phrase-aware text-boundary containment now covers labels split into multiple
  PDF text fragments, such as phrase labels and math/subscript labels.
- Documentation contract drift across completed Issues 23-41 was reconciled so
  recently implemented work no longer appears open or branch-local.

### Tests

- Latest local full suite during Issue 40: 1084 pytest passed, 1 skipped,
  1 xfailed; ruff clean; Claude plugin validation passed.
- Latest main CI after Issue 41: `figure-agent tests` and
  `figure-agent full render tests` both succeeded.

## [0.5.3] - 2026-05-18

Loop-contract release for verify-only figure iteration and safe patch handoff.

### Added

- `/fig_loop` records verify-only loop evidence under `.scratch/fig-loop-runs/`
  with stop reasons, escalation level, axis verdict evidence, active patch
  target, and optional single-target patch handoff metadata.
- `/fig_adjudicate` scaffolds `critique_adjudication.yaml` from `critique.md`
  findings, hashes the source critique, and keeps unresolved findings visible.
- `/fig_closeout` reports read-only post-patch closeout state for compile,
  critique, adjudication, export, and loop rerun freshness.
- `/fig_e2e_smoke` runs deterministic compile/export/status/loop smoke checks
  with JSON evidence for repeated usability validation.

### Changed

- Critique freshness now uses hash/rubric/generator metadata when available
  with mtime fallback for legacy critiques.
- Human-gate escalation distinguishes routine agent action, manual approval,
  ambiguous patch selection, and domain review.

## [0.5.2] - 2026-05-16

Acceptance-gate and critique-context hardening for the reference-conditioned
authoring loop.

### Added

- `scripts/subregion_active_set.py` parses text-form sub-region iteration logs
  and feeds active-target summaries into `/fig_critique` briefs.
- `scripts/reference_pack.py` parses Reference Roles tables and validates that
  reference rows have roles plus Do-Not-Transfer boundaries.
- Accepted-mode artifact validation now requires a passing `theory_guard.md`,
  provenance/publication compliance with `submission-safe: true`, and valid
  reference-pack boundaries when reference inputs are declared.

## [0.5.1] - 2026-05-16

Patch release for local Claude plugin installation hygiene.

### Added

- `scripts/plugin_package_audit.py` detects generated build/cache paths in an
  installed plugin cache and can remove them with `--clean`.
- Release contract coverage for package-cache cleanup and the README install
  note that explains when to run the audit.

### Changed

- Documentation now treats post-install cache audit as part of the local
  plugin-update runbook when the install source may contain generated files.

## [0.5.0] - 2026-05-09

Per-panel reference grounding and perception-data release. Keeps the product
identity as a paper-figure quality kernel, while adding build-side descriptive
geometry data and panel-grounded critique context.

### Added

- **v0.4.2 Perception Data Only** — `/fig_compile` now always writes
  `build/perception/extract.yaml` and `build/perception/overlay.png` after a
  successful PDF/PNG build. The pack is descriptive only: raw pdfplumber
  primitives plus endpoint overlay, no topology judgment or lonely-endpoint
  classifier.
- **v0.5 Per-panel references** — `spec.yaml.panels[].reference_image` plus
  `panels[].bbox_pdf_cm` can ground `/fig_critique` on build-crop/reference
  pairs. Missing bbox emits a warning instead of silently pretending the panel
  was compared.
- `scripts/spec_bbox_helper.py` — converts source TikZ cm boxes into PDF-cm
  `bbox_pdf_cm` lines so users do not hand-compute resizebox/border offsets.
- `examples/fig1_overview_v2/` — multi-panel dogfood fixture with reference
  images, coordinate hints, critique notes, and design record.

### Changed

- `pdfplumber` is now a runtime dependency because `/fig_compile` requires it
  for the perception pack and `/fig_critique` uses it for panel cropping.
- `/fig_status` now honors Layer 5 export content state directly: when
  `exports_substate == STALE`, status reports `stale_export` and routes to
  `/fig_export` even if export file mtimes are newer than the source files.
- `/fig_status` freshness now includes `spec.yaml`, figure-level reference
  image, optional `coordinate_hints.yaml`, and the style lock. `/fig_critique`
  additionally treats participating panel reference images as freshness
  sources.

### Tests

- 221 pytest pass, 1 xfail; ruff clean.
