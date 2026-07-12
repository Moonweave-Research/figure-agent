#!/usr/bin/env bash
# compile.sh — raw TikZ .tex → build/<name>.pdf + build/<name>.png
# Usage:   compile.sh <path/to/file.tex>
# Engine:  LATEX_ENGINE env var (default: lualatex)
#          Override: LATEX_ENGINE=xelatex ./compile.sh file.tex

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
UV_RUN=(uv run --project "$WORKFLOW_DIR")
SCRIPT_IMPORT_PATH="${WORKFLOW_DIR}/scripts:${WORKFLOW_DIR}/scripts/checks"
if [[ -n "${PYTHONPATH:-}" ]]; then
  export PYTHONPATH="${SCRIPT_IMPORT_PATH}:${PYTHONPATH}"
else
  export PYTHONPATH="$SCRIPT_IMPORT_PATH"
fi
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

SEMANTIC_CONTRACT="$(dirname "$TEX_INPUT")/semantic_contract.yaml"
if [[ -f "$SEMANTIC_CONTRACT" ]]; then
  echo 'Gate: Semantic role, connector, and label contract...' >&2
  "${UV_RUN[@]}" python3 \
    "$WORKFLOW_DIR/scripts/quality/semantic_legibility_contract.py" \
    "$SEMANTIC_CONTRACT"
fi

echo 'Lint: Style Lock check (BLOCKER fails, WARN reports)...' >&2
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/lint_tex.py" "$TEX_INPUT"

# Opt-in strict mode: when FIGURE_AGENT_STRICT=1, propagate --strict to the
# collision/clash checkers so non-zero findings fail the compile (default
# behavior is report-only with exit 0 to preserve dogfood ergonomics).
STRICT_ARGS=()
VISUAL_CLASH_ARGS=()
if [[ "${FIGURE_AGENT_STRICT:-}" == "1" ]]; then
  STRICT_ARGS=(--strict)
  VISUAL_CLASH_ARGS=(--strict --ignore-known-fp)
  echo 'Strict mode: collision/clash findings will fail the compile.' >&2
fi

ENGINE="${LATEX_ENGINE:-lualatex}"

cd "$(dirname "$TEX_INPUT")"
FILE="$(basename "$TEX_INPUT")"
BASE="${FILE%.tex}"
BUILD_DIR="build"
WRAPPED_FILE="${BUILD_DIR}/.${BASE}.figure-agent-wrapper.tex"
COMPILE_FILE="$FILE"

mkdir -p "$BUILD_DIR"

if ! grep -q '\\documentclass' "$FILE"; then
  cat > "$WRAPPED_FILE" <<EOF
\documentclass[border=8pt]{standalone}
\usepackage{polymer-paper-preamble}

\begin{document}
\resizebox{90mm}{!}{%
\begin{tikzpicture}[
  every node/.style={font=\textsf{\fontsize{8}{10}\selectfont}},
]
EOF
  cat "$FILE" >> "$WRAPPED_FILE"
  cat >> "$WRAPPED_FILE" <<EOF
\end{tikzpicture}%
}
\end{document}
EOF
  COMPILE_FILE="$WRAPPED_FILE"
fi

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
"$ENGINE" -interaction=nonstopmode -jobname="$BASE" -output-directory="$BUILD_DIR" "$COMPILE_FILE"
pdftocairo -png -r 600 -singlefile "$PDF_OUT" "${BUILD_DIR}/${BASE}"
# The PDF/PNG now exist and are valid. The remaining checkers are report-only
# unless FIGURE_AGENT_STRICT=1. In report-only mode, a best-effort checker that
# exits non-zero (e.g. a poppler decode hiccup on a custom-font PDF) must not
# abort the build or trip the ERR trap that deletes the good output. Drop the
# trap and disable -e for the report-only block; strict mode keeps the hard gate.
if [[ ${#STRICT_ARGS[@]} -eq 0 ]]; then
  trap - ERR
  set +e
fi
STRICT_CHECK_FAILURE=0
run_report_check() {
  local status=0
  "$@" || status=$?
  if [[ ${#STRICT_ARGS[@]} -ne 0 && $status -ne 0 ]]; then
    STRICT_CHECK_FAILURE=1
  fi
  return 0
}
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_collisions.py" ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_visual_clash.py" \
  ${VISUAL_CLASH_ARGS[@]+"${VISUAL_CLASH_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/visual_clash.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_text_boundary_clash.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/text_boundary_clash.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_label_path_proximity.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/label_path_proximity.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_undeclared_geometry.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --tex "$FILE" \
  --json-output "${BUILD_DIR}/undeclared_geometry.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_label_hyphenation.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/label_hyphenation.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/semantic_assertions.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/semantic_assertions.json" \
  "$PDF_OUT"
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/vector_clearance.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --tex "$FILE" \
  --json-output "${BUILD_DIR}/vector_clearance.json" \
  "$PDF_OUT"
# Directional-physics assertions read from the .tex (a reversed force/bend arrow is
# a defect no render detector catches). STRICT-gated like the other clash checkers.
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_tex_assertions.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/tex_assertions.json" \
  "$FILE"
# Physics-intent grounding meta-check (advisory: which figures still need assertions).
# Always report-only — it surfaces a TODO, not a defect, so it never fails a build.
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_physics_grounding.py" \
  --json-output "${BUILD_DIR}/physics_grounding.json" \
  "$PWD"
if [[ -f "coordinate_hints.yaml" ]]; then
  run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_layout_drift.py" \
    ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
    .
fi
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/perception_pack.py" "$BASE"
ARTIFACT_STATUS=0
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/visual_finding_artifacts.py" . \
  --artifact-base "$BASE" || ARTIFACT_STATUS=$?
if [[ $ARTIFACT_STATUS -ne 0 ]]; then
  echo "ERROR: visual finding artifact generation failed" >&2
  trap - ERR
  exit "$ARTIFACT_STATUS"
fi
# Injection receipt (spec §4 Phase 1a): surface the injected use_as_constraint
# conventions with their source quotes so the author sees them on every figure.
# Report-only; best-effort — must never fail the build (no FIGURE_AGENT_WORKSPACE
# in some invocations means the fixture is unresolvable, which is fine to skip).
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/convention_receipt.py" "$BASE" --write >/dev/null || true
trap - ERR

if [[ $STRICT_CHECK_FAILURE -ne 0 ]]; then
  echo "ERROR: strict detector gate failed after review evidence generation" >&2
  exit 1
fi

echo "Generated: ${BUILD_DIR}/${BASE}.pdf, ${BUILD_DIR}/${BASE}.png (engine: $ENGINE)"
