#!/usr/bin/env bash
# Convert SVG to PNG at 600 dpi for raster export.
set -euo pipefail

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "Error: rsvg-convert not found. Install via: brew install librsvg" >&2
  exit 127
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $(basename "$0") <input.svg> <output.png>" >&2
  exit 1
fi

if [[ ! -f "$1" ]]; then
  echo "Error: input file not found: $1" >&2
  exit 1
fi

rsvg-convert -d 600 -p 600 -f png -o "$2" "$1"
