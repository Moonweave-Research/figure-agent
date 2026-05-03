---
description: Read-only stage inference from filesystem + spec.yaml; no persistent state written.
---

Inspect the current pipeline stage for a figure without modifying any files.

**Usage**: `/fig_status [<name>]`

`<name>` is optional. With no argument, prints a one-line summary for every figure under `examples/`.

Run from the plugin root:

```
uv run python3 scripts/status.py                   # all figures (one line each)
uv run python3 scripts/status.py examples/<name>   # one figure (full check list + Next:)
```

## Stages

| Stage | Meaning | Next hint |
|-------|---------|-----------|
| 0 | directory missing | /fig_new <name> |
| 1 | spec.yaml present; no .tex authored yet | author <name>.tex from briefing.md, then /fig_compile <name> |
| 2 | .tex present; build pdf missing or stale | /fig_compile <name> |
| 3 | build pdf fresh; no exports | /fig_export <name> (or [legacy] /fig_review for external critic brief) |
| 4 | export artifact present | done (or revise + recompile + re-export) |

The v0.1 stages 2/3 (preview-images-without-selection / selected_preview-set-without-tex) were removed in the v0.2 frozen-legacy cleanup along with `/fig_prompt` and `/fig_preview_select`. Active authoring now goes directly from `briefing.md` to `<name>.tex`; see `docs/architecture-overview.md` Layer 3 for the full picture.

Stage 4 next-hint variants (priority order):

- `stale_export` source set is newer than exports → re-run /fig_compile then /fig_export.
- `partial_export` not all four export artifacts present → re-run /fig_export.
- `accepted: false` declared in spec.yaml → resolve QUALITY_AUDIT.md defects and flip the flag.
- otherwise → done.

Stage 4 corresponds to old v0.1 stage 6; print format is now `stage X/4` (was `stage X/6`).

Notes that may appear:

- `partial_export` — not all four of pdf/svg/tif/png are present in `exports/`.
- `stale_export` — `<name>.tex`, `briefing.md`, or the style lock is newer than the export artifacts; re-run `/fig_compile` then `/fig_export`.
- `reference_image_missing` — `spec.yaml` names a `reference_image` path that is not present relative to the example directory.
- `coordinate_hints_missing` — `reference_image` exists but no `coordinate_hints.yaml` has been generated; run `/fig_extract <name>` (Layer 2.5).
- `coordinate_hints_stale` — `coordinate_hints.yaml` is older than the reference image; re-run `/fig_extract <name> --rebuild`.
- `coordinate_hints_parse_error` — `coordinate_hints.yaml` is not valid YAML; regenerate with `/fig_extract <name> --rebuild`.
- `previews_not_directory` — `examples/<name>/previews` exists as a file, not a directory.

Freshness source set matches `/fig_review`: `<name>.tex`, `briefing.md`, and `styles/polymer-paper-preamble.sty`. Editing any of these without recompiling marks the build pdf or exports as stale.

Next: follow the printed Next: hint for this figure's stage.
