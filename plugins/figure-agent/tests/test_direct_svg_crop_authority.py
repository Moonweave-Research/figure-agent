from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml
from direct_svg_crop_authority import CropAuthorityError, create_authority_crops
from PIL import Image


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_test_png(root: Path, *, width: int = 120, height: int = 80) -> Path:
    source = root / "benchmark.png"
    Image.new("RGB", (width, height), (245, 246, 248)).save(source, format="PNG")
    return source


def _write_manifest(
    root: Path,
    *,
    crops: dict[str, list[int]] | None = None,
) -> Path:
    source = _write_test_png(root)
    payload: dict[str, Any] = {
        "schema": "figure-agent.direct-svg-crop-authority.v1",
        "algorithm": "pillow.crop.v1",
        "source": {
            "path": "benchmark.png",
            "sha256": _sha256(source),
            "width": 120,
            "height": 80,
        },
        "crops": {
            panel: {"bbox": bbox, "output": f"panel-{panel.lower()}.png"}
            for panel, bbox in (
                crops
                or {
                    "C": [40, 0, 120, 40],
                    "F": [80, 40, 120, 80],
                }
            ).items()
        },
        "publication_acceptance": "not_claimed",
    }
    manifest = root / "crop-authority.yaml"
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return manifest


def test_crop_manifest_binds_source_geometry_and_output_hashes(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)

    first = create_authority_crops(manifest)
    first_bytes = {
        panel: (tmp_path / item["output"]).read_bytes()
        for panel, item in first["crops"].items()
    }
    second = create_authority_crops(manifest)

    assert first == second
    assert set(first["crops"]) == {"C", "F"}
    for panel, item in second["crops"].items():
        output = tmp_path / item["output"]
        assert output.read_bytes() == first_bytes[panel]
        assert item["sha256"] == _sha256(output)
        assert Image.open(output).mode == "RGB"


def test_crop_manifest_rejects_source_hash_mismatch(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    manifest.parent.joinpath("benchmark.png").write_bytes(b"changed")

    with pytest.raises(CropAuthorityError, match="source_hash_mismatch"):
        create_authority_crops(manifest)


def test_crop_manifest_rejects_source_dimension_mismatch(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path)
    payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    payload["source"]["width"] = 121
    manifest.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(CropAuthorityError, match="source_geometry_mismatch"):
        create_authority_crops(manifest)


def test_crop_manifest_rejects_out_of_bounds_bbox(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        crops={"C": [40, 0, 121, 40], "F": [80, 40, 120, 80]},
    )

    with pytest.raises(CropAuthorityError, match="crop_out_of_bounds"):
        create_authority_crops(manifest)


def test_crop_manifest_requires_exact_panel_set(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, crops={"C": [40, 0, 120, 40]})

    with pytest.raises(CropAuthorityError, match="panels_must_be_C_and_F"):
        create_authority_crops(manifest)


def test_crop_manifest_rejects_non_integer_bbox(tmp_path: Path) -> None:
    manifest = _write_manifest(
        tmp_path,
        crops={"C": [40.5, 0, 120, 40], "F": [80, 40, 120, 80]},  # type: ignore[list-item]
    )

    with pytest.raises(CropAuthorityError, match="crop_bbox_invalid"):
        create_authority_crops(manifest)
