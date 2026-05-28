---
description: Export figure to PDF / SVG / TIFF / PNG (600 dpi raster) in exports/.
---

Export final figure.

**Usage**: `/fig_export <name>`

Run from the plugin root.
`<name>` maps to `examples/<name>/`.

Steps:
1. Run: `uv run python scripts/run_export.py <name>`.
   - If the fixture has a usable figure-level `reference_image`, or a panel with both `reference_image` and `bbox_pdf_cm`, a fresh pre-export `critique.md` is required first. Run `/fig_critique <name>` if the script reports `critique_missing` or `critique_stale`. Pass `--skip-critique` only for an intentional draft export.
   - If the script reports `reference_image_missing` or `panel_reference_image_missing`, fix the declared path or add the file. `--skip-critique` does not override broken reference configuration.
   - The orchestrator then reads the exports/ sub-state and dispatches:
     - **MISSING** or **STALE** → regenerate PDF / SVG / TIFF / PNG.
     - **FRESH** → no-op.
     - **TRACKED_GOLDEN** → skip with warning. Pass `--force-golden` to overwrite the curated golden artifacts (rare; only when intentionally rolling forward the reference).
2. Report file sizes and paths from the script output.
3. Suggest commit if user is happy: `git add -f examples/<name>/exports/<name>.pdf examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.tif examples/<name>/exports/<name>.png`. Only relevant for promoting a new golden fixture; routine work leaves exports/ ignored.

`/fig_export` is the export gate, not the whole loop. It is the point where
reference-grounded critique freshness is enforced before export regeneration.
If this command reports `critique_missing` or `critique_stale`, return to
`/fig_critique <name>` instead of repeatedly compiling. SVG polish does not
begin here: it starts only after a generated export is current and the
remaining work is visual-only finalization (see `/fig_loop` SVG Polish
Handoff).

For generated-export fixtures without polished-SVG opt-in, the generated
`exports/<name>.svg` is not itself a critique freshness input. Treat any
post-export critique as a final review of the current rendered candidate, not
as a hidden export mutation gate.

Human-gated. No automatic commit.

Next: done — outputs in examples/<name>/exports/. To revise, edit <name>.tex and re-run /fig_compile, /fig_critique when reference-grounded critique is required, then /fig_export.
