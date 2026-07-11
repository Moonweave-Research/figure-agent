from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_visual_clash  # noqa: E402
import semantic_region_contract  # noqa: E402


def _module():
    try:
        return importlib.import_module("visual_finding_attribution")
    except ModuleNotFoundError:
        pytest.fail("scripts/visual_finding_attribution.py should exist")


def _geometry(
    *,
    media: list[float] | None = None,
    crop: list[float] | None = None,
    rotation: int = 0,
    page_index: int = 0,
) -> dict:
    value = {
        "coordinate_space": "pdf_cm",
        "page_index": page_index,
        "origin": "bottom_left",
        "media_box_pdf_cm": media or [0.0, 0.0, 10.0, 10.0],
        "crop_box_pdf_cm": crop or [0.0, 0.0, 10.0, 10.0],
        "rotation_deg": rotation,
    }
    value["render_geometry_hash"] = semantic_region_contract.render_geometry_hash(value)
    return value


def _source(tmp_path: Path) -> tuple[Path, dict]:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    source_path = fixture / "figure.tex"
    source_text = (
        "% figure-agent:start target.region\n"
        "\\draw (0,0) -- (1,1);\n"
        "% figure-agent:end target.region\n"
    )
    source_path.write_text(source_text, encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        "panels:\n  - id: TARGET\n    bbox_pdf_cm: [0, 0, 5, 10]\n",
        encoding="utf-8",
    )
    selector = {
        "path": "figure.tex",
        "selector_id": "target.region",
        "anchor_start": "% figure-agent:start target.region",
        "anchor_end": "% figure-agent:end target.region",
        "source_sha256": f"sha256:{hashlib.sha256(source_text.encode()).hexdigest()}",
        "line_start": 1,
        "line_end": 3,
        "binding_state": "exact",
        "binding_reason": "anchors_and_snapshot_match",
        "resolved_line_start": 1,
        "resolved_line_end": 3,
    }
    return fixture, selector


def _contract(selector: dict, regions: list[dict] | None = None, **geometry_kwargs) -> dict:
    geometry = _geometry(**geometry_kwargs)
    return {
        "schema": "figure-agent.semantic-regions.v1",
        "page_geometry": geometry,
        "regions": regions
        or [
            {
                "id": "target.region",
                "panel_id": "TARGET",
                "role": "label",
                "bbox_pdf_cm": [1.0, 1.0, 3.0, 3.0],
                "source": selector,
                "provenance": "declared_by_author",
            }
        ],
    }


def _render(geometry: dict, *, image_size: list[int] | None = None, raster_box="media_box"):
    return {
        "page_geometry": geometry,
        "image_size_px": image_size or [1000, 1000],
        "pixel_origin": "top_left",
        "raster_box": raster_box,
        "fragment_transform": [1, 0, 0, 1, 0, 0],
    }


