#!/usr/bin/env bash
# export_svg.sh — PDF → SVG with text preserved as <text> nodes.
# Usage: scripts/export_svg.sh <input.pdf> <output.svg>
#
# Uses dvisvgm in --pdf mode so labels survive as semantic <text> elements
# instead of being outlined into glyph paths. Fonts are embedded via woff2
# so the SVG renders correctly without external font files.
#
# Requirements:
#   - dvisvgm (ships with TeX Live; standalone via `brew install dvisvgm`)
#   - mutool (mupdf-tools) OR Ghostscript < 10.01.0 on the PATH for --pdf
#     input parsing. dvisvgm 3.x rejects Ghostscript >= 10.01.0.

set -euo pipefail

if ! command -v dvisvgm >/dev/null 2>&1; then
  echo "Error: dvisvgm not found. Install via TeX Live or 'brew install dvisvgm'." >&2
  exit 127
fi

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

# --pdf: take a PDF as input (requires mutool or compatible Ghostscript)
# --font-format=woff2: embed fonts so <text> elements render out of the box
dvisvgm --pdf --font-format=woff2 "$PDF_INPUT" -o "$SVG_OUTPUT" >/dev/null

echo "Generated: $SVG_OUTPUT"
