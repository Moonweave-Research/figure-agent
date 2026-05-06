from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "README.md"
V14_HANDBACK = ROOT / "global_composition_asset_boundary_handback_v14.md"

REQUIRED_MANIFEST_TOKENS = (
    "fig1_reference_semantic.svg",
    "fig1_reference_semantic.png",
    "reference_vs_fig1_reference_semantic.png",
    "visual_layout.yaml",
    "reference_layout_spec_v1.md",
    "dos_reference_schematic_handback_v9.md",
    "dos_density_profile_handback_v10.md",
    "dos_schematic_polish_handback_v11.md",
    "visual_cohesion_handback_v12.md",
    "support_panel_cohesion_handback_v13.md",
    "global_composition_asset_boundary_handback_v14.md",
    "legacy annotated redraw",
    "layout/style evidence only",
)

REQUIRED_V14_TOKENS = (
    "Reusable asset candidates",
    "Fig1-only boundaries",
    "Human visual review",
)


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if not MANIFEST.exists():
        return _fail(f"missing experiment manifest: {MANIFEST}")
    manifest = MANIFEST.read_text()
    for token in REQUIRED_MANIFEST_TOKENS:
        if token not in manifest:
            return _fail(f"experiment manifest missing token: {token}")

    if not V14_HANDBACK.exists():
        return _fail(f"missing v14 asset-boundary handback: {V14_HANDBACK}")
    handback = V14_HANDBACK.read_text()
    for token in REQUIRED_V14_TOKENS:
        if token not in handback:
            return _fail(f"v14 handback missing asset-boundary token: {token}")

    print("fig1 docs manifest passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
