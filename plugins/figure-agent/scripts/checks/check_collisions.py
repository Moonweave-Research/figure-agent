#!/usr/bin/env python3
"""
check_collisions.py — PDF 텍스트 레이블 충돌 감지기
Usage: python3 scripts/check_collisions.py <file.pdf> [--iou-thresh 0.05]
Output: WARN lines for overlapping labels. Default is report-only exit 0;
--strict exits 1 when any collision is found.
"""

import argparse
import hashlib
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path


def extract_word_bboxes(pdf_path: Path) -> list[dict]:
    """pdftotext -bbox로 렌더된 텍스트 bbox 추출."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    result = subprocess.run(
        ["pdftotext", "-bbox", str(pdf_path), str(tmp_path)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {result.stderr}")

    html_text = tmp_path.read_text(encoding="utf-8", errors="replace")
    tmp_path.unlink()

    # pdftotext HTML can contain glyph bytes that are not strict XML.
    word_pattern = re.compile(r"<word\b([^>]*)>(.*?)</word>", re.DOTALL)
    attr_pattern = re.compile(r"\b(xMin|yMin|xMax|yMax)=\"([^\"]+)\"")
    words = []
    for match in word_pattern.finditer(html_text):
        attrs = dict(attr_pattern.findall(match.group(1)))
        if not {"xMin", "yMin", "xMax", "yMax"}.issubset(attrs):
            continue
        text = re.sub(r"<[^>]+>", "", match.group(2))
        text = html.unescape(text).replace("\x00", "").strip()
        if not text:
            continue
        words.append(
            {
                "text": text,
                "xmin": float(attrs["xMin"]),
                "ymin": float(attrs["yMin"]),
                "xmax": float(attrs["xMax"]),
                "ymax": float(attrs["yMax"]),
            }
        )
    return words


def iou(a: dict, b: dict) -> float:
    """두 bbox의 Intersection over Union."""
    ix1 = max(a["xmin"], b["xmin"])
    iy1 = max(a["ymin"], b["ymin"])
    ix2 = min(a["xmax"], b["xmax"])
    iy2 = min(a["ymax"], b["ymax"])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (a["xmax"] - a["xmin"]) * (a["ymax"] - a["ymin"])
    area_b = (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def find_collisions(words: list[dict], iou_thresh: float) -> list[tuple]:
    """IoU > iou_thresh인 쌍 반환."""
    collisions = []
    for i, a in enumerate(words):
        for b in words[i + 1 :]:
            score = iou(a, b)
            if score > iou_thresh:
                collisions.append((a, b, score))
    return collisions


DEFAULT_LINE_VERTICAL_OVERLAP_PT = 0.5
DEFAULT_LINE_HORIZONTAL_OVERLAP_PT = 2.0


def group_text_runs(words: list[dict]) -> list[dict]:
    """Group words into visual text runs (one label / one line of a label).

    Word-pair IoU cannot see a two-line crowding failure: when two long runs
    overlap by a thin horizontal band, the intersection is tiny next to the
    union of two wide word boxes, so IoU stays under any usable threshold even
    though a reader sees the descenders of one line touching the next.  Runs
    are the unit that actually collides, so they are reconstructed here.
    """
    ordered = sorted(
        words, key=lambda w: ((w["ymin"] + w["ymax"]) / 2.0, w["xmin"], w["text"])
    )
    runs: list[dict] = []
    for word in ordered:
        height = max(word["ymax"] - word["ymin"], 1e-6)
        center = (word["ymin"] + word["ymax"]) / 2.0
        placed = False
        for run in runs:
            run_height = max(run["ymax"] - run["ymin"], 1e-6)
            reference = min(height, run_height)
            # Merge on band overlap rather than baseline equality: a math
            # sub/superscript sits off the baseline but still shares most of
            # its neighbour's ink band, and splitting it off would report the
            # script as colliding with its own base glyph.
            shared = min(word["ymax"], run["ymax"]) - max(word["ymin"], run["ymin"])
            if shared < 0.35 * reference:
                continue
            # Horizontal membership, not left-to-right adjacency: a subscript
            # can sit between two glyphs the run already owns, so the test is
            # whether the word lies inside the run's span or within one word
            # gap of either end.
            reach = 1.5 * max(height, run_height)
            adjacent = (
                run["xmax"] <= word["xmin"] <= run["xmax"] + reach
                or run["xmin"] - reach <= word["xmax"] <= run["xmin"]
            )
            # A word already inside the run's span joins it: that is the math
            # sub/superscript case, where the script sits between glyphs the
            # run already owns and must not be reported against its own base.
            inside = (
                word["xmin"] >= run["xmin"] - 0.3 * reach
                and word["xmax"] <= run["xmax"] + 0.3 * reach
            )
            if not (adjacent or inside):
                continue
            run["words"].append(word)
            run["xmin"] = min(run["xmin"], word["xmin"])
            run["xmax"] = max(run["xmax"], word["xmax"])
            run["ymin"] = min(run["ymin"], word["ymin"])
            run["ymax"] = max(run["ymax"], word["ymax"])
            run["center"] = (run["ymin"] + run["ymax"]) / 2.0
            placed = True
            break
        if not placed:
            runs.append(
                {
                    "words": [word],
                    "xmin": word["xmin"],
                    "xmax": word["xmax"],
                    "ymin": word["ymin"],
                    "ymax": word["ymax"],
                    "center": center,
                }
            )
    for run in runs:
        run["text"] = " ".join(w["text"] for w in sorted(run["words"], key=lambda w: w["xmin"]))
    return runs


def find_line_overlaps(
    words: list[dict],
    *,
    min_vertical_overlap_pt: float = DEFAULT_LINE_VERTICAL_OVERLAP_PT,
    min_horizontal_overlap_pt: float = DEFAULT_LINE_HORIZONTAL_OVERLAP_PT,
) -> list[tuple]:
    """Return run pairs whose ink bands overlap in both axes."""
    runs = group_text_runs(words)
    overlaps = []
    for i, a in enumerate(runs):
        for b in runs[i + 1 :]:
            vertical = min(a["ymax"], b["ymax"]) - max(a["ymin"], b["ymin"])
            horizontal = min(a["xmax"], b["xmax"]) - max(a["xmin"], b["xmin"])
            if vertical < min_vertical_overlap_pt:
                continue
            if horizontal < min_horizontal_overlap_pt:
                continue
            overlaps.append((a, b, vertical, horizontal))
    return sorted(overlaps, key=lambda item: (-item[2], -item[3], item[0]["text"]))


def _run_payload(run: dict) -> dict:
    return {
        "text": run["text"],
        "bbox_pdf": [run["xmin"], run["ymin"], run["xmax"], run["ymax"]],
    }


def _bbox_payload(word: dict) -> dict:
    return {
        "text": word["text"],
        "bbox_pdf": [word["xmin"], word["ymin"], word["xmax"], word["ymax"]],
    }


def collision_payload(
    pdf_path: Path,
    words: list[dict],
    collisions: list[tuple],
    iou_thresh: float,
    *,
    fixture: str | None = None,
    render_image: Path | None = None,
    line_overlaps: list[tuple] | None = None,
) -> dict:
    ordered = sorted(
        collisions,
        key=lambda item: (
            -item[2],
            item[0]["text"],
            item[1]["text"],
            item[0]["xmin"],
            item[0]["ymin"],
        ),
    )
    try:
        examples_index = pdf_path.parts.index("examples")
        fixture_dir = Path(*pdf_path.parts[: examples_index + 2])
    except (ValueError, IndexError):
        fixture_dir = pdf_path.parent.parent
    payload = {
        "schema": "figure-agent.text-collisions.v1",
        "fixture": fixture or fixture_dir.name,
        "render_pdf": str(pdf_path.relative_to(fixture_dir)),
        "render_pdf_sha256": (
            "sha256:" + hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        ),
        "iou_threshold": iou_thresh,
        "word_count": len(words),
        "collisions": [
            {
                "id": f"TC{index:03d}",
                "texts": [a["text"], b["text"]],
                "iou": round(score, 6),
                "a": _bbox_payload(a),
                "b": _bbox_payload(b),
                "source_mapping": None,
            }
            for index, (a, b, score) in enumerate(ordered, start=1)
        ],
        "total": len(ordered),
        "line_overlaps": [
            {
                "id": f"TL{index:03d}",
                "texts": [a["text"], b["text"]],
                "vertical_overlap_pt": round(vertical, 6),
                "horizontal_overlap_pt": round(horizontal, 6),
                "a": _run_payload(a),
                "b": _run_payload(b),
            }
            for index, (a, b, vertical, horizontal) in enumerate(
                line_overlaps or [], start=1
            )
        ],
        "line_overlap_total": len(line_overlaps or []),
    }
    if render_image is not None:
        payload["render_path"] = str(render_image.relative_to(fixture_dir))
        payload["render_sha256"] = (
            "sha256:" + hashlib.sha256(render_image.read_bytes()).hexdigest()
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="PDF 텍스트 레이블 충돌 감지기")
    parser.add_argument("pdf", type=Path, help="컴파일된 PDF 경로")
    parser.add_argument(
        "--iou-thresh",
        type=float,
        default=0.05,
        help="충돌 판정 IoU 임계값 (기본 0.05)",
    )
    parser.add_argument(
        "--strict-line-overlap",
        action="store_true",
        default=False,
        help=(
            "let text-line band overlaps fail the run. Off by default: the "
            "finding is always reported, but only a fixture that declares "
            "text_line_overlap_gate: strict is gated on it."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any collision is found (default: report-only, exit 0)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="구조화된 충돌 보고서를 기록할 JSON 경로",
    )
    parser.add_argument(
        "--fixture",
        help="compile.sh가 cwd를 변경한 경우 보존할 fixture 이름",
    )
    parser.add_argument(
        "--render-image",
        type=Path,
        help="PNG render whose bytes produced this collision report",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")
    if args.fixture and len(Path(args.fixture).parts) != 1:
        parser.error("fixture must be one safe path component")
    if args.render_image is not None and not args.render_image.is_file():
        raise FileNotFoundError(f"render image not found: {args.render_image}")

    words = extract_word_bboxes(args.pdf)
    collisions = find_collisions(words, args.iou_thresh)
    line_overlaps = find_line_overlaps(words)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(
                collision_payload(
                    args.pdf,
                    words,
                    collisions,
                    args.iou_thresh,
                    fixture=args.fixture,
                    render_image=args.render_image,
                    line_overlaps=line_overlaps,
                ),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    if not collisions and not line_overlaps:
        print(f"OK: no collisions found in {args.pdf.name} ({len(words)} words)")
        return 0

    for a, b, score in sorted(collisions, key=lambda x: -x[2]):
        print(
            f"WARN collision IoU={score:.3f}: "
            f'"{a["text"]}" [{a["xmin"]:.1f},{a["ymin"]:.1f}] '
            f'× "{b["text"]}" [{b["xmin"]:.1f},{b["ymin"]:.1f}]'
        )
    for a, b, vertical, horizontal in line_overlaps:
        print(
            f"WARN line overlap v={vertical:.2f}pt h={horizontal:.2f}pt: "
            f'"{a["text"]}" × "{b["text"]}"'
        )
    if collisions:
        print(f"\n{len(collisions)} collision(s) in {args.pdf.name}")
    if line_overlaps:
        gated = args.strict and args.strict_line_overlap
        state = "blocking" if gated else "report-only"
        print(
            f"{len(line_overlaps)} text-line overlap(s) in {args.pdf.name} "
            f"({state})"
        )
    if not args.strict:
        return 0
    if collisions:
        return 1
    return 1 if (line_overlaps and args.strict_line_overlap) else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
