#!/usr/bin/env python3
"""
check_visual_clash.py — render-based visual clash detector for TikZ PDFs.

Usage: python3 scripts/check_visual_clash.py <file.pdf> [--dpi 600]
Output: WARN lines for likely text-on-path/fill, near-miss, and clipping.
Default is report-only exit 0; --strict exits 1 when any unsuppressed clash
candidate remains.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class VisualIssue:
    kind: str
    text: str
    detail: str
    bbox: tuple[int, int, int, int]


KNOWN_FALSE_POSITIVES_PATH = Path(__file__).resolve().parents[2] / "_known_false_positives.yaml"


def extract_pdf_words_and_page(pdf_path: Path) -> tuple[list[dict], tuple[float, float]]:
    """Return pdftotext word bboxes and first-page size in PDF points."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    result = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "1", "-bbox", str(pdf_path), str(tmp_path)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed: {result.stderr}")

    html_text = tmp_path.read_text(encoding="utf-8", errors="replace")
    tmp_path.unlink()

    page_match = re.search(
        r"<page\b[^>]*\bwidth=\"([^\"]+)\"[^>]*\bheight=\"([^\"]+)\"",
        html_text,
    )
    if page_match is None:
        raise RuntimeError("pdftotext output has no page element")
    page_size = (float(page_match.group(1)), float(page_match.group(2)))

    words = []
    word_pattern = re.compile(r"<word\b([^>]*)>(.*?)</word>", re.DOTALL)
    attr_pattern = re.compile(r"\b(xMin|yMin|xMax|yMax)=\"([^\"]+)\"")
    for match in word_pattern.finditer(html_text):
        attrs = dict(attr_pattern.findall(match.group(1)))
        if not {"xMin", "yMin", "xMax", "yMax"}.issubset(attrs):
            continue
        text = re.sub(r"<[^>]+>", "", match.group(2))
        text = html_unescape(text).strip()
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
    return words, page_size


def html_unescape(text: str) -> str:
    """Decode HTML entities while tolerating invalid pdftotext characters."""
    return html.unescape(text).replace("\x00", "")


def render_pdf_first_page(pdf_path: Path, dpi: int) -> Image.Image:
    """Render first PDF page to an RGB PIL image via poppler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = Path(tmpdir) / "page"
        result = subprocess.run(
            [
                "pdftoppm",
                "-f",
                "1",
                "-singlefile",
                "-r",
                str(dpi),
                "-png",
                str(pdf_path),
                str(prefix),
            ],
            capture_output=True,
            text=True,
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftoppm failed: {result.stderr}")
        return Image.open(prefix.with_suffix(".png")).convert("RGB")


def bbox_pt_to_px(
    word: dict, page_size_pt: tuple[float, float], image_size_px: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Convert pdftotext point coordinates to image pixels."""
    page_w, page_h = page_size_pt
    img_w, img_h = image_size_px
    sx = img_w / page_w if page_w else 1.0
    sy = img_h / page_h if page_h else 1.0
    return (
        round(word["xmin"] * sx),
        round(word["ymin"] * sy),
        round(word["xmax"] * sx),
        round(word["ymax"] * sy),
    )


