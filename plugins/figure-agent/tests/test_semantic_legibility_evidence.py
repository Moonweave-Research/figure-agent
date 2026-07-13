from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_region_contract import render_geometry_hash  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "quality" / "semantic_legibility_evidence.py"


def _module():
    try:
        return importlib.import_module("semantic_legibility_evidence")
    except ModuleNotFoundError:
        pytest.fail("scripts/quality/semantic_legibility_evidence.py should exist")


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _input(tmp_path: Path) -> tuple[Path, dict]:
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    source = fixture / "figure.tex"
    source.write_text(
        "% figure-agent:start trap_site\ntrap site\n% figure-agent:end trap_site\n"
        "% figure-agent:start capture_event\ncapture event\n"
        "% figure-agent:end capture_event\n"
        "% figure-agent:start voltage_relation\nvoltage relation\n"
        "% figure-agent:end voltage_relation\n",
        encoding="utf-8",
    )
    (fixture / "spec.yaml").write_text(
        "panels:\n  - id: A\n    bbox_pdf_cm: [0, 0, 10, 10]\n",
        encoding="utf-8",
    )
    render = fixture / "render.png"
    Image.new("RGB", (100, 100), "white").save(render)
    page = fixture / "page.pdf"
    page.write_bytes(b"immutable page bytes")

    geometry = {
        "coordinate_space": "pdf_cm",
        "page_index": 0,
        "origin": "bottom_left",
        "media_box_pdf_cm": [0.0, 0.0, 10.0, 10.0],
        "crop_box_pdf_cm": [0.0, 0.0, 10.0, 10.0],
        "rotation_deg": 0,
    }
    geometry["render_geometry_hash"] = render_geometry_hash(geometry)
    source_hash = _sha256(source)

    def region(semantic_id: str, bbox_pdf_cm: list[float], lines: tuple[int, int]) -> dict:
        return {
            "id": semantic_id,
            "panel_id": "A",
            "role": "semantic_subject",
            "bbox_pdf_cm": bbox_pdf_cm,
            "source": {
                "path": "figure.tex",
                "selector_id": semantic_id,
                "anchor_start": f"% figure-agent:start {semantic_id}",
                "anchor_end": f"% figure-agent:end {semantic_id}",
                "source_sha256": source_hash,
                "line_start": lines[0],
                "line_end": lines[1],
                "resolved_line_start": lines[0],
                "resolved_line_end": lines[1],
                "binding_state": "exact",
                "binding_reason": "anchors_and_snapshot_match",
            },
            "provenance": "declared_by_author",
        }

    semantic_regions = {
        "schema": "figure-agent.semantic-regions.v1",
        "page_geometry": geometry,
        "regions": [
            region("trap_site", [1, 1, 3, 3], (1, 3)),
            region("capture_event", [4, 1, 6, 3], (4, 6)),
            region("voltage_relation", [1, 5, 6, 7], (7, 9)),
        ],
    }
    _write_yaml(fixture / "semantic_regions.yaml", semantic_regions)

    semantic_contract = {
        "schema": "figure-agent.failure-first-semantic-contract.v1",
        "fixture": "fixture",
        "required_objects": [
            "trap_site",
            "capture_event",
            "electrode_left",
            "electrode_right",
        ],
        "semantic_legibility": {
            "object_roles": [
                {
                    "object_id": "trap_site",
                    "declared_role": "trap_site",
                    "forbidden_readings": ["capture_event"],
                },
                {
                    "object_id": "capture_event",
                    "declared_role": "capture_event",
                    "forbidden_readings": ["trap_site"],
                },
                {
                    "object_id": "electrode_left",
                    "declared_role": "electrode",
                    "forbidden_readings": [],
                },
                {
                    "object_id": "electrode_right",
                    "declared_role": "electrode",
                    "forbidden_readings": [],
                },
            ],
            "visible_connectors": [
                {
                    "connector_id": "voltage_relation",
                    "from_object": "electrode_left",
                    "to_object": "electrode_right",
                    "declared_role": "electrical_bias_lead",
                    "render_style": "electrical_bias_lead",
                }
            ],
            "forbidden_connectors": [],
            "label_ownership": [],
            "electrical_topology": {
                "nodes": [
                    {"object_id": "electrode_left", "declared_state": "source"},
                    {
                        "object_id": "electrode_right",
                        "declared_state": "ground_reference",
                    },
                ],
                "connections": [
                    {
                        "connection_id": "voltage_relation",
                        "from_object": "electrode_left",
                        "to_object": "electrode_right",
                        "declared_role": "electrical_bias_lead",
                    }
                ],
            },
        },
        "publication_acceptance": "not_claimed",
    }
    _write_yaml(fixture / "semantic_contract.yaml", semantic_contract)

    full_hash = _sha256(render)
    page_hash = _sha256(page)
    subjects = [
        {
            "semantic_id": "trap_site",
            "kind": "object",
            "bbox_px": [10, 70, 30, 90],
            "expected_readings": ["gray cross is an available trap site"],
            "forbidden_readings": ["gray cross is a capture event"],
        },
        {
            "semantic_id": "capture_event",
            "kind": "object",
            "bbox_px": [40, 70, 60, 90],
            "expected_readings": ["red ring is a capture event"],
            "forbidden_readings": ["red ring is a trap site"],
        },
        {
            "semantic_id": "voltage_relation",
            "kind": "relation",
            "bbox_px": [10, 30, 60, 50],
            "expected_readings": ["V is connected to both electrodes"],
            "forbidden_readings": ["V is decorative or owns one electrode only"],
        },
    ]
    bindings = [
        {
            "semantic_id": item["semantic_id"],
            "region_id": item["semantic_id"],
            "binding_state": "exact",
            "full_render_sha256": full_hash,
            "page_sha256": page_hash,
        }
        for item in subjects
    ]
    payload = {
        "schema": "figure-agent.semantic-legibility-evidence-input.v1",
        "fixture_dir": ".",
        "semantic_contract": "semantic_contract.yaml",
        "semantic_regions": "semantic_regions.yaml",
        "render": {
            "full_render_path": "render.png",
            "full_render_sha256": full_hash,
            "page_path": "page.pdf",
            "page_sha256": page_hash,
            "detector_render": {
                "page_geometry": geometry,
                "image_size_px": [100, 100],
                "pixel_origin": "top_left",
                "raster_box": "media_box",
                "fragment_transform": [1, 0, 0, 1, 0, 0],
            },
        },
        "subjects": subjects,
        "bindings": bindings,
        "authority_claims": [
            {
                "semantic_id": item["semantic_id"],
                "authority_id": "maintained_contract",
                "claim": item["expected_readings"][0],
            }
            for item in subjects
        ],
        "required_distinctions": [
            {
                "question_id": "trap_site_vs_capture_event",
                "semantic_ids": ["trap_site", "capture_event"],
                "question": (
                    "Are gray crosses visually distinct from red rings as trap sites "
                    "versus capture events?"
                ),
            }
        ],
        "human_review_questions": [
            {
                "question_id": "voltage_both_electrodes",
                "semantic_ids": ["voltage_relation"],
                "question": "Does V read as connected to both electrodes?",
            }
        ],
        "semantic_preservation": "not_claimed_pending_human_review",
        "publication_acceptance": "not_claimed",
    }
    input_path = fixture / "input.yaml"
    _write_yaml(input_path, payload)
    return input_path, payload


