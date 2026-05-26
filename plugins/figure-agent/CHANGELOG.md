# Changelog

All notable changes to figure-agent are documented here.

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

## [0.2.0] - 2026-05-04

Architecture cleanup release. Slims the v0.1 11-layer model to 7 functional
pipeline layers + 1 cross-cutting group, deletes dead frozen-orchestration
code, and introduces L4.5 Vision Critique as the new value-add — host
Claude Code main loop reads the build PNG via the Read tool and writes
structured `critique.md` (YAML front-matter + Markdown summary, schema v1).
Subscription tokens only; no external Anthropic API call originates from
plugin code.

Reference design: `docs/architecture-v0.2-proposal.md` (Status: ACCEPTED).

### Added

- **L4.5 Vision Critique** — `/fig_critique <name>` slash command,
  `scripts/critique_brief.py` (renamed + extended from `review_brief.py`),
  `examples/<name>/critique.md` schema (YAML front-matter v1 + Markdown body,
  verdict ∈ {ready, revise, block}, severity ∈ {BLOCKER, MAJOR, MINOR, NIT},
  category ∈ {physics, label_placement, whitespace, hierarchy, palette, style}).
  Report-only for v0.2; auto-apply gated on N=5+ dogfood accuracy ≥ 80%.
- `docs/architecture-v0.2-proposal.md` — living design doc capturing the
  layer redesign, blast-radius analysis, and PR-by-PR execution plan.
- `docs/trials/n3_2026_05_04.md` + 3 N=3 trial fixtures
  (`examples/n3_trial_0{1,2,3}_*`) — empirical α/γ decision data.
- `.github/workflows/test.yml` — CI runs ruff + pytest on push/PR with
  full apt deps (qpdf, imagemagick, tesseract, ttf-mscorefonts, texlive
  fonts/pictures extras) and pre-builds the smoke fixture.
- `scripts/{palette, ocr, vtrace}.py` — split out of `reference_extract.py`
  monolith.

### Changed

- **Layer 2.5**: `scripts/reference_extract.py` 1060 → 263 lines (facade
  pattern over `palette.py` / `ocr.py` / `vtrace.py`); rot CRITICAL → SAFE.
  Public API surface unchanged (`PALETTE`, `EXTRACTION_VERSION`,
  `palette_shape_clusters`, `ocr_text_labels`, `extract_coordinate_hints`
  still importable from `reference_extract`).
- **Layer 7 stage model**: 7 stages (0..6) → 5 stages (0..4). Stages 2/3
  (preview-images-without-selection / `selected_preview`-set-without-tex)
  removed. Print format becomes `stage X/4` (was `X/6`). Stage notes catalog
  no longer emits `selected_preview_missing`.
- **L4.5 rename**: `commands/fig_review.md` → `commands/fig_critique.md`,
  `scripts/review_brief.py` → `scripts/critique_brief.py`,
  `tests/test_review_brief.py` → `tests/test_critique_brief.py`,
  `ReviewBriefError` → `CritiqueBriefError`, requested output format
  changed from flat Markdown table to YAML front-matter + Markdown body.
- Identity surfaces (CLAUDE.md / AGENTS.md / README.md / SKILL.md /
  plugin.json) re-aligned: workflow listing now includes `/fig_critique`
  under Active; policy clarified to "no external vision API; host
  orchestration via the main loop is permitted".
- `commands/fig_status.md` — Stage table fully rewritten (5 rows, 0..4).
- `docs/architecture-overview.md` — Layer 4.5 section added; Layer 9
  rewritten as deletion record; Layer 7 docstring renumbered to 0..4.
- `docs/quality-kernel-goal.md` — Frozen Legacy Helpers section rewritten
  with PR cleanup history.

### Removed

