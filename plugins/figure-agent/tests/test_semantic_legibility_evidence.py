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


def _selected_sha256(path: Path, line_start: int, line_end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    selected = "".join(lines[line_start - 1 : line_end]).encode()
    return f"sha256:{hashlib.sha256(selected).hexdigest()}"


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
    page_render = fixture / "page-render.png"
    Image.new("RGB", (100, 100), "white").save(page_render)
    nondeterministic_pdf = fixture / "page.pdf"
    nondeterministic_pdf.write_bytes(b"first nondeterministic PDF serialization")

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
                "selected_content_sha256": _selected_sha256(source, lines[0], lines[1]),
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
    page_render_hash = _sha256(page_render)
    legacy_page_hash = _sha256(nondeterministic_pdf)
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
            "page_render_sha256": page_render_hash,
            "page_sha256": legacy_page_hash,
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
            "page_render_path": "page-render.png",
            "page_render_sha256": page_render_hash,
            "page_index": 0,
            "page_path": "page.pdf",
            "page_sha256": legacy_page_hash,
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
    assert first["render_evidence"] == {
        "full_render": {
            "role": "canonical_full_figure_raster",
            "sha256": first["input_hashes"]["full_render_sha256"],
        },
        "page_render": {
            "role": "canonical_page_raster",
            "page_index": 0,
            "sha256": first["input_hashes"]["page_render_sha256"],
        },
    }
    assert {item["kind"] for item in first["subjects"]} == {"object", "relation"}
    for subject in first["subjects"]:
        assert subject["state"] == "exact"
        assert subject["panel_id"] == "A"
        assert subject["human_verdict"] == "pending"
        assert subject["semantic_declaration"]
        assert subject["selector_snapshot"]["selector_id"] == subject["semantic_id"]
        assert subject["hashes"]["full_render_sha256"].startswith("sha256:")
        assert subject["hashes"]["page_render_sha256"].startswith("sha256:")
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


def test_stable_page_raster_keeps_bindings_fresh_across_pdf_regeneration(
    tmp_path: Path,
) -> None:
    module = _module()
    input_path, _ = _input(tmp_path)
    output_dir = tmp_path / "packet"

    first = module.compile_semantic_legibility_evidence(input_path, output_dir)
    (input_path.parent / "page.pdf").write_bytes(
        b"second nondeterministic PDF serialization with different metadata"
    )
    second = module.compile_semantic_legibility_evidence(input_path, output_dir)

    assert {subject["state"] for subject in first["subjects"]} == {"exact"}
    assert second == first
    assert second["input_hashes"]["page_render_sha256"] == _sha256(
        input_path.parent / "page-render.png"
    )


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing_anchor", "source_anchor_missing"),
        ("duplicate_anchor", "source_anchor_duplicate"),
        ("stale_lines", "source_line_snapshot_stale"),
        ("stale_content", "source_selected_content_hash_mismatch"),
    ],
)
def test_exact_binding_validates_source_selector_snapshot(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    regions_path = input_path.parent / "semantic_regions.yaml"
    regions = yaml.safe_load(regions_path.read_text(encoding="utf-8"))
    source = input_path.parent / "figure.tex"
    selector = regions["regions"][0]["source"]
    if mutation == "missing_anchor":
        selector["anchor_start"] = "% absent anchor"
    elif mutation == "duplicate_anchor":
        source.write_text(
            source.read_text(encoding="utf-8") + "% figure-agent:start trap_site\n",
            encoding="utf-8",
        )
        new_hash = _sha256(source)
        for region in regions["regions"]:
            region["source"]["source_sha256"] = new_hash
    elif mutation == "stale_lines":
        selector["line_start"] = 2
    else:
        selector["selected_content_sha256"] = "sha256:" + "0" * 64
    _write_yaml(regions_path, regions)
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    subject = next(item for item in packet["subjects"] if item["semantic_id"] == "trap_site")
    assert subject["state"] == "unbound"
    assert subject["review_disposition"] == "review_only"
    assert subject["reason"] == reason
    assert "crop" not in subject


def test_declared_detector_image_size_must_match_actual_raster(tmp_path: Path) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    payload["render"]["detector_render"]["image_size_px"] = [101, 100]
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    assert {subject["state"] for subject in packet["subjects"]} == {"unbound"}
    assert {subject["reason"] for subject in packet["subjects"]} == {"render_image_size_mismatch"}


def test_mid_compile_failure_preserves_prior_packet_generated_crops_and_human_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module()
    input_path, _ = _input(tmp_path)
    output_dir = tmp_path / "packet"
    first = module.compile_semantic_legibility_evidence(input_path, output_dir)
    note = output_dir / "crops" / "reviewer-note.txt"
    note.write_text("human-owned", encoding="utf-8")
    prior_packet = (output_dir / "packet.json").read_bytes()
    prior_crops = {
        subject["crop"]["path"]: (output_dir / subject["crop"]["path"]).read_bytes()
        for subject in first["subjects"]
    }
    calls = 0
    original = module.draw_attribution_box

    def fail_on_second(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected staging failure")
        original(*args, **kwargs)

    monkeypatch.setattr(module, "draw_attribution_box", fail_on_second)

    with pytest.raises(RuntimeError, match="injected staging failure"):
        module.compile_semantic_legibility_evidence(input_path, output_dir)

    assert (output_dir / "packet.json").read_bytes() == prior_packet
    assert note.read_text(encoding="utf-8") == "human-owned"
    assert {path: (output_dir / path).read_bytes() for path in prior_crops} == prior_crops


def test_symlink_output_is_rejected_without_touching_target(tmp_path: Path) -> None:
    module = _module()
    input_path, _ = _input(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("untouched", encoding="utf-8")
    output_dir = tmp_path / "packet"
    output_dir.mkdir()
    (output_dir / "crops").symlink_to(outside, target_is_directory=True)

    with pytest.raises(module.SemanticLegibilityEvidenceError, match="output_symlink"):
        module.compile_semantic_legibility_evidence(input_path, output_dir)

    assert sentinel.read_text(encoding="utf-8") == "untouched"


@pytest.mark.parametrize(
    ("mutation", "state", "reason"),
    [
        ("missing", "unbound", "authority_claim_missing"),
        ("duplicate_id", "blocked_authority_conflict", "authority_provenance_duplicate"),
    ],
)
def test_exact_subject_requires_unique_authority_provenance(
    tmp_path: Path, mutation: str, state: str, reason: str
) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    if mutation == "missing":
        payload["authority_claims"] = [
            claim for claim in payload["authority_claims"] if claim["semantic_id"] != "trap_site"
        ]
    else:
        payload["authority_claims"].append(dict(payload["authority_claims"][0]))
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    subject = next(item for item in packet["subjects"] if item["semantic_id"] == "trap_site")
    assert subject["state"] == state
    assert subject["review_disposition"] == "review_only"
    assert subject["reason"] == reason


def test_unknown_authority_claim_subject_emits_unbound_diagnostic(tmp_path: Path) -> None:
    module = _module()
    input_path, payload = _input(tmp_path)
    payload["authority_claims"].append(
        {
            "semantic_id": "not_a_declared_subject",
            "authority_id": "maintained_contract",
            "claim": "unknown claim",
        }
    )
    _write_yaml(input_path, payload)

    packet = module.compile_semantic_legibility_evidence(input_path, tmp_path / "packet")

    assert packet["authority_diagnostics"] == [
        {
            "semantic_id": "not_a_declared_subject",
            "state": "unbound",
            "review_disposition": "review_only",
            "reason": "authority_claim_subject_unknown",
        }
    ]


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
    assert packet["input_hashes"]["page_render_sha256"] == (
        "sha256:5a87f8028a20439fecab2491c7114163dec33d77e05290ad80003f830e331947"
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
