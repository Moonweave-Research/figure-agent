"""Vtracer-based structural region extraction from a reference PNG.

Layer 2.5 sub-module of `reference_extract`. Uses vtracer to vectorize the
reference image and extracts panel arcs, border boxes, chain rows, S-atom
positions, trap levels, plot boxes, plot curves, and lobe-like regions
from the resulting SVG paths.

vtracer is an optional dependency: extraction returns
`{"status": "unavailable"}` cleanly if the package is not importable.
"""

from __future__ import annotations

import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_CANVAS_WIDTH_CM = 14.0


def _classify_color_family(r: int, g: int, b: int) -> str | None:
    # Mid-gray: polymer chain color — moderate dark gray, low saturation.
    # Must run before the mx-mn < 40 saturation guard because chain-gray pixels
    # are near-achromatic (max-min ≈ 0) and would early-return otherwise.
    if 45 < r < 145 and abs(r - g) < 25 and abs(g - b) < 25:
        return "chain_gray"
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 40:
        return None
    # b > r + 70 (not +40) ensures indigo/purple (#6F3F9D: b=157, r=111 → diff=46) is
    # not mis-classified as blue — it falls through to the purple branch instead.
    if b > r + 70 and b > g + 20 and r < 130:
        return "blue"
    if r > 160 and g > 80 and b < 100 and r > g + 40:
        return "orange"
    if r > 100 and b > r - 40 and b > g + 30 and r < 225:
        return "purple"
    if g > 90 and b > 80 and r < 80:
        return "teal"
    return None


def _get_translate(elem: ET.Element) -> tuple[float, float]:
    tr = elem.get("transform", "")
    m = re.search(r"translate\(([^,]+),([^)]+)\)", tr)
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def _parse_svg_path_bounds(d: str) -> tuple[float, float, float, float] | None:
    numbers = re.findall(r"[-+]?\d*\.?\d+", d)
    if not numbers:
        return None
    coords = [float(n) for n in numbers]
    if len(coords) < 2:
        return None
    xs = [coords[i] for i in range(0, len(coords), 2)]
    ys = [coords[i] for i in range(1, len(coords), 2)]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _path_global_bbox(d: str, tx: float, ty: float) -> tuple[float, float, float, float] | None:
    bounds = _parse_svg_path_bounds(d)
    if bounds is None:
        return None
    x1, y1, x2, y2 = bounds
    return x1 + tx, y1 + ty, x2 + tx, y2 + ty


