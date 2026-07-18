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

# A copied execution-repair-v* source is immutable review evidence. It keeps
# the fixture's generic schematic profile, but a later live coverage contract
# cannot make its strict replay fail.
HISTORICAL_REPAIR_REPLAY=0
if [[ "$(basename "$(dirname "$TEX_INPUT")")" =~ ^execution-repair-v[0-9]+$ ]]; then
  HISTORICAL_REPAIR_REPLAY=1
fi
LIVE_REPAIR_VERIFY="${FIGURE_AGENT_LIVE_REPAIR_VERIFY:-0}"
LIVE_ASSERTION_TARGET=0
if [[ $HISTORICAL_REPAIR_REPLAY -eq 0 || "$LIVE_REPAIR_VERIFY" == "1" ]]; then
  LIVE_ASSERTION_TARGET=1
fi

FIXTURE_NAME=""
FIXTURE_ROOT=""
FIXTURE_TAIL="${TEX_INPUT#*examples/}"
if [[ -n "${FIGURE_AGENT_FIXTURE_NAME:-}" ]]; then
  FIXTURE_NAME="$FIGURE_AGENT_FIXTURE_NAME"
elif [[ "$FIXTURE_TAIL" != "$TEX_INPUT" ]]; then
  FIXTURE_NAME="${FIXTURE_TAIL%%/*}"
fi
COLLISION_FIXTURE_ARGS=()
UNDECLARED_GEOMETRY_SPEC_ARGS=()
TEX_ASSERTION_SPEC_ARGS=()
STATE_FIELD_GEOMETRY_SPEC_ARGS=()
LAYOUT_CONTRACT=""
if [[ -n "$FIXTURE_NAME" ]]; then
  COLLISION_FIXTURE_ARGS=(--fixture "$FIXTURE_NAME")
  FIXTURE_WORKSPACE="${FIGURE_AGENT_WORKSPACE:-$WORKFLOW_DIR}"
  FIGURE_SPEC="${FIXTURE_WORKSPACE}/examples/${FIXTURE_NAME}/spec.yaml"
  FIXTURE_ROOT="${FIXTURE_WORKSPACE}/examples/${FIXTURE_NAME}"
  LAYOUT_CONTRACT="${FIXTURE_ROOT}/layout_lanes.yaml"
  TEX_INPUT_DIR="$(cd "$(dirname "$TEX_INPUT")" && pwd)"
  TEX_INPUT_ABS="${TEX_INPUT_DIR}/$(basename "$TEX_INPUT")"
  # An explicitly named fixture is sufficient for a live source outside the
  # examples tree, but never turns immutable execution-repair evidence into a
  # current-source assertion target.
  if [[ $LIVE_ASSERTION_TARGET -eq 1 && ( "$TEX_INPUT_ABS" == "$FIXTURE_ROOT/"* || -n "${FIGURE_AGENT_FIXTURE_NAME:-}" ) && -f "$FIGURE_SPEC" ]]; then
    UNDECLARED_GEOMETRY_SPEC_ARGS=(--spec "$FIGURE_SPEC")
    TEX_ASSERTION_SPEC_ARGS=(--spec "$FIGURE_SPEC")
    STATE_FIELD_GEOMETRY_SPEC_ARGS=(--spec "$FIGURE_SPEC")
  fi
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
VISUAL_CLASH_ARGS=(--ignore-known-fp)
if [[ "${FIGURE_AGENT_STRICT:-}" == "1" ]]; then
  STRICT_ARGS=(--strict)
  VISUAL_CLASH_ARGS=(--strict --ignore-known-fp)
  echo 'Strict mode: collision/clash findings will fail the compile.' >&2
fi
UNDECLARED_GEOMETRY_STRICT_ARGS=("${STRICT_ARGS[@]}")
if [[ $LIVE_ASSERTION_TARGET -eq 0 ]]; then
  UNDECLARED_GEOMETRY_STRICT_ARGS=()
  echo "INFO: historical repair replay reports, but does not strict-gate, live coverage requirements" >&2
fi

ENGINE="${LATEX_ENGINE:-lualatex}"

cd "$(dirname "$TEX_INPUT")"
FILE="$(basename "$TEX_INPUT")"
BASE="${FILE%.tex}"
BUILD_DIR="build"
WRAPPED_FILE="${BUILD_DIR}/.${BASE}.figure-agent-wrapper.tex"
COMPILE_FILE="$FILE"

mkdir -p "$BUILD_DIR"

# All detector reports and review artifacts below are fixture-scoped rather
# than BASE-scoped. Serialize compiles in the same fixture so two variants
# cannot overwrite visual_clash.json or visual_findings while either run is
# still consuming them. File descriptor 9 keeps the advisory lock for the
# lifetime of this shell and releases it automatically on exit.
COMPILE_LOCK="${BUILD_DIR}/.figure-agent-compile.lock"
exec 9>"$COMPILE_LOCK"
if command -v lockf >/dev/null 2>&1; then
  if ! lockf -s -t 0 9; then
    echo "ERROR: another figure-agent compile is active for this fixture" >&2
    exit 75
  fi
