from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SOURCE_MANIFEST = PLUGIN_ROOT / "benchmarks" / "hybrid_pilot_source.yaml"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "hybrid"))

from critique_zoom_crops import build_zoom_crop_pack  # noqa: E402
from fragment_contract import FragmentContractError, validate_fragment_package  # noqa: E402
from semantic_region_contract import load_semantic_region_contract  # noqa: E402
from visual_finding_attribution import attribute_visual_finding  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_hybrid_pilot_source_is_a_complete_tracked_provenance_gate() -> None:
    payload = yaml.safe_load(SOURCE_MANIFEST.read_text(encoding="utf-8"))

    assert payload["schema"] == "figure-agent.hybrid-pilot-source.v1"
    assert payload["gate"] == "passed"
    assert payload["source_fixture"] == "fig1_overview_v2_pair_001_vault"
    assert "dogfood_001" not in payload["source_fixture"]
    source_commit = payload["source_commit"]
    source_tree = payload["source_tree"]
    tree_path = f"plugins/figure-agent/examples/{payload['source_fixture']}"
    actual_tree = subprocess.run(
        ["git", "rev-parse", f"{source_commit}:{tree_path}"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert actual_tree == source_tree

    roles = {item["role"] for item in payload["inputs"]}
    assert {"editable_tex", "briefing", "spec", "authoring_plan", "reference_pack"} <= roles
    for item in payload["inputs"]:
        path = PLUGIN_ROOT / item["path"]
        assert path.is_file()
        assert item["sha256"] == f"sha256:{_sha256(path)}"

    baseline = payload["baseline_reproduction"]
    assert baseline["clean_checkout"] is True
    assert baseline["compile_exit"] == 0
    assert baseline["fixed_raster_repeatable"] is True
    assert baseline["pdf_bytes_repeatable"] is False
    assert baseline["raster_sha256"].startswith("sha256:")
    assert payload["publication_acceptance"] == "not_claimed"


def _write_fragment_package(tmp_path: Path, svg: str) -> Path:
    fragment_dir = tmp_path / "fragments"
    fragment_dir.mkdir()
    generator = fragment_dir / "generator.py"
    generator.write_text("print('deterministic generator')\n", encoding="utf-8")
    svg_path = fragment_dir / "fragment.svg"
    svg_path.write_text(svg, encoding="utf-8")
    pdf_path = fragment_dir / "fragment.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nsemantic fragment\n")
    manifest = {
        "schema": "figure-agent.semantic-fragment.v1",
        "view_box": [0, 0, 200, 120],
        "semantic_objects": [
            {"id": "trap.shallow", "role": "trap_site"},
            {"id": "trap.deep", "role": "trap_site"},
        ],
        "relations": [
            {"subject": "trap.shallow", "predicate": "shallower_than", "object": "trap.deep"}
        ],
        "ownership": {
            "svg": ["complex_geometry"],
            "tikz": ["global_panel_composition", "text_labels", "inter_panel_arrows"],
        },
        "generator": {
            "path": "generator.py",
            "sha256": f"sha256:{_sha256(generator)}",
        },
        "inputs": [],
        "assets": [],
        "artifacts": {
            "svg": {"path": "fragment.svg", "sha256": f"sha256:{_sha256(svg_path)}"},
            "pdf": {"path": "fragment.pdf", "sha256": f"sha256:{_sha256(pdf_path)}"},
        },
        "toolchain": {"python": "3.12", "svg_to_pdf": "rsvg-convert"},
        "publication_acceptance": "not_claimed",
    }
    manifest_path = fragment_dir / "fragment_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_fragment_contract_accepts_declared_ids_relations_and_ownership(
    tmp_path: Path,
) -> None:
    manifest = _write_fragment_package(
        tmp_path,
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
        '<g id="trap.shallow" data-semantic="true"><circle cx="40" cy="40" r="8"/></g>'
        '<g id="trap.deep" data-semantic="true"><circle cx="140" cy="80" r="8"/></g>'
        "</svg>",
    )

    result = validate_fragment_package(manifest)

    assert result["semantic_ids"] == ["trap.deep", "trap.shallow"]
    assert result["publication_acceptance"] == "not_claimed"


def test_fragment_contract_rejects_orphaned_manifest_semantic_id(tmp_path: Path) -> None:
    manifest = _write_fragment_package(
        tmp_path,
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
        '<g id="trap.shallow" data-semantic="true"/>'
        "</svg>",
    )

    with pytest.raises(FragmentContractError, match="semantic_id_mismatch"):
        validate_fragment_package(manifest)