def test_conflicting_normalized_authority_claims_block_subject(tmp_path: Path) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    payload["authority_claims"].append(
        {
            "semantic_id": "trap_site",
            "authority_id": "briefing",
            "claim": "  RED RING is a capture event  ",
        }
    )
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    subject = next(item for item in packet["subjects"] if item["semantic_id"] == "trap_site")
    assert subject["state"] == "blocked_authority_conflict"
    assert subject["review_disposition"] == "review_only"
    assert subject["normalized_authority_claims"] == [
        "gray cross is an available trap site",
        "red ring is a capture event",
    ]
    assert "crop" not in subject


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "binding_missing"),
        ("stale", "binding_stale"),
        ("duplicate", "binding_duplicate"),
        ("render_hash", "full_render_hash_mismatch"),
    ],
)
def test_invalid_render_object_selector_bindings_fail_closed(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    binding = payload["bindings"][0]
    if mutation == "missing":
        payload["bindings"].pop(0)
    elif mutation == "stale":
        binding["binding_state"] = "stale"
    elif mutation == "duplicate":
        payload["bindings"].append(dict(binding))
    else:
        binding["full_render_sha256"] = "sha256:" + "0" * 64
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    subject = next(item for item in packet["subjects"] if item["semantic_id"] == "trap_site")
    assert subject["state"] == "unbound"
    assert subject["review_disposition"] == "review_only"
    assert subject["reason"] == reason
    assert "crop" not in subject


def test_exact_bindings_emit_deterministic_human_review_evidence(
    tmp_path: Path,
) -> None:
    module = _module()
    input_path, _ = _input(tmp_path)
    output_dir = tmp_path / "packet"

    first = module.compile_semantic_legibility_evidence(input_path, output_dir)
    second = module.compile_semantic_legibility_evidence(input_path, output_dir)

    assert first == second
    assert first["schema"] == "figure-agent.semantic-legibility-evidence.v1"
    assert first["review_input_hash"].startswith("sha256:")
    assert first["human_verdict"] == "pending"
    assert first["semantic_preservation"] == "not_claimed_pending_human_review"
    assert first["publication_acceptance"] == "not_claimed"
    assert {item["kind"] for item in first["subjects"]} == {"object", "relation"}
    for subject in first["subjects"]:
        assert subject["state"] == "exact"
        assert subject["panel_id"] == "A"
        assert subject["human_verdict"] == "pending"
        assert subject["semantic_declaration"]
        assert subject["selector_snapshot"]["selector_id"] == subject["semantic_id"]
        assert subject["hashes"]["full_render_sha256"].startswith("sha256:")
        assert subject["hashes"]["page_sha256"].startswith("sha256:")
        assert subject["hashes"]["crop_sha256"].startswith("sha256:")
        assert subject["coordinate_space"]["name"] == "pdf_cm"
        assert subject["expected_readings"]
        assert subject["forbidden_readings"]
        assert (output_dir / subject["crop"]["path"]).is_file()

    distinction = next(
        question
        for question in first["human_review_questions"]
        if question["question_id"] == "trap_site_vs_capture_event"
    )
    assert distinction["question_kind"] == "required_visual_distinction"
    assert distinction["status"] == "pending"
    assert distinction["semantic_ids"] == ["trap_site", "capture_event"]
    assert json.loads((output_dir / "packet.json").read_text(encoding="utf-8")) == first


def test_cli_writes_packet_and_preserves_non_acceptance_boundary(tmp_path: Path) -> None:
    input_path, _ = _input(tmp_path)
    output_dir = tmp_path / "packet"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(input_path), str(output_dir), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["semantic_preservation"] == "not_claimed_pending_human_review"
    assert payload["publication_acceptance"] == "not_claimed"
    assert payload["human_verdict"] == "pending"


def test_recompile_preserves_unrelated_output_files(tmp_path: Path) -> None:
    module = _module()
    input_path, _ = _input(tmp_path)
    output_dir = tmp_path / "packet"
    output_dir.mkdir()
    note = output_dir / "reviewer-note.txt"
    note.write_text("human-owned", encoding="utf-8")

    module.compile_semantic_legibility_evidence(input_path, output_dir)

    assert note.read_text(encoding="utf-8") == "human-owned"


def test_fig3_v12_packet_is_hash_bound_and_blocks_s60_conflict() -> None:
    review_dir = (
        PLUGIN_ROOT
        / "examples"
        / "fig3_resistance_mechanism"
        / "review"
        / "failure-first"
        / "semantic-review-v12"
    )
    packet = json.loads((review_dir / "packet" / "packet.json").read_text(encoding="utf-8"))
    v12 = review_dir.parent / "execution-repair-v12"

    assert packet["input_hashes"]["full_render_sha256"] == (
        "sha256:5a87f8028a20439fecab2491c7114163dec33d77e05290ad80003f830e331947"
    )
    assert packet["input_hashes"]["page_sha256"] == (
        "sha256:f1b75edf06aca9619a22532d96136d5878c9eb51f3d2bd659589cc3ba5ce7bdb"
    )
    source_hashes = {
        subject.get("selector_snapshot", {}).get("source_sha256")
        for subject in packet["subjects"]
        if subject["state"] == "exact"
    }
    assert source_hashes == {_sha256(v12 / "repaired_generated.tex")}
    assert packet["subjects"][-1] == {
        "expected_readings": ["S60 is a discrete low-sulfur trap distribution"],
        "forbidden_readings": ["S60 is a continuous broad distribution"],
        "kind": "object",
        "normalized_authority_claims": [
            "s60 is a discrete shallow and deep distribution",
            "s60 is a discrete single deep distribution",
        ],
        "reason": "conflicting_normalized_authority_claims",
        "review_disposition": "review_only",
        "semantic_id": "s60_distribution",
        "state": "blocked_authority_conflict",
    }
    questions = {item["question_id"]: item for item in packet["human_review_questions"]}
    assert questions["voltage_connected_to_both_electrodes"]["status"] == "pending"
    assert questions["trap_sites_vs_capture_events"]["status"] == "pending"
    assert questions["breadth_vs_magnitude"]["status"] == "pending"
    assert questions["s60_distribution_authority"]["status"] == "blocked"
    assert packet["semantic_preservation"] == "not_claimed_pending_human_review"
    assert packet["publication_acceptance"] == "not_claimed"