- `scripts/{prompt_gen, redact, llm_author_prompt}.py` (PR #8a).
- `commands/{fig_prompt, fig_preview_select}.md` (PR #8a).
- `prompts/llm_author_tikz.md` (PR #8a).
- `tests/test_{prompt_gen, redact, llm_author_prompt}.py` (PR #8a) +
  3 prompt-template assertions in `test_release_contract.py`.
- `spec.yaml.selection_notes` consumer (PR #8a) and
  `spec.yaml.selected_preview` stage-gate consumer (PR #8b). Existing
  fixture spec.yaml files retain the field strings as historical record;
  yaml ignores unknown keys for surviving consumers.
- `scripts/status.py` `_has_image_files` helper (only consumer was the
  removed previews stage gate).

### Fixed

- CI workflow installed missing system packages (`qpdf`, `imagemagick`,
  `tesseract-ocr`, `texlive-fonts-extra`, `texlive-pictures`,
  `ttf-mscorefonts-installer` with EULA pre-accepted) so the lualatex
  `fontspec` Arial lookup succeeds and the qpdf/magick test families run.
- `tests/test_band_diagram_byte_classifier.py` — diff capture switched to
  `encoding="latin-1"` to tolerate cross-platform binary stream blobs in
  the qpdf qdf output; test now skipped on non-darwin until a platform-
  aware baseline pair lands.
- `commands/fig_compile.md`, `commands/fig_status.md`, `scripts/status.py`,
  `scripts/lint_tex.py` — `/fig_review` / `prompts/llm_author_tikz.md`
  references re-pointed to the surviving `/fig_critique` /
  `styles/polymer-paper-preamble.sty` targets.

### Tests

- 188 pytest pass (was 242; -54 from deleted frozen tests +
  selected_preview tests + parser test). ruff clean.

## [0.1.14] - 2026-05-03

Release coordination: forward-jumped from v0.1.9 tag (v0.1.10/11/12 were active
in plugin.json but lacked git tags). v0.1.14 consolidates all 4 shipped PRs (#1–#4)
under a single semver tag. No code changes beyond v0.1.13.

## [0.1.13] - 2026-05-03

Multi-pilot release: BellCurve + BandDiagram macro style-decoupling, Layer 5
export staleness, and BandDiagram dogfood findings. L3 progress 60→65%
(2 of 8 flagship macros decoupled); L5/L7/L8 closed to 100%.

### Added

- `\BandDiagram[<style-keys>]{...}` optional first argument for caller-side
  pgfkeys override (rounded teal frame, CB/VB bandboxes, axis, Et marker,
  trap dashes). `\BD@opts` storage + `\expandafter\tikzset` apply pattern
  (pgfkeys non-expansion workaround). See `docs/macros/band-diagram.md`.
- `\BellCurve[<style-keys>]{x1,y1,x2,y2,orientation}` decoupled style
  primitive: caller supplies draw/fill/line width via pgfkeys; default
  `bell curve/.style` is outline-only with palette-neutral cGray.
- Layer 5 export pipeline staleness model — 4-state machine
  (`MISSING` / `TRACKED_GOLDEN` / `STALE` / `FRESH`) via qpdf metadata-strip
  content-hash. `/fig_export` auto-rebuilds `STALE` / `MISSING`, skips
  `TRACKED_GOLDEN` with warning.
- `docs/macros/band-diagram.md` — caller reference for `\BandDiagram[#1]`.
- `docs/macros/band-diagram-gaps.md` — dogfood findings from 2026-05-03
  `examples/fig3_trapping_concept` partial migration: 5 macro API gaps
  identified (visual model mismatch, TrapLevel extent, Et text persistence,
  bandbox label customization, trap-free panel incompatibility). v0.3 spec
  deferred until multi-fixture pressure confirms which gaps are generic.

### Fixed

- BellCurve PR Codex review follow-ups (F1, F2): `\BellCurve@parse`
  expansion-order corrections for orientation handling.
- Layer 5 metadata-strip regex covers `/CreationDate` alongside `/ID`.

### Tests

- 242 pytest pass (5 new BandDiagram API + byte-classifier tests).

## [0.1.12] - 2026-05-01

### Fixed

- `scripts/check_layout_drift.py`: repeated single-token labels now choose
  the closest reference/PDF pair instead of blindly pairing first hits. This
  fixes the false `deep` drift on `golden_trap_depth_picture` while preserving
  alternate-form fallback behavior.

### Changed

- `examples/golden_trap_depth_picture`: refreshed the fixture render after
  right-panel label spacing and bottom annotation readability tweaks. The
  fixture remains `accepted: false`; accepted-mode still rejects the unresolved
  visual clash budget.

### Tests

- Added regression coverage for repeated single-token drift matching and
  alternate-form fallback.

## [0.1.7.2] - 2026-04-29

Cleanup release that closes the v0.1.6-era pending bugfix for stray
no-extension files in `exports/`.

### Fixed

- `scripts/svg_to_png.sh`: reject output paths that do not end with `.png`
  with a clear stderr message instead of letting `rsvg-convert` silently
  write a no-extension stray file the user has to `rm` manually.
- `scripts/export_svg.sh`: same defense for `.svg` outputs — `pdftocairo
  -svg` writes to the exact path given, so a caller dropping the suffix
  produced a no-extension stray file with the same recovery cost.
- Adds `tests/test_export_svg.py` and a new case in `tests/test_svg_to_png.py`
  locking the suffix guard against regression.

110 pytest pass (108 → 110), ruff clean.

## [0.1.7.1] - 2026-04-29

Hardening release driven by the 4-agent mid-review of v0.1.7 before its
first remote push. Findings: non-string YAML scalars crashed the strip
with TypeError, all-HTML-comment input silently fell back without a
warning, the fallback string was prose an LLM might mis-read, and the
priority-order paragraph was placed after the user-supplied content.

### Fixed

- `scripts/llm_author_prompt.py` `_coerce_selection_notes` helper:
  warns to stderr (naming the example dir and encountered type) and
  coerces to str when `selection_notes` is non-string (int, list, dict,
  bare YAML date such as `2026-04-29`). Prevents TypeError from
  `_HTML_COMMENT.sub` reaching the user as an unhelpful traceback.
- `scripts/llm_author_prompt.py`: warn to stderr when `selection_notes`
  is non-empty before HTML-comment stripping but reduces to empty
  afterward — surfaces the silent-content-loss case the original
  v0.1.7 risk register anticipated.
- `scripts/llm_author_prompt.py`: shorten the missing-key fallback from
  the prose `"(none — only preview filename selected)"` to `"(none)"`
  for parity with the existing `selected_preview` fallback and the
  briefing `_section_body` `(empty)` sentinel.

### Changed

- `prompts/llm_author_tikz.md`: priority-order paragraph is now placed
  **before** the `{{selection_notes}}` placeholder so the LLM absorbs the
  precedence rule before reading user content.
- `prompts/llm_author_tikz.md`: priority paragraph extended to cover the
  extension pattern (selection notes adding visual detail consistent
  with §6) — the dogfood `fig3_trap_schematic_v97/spec.yaml` shows this
  is the real common pattern, not contradiction.

### Tests

- Three regression tests in `tests/test_llm_author_prompt.py`:
  `test_selection_notes_non_string_warns_and_coerces`,
  `test_selection_notes_empty_after_html_strip_warns_and_falls_back`,
  `test_priority_order_paragraph_present_in_output`.
- Updated existing absent-case test to lock the new structural
  relationship (priority paragraph immediately followed by the
  substituted placeholder).

108 pytest pass (105 → 108), ruff clean.

## [0.1.7] - 2026-04-29

### Added

- `prompts/llm_author_tikz.md` `### Selection notes` section with
  preview-grounded authoring guide. Priority order text directs the LLM
  to honor `briefing.md` §6 invariants over selection notes when they
  conflict (`§6 invariants > §3 composition intent > selection notes`).
- `commands/fig_preview_select.md` step 6: recommended 4-heading
  template for `selection_notes` (Visual motifs to preserve / Preview
  errors to fix in TikZ / Labels to lift / Style overrides). Free-form
  remains accepted; HTML-comment author-only notes are stripped.
- `commands/fig_new.md` scaffolds `spec.yaml` with an empty
  `selection_notes: ""` key so new examples have the field present.
- `docs/design-v0.1.md` per-figure folder contract lists
  `selection_notes` as a recognized `spec.yaml` key.
- `docs/roadmap-v0.1.7-selection-notes.md` records the audit-driven
  rationale for plumbing this orphan field instead of adding a
  `/fig_decompose` slash command, and defines the v0.1.x empirical
  validation window plus three trigger-based v0.2 branches.
- `tests/test_llm_author_prompt.py` four new tests covering plumbing,
  HTML-comment stripping (parity with `parse_briefing`), missing-key
  fallback, and backslash preservation through `str.replace`.
- `examples/fig3_trap_schematic_v97/` activated as a tracked dogfood
  fixture demonstrating the 4-heading `selection_notes` convention end
  to end.

### Changed

- `scripts/llm_author_prompt.py` reads `spec.yaml.selection_notes`,
  strips HTML comments using `inputs._HTML_COMMENT` (parity with the
  briefing parser), and substitutes the result into `{{selection_notes}}`
  with a fallback string when the field is missing or whitespace-only.
  Until v0.1.7 the field was declared in `spec.yaml`, parsed by
  `parse_spec`, and never read by any production script — users who
  wrote preview-grounded element-inventory content into it (see
  `examples/fig3_trap_schematic_v97/spec.yaml`) had no way for it to
  reach the LLM authoring prompt.

## [0.1.6] - 2026-04-29

### Added

- `scripts/lint_tex.py` — BLOCKER-tier Style Lock check (`\definecolor`, font override, raw hex,
  non-palette TikZ colors). Integrated into /fig_compile as pre-compile gate: lualatex only runs
  if lint passes; `build/` untouched on lint failure.
- /fig_status <name> — read-only stage inference from filesystem + spec.yaml; prints stage N/6 + Next: hint. No arg = summary of all examples.
- `lint_tex.py` WARN tier: `flagship_macros_unused` (fires once per file when no flagship macro is called) and `thin_stroke` (fires per occurrence when `line width` < 0.25pt). WARN-only exits 0; only BLOCKERs exit 1.
- `prompts/llm_author_tikz.md` — parameterised template for generating a
  filled LLM TikZ authoring prompt from a figure-agent example. §3 is the
  single source of the scaffolding contract; the LLM emits a complete
  standalone `.tex` (`compile.sh` runs `lualatex` on the file directly with
  no wrapper).
- `scripts/llm_author_prompt.py` — CLI and `build_prompt()` helper that
  fills `llm_author_tikz.md` with spec, briefing, palette, and flagship
  macro signatures parsed from preamble comments of the form
  `% \Name{args}: description` (single source of truth for arg semantics,
  no hardcoded signature drift).
- `styles/polymer-paper-preamble.sty` — `% \IsoBlock{w}{d}{h}{color}{hook}`
  signature comment so all four flagship macros expose a structured
  signature line for `llm_author_prompt.py` to read.

### Fixed

- `lint_tex.py` plugged three Style Lock bypasses caught by external review:
  (1) implicit positional colors in TikZ option blocks (`\node[red] {};`,
  `\draw[thick, blue]`) are now rejected via a hardcoded
  `KNOWN_NON_PALETTE_COLORS` set scanned inside `\[...\]` blocks;
  (2) brace-enclosed values (`\node[fill={red}]`) are now matched by an
  optional `\{?...\}?` in the key-value regex; (3) `strip_tex_comment` now
  consumes both characters on every backslash escape so `\\%` (LaTeX newline
  followed by a real comment) correctly truncates and no longer false-flags
  commented-out diagnostics.
- `lint_tex.py` `parse_palette` returns an empty set when
  `polymer-paper-preamble.sty` is missing instead of raising; the CLI now
  exits with code 2 and a clear stderr message in that case (distinct from
  exit 1 for actual lint violations).
- `/fig_status` freshness source set now matches `/fig_review`: `<name>.tex`, `briefing.md`,
  and `styles/polymer-paper-preamble.sty`. Editing the briefing or style lock no longer leaves
  the build pdf or exports falsely reported as fresh.
- `/fig_status` adds a `stale_export` note when any source is newer than an export artifact;
  the `Next:` hint becomes "re-run /fig_compile then /fig_export" instead of "done" so the
  primary action agrees with the diagnostic.
- `/fig_status` adds a `selected_preview_missing` note when `spec.yaml` names a preview that
  is not present in `previews/`.
- `/fig_status` no longer crashes when `examples/<name>/previews` exists as a file rather
  than a directory; reports stage 1 with a `previews_not_directory` note.

### Changed

- All six command docs now end with a single-line Next: footer for consistent affordance.
- `prompt_gen.py` module docstring updated to reflect post-input-extraction responsibility
  (prompt composition and normalization via `inputs` + `redact`, not parsing).
- `SKILL.md` trimmed (145→84 lines) by removing command-level details kept in `commands/*.md`
  ("What the prompt must contain", "What the compile must guarantee") and historical rationale
  (design context documented in `docs/design-v0.1.md`).
- `Violation` NamedTuple gains `severity` field (`"blocker"` | `"warn"`); all existing violations set `severity="blocker"`.
- Dogfood regression tests refactored to filter on `severity="blocker"` and positively assert `flagship_macros_unused` WARN exists.
- `/fig_preview_select` Next: footer now points at `llm_author_prompt.py` as the authoring entry point.

Runtime-output Next: footer in command scripts deferred to v0.2 (touches 6 scripts).

### Deprecated

- `prompt_gen` re-exports of `parse_briefing` and `parse_spec` (backwards-compat shim for 0.1.x)
  will be removed in v0.2. Migration: when importing from `scripts/`, use `from inputs import parse_briefing, parse_spec`.
  (v0.2 will make `scripts/` a proper package with package-relative imports.)
- `redact.py` module will be renamed to `normalize.py` in v0.2; the function name and
  behavior do not change.

## [0.1.5] - 2026-04-28

### Fixed

- Force white background in PNG raster export so figures without explicit
  panel-background fills render correctly in PNG viewers that treat transparency
  as black.

## [0.1.4] - 2026-04-28

### Fixed

- Preserve negated forbidden prompt lines such as `not allowed`, keep in-section
  blockquotes, and warn when literal details are kept inside physics invariants.
- Make `/fig_review` use repo-relative render paths, reject stale renders, and
  include line-numbered TikZ source for critic citations.
- Align design docs, release-gate docs, and local package metadata with shipped
  `/fig_review` behavior.

## [0.1.3] - 2026-04-28

### Added

- Add `/fig_review`, a halt-stage slash command that emits a self-contained
  Reviewer brief for external physics and aesthetic critique.

### Changed

- Update the documented workflow to include `/fig_review` between compile and export.

## [0.1.2] - 2026-04-28

### Added

- Surface `briefing.md` §6 Physics invariants near the top of generated prompts
  and preserve them verbatim so conceptual constraints remain hard constraints.
- Report literal details inside §6 as kept physics-invariant audit items.
- Document `/fig_review` as a v0.2 Claude-assisted critique direction.

## [0.1.1] - 2026-04-28

### Fixed

- Print `/fig_prompt` output in copy-friendly order: normalized prompt first,
  then normalization audit, then next steps, all on stdout.
- Drop author-facing bare label headers from generated prompt bullets while
  preserving real content bullets with text after a colon.

### Added

- Add `styles/tex_template.tex`, a single-panel TikZ starter that compiles
  out-of-the-box and uses `polymer-paper-preamble` Style Lock.
- Document the starter copy command in `README.md` and `/fig_preview_select`.
- Add regression tests for prompt output ordering and meta-label filtering.

## [0.1.0] - 2026-04-28

### Added

- Define figure-agent v0.1 as prompt intent control plus human/LLM-authored
  TikZ compile, checks, and export.
- Normalize literal-heavy prompt details while preserving schematic intent and
  domain terms.
- Use `examples/<name>/build/<name>.pdf` as the canonical compile/check/export
  artifact.
- Export PDF, SVG, TIFF, and PNG, with TIFF/PNG raster output at 600 dpi.

### Not In v0.1

- No image-generation API calls.
- No automatic preview-to-vector reconstruction.
- Selected previews are inspiration only; final TikZ remains editable source.