@pytest.mark.parametrize(
    ("unsafe_svg", "message"),
    [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120"><script/></svg>',
            "script_forbidden",
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
            '<g onload="alert(1)"/></svg>',
            "event_handler_forbidden",
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
            '<image href="https://example.com/a.png"/></svg>',
            "external_url_forbidden",
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 120">'
            "<style>text{font-family:sans}</style></svg>",
            "ambient_style_forbidden",
        ),
    ],
)
def test_fragment_contract_rejects_unsafe_svg_features(
    tmp_path: Path,
    unsafe_svg: str,
    message: str,
) -> None:
    manifest = _write_fragment_package(tmp_path, unsafe_svg)

    with pytest.raises(FragmentContractError, match=message):
        validate_fragment_package(manifest)


@pytest.mark.parametrize(
    "manifest",
    [
        "examples/fig1_hybrid_complex_panel_pilot/fragments/fragment_manifest.json",
        "examples/fig3_trap_schematic_slice3_semantic/fragments/fragment_manifest.json",
    ],
)
def test_fragment_contract_generalizes_across_fig1_and_fig3(manifest: str) -> None:
    result = validate_fragment_package(PLUGIN_ROOT / manifest)
    assert result["publication_acceptance"] == "not_claimed"
    assert result["semantic_ids"]


def test_fig3_semantic_regions_refuse_drifted_source_attribution_without_fig1_imports(
    tmp_path: Path,
) -> None:
    fixture = PLUGIN_ROOT / "examples" / "fig3_trap_schematic_slice3_semantic"
    regions = yaml.safe_load((fixture / "semantic_regions.yaml").read_text(encoding="utf-8"))
    fragment = validate_fragment_package(fixture / "fragments" / "fragment_manifest.json")

    contract = load_semantic_region_contract(fixture)
    assert {item["id"] for item in regions["semantic_objects"]} == set(fragment["semantic_ids"])
    assert contract["regions"][0]["source"]["binding_state"] == "exact"

    finding = {"id": "slice3-panel-e-probe", "bbox_px": [2100, 1900, 2300, 2100]}
    detector_render = {
        "page_geometry": contract["page_geometry"],
        "pixel_origin": "top_left",
        "image_size_px": [4457, 2894],
        "fragment_transform": [1, 0, 0, 1, 0, 0],
        "raster_box": "media_box",
    }
    tex_name = "fig3_trap_schematic_slice3_semantic.tex"

    # Genuine historical-drift refusal: the contract hash-binds the region to the
    # source bytes it was captured from. Drift the .tex so its sha256 no longer
    # matches the bound source_sha256 and confirm the attributor refuses to bind
    # (rather than mis-attributing to a now-stale region) while still surfacing
    # the geometric region candidate. Hermetic: only the attribution inputs the
    # producer reads (spec.yaml + the source .tex) are copied into tmp_path.
    drifted = tmp_path / fixture.name
    drifted.mkdir(parents=True)
    shutil.copyfile(fixture / "spec.yaml", drifted / "spec.yaml")
    (drifted / tex_name).write_bytes(
        (fixture / tex_name).read_bytes() + b"\n% drifted after contract capture\n"
    )

    attribution = attribute_visual_finding(
        finding,
        detector_render=detector_render,
        semantic_contract=contract,
        fixture_dir=drifted,
    )
    assert attribution["state"] == "unbound"
    assert attribution["reason"] == "source_hash_mismatch"
    assert attribution["region_candidates"] == ["e.structural_origin_fragment"]

    patterns = regions["forbidden_import_patterns"]
    derivative_sources = [fixture / tex_name]
    derivative_sources.extend((fixture / "fragments").glob("*.py"))
    for source in derivative_sources:
        contents = source.read_text(encoding="utf-8").lower()
        assert all(pattern.lower() not in contents for pattern in patterns)


def test_fig3_full_render_and_panel_e_use_general_zoom_crop_contract(tmp_path: Path) -> None:
    source = PLUGIN_ROOT / "examples" / "fig3_trap_schematic_slice3_semantic"
    fixture = tmp_path / source.name
    render = fixture / "review" / "full-render.png"
    panel = fixture / "review" / "panel-e-render.png"
    render.parent.mkdir(parents=True)
    shutil.copyfile(source / "review" / "full-render.png", render)
    shutil.copyfile(source / "review" / "panel-e-render.png", panel)

    crops = build_zoom_crop_pack(fixture, render, panel_crop_paths=(panel,))

    crop_ids = {item["id"] for item in crops}
    assert {"full_q1", "full_q2", "full_q3", "full_q4"} <= crop_ids
    assert any(item.startswith("panel_panel-e-render_s") for item in crop_ids)
    manifest = fixture / "build" / "audit_crops" / "manifest.json"
    assert manifest.is_file()
    assert json.loads(manifest.read_text(encoding="utf-8"))["fixture"] == fixture.name
