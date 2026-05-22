---
description: Read-only stage inference from filesystem + spec.yaml; no persistent state written.
---

Inspect the current pipeline stage for a figure without modifying any files.

**Usage**: `/fig_status [<name>]`

`<name>` is optional. With no argument, prints a one-line summary for every figure under `examples/`.

Run from the plugin root:

```
uv run python3 scripts/status.py                   # all figures (one line each)
uv run python3 scripts/status.py examples/<name>   # one figure (check list + state vector + Next:)
```

## Traffic Controller Contract

Agents should treat `/fig_status <name>` as the canonical first check unless
the user explicitly requested a lower-level command (`/fig_compile`,
`/fig_critique`, `/fig_adjudicate`, `/fig_loop`, `/fig_export`, `/fig_closeout`).
The printed `Next:` hint plus the state vector (`render_state`,
`critique_state`, `export_state`, `acceptance_state`, `workflow_ready`,
`release_ready`, `final_artifact_state`, `publication_gate_state`) is the
workflow's authoritative next action. Agents must not jump from build to
export, critique, loop, polish, release, or acceptance/provenance promotion by
intuition or memory when `Next:` or `Publication gate:` points elsewhere.
Rerun `/fig_status <name>` after every completed action to derive the next
step.

Single-figure output also prints an `Explanation:` line. This line separates
fixture freshness work from human-only publication decisions:

- `fixture_freshness` blockers mean an artifact is missing or stale, such as
  `render_stale`, `critique_stale`, or `export_missing`.
- `human_blocker` blockers mean the plugin must stop for accepted/golden
  roll-forward, publication provenance, or human acceptance.
- `plugin_state` entries such as `critique_not_required` are informational and
  do not ask the agent to fabricate a critique.

`Explanation:` is derived from the same state vector as `Next:`. It is a
readability layer, not a separate readiness rule.

## Stages

| Stage | Meaning | Next hint |
|-------|---------|-----------|
| 0 | directory missing | /fig_new <name> |
| 1 | spec.yaml present; no .tex authored yet | author <name>.tex from briefing.md, then /fig_compile <name> |
| 2 | .tex present; build pdf missing or stale | /fig_compile <name> |
| 3 | build pdf fresh; no exports | fix declared missing references, or run /fig_critique <name> when reference-grounded critique is missing/stale, then /fig_export <name> |
| 4 | export artifact present | repair any stale/missing critique, export, final-artifact, or acceptance gate; otherwise done |

The v0.1 stages 2/3 (preview-images-without-selection / selected_preview-set-without-tex) were removed in the v0.2 frozen-legacy cleanup along with `/fig_prompt` and `/fig_preview_select`. Active authoring now goes directly from `briefing.md` to `<name>.tex`; see `docs/architecture-overview.md` Layer 3 for the full picture.

Stage 4 next-hint variants (priority order):

- `spec_parse_error` or `style_profile_unknown` → fix `spec.yaml` before continuing.
- `missing_briefing` → complete `briefing.md` before continuing.
- `critique_reference_missing` declared reference input is missing → fix `spec.yaml` path or add the file before continuing.
- stale export plus `critique_missing` / `critique_stale` → run `/fig_critique <name>` first, then `/fig_export <name>`.
- `stale_export` render source set is newer than exports → if `render_state` is not `FRESH`, re-run /fig_compile then /fig_export; if render is already fresh and critique is fresh/not-required, re-run /fig_export only.
- `exports_substate == STALE` because export PDF content differs from build PDF
  or required siblings are missing → re-run /fig_export.
- `partial_export` not all four export artifacts present → re-run /fig_export.
- `critique_missing` or `critique_stale` with exports otherwise present → run `/fig_critique <name>` before continuing.
- `final_artifact_missing` / `final_artifact_invalid` / `final_artifact_stale` / `final_artifact_blocked` for a declared polished SVG → repair the manifest, polished SVG, audit, or semantic backport before acceptance/release.
- `accepted: false` declared in spec.yaml → resolve QUALITY_AUDIT.md defects and flip the flag.
- otherwise → done.

Stage 4 corresponds to old v0.1 stage 6; print format is now `stage X/4` (was `stage X/6`).

## State Vector

`/fig_status` reports a compact state vector in addition to the stage number:

