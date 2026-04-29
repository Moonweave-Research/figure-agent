---
description: Export figure to PDF / SVG / TIFF / PNG (600 dpi raster) in exports/.
---

Export final figure.

**Usage**: `/fig_export <name>`

Run from the plugin root.
`<name>` maps to `examples/<name>/`.

Steps:
1. Verify compile succeeded (`examples/<name>/build/<name>.pdf` exists).
2. Copy PDF to `examples/<name>/exports/<name>.pdf`.
3. Run `bash scripts/export_svg.sh examples/<name>/build/<name>.pdf examples/<name>/exports/<name>.svg`.
4. For TIFF: `pdftocairo -tiff -r 600 -singlefile examples/<name>/build/<name>.pdf examples/<name>/exports/<name>`. For PNG 600 dpi: `bash scripts/svg_to_png.sh examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.png`.
5. Report file sizes and paths.
6. Suggest commit if user is happy: `git add -f examples/<name>/exports/<name>.pdf examples/<name>/exports/<name>.svg examples/<name>/exports/<name>.tif examples/<name>/exports/<name>.png`.

Human-gated. No automatic commit.

Next: done — outputs in examples/<name>/exports/. To revise, edit <name>.tex and re-run /fig_compile then /fig_export.
