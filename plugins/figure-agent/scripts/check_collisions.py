#!/usr/bin/env python3
"""
check_collisions.py — PDF 텍스트 레이블 충돌 감지기
Usage: python3 scripts/check_collisions.py <file.pdf> [--iou-thresh 0.05]
Output: WARN lines for overlapping labels. Exit 0 always (report-only, no auto-fix).
"""

import argparse
import html
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
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {result.stderr}")

    html_text = tmp_path.read_text(encoding="utf-8")
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
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any collision is found (default: report-only, exit 0)",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    words = extract_word_bboxes(args.pdf)
    collisions = find_collisions(words, args.iou_thresh)

    if not collisions:
        print(f"OK: no collisions found in {args.pdf.name} ({len(words)} words)")
        return 0

    for a, b, score in sorted(collisions, key=lambda x: -x[2]):
        print(
            f"WARN collision IoU={score:.3f}: "
            f'"{a["text"]}" [{a["xmin"]:.1f},{a["ymin"]:.1f}] '
            f'× "{b["text"]}" [{b["xmin"]:.1f},{b["ymin"]:.1f}]'
        )
    print(f"\n{len(collisions)} collision(s) in {args.pdf.name}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
