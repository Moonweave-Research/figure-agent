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

# Defend against the caller (LLM running /fig_export, hand-typed shell) passing
# an output path that lacks the .png suffix. Without this guard, rsvg-convert
# silently writes to the exact path given, producing a no-extension stray file
# in exports/ that has to be `rm`'d manually.
if [[ "$2" != *.png ]]; then
  echo "Error: output path must end with .png, got: $2" >&2
  exit 1
fi

rsvg-convert -b white -d 600 -p 600 -f png -o "$2" "$1"
