from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SOURCE_MANIFEST = PLUGIN_ROOT / "benchmarks" / "hybrid_pilot_source.yaml"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "hybrid"))

from fragment_contract import FragmentContractError, validate_fragment_package  # noqa: E402


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