def structural_regions_from_reference(
    reference_path: Path,
    image_size_px: tuple[int, int],
    *,
    canvas_width_cm: float = DEFAULT_CANVAS_WIDTH_CM,
) -> dict:
    """Extract panel arcs, border boxes, and chain rows via vtracer Python API.

    Returns a dict with 'status' key:
      'ok'          — extraction succeeded; panel_arcs / border_boxes / chain_rows populated.
      'unavailable' — vtracer Python package not importable.
      'failed'      — vtracer available but extraction raised an exception.

      plot_boxes[]     Large gray axis-background rectangles inside each evidence panel arc.
      plot_curves[]    Curve bounding boxes: power-law line (panel blue)
                       and Debye decay (panel purple).
      ispd_lobes[]     ISPD bell curve bounding boxes: shallow (orange) and deep (purple/lavender).
      right_gaussians[] g(Et) sideways Gaussians in band diagram: shallow (peach) and deep (purple).
    """
    try:
        import vtracer as _vtracer
    except ImportError:
        return {"status": "unavailable"}

    try:
        img_w, img_h = image_size_px
        cm_per_px = canvas_width_cm / img_w

        with tempfile.TemporaryDirectory() as td:
            svg_path = Path(td) / "vectorized.svg"
            _vtracer.convert_image_to_svg_py(
                str(reference_path),
                str(svg_path),
                colormode="color",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                color_precision=6,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )
            tree = ET.parse(svg_path)

        ns = {"svg": "http://www.w3.org/2000/svg"}
        root = tree.getroot()

        # Collect individual path bboxes per color-family (image-px space).
        # Union-bbox-per-family is wrong: scattered noise paths inflate the bbox to
        # canvas size. Instead keep all individual bboxes and return the largest ones.
        family_paths: dict[str, list[tuple[float, float, float, float]]] = {}
        raw_paths: dict[str, list[dict]] = {}  # NEW: 면적 필터 없는 개별 path 정보

        for path_elem in root.findall(".//svg:path", ns):
            fill = path_elem.get("fill", "")
            if not fill or fill == "none":
                style = path_elem.get("style", "")
                for part in style.split(";"):
                    part = part.strip()
                    if part.startswith("fill:"):
                        fill = part[5:].strip()
                        break
            if not fill or fill == "none" or not fill.startswith("#") or len(fill) != 7:
                continue

            h = fill.lstrip("#")
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            except ValueError:
                continue

            family = _classify_color_family(r, g, b)
            if family is None:
                continue

            tx, ty = _get_translate(path_elem)
            bb = _path_global_bbox(path_elem.get("d", ""), tx, ty)
            if bb is None:
                continue

            family_paths.setdefault(family, []).append(bb)
            # Also store individual path metadata for small-feature extraction
            x1, y1, x2, y2 = bb
            w_px = x2 - x1
            h_px = y2 - y1
            area_px2 = w_px * h_px
            raw_paths.setdefault(family, []).append(
                {
                    "bbox_px": (x1, y1, x2, y2),
                    "area_px2": area_px2,
                    "w_px": w_px,
                    "h_px": h_px,
                    "x_center_cm": (x1 + x2) / 2 * cm_per_px,
                    "y_center_cm": (img_h - (y1 + y2) / 2) * cm_per_px,
                    "x1_cm": x1 * cm_per_px,
                    "x2_cm": x2 * cm_per_px,
                    "y1_cm": (img_h - y2) * cm_per_px,
                    "y2_cm": (img_h - y1) * cm_per_px,
                }
            )

        def _to_region(family: str, px: list[float]) -> dict:
            x1_px, y1_px, x2_px, y2_px = px
            # TikZ y-flip: y=0 at bottom → y_tikz = (img_h - y_img) * cm_per_px
            x1_cm = round(x1_px * cm_per_px, 2)
            x2_cm = round(x2_px * cm_per_px, 2)
            y1_cm = round((img_h - y2_px) * cm_per_px, 2)
            y2_cm = round((img_h - y1_px) * cm_per_px, 2)
            area = round((x2_cm - x1_cm) * (y2_cm - y1_cm), 2)
            return {
                "color_family": family,
                "bbox_px": [int(x1_px), int(y1_px), int(x2_px), int(y2_px)],
                "bbox_cm": [x1_cm, y1_cm, x2_cm, y2_cm],
                "area_cm2": area,
            }

        # Union bbox of paths above a minimum individual area.
        # Single-dominant-path fails when vtracer tessellates a large arc into many
        # small segments (observed for the purple panel arc). Noise micro-paths
        # (anti-aliasing artifacts) are excluded by the MIN_PATH_AREA_PX2 floor.
        # 50 000 px² ≈ 3.4 cm² at 121 px/cm — keeps major panel arc paths only;
        # plot curves and text (typically 1 000–40 000 px²) are excluded.
        MIN_PATH_AREA_PX2 = 50_000

        # Panel arcs are confined to the left evidence zone (x center < canvas * 0.45).
        # Lavender/purple paths in the right zone (band diagram background, x > 10 cm)
        # would otherwise inflate the purple panel arc bbox after the r<225 classifier
        # expansion introduced for ispd_lobes deep detection.
        _PANEL_ARC_MAX_X_CENTER_PX = img_w * 0.45  # ≈761 px for 1693 px canvas

        def _union_bbox(
            bboxes: list[tuple[float, float, float, float]],
            *,
            left_zone_only: bool = False,
        ) -> list[float] | None:
            large = [
                (x1, y1, x2, y2)
                for x1, y1, x2, y2 in bboxes
                if (x2 - x1) * (y2 - y1) >= MIN_PATH_AREA_PX2
                and (not left_zone_only or (x1 + x2) / 2 < _PANEL_ARC_MAX_X_CENTER_PX)
            ]
            if not large:
                return None
            return [
                min(bb[0] for bb in large),
                min(bb[1] for bb in large),
                max(bb[2] for bb in large),
                max(bb[3] for bb in large),
            ]

        panel_arcs = sorted(
            [
                _to_region(f, ub)
                for f in ("blue", "orange", "purple")
                if (ub := _union_bbox(family_paths.get(f, []), left_zone_only=True)) is not None
            ],
            key=lambda r: -r["area_cm2"],
        )
        border_boxes = sorted(
            [
                _to_region(f, ub)
                for f in ("teal",)
                if (ub := _union_bbox(family_paths.get(f, []))) is not None
            ],
            key=lambda r: -r["area_cm2"],
        )

        # Chain rows: horizontal gray paths anywhere in the figure.
        # Bounds are canvas-relative so thresholds generalise across fixtures:
        #   x_center: 10 %–90 % of canvas width  (excludes far-left icons / far-right axis)
        #   y_center: 5 %–95 % of canvas height  (excludes page margins only)
        # Previously these were hardcoded to one fixture layout (4.0-11.5 cm,
        # y > 2.8 cm) which excluded legitimate chains in other fixtures.
        canvas_w_cm = img_w * cm_per_px
        canvas_h_cm = img_h * cm_per_px
        MID_X_MIN_CM = canvas_w_cm * 0.10
        MID_X_MAX_CM = canvas_w_cm * 0.90
        # 18 % floor keeps golden_trap_depth chains at y≈1.7 cm while excluding
        # axis-tick and annotation-line false positives at y<1.4 cm.
        MID_Y_MIN_CM = canvas_h_cm * 0.18
        MIN_CHAIN_WIDTH_CM = 1.5
        MAX_CHAIN_HEIGHT_CM = 0.8

        chain_candidates: list[tuple[float, float, float, float]] = []  # (y_center, x1, x2, x_span)

        for bb in family_paths.get("chain_gray", []):
            x1, y1, x2, y2 = bb
            x1_cm = x1 * cm_per_px
            x2_cm = x2 * cm_per_px
            y1_cm = (img_h - y2) * cm_per_px
            y2_cm = (img_h - y1) * cm_per_px
            x_span = x2_cm - x1_cm
            y_span = y2_cm - y1_cm
            x_center = (x1_cm + x2_cm) / 2
            y_center = (y1_cm + y2_cm) / 2
            if (
                MID_X_MIN_CM < x_center < MID_X_MAX_CM
                and y_center > MID_Y_MIN_CM
                and y_span < MAX_CHAIN_HEIGHT_CM
            ):
                chain_candidates.append((y_center, x1_cm, x2_cm, x_span))

        # Cluster by y-position (within 0.5 cm = same chain row)
        CLUSTER_RADIUS_CM = 0.50
        chain_rows_raw: list[dict] = []

        if chain_candidates:
            chain_candidates.sort(key=lambda c: c[0])  # sort by y_center
            clusters: list[list[tuple]] = []
            for cand in chain_candidates:
                placed = False
                for cluster in clusters:
                    if abs(cand[0] - cluster[0][0]) < CLUSTER_RADIUS_CM:
                        cluster.append(cand)
                        placed = True
                        break
                if not placed:
                    clusters.append([cand])

            for cluster in clusters:
                y_centers = [c[0] for c in cluster]
                x1s = [c[1] for c in cluster]
                x2s = [c[2] for c in cluster]
                total_x_span = sum(c[3] for c in cluster)
                chain_rows_raw.append(
                    {
                        "y_center_cm": round(sum(y_centers) / len(y_centers), 2),
                        "x_span_cm": [round(min(x1s), 2), round(max(x2s), 2)],
                        "path_count": len(cluster),
                        "total_x_span_cm": round(total_x_span, 2),
                    }
                )

            # Filter clusters: total_x_span and path_count quality gates.
            # y_center lower bound is canvas-relative (MID_Y_MIN_CM, already applied
            # per-candidate above) — no fixture-specific hardcoded floor here.
            chain_rows_raw = [
                r
                for r in chain_rows_raw
                if r["total_x_span_cm"] >= MIN_CHAIN_WIDTH_CM and r["path_count"] >= 2
            ]

            # Sort by total_x_span descending (most complete chains first),
            # then re-sort by y_center descending (top to bottom in TikZ)
            chain_rows_raw.sort(key=lambda r: -r["total_x_span_cm"])
            chain_rows = sorted(chain_rows_raw[:5], key=lambda r: -r["y_center_cm"])
            # Remove helper field
            for row in chain_rows:
                del row["total_x_span_cm"]
        else:
            chain_rows = []

        # S-atom positions: small amber/orange dots on chain rows
        s_atoms: list[dict] = []
        chain_y_centers = [row["y_center_cm"] for row in chain_rows]
        for path_info in raw_paths.get("orange", []):
            area = path_info["area_px2"]
            if not (50 <= area <= 1500):  # 크기 필터: panel arc(>80k) 제외
                continue
            xc = path_info["x_center_cm"]
            yc = path_info["y_center_cm"]
            # Canvas-relative position bounds (replaces fixture-specific hardcoded range).
            # panel_arcs exclusion further removes paths inside evidence panel ovals.
            if not (canvas_w_cm * 0.08 <= xc <= canvas_w_cm * 0.92):
                continue
            if not (canvas_h_cm * 0.03 <= yc <= canvas_h_cm * 0.97):
                continue
            # Exclude paths whose center lies inside a detected panel arc bbox.
            # This replaces the old x>4.5 hack that was fixture-specific.
            if any(
                a["bbox_cm"][0] <= xc <= a["bbox_cm"][2]
                and a["bbox_cm"][1] <= yc <= a["bbox_cm"][3]
                for a in panel_arcs
            ):
                continue
            # Also exclude paths inside the band-diagram border (right zone).
            if any(
                b["bbox_cm"][0] <= xc <= b["bbox_cm"][2]
                and b["bbox_cm"][1] <= yc <= b["bbox_cm"][3]
                for b in border_boxes
            ):
                continue
            if not chain_y_centers:
                continue
            dists = [abs(yc - cy) for cy in chain_y_centers]
            min_dist = min(dists)
            if min_dist > 0.55:
                continue
            s_atoms.append(
                {
                    "x_cm": round(xc, 2),
                    "y_cm": round(yc, 2),
                    "chain_row_index": dists.index(min_dist),
                    "area_px2": int(area),
                }
            )
        s_atoms.sort(key=lambda a: (a["chain_row_index"], a["x_cm"]))

        # Trap levels: orange (shallow) + purple (deep) horizontal dashes inside teal border
        TRAP_MIN_AREA_PX2 = 60
        TRAP_MAX_AREA_PX2 = 4000
        TRAP_ASPECT_MIN = 3.0  # w >= 3*h (horizontal dash)

        trap_levels: list[dict] = []

        if border_boxes:
            tb = border_boxes[0]["bbox_cm"]  # [x1, y1, x2, y2]
            tb_x1, tb_y1, tb_x2, tb_y2 = tb
        else:
            tb_x1, tb_y1, tb_x2, tb_y2 = 0, 0, 14, 8

        for fam, role in [("orange", "shallow"), ("purple", "deep")]:
            for path_info in raw_paths.get(fam, []):
                area = path_info["area_px2"]
                if not (TRAP_MIN_AREA_PX2 <= area <= TRAP_MAX_AREA_PX2):
                    continue
                w, h = path_info["w_px"], path_info["h_px"]
                if h == 0 or w / h < TRAP_ASPECT_MIN:
                    continue
                xc = path_info["x_center_cm"]
                yc = path_info["y_center_cm"]
                if not (tb_x1 <= xc <= tb_x2 and tb_y1 <= yc <= tb_y2):
                    continue
                trap_levels.append(
                    {
                        "color_family": fam,
                        "level_role": role,
                        "x_cm": round(xc, 2),
                        "y_cm": round(yc, 2),
                        "w_cm": round(path_info["x2_cm"] - path_info["x1_cm"], 2),
                        "h_cm": round(path_info["y2_cm"] - path_info["y1_cm"], 2),
                    }
                )

        trap_levels.sort(key=lambda t: -t["y_cm"])  # top to bottom (TikZ: high y = top)

        # plot_boxes: axis background rectangles inside each panel arc
        # Detected as large gray rects (chain_gray, area 25k-60k px², aspect < 4)
        PLOT_BOX_MIN_AREA = 40000
        PLOT_BOX_MAX_AREA = 60000
        PLOT_BOX_MAX_ASPECT = 4.0

        plot_boxes: list[dict] = []
        for path_info in raw_paths.get("chain_gray", []):
            area = path_info["area_px2"]
            if not (PLOT_BOX_MIN_AREA <= area <= PLOT_BOX_MAX_AREA):
                continue
            w_px, h_px = path_info["w_px"], path_info["h_px"]
            if h_px == 0:
                continue
            if max(w_px / h_px, h_px / w_px) > PLOT_BOX_MAX_ASPECT:
                continue
            xc = path_info["x_center_cm"]
            yc = path_info["y_center_cm"]
            for arc in panel_arcs:
                bx1, by1, bx2, by2 = arc["bbox_cm"]
                if bx1 <= xc <= bx2 and by1 <= yc <= by2:
                    plot_boxes.append(
                        {
                            "panel_family": arc["color_family"],
                            "bbox_cm": [
                                round(path_info["x1_cm"], 2),
                                round(path_info["y1_cm"], 2),
                                round(path_info["x2_cm"], 2),
                                round(path_info["y2_cm"], 2),
                            ],
                        }
                    )
                    break

        # plot_curves: colored/gray curve paths inside panel arc bboxes
        # Panel ①: blue power-law line (area 15k-45k px², inside blue arc)
        # Panel ③: gray Debye decay (area 15k-45k px², chain_gray, y < 3.5 cm, inside purple arc)
        PLOT_CURVE_MIN_AREA = 15000
        PLOT_CURVE_MAX_AREA = 45000

        plot_curves: list[dict] = []

        # Panel ① power-law line (blue family)
        for path_info in raw_paths.get("blue", []):
            area = path_info["area_px2"]
            if not (PLOT_CURVE_MIN_AREA <= area <= PLOT_CURVE_MAX_AREA):
                continue
            xc = path_info["x_center_cm"]
            yc = path_info["y_center_cm"]
            if xc > 3.5:  # arc 파편(x_center≈4.13) 제외
                continue
            for arc in panel_arcs:
                if arc["color_family"] != "blue":
                    continue
                bx1, by1, bx2, by2 = arc["bbox_cm"]
                if bx1 <= xc <= bx2 and by1 <= yc <= by2:
                    plot_curves.append(
                        {
                            "panel_family": "blue",
                            "element": "power_law_line",
                            "color_family": "blue",
                            "bbox_cm": [
                                round(path_info["x1_cm"], 2),
                                round(path_info["y1_cm"], 2),
                                round(path_info["x2_cm"], 2),
                                round(path_info["y2_cm"], 2),
                            ],
                        }
                    )
                    break

        # Panel ③ Debye decay curve (chain_gray, lower y region)
        for path_info in raw_paths.get("chain_gray", []):
            area = path_info["area_px2"]
            if not (PLOT_CURVE_MIN_AREA <= area <= PLOT_CURVE_MAX_AREA):
                continue
            yc = path_info["y_center_cm"]
            if yc > 3.5:  # Panel ③ is at y=0.26-3.04
                continue
            xc = path_info["x_center_cm"]
            for arc in panel_arcs:
                if arc["color_family"] != "purple":
                    continue
                bx1, by1, bx2, by2 = arc["bbox_cm"]
                if bx1 <= xc <= bx2 and by1 <= yc <= by2:
                    plot_curves.append(
                        {
                            "panel_family": "purple",
                            "element": "debye_decay_curve",
                            "color_family": "gray",
                            "bbox_cm": [
                                round(path_info["x1_cm"], 2),
                                round(path_info["y1_cm"], 2),
                                round(path_info["x2_cm"], 2),
                                round(path_info["y2_cm"], 2),
                            ],
                        }
                    )
                    break

        # ispd_lobes: ISPD panel (orange arc) bell curve lobes
        # Shallow (orange, area 2k-30k px²), Deep (purple/lavender, area 2k-25k px²)
        ISPD_MIN_AREA = 2000
        ISPD_MAX_AREA = 30000

        ispd_lobes: list[dict] = []
        orange_arc = next((a for a in panel_arcs if a["color_family"] == "orange"), None)
        if orange_arc:
            oax1, oay1, oax2, oay2 = orange_arc["bbox_cm"]
            panel_center_x = (oax1 + oax2) / 2
            for fam, role in [("orange", "shallow"), ("purple", "deep")]:
                all_inside = []
                for path_info in raw_paths.get(fam, []):
                    area = path_info["area_px2"]
                    if not (ISPD_MIN_AREA <= area <= ISPD_MAX_AREA):
                        continue
                    xc = path_info["x_center_cm"]
                    yc = path_info["y_center_cm"]
                    if not (oax1 <= xc <= oax2 and oay1 <= yc <= oay2):
                        continue
                    # Exclude arrow exit paths (right half of panel).
                    # Bell curves sit left of panel center; the "→ g(Et)" arrow
                    # exit region (x=2.79-4.97) inflates the union bbox otherwise.
                    if xc > panel_center_x:
                        continue
                    all_inside.append(path_info)
                if all_inside:
                    x1s = [p["x1_cm"] for p in all_inside]
                    y1s = [p["y1_cm"] for p in all_inside]
                    x2s = [p["x2_cm"] for p in all_inside]
                    y2s = [p["y2_cm"] for p in all_inside]
                    ispd_lobes.append(
                        {
                            "level_role": role,
                            "color_family": fam,
                            "bbox_cm": [
                                round(min(x1s), 2),
                                round(min(y1s), 2),
                                round(max(x2s), 2),
                                round(max(y2s), 2),
                            ],
                        }
                    )

        # right_gaussians: g(Et) Gaussian shapes in band diagram right zone
        # Detected by position (x>12 cm, inside teal border) and shape (h > w)
        # Covers unclassified peach (#FACAA9 shallow) and purple (#6B3F99 deep)
        RIGHT_GAUSS_MIN_AREA = 8000
        RIGHT_GAUSS_MAX_AREA = 22000
        RIGHT_GAUSS_MIN_X_CM = 12.0

        right_gaussians: list[dict] = []
        if border_boxes:
            tb_x1, tb_y1, tb_x2, tb_y2 = border_boxes[0]["bbox_cm"]
            tb_mid_y = (tb_y1 + tb_y2) / 2

            for path_elem in root.findall(".//svg:path", ns):
                fill = path_elem.get("fill", "")
                if not fill.startswith("#") or len(fill) != 7:
                    continue
                tr_val = path_elem.get("transform", "")
                m_tr = re.search(r"translate\(([^,]+),([^)]+)\)", tr_val)
                tx_r = float(m_tr.group(1)) if m_tr else 0.0
                ty_r = float(m_tr.group(2)) if m_tr else 0.0
                bb_r = _path_global_bbox(path_elem.get("d", ""), tx_r, ty_r)
                if bb_r is None:
                    continue
                rx1, ry1, rx2, ry2 = bb_r
                area_r = (rx2 - rx1) * (ry2 - ry1)
                if not (RIGHT_GAUSS_MIN_AREA <= area_r <= RIGHT_GAUSS_MAX_AREA):
                    continue
                rxc_cm = (rx1 + rx2) / 2 * cm_per_px
                ryc_cm = (img_h - (ry1 + ry2) / 2) * cm_per_px
                if not (RIGHT_GAUSS_MIN_X_CM <= rxc_cm <= tb_x2):
                    continue
                if not (tb_y1 <= ryc_cm <= tb_y2):
                    continue
                # Shape filter: taller than wide (h/w > 1.0) — excludes wide teal bars
                w_r = (rx2 - rx1) * cm_per_px
                h_r = (ry2 - ry1) * cm_per_px
                if w_r == 0 or h_r / w_r < 1.0:
                    continue
                level = "shallow" if ryc_cm > tb_mid_y else "deep"
                right_gaussians.append(
                    {
                        "level_role": level,
                        "fill_hex": fill,
                        "bbox_cm": [
                            round(rx1 * cm_per_px, 2),
                            round((img_h - ry2) * cm_per_px, 2),
                            round(rx2 * cm_per_px, 2),
                            round((img_h - ry1) * cm_per_px, 2),
                        ],
                    }
                )
            right_gaussians.sort(key=lambda g: -g["bbox_cm"][3])  # top y first

        return {
            "status": "ok",
            "image_px": [img_w, img_h],
            "cm_per_px": round(cm_per_px, 5),
            "panel_arcs": panel_arcs,
            "border_boxes": border_boxes,
            "chain_rows": chain_rows,
            "s_atoms": s_atoms,
            "trap_levels": trap_levels,
            "plot_boxes": plot_boxes,
            "plot_curves": plot_curves,
            "ispd_lobes": ispd_lobes,
            "right_gaussians": right_gaussians,
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
