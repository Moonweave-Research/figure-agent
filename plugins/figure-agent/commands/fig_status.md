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

## Stages

| Stage | Meaning | Next hint |
|-------|---------|-----------|
| 0 | directory missing | /fig_new <name> |
| 1 | spec.yaml present; no .tex authored yet | author <name>.tex from briefing.md, then /fig_compile <name> |
| 2 | .tex present; build pdf missing or stale | /fig_compile <name> |
| 3 | build pdf fresh; no exports | fix declared missing references, or run /fig_critique <name> when reference-grounded critique is missing/stale, then /fig_export <name> |
| 4 | export artifact present | done (or revise + recompile + re-export) |

The v0.1 stages 2/3 (preview-images-without-selection / selected_preview-set-without-tex) were removed in the v0.2 frozen-legacy cleanup along with `/fig_prompt` and `/fig_preview_select`. Active authoring now goes directly from `briefing.md` to `<name>.tex`; see `docs/architecture-overview.md` Layer 3 for the full picture.

Stage 4 next-hint variants (priority order):

- `critique_reference_missing` declared reference input is missing → fix `spec.yaml` path or add the file before continuing.
- `stale_export` render source set is newer than exports → if `render_state` is not `FRESH`, re-run /fig_compile then /fig_export; if render is already fresh, re-run /fig_export only.
- `exports_substate == STALE` because export PDF content differs from build PDF
  or required siblings are missing → re-run /fig_export.
- `partial_export` not all four export artifacts present → re-run /fig_export.
- `accepted: false` declared in spec.yaml → resolve QUALITY_AUDIT.md defects and flip the flag.
- otherwise → done.

Stage 4 corresponds to old v0.1 stage 6; print format is now `stage X/4` (was `stage X/6`).

## State Vector

`/fig_status` reports a compact state vector in addition to the stage number:

- `render_state`: `NOT_SCAFFOLDED`, `NOT_AUTHORED`, `MISSING`, `STALE`, or `FRESH`.
- `critique_state`: `NOT_REQUIRED`, `MISSING`, `STALE`, `REFERENCE_MISSING`, or `FRESH`.
- `export_state`: same value as `exports_substate` (`MISSING`, `TRACKED_GOLDEN`, `STALE`, or `FRESH`).
- `acceptance_state`: `NOT_DECLARED`, `NOT_ACCEPTED`, or `ACCEPTED`.
- `final_ready`: `true` only when stage 4 has no notes, render is fresh, export is fresh or tracked golden, critique is fresh/not-required, and `accepted` is not `false`.

The no-argument summary includes `ready: true|false` for quick triage across all fixtures.

Notes that may appear:

- `partial_export` — not all four of pdf/svg/tif/png are present in `exports/`.
- `stale_export` — either the freshness source set is newer than export artifacts, or Layer 5 reports `exports_substate == STALE`. If source files are newer, re-run `/fig_compile` then `/fig_export`; if only export content differs from the fresh build PDF, re-run `/fig_export`.
- `reference_image_missing` — `spec.yaml` names a `reference_image` path that is not present relative to the example directory.
- `coordinate_hints_missing` — `reference_image` exists but no `coordinate_hints.yaml` has been generated; run `/fig_extract <name>` (Layer 2.5).
- `coordinate_hints_stale` — `coordinate_hints.yaml` is older than the reference image; re-run `/fig_extract <name> --rebuild`.
- `coordinate_hints_parse_error` — `coordinate_hints.yaml` is not valid YAML; regenerate with `/fig_extract <name> --rebuild`.
- `previews_not_directory` — `examples/<name>/previews` exists as a file, not a directory.
- `panel_reference_image_missing` — a panel declares `bbox_pdf_cm` and `reference_image` but the image file is not found at the declared path relative to the example directory; correct the path in `spec.yaml` or add the file before running `/fig_critique <name>`.
- `critique_reference_missing` — a declared reference input needed for critique/export is missing; fix the path or add the file before `/fig_critique` or `/fig_export`.
- `critique_missing` — the fixture has a usable figure-level `reference_image` or at least one panel with both `reference_image` and `bbox_pdf_cm`, but no `critique.md`; run `/fig_critique <name>` before `/fig_export <name>`.
- `critique_stale` — `critique.md` is older than a critique input (`<name>.tex`, `briefing.md`, `spec.yaml`, usable reference image, participating panel reference image, `coordinate_hints.yaml`, reference-conditioned authoring docs, or Style Lock); re-run `/fig_critique <name>`.

Build/export freshness source set: `<name>.tex`, `briefing.md`, `spec.yaml`,
and `styles/polymer-paper-preamble.sty`. Reference images and
`coordinate_hints.yaml` are critique/reference context, not render outputs; editing
them makes critique stale but does not require `/fig_compile` by itself.
`/fig_critique` additionally checks panel reference images that participate in
crop/reference comparison and optional reference-conditioned authoring docs
(`authoring_contract.md`, `reference/reference_pack.md`, `authoring_plan.md`,
`theory_guard.md`).

Next: follow the printed Next: hint for this figure's stage.
