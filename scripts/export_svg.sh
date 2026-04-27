#!/usr/bin/env bash
# export_svg.sh — PDF → SVG
# Usage: scripts/export_svg.sh <input.pdf> <output.svg>

set -euo pipefail

if ! command -v pdftocairo >/dev/null 2>&1; then
  echo "Error: pdftocairo not found. Install poppler-utils." >&2
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

pdftocairo -svg "$PDF_INPUT" "$SVG_OUTPUT"

echo "Generated: $SVG_OUTPUT"