- `render_state`: `NOT_SCAFFOLDED`, `NOT_AUTHORED`, `MISSING`, `STALE`, or `FRESH`.
- `critique_state`: `NOT_REQUIRED`, `MISSING`, `STALE`, `REFERENCE_MISSING`, or `FRESH`.
- `export_state`: same value as `exports_substate` (`MISSING`, `TRACKED_GOLDEN`, `STALE`, or `FRESH`).
- `acceptance_state`: `NOT_DECLARED`, `NOT_ACCEPTED`, or `ACCEPTED`.
- `workflow_ready`: `true` when stage 4 has no blocking notes, render is fresh, export is fresh or tracked golden, and critique is fresh/not-required. `coordinate_hints_*` and `final_artifact_*` notes are non-blocking for workflow closure; final artifacts are enforced by `release_ready` / `final_ready`.
- `golden_ready`: `true` when `workflow_ready` is true and `accepted: true` is declared.
- `final_artifact_state`: `NONE`, `MISSING`, `INVALID`, `STALE`, `BLOCKED`, or `FRESH`.
- `final_artifact_kind`: `generated_export` or `polished_svg`.
- `final_artifact_path`: current generated export or declared polished artifact path.
- `release_ready`: `true` when `golden_ready` is true, the export state is content-fresh (`FRESH`, not merely `TRACKED_GOLDEN`), and any declared polished SVG final artifact is fresh and unblocked.
- `final_ready`: compatibility alias for `release_ready`.
- `publication_gate_state`: `NOT_APPLICABLE`, `PASS`,
  `HUMAN_ACCEPTANCE_REQUIRED`, or `PROVENANCE_REQUIRED`. This is separate from
  `release_ready`: target-journal/provenance decisions remain explicit human
  gates even when render/export/final-artifact state is otherwise ready.
- `publication_gate_failures`: typed blocker records with `code`, `category`,
  `actor`, `message`, and `required_action`. The single-figure printed output
  shows the first blocker as `Publication blocker:` when present.
- `status_explanation`: structured explanation with `summary`,
  `first_blocker`, and buckets for `plugin_state`, `fixture_freshness`, and
  `human_blockers`. `/fig_driver --dry-run` reuses this same object.

For polished SVG final artifacts, `publication_gate_state` also enforces the
publication disclosure field because the submitted artifact may include human
SVG edits beyond generated TikZ exports.

The no-argument summary includes `ready: true|false`, which follows
`release_ready`, and appends `publication: <state>` when the publication gate
is applicable. Treat `ready: true` plus `publication: PROVENANCE_REQUIRED` as
artifact-ready but not submission-ready.

Notes that may appear:

- `spec_parse_error` — `spec.yaml` is malformed or semantically invalid; fix it before continuing.
- `style_profile_unknown` — `spec.yaml.style_profile` is not one of the known style profiles.
- `partial_export` — not all four of pdf/svg/tif/png are present in `exports/`.
- `stale_export` — either the freshness source set is newer than export artifacts, or Layer 5 reports `exports_substate == STALE`. If `render_state` is stale, re-run `/fig_compile` then `/fig_export`; if render is already fresh and only exports are behind, re-run `/fig_export`.
- `reference_image_missing` — `spec.yaml` names a `reference_image` path that is not present relative to the example directory.
- `coordinate_hints_missing` — `reference_image` exists but no `coordinate_hints.yaml` has been generated; run `/fig_extract <name>` (Layer 2.5).
- `coordinate_hints_stale` — `coordinate_hints.yaml` is older than the reference image; re-run `/fig_extract <name> --rebuild`.
- `coordinate_hints_parse_error` — `coordinate_hints.yaml` is not valid YAML; regenerate with `/fig_extract <name> --rebuild`.
- `coordinate_hints_outdated` — `coordinate_hints.yaml` predates the current authored/rendered source and should be refreshed when reference alignment matters.
- `final_artifact_missing`, `final_artifact_invalid`, `final_artifact_stale`, `final_artifact_blocked` — a declared polished SVG final artifact needs repair before release readiness.
- `previews_not_directory` — `examples/<name>/previews` exists as a file, not a directory.
- `panel_reference_image_missing` — a panel declares `bbox_pdf_cm` and `reference_image` but the image file is not found at the declared path relative to the example directory; correct the path in `spec.yaml` or add the file before running `/fig_critique <name>`.
- `critique_reference_missing` — a declared reference input needed for critique/export is missing; fix the path or add the file before `/fig_critique` or `/fig_export`.
- `critique_missing` — the fixture has a usable figure-level `reference_image` or at least one panel with both `reference_image` and `bbox_pdf_cm`, but no `critique.md`; run `/fig_critique <name>` before `/fig_export <name>`.
- `critique_stale` — `critique.md` hash metadata does not match current critique inputs, rubric version, or generator version; legacy critiques without hash metadata fall back to mtime comparison against `<name>.tex`, `briefing.md`, `spec.yaml`, usable reference image, participating panel reference image, `coordinate_hints.yaml`, reference-conditioned authoring docs, `subregion_iteration_log.md`, and Style Lock. Re-run `/fig_critique <name>`.

Build/export freshness source set: `<name>.tex`, `briefing.md`, `spec.yaml`,
and `styles/polymer-paper-preamble.sty`. Reference images and
`coordinate_hints.yaml` are critique/reference context, not render outputs; editing
them makes critique stale but does not require `/fig_compile` by itself.
`/fig_critique` additionally checks panel reference images that participate in
crop/reference comparison and optional reference-conditioned authoring docs
(`authoring_contract.md`, `reference/reference_pack.md`, `authoring_plan.md`,
`theory_guard.md`, `subregion_iteration_log.md`).

Next: follow the printed Next: hint for this figure's stage.