def expand_bbox(
    bbox: tuple[int, int, int, int], padding_px: int, image_size_px: tuple[int, int]
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    w, h = image_size_px
    return (
        max(0, x1 - padding_px),
        max(0, y1 - padding_px),
        min(w, x2 + padding_px),
        min(h, y2 + padding_px),
    )


def _region_stats(image: Image.Image, bbox: tuple[int, int, int, int]) -> dict:
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        return {"dark_ratio": 0.0, "luma_std": 0.0, "edge_density": 0.0}

    arr = np.asarray(image.crop((x1, y1, x2, y2)).convert("L"), dtype=np.float32)
    dark_ratio = float(np.mean(arr < 180))
    luma_std = float(np.std(arr))
    gx = np.abs(np.diff(arr, axis=1)).mean() if arr.shape[1] > 1 else 0.0
    gy = np.abs(np.diff(arr, axis=0)).mean() if arr.shape[0] > 1 else 0.0
    edge_density = float((gx + gy) / 255.0)
    return {"dark_ratio": dark_ratio, "luma_std": luma_std, "edge_density": edge_density}


def _ring_stats(
    image: Image.Image,
    inner: tuple[int, int, int, int],
    outer: tuple[int, int, int, int],
) -> dict:
    """Return stats for the padded area around a text bbox, excluding the text bbox."""
    ox1, oy1, ox2, oy2 = outer
    ix1, iy1, ix2, iy2 = inner
    if ox2 <= ox1 or oy2 <= oy1:
        return {"dark_ratio": 0.0, "luma_std": 0.0, "edge_density": 0.0}

    arr = np.asarray(image.crop(outer).convert("L"), dtype=np.float32)
    mask = np.ones(arr.shape, dtype=bool)
    rel_x1 = max(0, ix1 - ox1)
    rel_y1 = max(0, iy1 - oy1)
    rel_x2 = min(arr.shape[1], ix2 - ox1)
    rel_y2 = min(arr.shape[0], iy2 - oy1)
    mask[rel_y1:rel_y2, rel_x1:rel_x2] = False
    ring = arr[mask]
    if ring.size == 0:
        return {"dark_ratio": 0.0, "luma_std": 0.0, "edge_density": 0.0}

    dark_ratio = float(np.mean(ring < 180))
    luma_std = float(np.std(ring))
    edge_arr = arr.copy()
    edge_arr[~mask] = float(np.median(ring))
    gx = np.abs(np.diff(edge_arr, axis=1)).mean() if edge_arr.shape[1] > 1 else 0.0
    gy = np.abs(np.diff(edge_arr, axis=0)).mean() if edge_arr.shape[0] > 1 else 0.0
    edge_density = float((gx + gy) / 255.0)
    return {"dark_ratio": dark_ratio, "luma_std": luma_std, "edge_density": edge_density}


def _fill_under_text_stats(
    image: Image.Image,
    bbox: tuple[int, int, int, int],
    outer: tuple[int, int, int, int],
) -> dict:
    """Compare the text bbox background with the nearby surrounding region."""
    x1, y1, x2, y2 = bbox
    ox1, oy1, ox2, oy2 = outer
    if x2 <= x1 or y2 <= y1 or ox2 <= ox1 or oy2 <= oy1:
        return {
            "mean_delta": 0.0,
            "bbox_mean": 255.0,
            "outer_mean": 255.0,
            "bbox_std": 0.0,
            "ring_std": 0.0,
        }

    bbox_arr = np.asarray(image.crop(bbox).convert("L"), dtype=np.float32)
    outer_arr = np.asarray(image.crop(outer).convert("L"), dtype=np.float32)
    mask = np.ones(outer_arr.shape, dtype=bool)
    rel_x1 = max(0, x1 - ox1)
    rel_y1 = max(0, y1 - oy1)
    rel_x2 = min(outer_arr.shape[1], x2 - ox1)
    rel_y2 = min(outer_arr.shape[0], y2 - oy1)
    mask[rel_y1:rel_y2, rel_x1:rel_x2] = False
    ring = outer_arr[mask]
    if ring.size == 0:
        return {
            "mean_delta": 0.0,
            "bbox_mean": float(np.mean(bbox_arr)),
            "outer_mean": float(np.mean(outer_arr)),
            "bbox_std": 0.0,
            "ring_std": 0.0,
        }

    return {
        "mean_delta": float(abs(np.mean(bbox_arr) - np.mean(ring))),
        "bbox_mean": float(np.mean(bbox_arr)),
        "outer_mean": float(np.mean(outer_arr)),
        "bbox_std": float(np.std(bbox_arr)),
        "ring_std": float(np.std(ring)),
    }


def detect_visual_clashes(
    image: Image.Image,
    words: list[dict],
    page_size_pt: tuple[float, float],
    *,
    padding_px: int = 4,
) -> list[VisualIssue]:
    """Detect visual-risk candidates around rendered text bboxes."""
    issues: list[VisualIssue] = []
    image_size = image.size
    page_w, page_h = page_size_pt

    for word in words:
        text = word["text"]
        bbox = bbox_pt_to_px(word, page_size_pt, image_size)
        if word["xmin"] < 0 or word["ymin"] < 0 or word["xmax"] > page_w or word["ymax"] > page_h:
            issues.append(VisualIssue("clipping", text, "bbox extends outside PDF page", bbox))
            continue

        padded = expand_bbox(bbox, padding_px, image_size)
        stats = _ring_stats(image, bbox, padded)
        fill_stats = _fill_under_text_stats(image, bbox, padded)
        if stats["dark_ratio"] >= 0.03 and stats["edge_density"] >= 0.004:
            issues.append(
                VisualIssue(
                    "text_on_path",
                    text,
                    (f"dark={stats['dark_ratio']:.3f}, edge={stats['edge_density']:.3f}"),
                    bbox,
                )
            )
        elif (
            (
                fill_stats["mean_delta"] >= 18.0
                or (fill_stats["bbox_mean"] <= 245.0 and fill_stats["outer_mean"] <= 245.0)
            )
            and fill_stats["bbox_std"] <= 35.0
            and fill_stats["ring_std"] <= 35.0
        ):
            issues.append(
                VisualIssue(
                    "text_on_fill",
                    text,
                    (
                        f"fill_delta={fill_stats['mean_delta']:.1f}, "
                        f"bbox_mean={fill_stats['bbox_mean']:.1f}, "
                        f"bbox_std={fill_stats['bbox_std']:.1f}"
                    ),
                    bbox,
                )
            )
        elif stats["luma_std"] >= 36.0:
            issues.append(
                VisualIssue(
                    "text_on_fill",
                    text,
                    f"luma_std={stats['luma_std']:.1f}",
                    bbox,
                )
            )
        elif stats["dark_ratio"] >= 0.015 and stats["edge_density"] >= 0.004:
            issues.append(
                VisualIssue(
                    "near_miss",
                    text,
                    (
                        f"nearby dark pixels: dark={stats['dark_ratio']:.3f}, "
                        f"edge={stats['edge_density']:.3f}"
                    ),
                    bbox,
                )
            )

    return issues


def load_known_false_positive_patterns(path: Path = KNOWN_FALSE_POSITIVES_PATH) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    patterns = data.get("patterns") or []
    if not isinstance(patterns, list):
        return []
    return [pattern for pattern in patterns if isinstance(pattern, dict)]


def _detail_value(detail: str, key: str) -> float | None:
    match = re.search(rf"\b{re.escape(key)}=([-+]?\d+(?:\.\d+)?)", detail)
    if match is None:
        return None
    return float(match.group(1))


def _fixture_scope_matches(pattern: dict, fixture: str | None) -> bool:
    """A known-FP pattern only suppresses on the fixture(s) it was validated on.

    An un-scoped pattern (no ``fixture`` key) suppresses nothing: a global
    suppression would silence a real clash that merely shares a glyph — e.g.
    "PDMS", "Sulfur", "+", "−" — with a benign label on a different figure.
    """
    scope = pattern.get("fixture")
    if scope is None:
        return False
    if isinstance(scope, str):
        return scope == fixture
    if isinstance(scope, list):
        return fixture in scope
    return False


def _matches_known_false_positive(issue: VisualIssue, pattern: dict, fixture: str | None) -> bool:
    if not _fixture_scope_matches(pattern, fixture):
        return False
    pattern_id = pattern.get("id")
    kind = pattern.get("kind")
    if kind is not None and issue.kind != kind:
        return False

    glyph = pattern.get("glyph")
    if glyph is not None and issue.text != glyph:
        return False

    glyph_pattern = pattern.get("glyph_pattern")
    if glyph_pattern is not None and re.fullmatch(str(glyph_pattern), issue.text) is None:
        return False

    bbox_height_max = pattern.get("bbox_height_max")
    if bbox_height_max is not None:
        bbox_height = issue.bbox[3] - issue.bbox[1]
        if bbox_height > float(bbox_height_max):
            return False

    if pattern_id == "panel_label_superscript" and issue.kind != "text_on_fill":
        return False

    dark_min = pattern.get("dark_min")
    dark_max = pattern.get("dark_max")
    if dark_min is not None or dark_max is not None:
        dark = _detail_value(issue.detail, "dark")
        if dark is None:
            if pattern_id == "charge_symbol_filled_plus" and issue.kind == "text_on_fill":
                return True
            return False
        if dark_min is not None and dark < float(dark_min):
            return False
        if dark_max is not None and dark > float(dark_max):
            return False

    edge_max = pattern.get("edge_max")
    if edge_max is not None:
        edge = _detail_value(issue.detail, "edge")
        if edge is None or edge > float(edge_max):
            return False

    return glyph is not None or glyph_pattern is not None


def suppress_known_false_positives(
    issues: list[VisualIssue],
    patterns: list[dict],
    fixture: str | None,
) -> tuple[list[VisualIssue], int]:
    filtered: list[VisualIssue] = []
    suppressed = 0
    for issue in issues:
        if any(_matches_known_false_positive(issue, pattern, fixture) for pattern in patterns):
            suppressed += 1
        else:
            filtered.append(issue)
    return filtered, suppressed


def write_overlay(image: Image.Image, issues: list[VisualIssue], output_path: Path) -> None:
    """Write an annotated PNG for quick human inspection."""
    marked = image.copy()
    draw = ImageDraw.Draw(marked)
    colors = {
        "clipping": "red",
        "text_on_path": "orange",
        "text_on_fill": "purple",
        "near_miss": "gold",
    }
    for issue in issues:
        draw.rectangle(issue.bbox, outline=colors.get(issue.kind, "red"), width=3)
    marked.save(output_path)


def _metric_from_detail(detail: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for key, value in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)=([-+]?\d+(?:\.\d+)?)", detail):
        metrics[key] = float(value)
    return metrics


def _render_pdf_field(pdf_path: Path) -> str:
    if pdf_path.parent.name == "build":
        return str(Path("build") / pdf_path.name)
    return str(pdf_path)


def _fixture_name(pdf_path: Path) -> str:
    if pdf_path.parent.name == "build":
        return pdf_path.parent.parent.name
    return pdf_path.stem


def visual_clash_payload(
    pdf_path: Path,
    issues: list[VisualIssue],
    *,
    attribution_context: dict | None = None,
) -> dict:
    """Return the stable machine-readable visual-clash report."""
    candidates = []
    for index, issue in enumerate(issues, start=1):
        candidate = {
            "id": f"VC{index:03d}",
            "kind": issue.kind,
            "text": issue.text,
            "bbox_px": list(issue.bbox),
            "metric": _metric_from_detail(issue.detail),
            "tex_lines": None,
        }
        if attribution_context is not None:
            from visual_finding_attribution import attribute_visual_finding

            candidate["attribution"] = attribute_visual_finding(
                candidate,
                **attribution_context,
            )
        candidates.append(candidate)
    return {
        "fixture": _fixture_name(pdf_path),
        "render_pdf": _render_pdf_field(pdf_path),
        "candidates": candidates,
        "total": len(candidates),
    }


def write_visual_clash_json(pdf_path: Path, issues: list[VisualIssue], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(visual_clash_payload(pdf_path, issues), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render-based visual clash detector for compiled TikZ PDFs"
    )
    parser.add_argument("pdf", type=Path, help="컴파일된 PDF 경로")
    parser.add_argument("--dpi", type=int, default=600, help="렌더 DPI (기본 600)")
    parser.add_argument(
        "--overlay",
        type=Path,
        help="경고 bbox를 표시한 PNG 저장 경로",
    )
    parser.add_argument(
        "--ignore-known-fp",
        action="store_true",
        default=False,
        help="suppress known false-positive patterns (default OFF — report all)",
    )
    parser.add_argument(
        "--no-ignore-known-fp",
        dest="ignore_known_fp",
        action="store_false",
        help="explicit reset",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any unsuppressed clash candidate remains (default: report-only)",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="write machine-readable visual clash candidates to this JSON path",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    words, page_size = extract_pdf_words_and_page(args.pdf)
    image = render_pdf_first_page(args.pdf, args.dpi)
    issues = detect_visual_clashes(image, words, page_size)
    suppressed_count = 0
    if args.ignore_known_fp:
        issues, suppressed_count = suppress_known_false_positives(
            issues,
            load_known_false_positive_patterns(),
            _fixture_name(args.pdf),
        )
    if args.json_output:
        write_visual_clash_json(args.pdf, issues, args.json_output)

    print(f"visual clash report: {args.pdf.name} ({len(words)} words)")
    if not issues:
        print("OK: no visual clash candidates found")
        if args.json_output:
            print(f"visual clash JSON: {args.json_output}")
        if args.overlay:
            write_overlay(image, issues, args.overlay)
            print(f"overlay: {args.overlay}")
        if args.ignore_known_fp:
            print(f"{suppressed_count} suppressed (use --no-ignore-known-fp to see all)")
        return 0

    if args.json_output:
        print(f"WARN visual_clash: candidates serialized to {args.json_output}")
    else:
        for issue in issues:
            x1, y1, x2, y2 = issue.bbox
            print(f'WARN {issue.kind}: "{issue.text}" [{x1},{y1},{x2},{y2}] {issue.detail}')
        print(f"\n{len(issues)} visual clash candidate(s)")

    if args.overlay:
        write_overlay(image, issues, args.overlay)
        print(f"overlay: {args.overlay}")
    if args.ignore_known_fp:
        print(f"{suppressed_count} suppressed (use --no-ignore-known-fp to see all)")

    return 1 if args.strict else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
