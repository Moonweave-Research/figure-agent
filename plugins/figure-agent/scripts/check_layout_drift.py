#!/usr/bin/env python3
"""check_layout_drift.py — anchor-driven layout drift gate (Layer 6).

Compares the compiled PDF's text positions against the reference PNG's OCR
positions (Layer 2.5 coordinate_hints.yaml), using the human-curated
``golden_contract.required_labels`` from spec.yaml as anchors.

Usage:
    python3 scripts/check_layout_drift.py <example_dir> [--strict]

For each required label:
  * find the phrase in the OCR text_labels (reference) → ref normalized center
  * find the phrase in pdftotext words (build PDF) → pdf normalized center
  * drift = Euclidean distance in [0,1]^2 normalized canvas
  * matched_ok / drifted / uncovered_{ref,build,both}

Skips silently with exit 0 when:
  * spec.yaml has no golden_contract.required_labels (ordinary fixture), or
  * coordinate_hints.yaml is missing (Layer 2.5 not run).

--strict makes drifted labels exit 1 (uncovered remains exit 0 — a different
gate's job).
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402
from inputs import parse_spec  # noqa: E402

DEFAULT_DRIFT_THRESHOLD = 0.05  # fraction of normalized canvas

LabelSpec = str | list[str]


@dataclass(frozen=True)
class DriftResult:
    label: str
    matched_form: str | None
    status: str  # matched_ok | drifted | uncovered_ref | uncovered_build | uncovered_both
    ref_center: tuple[float, float] | None
    pdf_center: tuple[float, float] | None
    drift: float | None


def _normalize_token(text: str) -> str:
    """Lowercase + strip surrounding punctuation. Keep inner punct (e.g. trap-depth)."""
    return text.strip(" \t\n\r.,;:()[]{}'\"!?").lower()


def _label_forms(label: LabelSpec) -> list[str]:
    if isinstance(label, list):
        return [str(form) for form in label if str(form).strip()]
    return [str(label)]


def _phrase_tokens(phrase: str) -> list[str]:
    return [_normalize_token(t) for t in phrase.split() if _normalize_token(t)]


# Spatial matching tolerance. The step distance between two phrase tokens is
# accepted when it falls within `SPATIAL_TOL × max(any label dimension)`. A
# single center-distance metric handles both layouts that occur in practice:
# horizontal flow (same row, separated by a small gap) and vertical wrap
# (line break inside a multi-word phrase, where dy ≈ 1–2 × label height).
# OCR output ordering is not phrase-aware — noise tokens get interleaved —
# so geometry beats list contiguity.
SPATIAL_TOL = 2.5


def _word_center(word: dict) -> tuple[float, float]:
    return (
        0.5 * (word["xmin"] + word["xmax"]),
        0.5 * (word["ymin"] + word["ymax"]),
    )


def _word_max_dim(word: dict) -> float:
    return max(
        word["xmax"] - word["xmin"],
        word["ymax"] - word["ymin"],
        1.0,
    )


def _spatial_neighbor(
    prev: dict,
    candidates: list[dict],
    *,
    tol: float = SPATIAL_TOL,
) -> dict | None:
    """Pick the closest candidate within ``tol × max label dimension`` of prev.

    Returns the candidate with smallest center-to-center distance, or None
    when no candidate is close enough. Using max-dim instead of separate
    row/col bounds collapses horizontal-flow and vertical-wrap into one
    metric — both reflect "tokens that visually belong to one phrase".
    """
    prev_cx, prev_cy = _word_center(prev)
    best: dict | None = None
    best_dist: float | None = None
    for cand in candidates:
        cand_cx, cand_cy = _word_center(cand)
        dist = math.dist((prev_cx, prev_cy), (cand_cx, cand_cy))
        budget = tol * max(_word_max_dim(prev), _word_max_dim(cand))
        if dist > budget:
            continue
        if best_dist is None or dist < best_dist:
            best = cand
            best_dist = dist
    return best


def _find_phrase_in_words(
    phrase_tokens: list[str], words: list[dict]
) -> tuple[float, float, float, float] | None:
    """Find the spatially closest chain of words matching ``phrase_tokens``.

    For each candidate start, walks the phrase token-by-token, picking the
    nearest same-row neighbor for each next token. The chain with the
    smallest total step distance wins. Returns the union bbox, or None if
    any token has no spatially compatible neighbor.

    Single-token phrases fall back to the first match (no spatial constraint
    available with one word).
    """
    if not phrase_tokens or not words:
        return None
    norm = [_normalize_token(w["text"]) for w in words]
    starts = [words[i] for i, tok in enumerate(norm) if tok == phrase_tokens[0]]
    if not starts:
        return None

    if len(phrase_tokens) == 1:
        chain = [starts[0]]
    else:
        best_chain: list[dict] | None = None
        best_score: float | None = None
        for start in starts:
            chain = [start]
            ok = True
            for next_tok in phrase_tokens[1:]:
                used_ids = {id(w) for w in chain}
                pool = [
                    words[i]
                    for i, tok in enumerate(norm)
                    if tok == next_tok and id(words[i]) not in used_ids
                ]
                if not pool:
                    ok = False
                    break
                picked = _spatial_neighbor(chain[-1], pool)
                if picked is None:
                    ok = False
                    break
                chain.append(picked)
            if not ok:
                continue
            score = sum(
                math.dist(_word_center(chain[i]), _word_center(chain[i + 1]))
                for i in range(len(chain) - 1)
            )
            if best_score is None or score < best_score:
                best_chain = chain
                best_score = score
        if best_chain is None:
            return None
        chain = best_chain

    xs0 = min(w["xmin"] for w in chain)
    ys0 = min(w["ymin"] for w in chain)
    xs1 = max(w["xmax"] for w in chain)
    ys1 = max(w["ymax"] for w in chain)
    return (xs0, ys0, xs1, ys1)


def _hints_to_word_list(hints: dict) -> list[dict]:
    """Convert coordinate_hints.text_labels to the same shape as pdf words."""
    out: list[dict] = []
    for entry in hints.get("text_labels", []) or []:
        bbox = entry.get("bbox")
        text = entry.get("text")
        if not bbox or not text or len(bbox) != 4:
            continue
        out.append(
            {
                "text": str(text),
                "xmin": float(bbox[0]),
                "ymin": float(bbox[1]),
                "xmax": float(bbox[2]),
                "ymax": float(bbox[3]),
            }
        )
    return out


def _center_norm(
    bbox: tuple[float, float, float, float], canvas: tuple[float, float]
) -> tuple[float, float]:
    cw, ch = canvas
    cx = 0.5 * (bbox[0] + bbox[2]) / cw if cw else 0.0
    cy = 0.5 * (bbox[1] + bbox[3]) / ch if ch else 0.0
    return (cx, cy)


def evaluate_drift(
    required_labels: list[LabelSpec],
    hints: dict,
    pdf_words: list[dict],
    pdf_page_size: tuple[float, float],
) -> list[DriftResult]:
    ref_words = _hints_to_word_list(hints)
    ref_size = hints.get("reference_image_size") or [0, 0]
    ref_canvas = (float(ref_size[0]), float(ref_size[1]))

    results: list[DriftResult] = []
    for label in required_labels:
        forms = _label_forms(label)
        ref_hit: tuple[str, tuple[float, float, float, float]] | None = None
        pdf_hit: tuple[str, tuple[float, float, float, float]] | None = None
        for form in forms:
            tokens = _phrase_tokens(form)
            if ref_hit is None:
                bbox = _find_phrase_in_words(tokens, ref_words)
                if bbox is not None:
                    ref_hit = (form, bbox)
            if pdf_hit is None:
                bbox = _find_phrase_in_words(tokens, pdf_words)
                if bbox is not None:
                    pdf_hit = (form, bbox)
            if ref_hit is not None and pdf_hit is not None and ref_hit[0] == pdf_hit[0]:
                break
        label_str = forms[0] if forms else str(label)
        if ref_hit is None and pdf_hit is None:
            results.append(DriftResult(label_str, None, "uncovered_both", None, None, None))
            continue
        if ref_hit is None:
            results.append(DriftResult(label_str, pdf_hit[0], "uncovered_ref", None, None, None))
            continue
        if pdf_hit is None:
            results.append(DriftResult(label_str, ref_hit[0], "uncovered_build", None, None, None))
            continue
        ref_center = _center_norm(ref_hit[1], ref_canvas)
        pdf_center = _center_norm(pdf_hit[1], pdf_page_size)
        drift = math.dist(ref_center, pdf_center)
        results.append(
            DriftResult(
                label_str,
                ref_hit[0] if ref_hit[0] == pdf_hit[0] else f"{ref_hit[0]} → {pdf_hit[0]}",
                "matched_ok",
                ref_center,
                pdf_center,
                drift,
            )
        )
    return results


def _aspect_line(ref_size: list[float], page_size: tuple[float, float]) -> str:
    if not ref_size or len(ref_size) < 2 or ref_size[1] == 0 or page_size[1] == 0:
        return "aspect: insufficient data"
    ref_a = ref_size[0] / ref_size[1]
    pdf_a = page_size[0] / page_size[1]
    delta = abs(ref_a - pdf_a) / max(ref_a, pdf_a)
    return f"aspect: ref={ref_a:.3f} pdf={pdf_a:.3f} mismatch={delta * 100:.1f}%"


def _resolve_pdf_path(example_dir: Path) -> Path | None:
    """Prefer build/ over exports/ (drift is a compile-stage gate)."""
    name = example_dir.name
    candidates = [
        example_dir / "build" / f"{name}.pdf",
        example_dir / "exports" / f"{name}.pdf",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_DRIFT_THRESHOLD,
        help="drift fraction (of normalized canvas) above which a label is flagged",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any matched label drifts beyond threshold",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="explicit PDF path; defaults to build/<name>.pdf then exports/<name>.pdf",
    )
    args = parser.parse_args()

    if not args.example_dir.is_dir():
        print(f"FAIL: example directory not found: {args.example_dir}", file=sys.stderr)
        return 1

    # Resolve so "." (compile.sh invocation) carries a real directory name for
    # build/<name>.pdf lookup.
    example_dir = args.example_dir.resolve()
    spec_path = example_dir / "spec.yaml"
    hints_path = example_dir / "coordinate_hints.yaml"

    if not spec_path.exists():
        print(f"SKIP: {example_dir.name} has no spec.yaml")
        return 0

    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    required = (spec.get("golden_contract") or {}).get("required_labels") or []
    if not required:
        print(f"SKIP: {example_dir.name} has no golden_contract.required_labels")
        return 0
    if not hints_path.exists():
        print(f"SKIP: {example_dir.name} has no coordinate_hints.yaml (run /fig_extract first)")
        return 0

    pdf_path = args.pdf if args.pdf is not None else _resolve_pdf_path(example_dir)
    if pdf_path is None or not pdf_path.exists():
        print(f"FAIL: no compiled PDF for {example_dir.name}", file=sys.stderr)
        return 1

    hints = yaml.safe_load(hints_path.read_text(encoding="utf-8")) or {}
    pdf_words, page_size = extract_pdf_words_and_page(pdf_path)

    results = evaluate_drift(required, hints, pdf_words, page_size)

    counts = {
        "matched_ok": 0,
        "drifted": 0,
        "uncovered_ref": 0,
        "uncovered_build": 0,
        "uncovered_both": 0,
    }
    drifted_results: list[DriftResult] = []
    for r in results:
        if r.status == "matched_ok" and r.drift is not None and r.drift > args.threshold:
            drifted_results.append(r)
            counts["drifted"] += 1
        else:
            counts[r.status] += 1

    print(f"layout drift report: {pdf_path.name} ({len(results)} required labels)")
    print(_aspect_line(hints.get("reference_image_size") or [], page_size))
    print(
        f"  matched_ok={counts['matched_ok']} drifted={counts['drifted']}"
        f" uncovered_ref={counts['uncovered_ref']}"
        f" uncovered_build={counts['uncovered_build']}"
        f" uncovered_both={counts['uncovered_both']}"
        f" (threshold={args.threshold:.3f})"
    )
    for r in results:
        if r.status == "matched_ok":
            assert r.drift is not None and r.ref_center is not None and r.pdf_center is not None
            tag = "DRIFT" if r.drift > args.threshold else "ok"
            print(
                f"  {tag:<5} {r.label!r}: drift={r.drift:.3f}"
                f" ref=({r.ref_center[0]:.3f},{r.ref_center[1]:.3f})"
                f" pdf=({r.pdf_center[0]:.3f},{r.pdf_center[1]:.3f})"
            )
        else:
            print(f"  {r.status:<15} {r.label!r}")

    if args.strict and drifted_results:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
