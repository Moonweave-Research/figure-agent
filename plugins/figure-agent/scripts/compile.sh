#!/usr/bin/env bash
# compile.sh — raw TikZ .tex → build/<name>.pdf + build/<name>.png
# Usage:   compile.sh <path/to/file.tex>
# Engine:  LATEX_ENGINE env var (default: lualatex)
#          Override: LATEX_ENGINE=xelatex ./compile.sh file.tex

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
export TEXINPUTS="${WORKFLOW_DIR}/styles/:${TEXINPUTS:-}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $(basename "$0") <file.tex>" >&2
  exit 1
fi

TEX_INPUT="$1"

if [[ ! -f "$TEX_INPUT" ]]; then
  echo "Error: file not found: $TEX_INPUT" >&2
  exit 1
fi

echo 'Lint: Style Lock check (BLOCKER fails, WARN reports)...' >&2
uv run python3 "$WORKFLOW_DIR/scripts/lint_tex.py" "$TEX_INPUT"

# Opt-in strict mode: when FIGURE_AGENT_STRICT=1, propagate --strict to the
# collision/clash checkers so non-zero findings fail the compile (default
# behavior is report-only with exit 0 to preserve dogfood ergonomics).
STRICT_ARGS=()
if [[ "${FIGURE_AGENT_STRICT:-}" == "1" ]]; then
  STRICT_ARGS=(--strict)
  echo 'Strict mode: collision/clash findings will fail the compile.' >&2
fi

ENGINE="${LATEX_ENGINE:-lualatex}"

cd "$(dirname "$TEX_INPUT")"
FILE="$(basename "$TEX_INPUT")"
BASE="${FILE%.tex}"
BUILD_DIR="build"

mkdir -p "$BUILD_DIR"

PDF_OUT="${BUILD_DIR}/${BASE}.pdf"
PNG_OUT="${BUILD_DIR}/${BASE}.png"

cleanup_failed_build() {
  local status=$?
  if [[ $status -ne 0 ]]; then
    rm -f "$PDF_OUT" "$PNG_OUT"
  fi
}
trap cleanup_failed_build ERR

rm -f "$PDF_OUT" "$PNG_OUT"
"$ENGINE" -interaction=nonstopmode -output-directory="$BUILD_DIR" "$FILE"
pdftocairo -png -r 600 -singlefile "$PDF_OUT" "${BUILD_DIR}/${BASE}"
uv run python3 "$WORKFLOW_DIR/scripts/check_collisions.py" "${STRICT_ARGS[@]}" "$PDF_OUT"
uv run python3 "$WORKFLOW_DIR/scripts/check_visual_clash.py" \
  "${STRICT_ARGS[@]}" \
  --json-output "${BUILD_DIR}/visual_clash.json" \
  "$PDF_OUT"
uv run python3 "$WORKFLOW_DIR/scripts/check_text_boundary_clash.py" \
  "${STRICT_ARGS[@]}" \
  --json-output "${BUILD_DIR}/text_boundary_clash.json" \
  "$PDF_OUT"
uv run python3 "$WORKFLOW_DIR/scripts/check_label_path_proximity.py" \
  "${STRICT_ARGS[@]}" \
  --json-output "${BUILD_DIR}/label_path_proximity.json" \
  "$PDF_OUT"
if [[ -f "coordinate_hints.yaml" ]]; then
  uv run python3 "$WORKFLOW_DIR/scripts/check_layout_drift.py" "${STRICT_ARGS[@]}" .
fi
uv run python3 "$WORKFLOW_DIR/scripts/perception_pack.py" "$BASE"
trap - ERR

echo "Generated: ${BUILD_DIR}/${BASE}.pdf, ${BUILD_DIR}/${BASE}.png (engine: $ENGINE)"
