#!/usr/bin/env bash
# export_svg.sh - semantic SVG source -> sibling PDF + 600 DPI PNG
# Usage: scripts/export_svg.sh <path/to/file.svg>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$WORKFLOW_DIR"

FIG_NAME=""
FIG_NAME_SEEN=0
NO_REF_REASON=""
NO_REF_SEEN=0
declare -a POSITIONAL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fig-name)
      FIG_NAME_SEEN=1
      FIG_NAME="${2:?--fig-name requires value}"
      shift 2
      ;;
    --fig-name=*)
      FIG_NAME_SEEN=1
      FIG_NAME="${1#--fig-name=}"
      shift
      ;;
    --no-ref=*)
      NO_REF_SEEN=1
      NO_REF_REASON="${1#--no-ref=}"
      shift
      ;;
    --no-ref)
      echo "ERROR: --no-ref requires =\"<reason>\" form" >&2
      exit 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

if [[ $# -lt 1 ]]; then
  echo "Usage: $(basename "$0") [--fig-name <name>] [--no-ref=\"<reason>\"] <file.svg>" >&2
  exit 1
fi

SVG_INPUT="$1"

if [[ "$FIG_NAME_SEEN" == "1" ]]; then
  if [[ -z "$FIG_NAME" ]]; then
    echo "ERROR: fig_name must not be empty" >&2
    exit 1
  fi
  if ! [[ "$FIG_NAME" =~ ^((fig|S|SC|TOC)[0-9]+([a-z]?)(_[a-z][a-z0-9_]*)?|_[A-Za-z0-9_]+)$ ]]; then
    echo "ERROR: invalid fig_name: $FIG_NAME" >&2
    exit 1
  fi
fi

if [[ -z "$FIG_NAME" ]]; then
  FIG_NAME="$(python3 - "$REPO_ROOT" "$SVG_INPUT" <<'PY'
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1]).resolve()
svg_path = pathlib.Path(sys.argv[2]).resolve()
references = repo_root / "references"
try:
    rel = svg_path.relative_to(references)
except ValueError:
    print("")
else:
    print(rel.parts[0] if len(rel.parts) >= 2 else "")
PY
)"
fi

GATE_ENABLED="${COMPILE_GATE_GAMMA:-1}"

if [[ "$GATE_ENABLED" == "1" && -n "$FIG_NAME" ]]; then
  if [[ "$NO_REF_SEEN" == "1" ]]; then
    if [[ -z "${NO_REF_REASON// }" ]]; then
      echo "ERROR: --no-ref reason must not be empty" >&2
      exit 1
    fi
    BYPASS_DIR="${REPO_ROOT}/references/${FIG_NAME}"
    mkdir -p "$BYPASS_DIR"
    BYPASS_LOG="${BYPASS_DIR}/_bypass_log.md"
    TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "${TS}: ${NO_REF_REASON}" >> "$BYPASS_LOG"
    echo "Gate γ bypassed: ${NO_REF_REASON}" >&2
  else
    if ! command -v uv >/dev/null 2>&1; then
      echo "Error: uv not found. Install uv or run with COMPILE_GATE_GAMMA=0." >&2
      exit 127
    fi
    MANIFEST="${REPO_ROOT}/references/${FIG_NAME}/manifest.md"
    if ! uv run --project "$REPO_ROOT" python3 "${REPO_ROOT}/scripts/_check_manifest.py" "$MANIFEST"; then
      echo "Gate γ FAIL: manifest invalid for fig_name=${FIG_NAME}" >&2
      exit 1
    fi

    if uv run --project "$REPO_ROOT" python3 -c "
import yaml, sys, pathlib
m = pathlib.Path(sys.argv[1]).read_text()
parts = m.split('---', 2)
d = yaml.safe_load(parts[1]) or {}
log = d.get('decision_log') or []
sys.exit(0 if log else 1)
" "$MANIFEST"; then
      :
    else
      echo "WARN: decision_log empty in $MANIFEST" >&2
    fi
  fi
elif [[ "$NO_REF_SEEN" == "1" ]]; then
  if [[ -z "$FIG_NAME" ]]; then
    echo "ERROR: --no-ref requires fig_name via --fig-name (or auto-detect path) to log bypass" >&2
    exit 1
  fi
fi

if [[ ! -f "$SVG_INPUT" ]]; then
  echo "Error: file not found: $SVG_INPUT" >&2
  exit 1
fi

case "$SVG_INPUT" in
  *.svg) ;;
  *)
    echo "Error: expected .svg input: $SVG_INPUT" >&2
    exit 1
    ;;
esac

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "Error: rsvg-convert not found. Install via: brew install librsvg" >&2
  exit 127
fi

OUT_DIR="$(dirname "$SVG_INPUT")"
FILE="$(basename "$SVG_INPUT")"
BASE="${FILE%.svg}"

rsvg-convert -f pdf -o "${OUT_DIR}/${BASE}.pdf" "$SVG_INPUT"
rsvg-convert -d 600 -p 600 -f png -o "${OUT_DIR}/${BASE}.png" "$SVG_INPUT"

echo "Generated: ${BASE}.pdf, ${BASE}.png (source: SVG)"
