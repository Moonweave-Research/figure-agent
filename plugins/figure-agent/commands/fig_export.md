---
description: Export figure to PDF / SVG / TIFF / PNG (600 dpi raster) in exports/.
---

Export final figure.

**Usage**: `/fig_export <name>`

Run from the plugin root.
`<name>` maps to `examples/<name>/`.

Steps:
1. Run: `uv run python scripts/run_export.py <name>`.
   - If the fixture has a usable figure-level `reference_image`, or a panel with both `reference_image` and `bbox_pdf_cm`, a fresh `critique.md` is required first. Run `/fig_critique <name>` if the script reports `critique_missing` or `critique_stale`. Pass `--skip-critique` only for an intentional draft export.
   - The orchestrator then reads the exports/ sub-state and dispatches:
     - **MISSING** or **STALE** → regenerate PDF / SVG / TIFF / PNG.
     - **FRESH** → no-op.
     - **TRACKED_GOLDEN** → skip with warning. Pass `--force-golden` to overwrite the curated golden artifacts (rare; only when intentionally rolling forward the reference).
2. Report file sizes and paths from the script output.
3. Suggest commit if user is happy: `git add -f examples/<name>/exports/<name>.pdf examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.tif examples/<name>/exports/<name>.png`. Only relevant for promoting a new golden fixture; routine work leaves exports/ ignored.

Human-gated. No automatic commit.

Next: done — outputs in examples/<name>/exports/. To revise, edit <name>.tex and re-run /fig_compile, /fig_critique when reference-grounded critique is required, then /fig_export.
