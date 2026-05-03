"""Palette-based shape cluster detection from a reference PNG.

Layer 2.5 sub-module of `reference_extract`. Finds connected components of
pixels matching each polymer-paper-preamble palette color, after a per-color
RGB-distance threshold and min-component-size filter.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import find_objects, label

# polymer-paper-preamble.sty palette. Keep in sync with the .sty file; if a new
# palette color is added there, add it here too (no automatic discovery yet).
PALETTE: dict[str, tuple[int, int, int]] = {
    "cAmber": (0x99, 0x7A, 0x1E),
    "cBlue": (0x44, 0x77, 0xAA),
    "cRed": (0xCC, 0x66, 0x77),
    "cTeal": (0x44, 0xAA, 0x99),
    "cGray": (70, 70, 70),
    "cLGray": (200, 200, 200),
    "cBrown": (0x5D, 0x48, 0x20),
    "cArmAmber": (0x8B, 0x6F, 0x3E),
    "cAmberSphere": (0xDD, 0xCC, 0x77),
}

# Per-color RGB Euclidean threshold. Tuned empirically on golden_target_001.png
# to balance detection of meaningful shapes against anti-aliasing noise.
# Specific saturated palette colors get a tighter threshold; broad amber-tan
# tones get a looser one because the reference renders them desaturated.
COLOR_GROUP = {
    "cAmber": "specific",
    "cBlue": "specific",
    "cRed": "specific",
    "cTeal": "specific",
    "cBrown": "specific",
    "cArmAmber": "broad",
    "cAmberSphere": "broad",
    "cGray": "gray",
    "cLGray": "gray",
}
# Empirically calibrated against golden_target_001.png (LLM-rendered, lightly
# desaturated). Tighter thresholds (specific=40, gray=30) lost real palette
# regions like the amber lobe labels because the LLM render does not hit the
# exact palette hex; loosen to 55/35 with min_component=200 so true positives
# survive while cArmAmber-class noise stays bounded by the broad-tone cap.
GROUP_THRESHOLDS = {
    "specific": 55,
    "broad": 55,
    "gray": 35,
}

DEFAULT_MIN_COMPONENT_PIXELS = 200


def palette_shape_clusters(
    image: np.ndarray,
    *,
    palette: dict[str, tuple[int, int, int]] | None = None,
    group_thresholds: dict[str, int] | None = None,
    color_group: dict[str, str] | None = None,
    min_component_pixels: int = DEFAULT_MIN_COMPONENT_PIXELS,
) -> dict[str, dict]:
    """Find connected components per palette color in the reference image.

    Returns:
        {color_name: {target_rgb, threshold, match_count, components: [...] }}
        Colors with no surviving component are omitted.
    """
    palette = palette or PALETTE
    group_thresholds = group_thresholds or GROUP_THRESHOLDS
    color_group = color_group or COLOR_GROUP

    # Upcast to int32 before subtracting and squaring: a single channel diff
    # can hit 255, and 255**2 = 65025 overflows int16 silently, which would
    # turn the whole-image dist_sq vector negative and match every pixel.
    rgb = image.astype(np.int32)
    out: dict[str, dict] = {}
    for color_name, target_rgb in palette.items():
        threshold = group_thresholds.get(color_group.get(color_name, "specific"), 40)
        diff = rgb - np.array(target_rgb, dtype=np.int32)
        dist_sq = (diff * diff).sum(axis=2)
        mask = dist_sq < (threshold * threshold)
        match_count = int(mask.sum())
        if match_count < min_component_pixels:
            continue
        labeled, ncomp = label(mask)
        slices = find_objects(labeled)
        components: list[dict] = []
        for idx, sl in enumerate(slices, start=1):
            if sl is None:
                continue
            ys, xs = sl
            comp_mask = labeled[sl] == idx
            pixel_count = int(comp_mask.sum())
            if pixel_count < min_component_pixels:
                continue
            components.append(
                {
                    "bbox": [int(xs.start), int(ys.start), int(xs.stop), int(ys.stop)],
                    "pixel_count": pixel_count,
                }
            )
        if not components:
            continue
        components.sort(key=lambda c: -c["pixel_count"])
        out[color_name] = {
            "target_rgb": list(target_rgb),
            "threshold": threshold,
            "match_count": match_count,
            "components": components,
        }
    return out
