from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _module():
    try:
        return importlib.import_module("semantic_region_contract")
    except ModuleNotFoundError:
        pytest.fail("scripts/semantic_region_contract.py should exist")


def _geometry() -> dict:
    return {
        "coordinate_space": "pdf_cm",
        "page_index": 0,
        "origin": "bottom_left",
        "media_box_pdf_cm": [0.0, 0.0, 17.8, 10.0],
        "crop_box_pdf_cm": [0.0, 0.0, 17.8, 10.0],
        "rotation_deg": 0,
    }


def _write_fixture(
    tmp_path: Path,
    *,
    source_text: str | None = None,
    region_updates: dict | None = None,
    geometry_updates: dict | None = None,
) -> tuple[Path, dict]:
    module = _module()
    fixture = tmp_path / "example"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "name: example\npanels:\n  - id: TARGET\n",
        encoding="utf-8",
    )
    source_text = source_text or (
        "\\begin{tikzpicture}\n"
        "% figure-agent:start target_panel.complex_region\n"
        "\\draw (0,0) -- (1,1);\n"
        "% figure-agent:end target_panel.complex_region\n"
        "\\end{tikzpicture}\n"
    )
    source_path = fixture / "example.tex"
    source_path.write_text(source_text, encoding="utf-8")
    geometry = _geometry()
    if geometry_updates:
        geometry.update(geometry_updates)
    geometry["render_geometry_hash"] = module.render_geometry_hash(geometry)
    region = {
        "id": "target_panel.complex_region",
        "panel_id": "TARGET",
        "role": "potential_profile",
        "bbox_pdf_cm": [10.1, 0.8, 12.9, 3.2],
        "source": {
            "path": "example.tex",
            "selector_id": "target_panel.complex_region",
            "anchor_start": "% figure-agent:start target_panel.complex_region",
            "anchor_end": "% figure-agent:end target_panel.complex_region",
            "source_sha256": f"sha256:{hashlib.sha256(source_text.encode()).hexdigest()}",
            "line_start": 2,
            "line_end": 4,
        },
        "provenance": "declared_by_author",
    }
    if region_updates:
        region.update(region_updates)
    (fixture / "semantic_regions.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.semantic-regions.v1",
                "page_geometry": geometry,
                "regions": [region],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return fixture, geometry


def test_loads_normalized_contract_with_exact_source_binding(tmp_path: Path) -> None:
    module = _module()
    fixture, detector_geometry = _write_fixture(tmp_path)

    payload = module.load_semantic_region_contract(
        fixture,
        detector_page_geometry=detector_geometry,
    )

    assert payload["schema"] == "figure-agent.semantic-regions.v1"
    assert payload["regions"][0]["bbox_pdf_cm"] == [10.1, 0.8, 12.9, 3.2]
    assert payload["regions"][0]["source"]["binding_state"] == "exact"
    assert payload["regions"][0]["source"]["resolved_line_start"] == 2
    assert payload["regions"][0]["source"]["resolved_line_end"] == 4
    assert payload["input_hashes"]["semantic_regions_sha256"].startswith("sha256:")
    assert payload["input_hashes"]["spec_sha256"].startswith("sha256:")
    assert payload["normalized_sha256"].startswith("sha256:")


@pytest.mark.parametrize(
    ("region_updates", "error"),
    [
        ({"panel_id": "MISSING"}, "unknown_panel"),
        ({"bbox_pdf_cm": [1, 2, 1, 3]}, "bbox_pdf_cm"),
        ({"bbox_pdf_cm": [1, 2, 18, 3]}, "outside_crop_box"),
        ({"source": {"path": "../outside.tex"}}, "unsafe_source_path"),
    ],
)
def test_rejects_invalid_region_declarations(
    tmp_path: Path,
    region_updates: dict,
    error: str,
) -> None:
    module = _module()
    fixture, _ = _write_fixture(tmp_path, region_updates=region_updates)

    with pytest.raises(module.SemanticRegionContractError, match=error):
        module.load_semantic_region_contract(fixture)


def test_rejects_duplicate_region_ids_and_declared_anchors(tmp_path: Path) -> None:
    module = _module()
    fixture, _ = _write_fixture(tmp_path)
    path = fixture / "semantic_regions.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["regions"].append(dict(payload["regions"][0]))
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(module.SemanticRegionContractError, match="duplicate_region_id"):
        module.load_semantic_region_contract(fixture)

    payload["regions"][1] = {
        **payload["regions"][1],
        "id": "target_panel.second_region",
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(module.SemanticRegionContractError, match="duplicate_anchor"):
        module.load_semantic_region_contract(fixture)


@pytest.mark.parametrize(
    ("source_text", "source_updates", "expected_state", "expected_reason"),
    [
        (
            "\\begin{tikzpicture}\n\\draw (0,0) -- (1,1);\n\\end{tikzpicture}\n",
            {},
            "unbound",
            "anchor_missing",
        ),
        (
            "% figure-agent:start target_panel.complex_region\n"
            "% figure-agent:start target_panel.complex_region\n"
            "% figure-agent:end target_panel.complex_region\n",
            {},
            "ambiguous",
            "anchor_duplicated_in_source",
        ),
        (
            None,
            {"line_start": 1, "line_end": 3},
            "ambiguous",
            "line_snapshot_stale",
        ),
        (
            None,
            {"source_sha256": "sha256:" + "0" * 64},
            "unbound",
            "source_hash_mismatch",
        ),
    ],
)
def test_source_binding_never_guesses_from_line_proximity(
    tmp_path: Path,
    source_text: str | None,
    source_updates: dict,
    expected_state: str,
    expected_reason: str,
) -> None:
    module = _module()
    fixture, _ = _write_fixture(tmp_path, source_text=source_text)
    path = fixture / "semantic_regions.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["regions"][0]["source"].update(source_updates)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = module.load_semantic_region_contract(fixture)
    source = result["regions"][0]["source"]
    assert source["binding_state"] == expected_state
    assert source["binding_reason"] == expected_reason
    assert "resolved_line_start" not in source
    assert "resolved_line_end" not in source


def test_rejects_reversed_line_snapshot(tmp_path: Path) -> None:
    module = _module()
    fixture, _ = _write_fixture(tmp_path)
    path = fixture / "semantic_regions.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["regions"][0]["source"].update({"line_start": 4, "line_end": 2})
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(module.SemanticRegionContractError, match="line_range_reversed"):
        module.load_semantic_region_contract(fixture)


def test_rejects_source_path_that_escapes_through_parent_symlink(tmp_path: Path) -> None:
    module = _module()
    fixture, _ = _write_fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    source_text = (fixture / "example.tex").read_text(encoding="utf-8")
    (outside / "external.tex").write_text(source_text, encoding="utf-8")
    (fixture / "linked").symlink_to(outside, target_is_directory=True)
    path = fixture / "semantic_regions.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["regions"][0]["source"]["path"] = "linked/external.tex"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(module.SemanticRegionContractError, match="unsafe_source_path"):
        module.load_semantic_region_contract(fixture)


def test_rejects_detector_render_geometry_mismatch(tmp_path: Path) -> None:
    module = _module()
    fixture, detector_geometry = _write_fixture(tmp_path)
    detector_geometry = {**detector_geometry, "rotation_deg": 90}
    detector_geometry["render_geometry_hash"] = module.render_geometry_hash(
        detector_geometry
    )

    with pytest.raises(module.SemanticRegionContractError, match="detector_geometry_mismatch"):
        module.load_semantic_region_contract(
            fixture,
            detector_page_geometry=detector_geometry,
        )
