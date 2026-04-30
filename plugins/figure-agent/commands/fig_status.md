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
| 1 | spec.yaml present; no preview images | [legacy] /fig_prompt — or author <name>.tex directly |
| 2 | previews/ has images; no selection recorded | [legacy] /fig_preview_select — or author <name>.tex directly |
| 3 | preview selected in spec.yaml; no .tex | author <name>.tex, then /fig_compile <name> |
| 4 | .tex present; build pdf missing or stale | /fig_compile <name> |
| 5 | build pdf fresh; no exports | /fig_export <name> (or [legacy] /fig_review for external critic brief) |
| 6 | export artifact present | done (or revise + recompile + re-export) |

Stage 1/2 hints carry a `[legacy]` marker because the v0.1 image-gen orchestration path (`/fig_prompt` → `/fig_preview_select` → preview-driven authoring) is no longer the active development direction. The active workflow drives `<name>.tex` authoring directly from `briefing.md` plus an optional `reference_image`; see `docs/architecture-overview.md` Layer 3 for the full picture. The legacy path remains supported for in-flight users.

Stage 6 next-hint variants (priority order):

- `stale_export` source set is newer than exports → re-run /fig_compile then /fig_export.
- `partial_export` not all four export artifacts present → re-run /fig_export.
- `accepted: false` declared in spec.yaml → resolve QUALITY_AUDIT.md defects and flip the flag.
- otherwise → done.

Notes that may appear:

- `partial_export` — not all four of pdf/svg/tif/png are present in `exports/`.
- `stale_export` — `<name>.tex`, `briefing.md`, or the style lock is newer than the export artifacts; re-run `/fig_compile` then `/fig_export`.
- `selected_preview_missing` — `spec.yaml` names a preview that is not in `previews/`.
- `reference_image_missing` — `spec.yaml` names a `reference_image` path that is not present relative to the example directory.
- `previews_not_directory` — `examples/<name>/previews` exists as a file, not a directory.

Freshness source set matches `/fig_review`: `<name>.tex`, `briefing.md`, and `styles/polymer-paper-preamble.sty`. Editing any of these without recompiling marks the build pdf or exports as stale.

Next: follow the printed Next: hint for this figure's stage.