def test_exact_attribution_preserves_detector_evidence_and_copies_valid_selector(
    tmp_path: Path,
) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(selector)
    finding = {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": 0.63}

    result = module.attribute_visual_finding(
        finding,
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["state"] == "exact"
    assert result["detector_bbox_px"] == [100.0, 700.0, 300.0, 900.0]
    assert result["detector_confidence"] == 0.63
    assert result["bbox_pdf_cm"] == pytest.approx([1.0, 1.0, 3.0, 3.0])
    assert result["panel_candidates"] == ["TARGET"]
    assert result["region_candidates"] == ["target.region"]
    assert result["source_selector"]["selector_id"] == "target.region"
    assert "tex_lines" not in result


def test_coordinate_mapping_is_dpi_invariant(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(selector)
    low = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": None},
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )
    high = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [200, 1400, 600, 1800], "confidence": None},
        detector_render=_render(contract["page_geometry"], image_size=[2000, 2000]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert high["bbox_pdf_cm"] == pytest.approx(low["bbox_pdf_cm"])


def test_overlap_is_ambiguous_without_declared_tie_breaker(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    regions = [
        {
            "id": "target.region",
            "panel_id": "TARGET",
            "role": "label",
            "bbox_pdf_cm": [1, 1, 3, 3],
            "source": selector,
            "provenance": "declared_by_author",
        },
        {
            "id": "target.annotation",
            "panel_id": "TARGET",
            "role": "annotation",
            "bbox_pdf_cm": [2, 1, 4, 3],
            "source": {**selector, "selector_id": "target.annotation"},
            "provenance": "declared_by_author",
        },
    ]
    contract = _contract(selector, regions)

    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [200, 700, 300, 900], "confidence": 0.4},
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["state"] == "ambiguous"
    assert result["region_candidates"] == ["target.annotation", "target.region"]
    assert "source_selector" not in result


def test_declared_containment_selects_the_more_specific_child(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    parent = {
        "id": "target.parent",
        "panel_id": "TARGET",
        "role": "panel_group",
        "bbox_pdf_cm": [0.5, 0.5, 4, 4],
        "contains": ["target.region"],
        "source": {**selector, "selector_id": "target.parent"},
        "provenance": "declared_by_author",
    }
    child = {
        "id": "target.region",
        "panel_id": "TARGET",
        "role": "label",
        "bbox_pdf_cm": [1, 1, 3, 3],
        "source": selector,
        "provenance": "declared_by_author",
    }
    contract = _contract(selector, [parent, child])

    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": 0.5},
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["state"] == "exact"
    assert result["region_candidates"] == ["target.region"]


def test_cropbox_rotation_and_fragment_transform_are_explicit(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(
        selector,
        media=[0, 0, 20, 10],
        crop=[5, 0, 15, 10],
        rotation=90,
    )
    contract["regions"][0]["bbox_pdf_cm"] = [5, 1, 7, 3]
    render = _render(contract["page_geometry"], raster_box="crop_box")
    render["fragment_transform"] = [1, 0, 0, 1, 100, 0]

    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [0, 100, 200, 300], "confidence": 0.5},
        detector_render=render,
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["bbox_pdf_cm"] == pytest.approx([6, 1, 8, 3])


def test_boundary_touch_and_missing_declaration_are_unbound(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(selector)

    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [300, 700, 400, 900], "confidence": None},
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["state"] == "unbound"
    assert result["region_candidates"] == []


def test_stale_source_or_render_geometry_cannot_yield_exact(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract({**selector, "source_sha256": "sha256:" + "0" * 64})
    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": 0.2},
        detector_render=_render(contract["page_geometry"]),
        semantic_contract=contract,
        fixture_dir=fixture,
    )
    assert result["state"] == "unbound"
    assert result["reason"] == "source_hash_mismatch"
    assert "source_selector" not in result

    stale_geometry = {**contract["page_geometry"], "render_geometry_hash": "sha256:" + "0" * 64}
    with pytest.raises(module.VisualFindingAttributionError, match="render_geometry_hash"):
        module.attribute_visual_finding(
            {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": 0.2},
            detector_render=_render(stale_geometry),
            semantic_contract={**contract, "page_geometry": stale_geometry},
            fixture_dir=fixture,
        )


@pytest.mark.parametrize(
    "finding",
    [
        {},
        {"id": "VC001", "bbox_px": [1, 2, 3], "confidence": 0.1},
        {"id": "VC001", "bbox_px": [3, 2, 1, 4], "confidence": 0.1},
        {"id": "VC001", "bbox_px": [1, 2, 3, 4], "confidence": "high"},
    ],
)
def test_rejects_malformed_detector_output(tmp_path: Path, finding: dict) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(selector)

    with pytest.raises(module.VisualFindingAttributionError, match="detector_finding"):
        module.attribute_visual_finding(
            finding,
            detector_render=_render(contract["page_geometry"]),
            semantic_contract=contract,
            fixture_dir=fixture,
        )


def test_page_index_mismatch_is_unbound(tmp_path: Path) -> None:
    module = _module()
    fixture, selector = _source(tmp_path)
    contract = _contract(selector, page_index=1)
    render_geometry = _geometry(page_index=0)

    result = module.attribute_visual_finding(
        {"id": "VC001", "bbox_px": [100, 700, 300, 900], "confidence": 0.1},
        detector_render=_render(render_geometry),
        semantic_contract=contract,
        fixture_dir=fixture,
    )

    assert result["state"] == "unbound"
    assert result["reason"] == "page_index_mismatch"


def test_visual_clash_result_assembly_can_attach_attribution(tmp_path: Path) -> None:
    fixture, selector = _source(tmp_path)
    contract = _contract(selector)
    pdf = fixture / "build" / "fixture.pdf"
    issue = check_visual_clash.VisualIssue(
        "near_miss",
        "label",
        "edge=0.1",
        (100, 700, 300, 900),
    )

    payload = check_visual_clash.visual_clash_payload(
        pdf,
        [issue],
        attribution_context={
            "detector_render": _render(contract["page_geometry"]),
            "semantic_contract": contract,
            "fixture_dir": fixture,
        },
    )

    candidate = payload["candidates"][0]
    assert candidate["bbox_px"] == [100, 700, 300, 900]
    assert candidate["attribution"]["state"] == "exact"
    assert candidate["attribution"]["source_selector"]["selector_id"] == "target.region"
