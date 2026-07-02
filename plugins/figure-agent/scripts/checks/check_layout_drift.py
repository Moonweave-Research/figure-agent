#!/usr/bin/env python3
"""Anchor-based layout drift check for fixtures with coordinate hints."""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402
from inputs import parse_spec  # noqa: E402

DEFAULT_DRIFT_THRESHOLD = 0.05

LabelSpec = str | list[str]


@dataclass(frozen=True)
class DriftResult:
    label: str
    matched_form: str | None
    status: str
    ref_center: tuple[float, float] | None
    pdf_center: tuple[float, float] | None
    drift: float | None


def _normalize_token(text: str) -> str:
    return text.strip(" \t\n\r.,;:()[]{}'\"!?").lower()


def _tokens(text: str) -> list[str]:
    return [token for token in (_normalize_token(part) for part in text.split()) if token]


def _label_forms(label: LabelSpec) -> list[str]:
    if isinstance(label, list):
        return [str(item) for item in label if str(item).strip()]
    return [str(label)]


def _center(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x0, y0, x1, y1 = bbox
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


def _union_bbox(words: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    bboxes = [_word_bbox(word) for word in words]
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def _word_bbox(word: dict[str, Any]) -> tuple[float, float, float, float]:
    if "bbox" in word and isinstance(word["bbox"], list | tuple) and len(word["bbox"]) == 4:
        return tuple(float(value) for value in word["bbox"])  # type: ignore[return-value]
    return (
        float(word["xmin"]),
        float(word["ymin"]),
        float(word["xmax"]),
        float(word["ymax"]),
    )


def _find_phrase_bbox(
    phrase: str,
    words: list[dict[str, Any]],
) -> tuple[float, float, float, float] | None:
    phrase_tokens = _tokens(phrase)
    if not phrase_tokens:
        return None
    normalized = [_normalize_token(str(word.get("text", ""))) for word in words]
    for index in range(0, len(words) - len(phrase_tokens) + 1):
        if normalized[index : index + len(phrase_tokens)] == phrase_tokens:
            return _union_bbox(words[index : index + len(phrase_tokens)])
    if len(phrase_tokens) == 1:
        token = phrase_tokens[0]
        for index, normalized_token in enumerate(normalized):
            if normalized_token == token:
                return _word_bbox(words[index])
    return None


def _required_labels(spec: dict[str, Any]) -> list[LabelSpec]:
    contract = spec.get("golden_contract")
    if not isinstance(contract, dict):
        return []
    labels = contract.get("required_labels")
    if not isinstance(labels, list):
        return []
    return [label for label in labels if isinstance(label, str | list)]


def evaluate_drift(
    required_labels: list[LabelSpec],
    coordinate_hints: dict[str, Any],
    pdf_words: list[dict[str, Any]],
    pdf_page_size: tuple[float, float],
) -> list[DriftResult]:
    reference_size = coordinate_hints.get("reference_image_size") or []
    if not isinstance(reference_size, list | tuple) or len(reference_size) != 2:
        return []
    ref_width, ref_height = float(reference_size[0]), float(reference_size[1])
    pdf_width, pdf_height = pdf_page_size
    if min(ref_width, ref_height, pdf_width, pdf_height) <= 0:
        return []

    ref_words = coordinate_hints.get("text_labels") or []
    if not isinstance(ref_words, list):
        ref_words = []

    results: list[DriftResult] = []
    for label in required_labels:
        best: DriftResult | None = None
        for ref_form in _label_forms(label):
            ref_bbox = _find_phrase_bbox(ref_form, ref_words)
            if ref_bbox is None:
                continue
            ref_center_px = _center(ref_bbox)
            ref_center = (ref_center_px[0] / ref_width, ref_center_px[1] / ref_height)
            for pdf_form in _label_forms(label):
                pdf_bbox = _find_phrase_bbox(pdf_form, pdf_words)
                if pdf_bbox is None:
                    continue
                pdf_center_pt = _center(pdf_bbox)
                pdf_center = (pdf_center_pt[0] / pdf_width, pdf_center_pt[1] / pdf_height)
                drift = math.dist(ref_center, pdf_center)
                matched_form = ref_form if ref_form == pdf_form else f"{ref_form} -> {pdf_form}"
                candidate = DriftResult(
                    label=str(label),
                    matched_form=matched_form,
                    status="matched",
                    ref_center=ref_center,
                    pdf_center=pdf_center,
                    drift=drift,
                )
                if best is None or drift < (best.drift or math.inf):
                    best = candidate
        if best is not None:
            results.append(best)
            continue

        forms = _label_forms(label)
        has_ref = any(_find_phrase_bbox(form, ref_words) is not None for form in forms)
        has_pdf = any(_find_phrase_bbox(form, pdf_words) is not None for form in forms)
        if has_ref:
            status = "uncovered_build"
        elif has_pdf:
            status = "uncovered_ref"
        else:
            status = "uncovered_both"
        results.append(
            DriftResult(
                label=str(label),
                matched_form=None,
                status=status,
                ref_center=None,
                pdf_center=None,
                drift=None,
            )
        )
    return results


def _resolve_fixture_dir(target: str) -> Path:
    path = Path(target)
    if target == ".":
        return Path.cwd()
    if path.is_absolute():
        return path
    if len(path.parts) == 1:
        return Path("examples") / path.parts[0]
    if len(path.parts) == 2 and path.parts[0] == "examples":
        return path
    raise ValueError("expected fixture name, examples/<fixture>, absolute fixture path, or .")


def _fixture_name(fixture_dir: Path) -> str:
    return fixture_dir.resolve().name


def run_check(
    fixture_dir: Path,
    *,
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
) -> tuple[int, list[str]]:
    name = _fixture_name(fixture_dir)
    spec_path = fixture_dir / "spec.yaml"
    hints_path = fixture_dir / "coordinate_hints.yaml"
    pdf_path = fixture_dir / "build" / f"{name}.pdf"
    if not spec_path.is_file():
        return 1, [f"ERROR missing spec.yaml: {spec_path}"]
    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    required_labels = _required_labels(spec)
    if not required_labels:
        return 0, [f"SKIP layout drift: no golden_contract.required_labels in {spec_path}"]
    if not hints_path.is_file():
        return 0, [f"SKIP layout drift: missing coordinate_hints.yaml in {fixture_dir}"]
    if not pdf_path.is_file():
        return 1, [f"ERROR missing build PDF: {pdf_path}"]

    hints = yaml.safe_load(hints_path.read_text(encoding="utf-8")) or {}
    if not isinstance(hints, dict):
        return 1, [f"ERROR invalid coordinate_hints.yaml: {hints_path}"]
    pdf_words, page_size = extract_pdf_words_and_page(pdf_path)
    results = evaluate_drift(required_labels, hints, pdf_words, page_size)

    lines: list[str] = []
    failures = 0
    for result in results:
        if result.drift is not None:
            if result.drift > threshold:
                failures += 1
                lines.append(
                    f"WARN layout drift {result.label}: {result.drift:.3f} > {threshold:.3f}"
                )
            else:
                lines.append(f"OK layout drift {result.label}: {result.drift:.3f}")
        elif result.status != "uncovered_ref":
            failures += 1
            lines.append(f"WARN layout drift {result.label}: {result.status}")
        else:
            lines.append(f"SKIP layout drift {result.label}: {result.status}")
    if not results:
        lines.append("SKIP layout drift: no comparable labels")
    return failures, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        help="fixture name, examples/<fixture>, absolute fixture path, or .",
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_DRIFT_THRESHOLD)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    try:
        failures, lines = run_check(_resolve_fixture_dir(args.fixture), threshold=args.threshold)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR layout drift: {exc}", file=sys.stderr)
        return 1
    for line in lines:
        print(line)
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