elif command -v flock >/dev/null 2>&1; then
  if ! flock -n 9; then
    echo "ERROR: another figure-agent compile is active for this fixture" >&2
    exit 75
  fi
else
  echo "ERROR: figure-agent compile requires lockf or flock" >&2
  exit 69
fi

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
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_collisions.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  ${COLLISION_FIXTURE_ARGS[@]+"${COLLISION_FIXTURE_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/collisions.json" \
  --render-image "$PNG_OUT" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_visual_clash.py" \
  ${VISUAL_CLASH_ARGS[@]+"${VISUAL_CLASH_ARGS[@]}"} \
  ${COLLISION_FIXTURE_ARGS[@]+"${COLLISION_FIXTURE_ARGS[@]}"} \
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
  ${UNDECLARED_GEOMETRY_STRICT_ARGS[@]+"${UNDECLARED_GEOMETRY_STRICT_ARGS[@]}"} \
  ${UNDECLARED_GEOMETRY_SPEC_ARGS[@]+"${UNDECLARED_GEOMETRY_SPEC_ARGS[@]}"} \
  --tex "$FILE" \
  --json-output "${BUILD_DIR}/undeclared_geometry.json" \
  "$PDF_OUT"
if [[ ${#STATE_FIELD_GEOMETRY_SPEC_ARGS[@]} -ne 0 ]]; then
  run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_state_field_geometry.py" \
    ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
    ${STATE_FIELD_GEOMETRY_SPEC_ARGS[@]+"${STATE_FIELD_GEOMETRY_SPEC_ARGS[@]}"} \
    --tex "$FILE" \
    --json-output "${BUILD_DIR}/state_field_geometry.json"
fi
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_label_hyphenation.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/label_hyphenation.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/semantic_assertions.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/semantic_assertions.json" \
  "$PDF_OUT"
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/vector_clearance.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  --tex "$FILE" \
  --json-output "${BUILD_DIR}/vector_clearance.json" \
  "$PDF_OUT"
# Directional-physics assertions read from the .tex (a reversed force/bend arrow is
# a defect no render detector catches). STRICT-gated like the other clash checkers.
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_tex_assertions.py" \
  ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
  ${TEX_ASSERTION_SPEC_ARGS[@]+"${TEX_ASSERTION_SPEC_ARGS[@]}"} \
  --json-output "${BUILD_DIR}/tex_assertions.json" \
  "$FILE"
# Physics-intent grounding meta-check (advisory: which figures still need assertions).
# Always report-only — it surfaces a TODO, not a defect, so it never fails a build.
# A prospective candidate under a fixture's review tree is deliberately a
# separate source artifact. Its physics grounding must still resolve against
# the parent fixture's briefing/spec rather than report a false missing-briefing
# warning for the candidate-only directory.
PHYSICS_GROUNDING_DIR="$PWD"
if [[ -n "$FIXTURE_ROOT" && "$TEX_INPUT_ABS" == "$FIXTURE_ROOT/review/"* ]]; then
  PHYSICS_GROUNDING_DIR="$FIXTURE_ROOT"
fi
run_report_check "${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/checks/check_physics_grounding.py" \
  --json-output "${BUILD_DIR}/physics_grounding.json" "$PHYSICS_GROUNDING_DIR"
if [[ -n "$LAYOUT_CONTRACT" && -f "$LAYOUT_CONTRACT" ]]; then
  run_report_check "${UV_RUN[@]}" python3 \
    "$WORKFLOW_DIR/scripts/checks/check_layout_drift.py" \
    ${STRICT_ARGS[@]+"${STRICT_ARGS[@]}"} \
    --pdf "$PWD/$PDF_OUT" \
    --layout-contract "$LAYOUT_CONTRACT" \
    --json-output "${BUILD_DIR}/layout_lanes.json"
elif [[ -f "coordinate_hints.yaml" ]]; then
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
STRICT_STATUS_ARGS=()
if [[ ${#STRICT_ARGS[@]} -ne 0 ]]; then
  STRICT_STATUS_ARGS+=(--strict-requested)
fi
if [[ $STRICT_CHECK_FAILURE -ne 0 ]]; then
  STRICT_STATUS_ARGS+=(--detector-failed)
fi
"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/strict_status.py" \
  --json-output "${BUILD_DIR}/strict_status.json" \
  "${STRICT_STATUS_ARGS[@]}"
trap - ERR

if [[ $STRICT_CHECK_FAILURE -ne 0 ]]; then
  echo "ERROR: strict detector gate failed after review evidence generation" >&2
  exit 1
fi

echo "Generated: ${BUILD_DIR}/${BASE}.pdf, ${BUILD_DIR}/${BASE}.png (engine: $ENGINE)"
