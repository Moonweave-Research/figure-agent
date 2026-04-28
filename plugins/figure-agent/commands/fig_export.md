---
description: Export figure to PDF / SVG / TIFF (600 dpi) in exports/.
---

Export final figure.

**Usage**: `/fig_export` (inside examples/<name>/ or --name)

Steps:
1. Verify compile succeeded (build/<name>.pdf exists).
2. Copy PDF to `exports/<name>.pdf`.
3. Run `bash scripts/export_svg.sh build/<name>.pdf exports/<name>.svg`.
4. For TIFF: `pdftocairo -tiff -r 600 -singlefile build/<name>.pdf exports/<name>`. For PNG 600 dpi: `bash scripts/svg_to_png.sh exports/<name>.svg exports/<name>.png`.
5. Report file sizes and paths.
6. Suggest commit if user is happy: `git add examples/<name>/exports/`.

Human-gated. No automatic commit.
