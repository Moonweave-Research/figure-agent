# Figure-Agent Plugin Development Closeout Status

**Date:** 2026-05-28 KST
**Status:** current main truth through v0.8.1 / Issue 63

## Bottom Line

The plugin-development chain is usable for real figure dogfood on current
`main`. The core loop now has deterministic compile/export/status gates,
host-vision critique contracts, audit evidence accounting, high-zoom crop
inputs, reference-calibrated critique packs, advisory scoring, publication
gates, SVG-polish routing, SVG-polish readiness surfacing, aesthetic lever
contracts, explicit text-boundary checks for box/rule overflow failures, and
explicit label-path proximity checks for zoom-only near-miss failures. The
v0.8 slice adds real-fixture audit-adoption accounting, a shared single
next-action summary, SVG-polish promotion dogfood evidence, opt-in journal
style-pack catalog support, and optional external vision review evidence.
The v0.8.1 patch adds opt-in reference-learning contracts, non-model
reference-aesthetic metric signals, loop-basin detection, and crop anomaly
accountability for reference-learning critiques.

This still does not mean the plugin can certify a Nature/Science-ready figure
by itself. It means the plugin now exposes the right evidence, stop boundaries,
and lint contracts so a human or host LLM cannot silently skip the known audit
surfaces.

## Latest Verified State

Most recent local full verification after Issue 63 / v0.8.1 release sync:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Results:

- Full test suite: `1371 passed, 1 skipped, 1 xfailed`.
- Ruff check: clean.
- Diff whitespace check: clean.
- Claude plugin validation: manifest, plugin directory, and marketplace pass.
- `full-render` remains intentionally skipped on normal PRs unless the
  workflow is label/main-triggered.

## Closed Critical Tracks

- Driver/status/loop routing: `/fig_status` is the canonical first state check,
  `/fig_drive` remains dry-run, and `/fig_loop` remains verify-only.
- Critique freshness and adjudication: hash-aware freshness, adjudication
  schema, sync helpers, and stale-state handling are implemented.
- Top-tier audit rubrics: structural completeness, label-target matching,
  physical plausibility, conceptual completeness, journal-grade assessment,
  top-tier audit, editorial art direction, and micro-defect surfaces are present.
- High-zoom audit: visual-clash bbox-centered crops, crop-read accountability,
  reference-calibrated critique packs, reference-calibrated advisory scoring,
  and fixture freshness UX cleanup are implemented through Issue 23A-E.
- Audit gate hardening: crop uncertainty stop boundaries, required audit input
  presence, crop content-hash integrity, historical visual-clash regression
  harness, and structured `accept_simplification_reason` are implemented
  through Issue 24A-E.
- Audit evidence UX and compliance: Issues 25-28 surface audit evidence in
  status/driver/loop flows, dogfood the fixture coverage, harden host critique
  compliance, and keep adjudication parity with critique micro-defect contracts.
- Visual-clash evidence pipeline: compile emits `build/visual_clash.json`, the
  critique brief ingests candidates, schema assigns stable `VC###` ids, and lint
  requires exact candidate accounting.
- Text-boundary evidence pipeline: compile emits `build/text_boundary_clash.json`
  from explicit `spec.yaml.text_boundary_checks`; critique/lint require `TB###`
  accounting for candidates.
- Label-path evidence pipeline: compile emits
  `build/label_path_proximity.json` from explicit
  `spec.yaml.label_path_proximity_checks`; critique/lint require `LP###`
  accounting for candidates, and the fig1 vault fixture now dogfoods two
  high-risk semantic path checks. Issue 54 extends clean-current adoption to
  `smoke_trap_demo` with line-body-only checks for its compact band diagram.
- Post-compile fixture state sweep: Issue 53 re-ran all 8 real fixtures through
  compile and `/fig_drive` mode checks, then tightened two misleading
  audit-evidence next-action hints.
- Authoring-boundary helpers: `text_boundary_spec_helper.py`, scoped
  `tex_coordinate_shift.py`, and `/fig_closeout` boundary-sync checks are
  implemented through Issues 30-32.
- Scoped containment: Issue 33 adds `text_allowlist` for `contain_text` row-box
  checks and dogfoods it on `fig1_overview_v2_pair_001_vault`.
