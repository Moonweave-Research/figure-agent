#!/usr/bin/env bash
# export_svg.sh — PDF → renderer-stable SVG with glyphs outlined as paths.
# Usage: scripts/export_svg.sh <input.pdf> <output.svg>
#
# The editable authority is TeX.  The derived SVG prioritizes visual fidelity:
# embedded-font <text> output has shown renderer-dependent kerning drift in
# librsvg, including visibly split voltage labels and panel titles.  Outlined
# glyphs keep the PDF geometry stable across browsers and rasterizers.
#
# Requirements:
#   - dvisvgm (ships with TeX Live; standalone via `brew install dvisvgm`)
#   - mutool (mupdf-tools) OR Ghostscript < 10.01.0 on the PATH for --pdf
#     input parsing. dvisvgm 3.x rejects Ghostscript >= 10.01.0.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <input.pdf> <output.svg>" >&2
  exit 1
fi

PDF_INPUT="$1"
SVG_OUTPUT="$2"

if [[ ! -f "$PDF_INPUT" ]]; then
  echo "Error: file not found: $PDF_INPUT" >&2
  exit 1
fi

# Defend against caller passing an output path that lacks the .svg suffix.
# dvisvgm writes to the exact path given; missing the suffix yields a
# no-extension stray file in exports/ that has to be `rm`'d manually.
if [[ "$SVG_OUTPUT" != *.svg ]]; then
  echo "Error: output path must end with .svg, got: $SVG_OUTPUT" >&2
  exit 1
fi

if ! command -v dvisvgm >/dev/null 2>&1; then
  echo "Error: dvisvgm not found. Install via TeX Live or 'brew install dvisvgm'." >&2
  exit 127
fi

# --pdf: take a PDF as input (requires mutool or compatible Ghostscript)
# --no-fonts=1: emit reusable glyph paths instead of renderer-dependent fonts
dvisvgm --pdf --no-fonts=1 "$PDF_INPUT" -o "$SVG_OUTPUT" >/dev/null

echo "Generated: $SVG_OUTPUT"