- Phrase-aware containment and status UX: Issue 34 handles split PDF words and
  math fragments; Issues 35-38 add aesthetic intent contracts, lint
  accountability, status surfacing, and compact lint summaries.
- Docs/readiness sync: Issues 39-41 reconcile completed contract docs, publish
  the plugin readiness matrix, and lock canonical usage docs.
- SVG polish route: Issues 42-48 implement bounded polish UX, semantic
  backport routing, aesthetic lever grammar, recipe execution, route surfacing,
  clean and real-fixture dogfood, and the explicit `svg_polish_readiness`
  contract. Issue 48 remains the release-truth anchor for SVG polish promotion
  readiness inside this later Issue 53 closeout.
- Final artifact/polish routing: polished SVG is surfaced as a final-artifact
  state, while SVG editing remains explicit human/external-tool work.
- Release gate binding: release mode consumes the latest current `/fig_loop`
  checkpoint and will not close release while adjudication, patch handoff, or
  human-gated loop blockers remain unresolved.
- Real-fixture audit adoption: Issue 57 records fixture-level audit opt-in
  state instead of implying coverage when a fixture lacks declarations.
- Single next-action UX: Issue 58 adds shared read-only `next_action_summary`
  output across status, driver, loop, and closeout flows.
- SVG polish promotion dogfood: Issue 59 records that real fixtures remain
  conservatively blocked behind stale critique evidence rather than being
  promoted to SVG polish prematurely.
- Journal style-pack catalog: Issue 60 adds opt-in venue/playbook packs for
  restrained main-text and separated expressive contexts.
- External vision review evidence: Issue 61 adds optional local
  `external_vision_review.yaml` import and conflict surfacing without adding a
  provider API dependency.
- Reference learning and aesthetic metrics: Issue 63 adds optional
  reference-learning contracts, deterministic reference-aesthetic metrics,
  status/loop/critique surfacing, repeated-basin detection, and v1.13 crop
  anomaly accountability without converting references into copy targets.

## Not A Remaining Blocker

- Existing completed issue files may still contain unchecked historical
  checklist bullets from earlier planning templates. Those are stale checklist
  artifacts, not live blockers, when the issue status says completed and later
  tests/PRs prove the behavior.
- `full-render` is intentionally skipped on normal PRs unless labeled; it runs
  on `main` and label-triggered PRs because the render dependency stack is slow.
- Host-vision critique is semi-automatic by design. The plugin prepares crops,
  candidate ids, schemas, and lint gates; it does not replace the host LLM or
  human art-direction judgment.
- SVG polish remains an explicit finalization path, not a hidden auto-editing
  path.

## Current Priority List

These are useful future improvements, but they are not required before using
the plugin for real figure work.

1. **Fixture adoption expansion.** More real fixtures should declare
   `text_boundary_layout` and/or `label_path_proximity_checks` when they contain
   row boxes, panel rules, internal display rectangles, reference lines,
   semantic curves, or other explicit label-boundary hazards. Current adoption:
   `fig1_overview_v2_pair_001_vault` and `smoke_trap_demo`.
2. **Paper-wide aesthetic context.** The plugin is strong at single-figure
   audit; it still needs a bounded way to carry visual language, restraint,
   typography, and palette intent across multiple figures in one manuscript.
3. **Audit UX compression.** `/fig_status`, `/fig_drive`, and `/fig_closeout`
   now expose a single next-action summary, but the human-readable output can
   still be made denser and easier to scan without weakening contracts.
4. **Positive SVG-polish promotion evidence.** The safe negative route is
   documented; the next useful evidence is a fresh fixture that legitimately
   reaches `ready_for_svg_polish`.

## Practical Use Guidance

For new real figure work, start with:

1. `/fig_status <name>`
2. `/fig_drive <name> --mode authoring --dry-run`
3. Execute only the returned safe next command.
4. Use `/fig_critique` when the driver reaches a host-vision critique boundary.
5. Run `/fig_adjudicate` after critique lint passes.
6. Run `/fig_loop` after critique/adjudication to record the next loop state.
7. Use `/fig_closeout` after each patch target.
8. Use `/fig_export` only after render and critique state are fresh enough for
   release/export work.

At this point, the core plugin release is usable. If continuing plugin
hardening, start with the real fixture state sweep. If not continuing plugin
hardening, the next live work is fixture-specific: refresh stale
renders/critiques/exports, then resolve any human publication provenance gate
for the target figure.
