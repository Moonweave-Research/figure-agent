from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_failure_first_panel_f_pilot"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from failure_ablation import evaluate_ablation  # noqa: E402
from review_evidence_pack import build_review_evidence_pack  # noqa: E402
from review_evidence_receipt import build_review_evidence_receipt  # noqa: E402
from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(relative: str) -> dict:
    return yaml.safe_load((FIXTURE / relative).read_text(encoding="utf-8"))


def test_pilot_pins_reviewed_source_and_exact_jig_authority() -> None:
    authority = _yaml("authority.yaml")
    assert authority["source"] == {
        "fixture": "fig1_overview_v5f_art_direction_001_vault",
        "commit": "7b159232959dc36ab63b08ce66e646a64bd139dd",
        "tree": "2e3696dbb04bdafacc0ba1adef334a3f7fe71f70",
        "review_state": "human_reviewed_revise",
        "historical_source_unchanged": True,
    }
    selector = authority["selector"]
    assert selector == {
        "selector_id": "panel_f.mechanism_scene",
        "anchor_start": "% figure-agent:start panel_f.mechanism_scene",
        "anchor_end": "% figure-agent:end panel_f.mechanism_scene",
        "coordinate_space": "pdf_cm",
        "page_index": 0,
        "render_geometry_hash": None,
        "review_input_hash": None,
        "hash_authority": "generated_receipt",
        "publication_acceptance": "not_claimed",
    }

    commit = authority["source"]["commit"]
    tree = subprocess.run(
        ["git", "rev-parse", f"{commit}^{{tree}}"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tree == authority["source"]["tree"]
    historical_path = (
        "plugins/figure-agent/examples/"
        "fig1_overview_v5f_art_direction_001_vault/"
        "fig1_overview_v5f_art_direction_001_vault.tex"
    )
    historical = subprocess.run(
        ["git", "show", f"{commit}:{historical_path}"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    raw = (FIXTURE / "review" / "states" / "raw.tex").read_text(encoding="utf-8")
    raw_without_anchors = raw.replace(
        "% figure-agent:start panel_f.mechanism_scene\n", ""
    ).replace("% figure-agent:end panel_f.mechanism_scene\n", "")
    assert raw_without_anchors == historical


def test_pilot_declares_semantics_and_bounded_repair_before_review() -> None:
    contract = _yaml("semantic_contract.yaml")
    assert set(contract["required_objects"]) >= {
        "panel_f.mechanical_jig",
        "panel_f.cantilever",
        "panel_f.electrode",
        "panel_f.coulomb_force",
        "panel_f.applied_voltage_cue",
    }
    assert set(contract["forbidden_implications"]) >= {
        "panel_f.ground_symbol",
        "panel_f.grounded_electrode",
        "panel_f.second_contact",
        "panel_f.electrical_contact_at_jig",
    }
    assert contract["repair"] == {
        "family": "clarify_mechanical_fixture_and_charge_encoding",
        "selector_id": "panel_f.mechanism_scene",
        "max_source_blocks": 1,
    }
    assert set(contract["protected_relations"]) >= {
        "mechanical_jig_holds_cantilever",
        "cantilever_separated_from_electrode_by_air_gap",
        "coulomb_force_points_away_from_electrode",
        "applied_voltage_cue_labels_electrode",
    }


def test_pilot_declares_role_connector_and_label_legibility() -> None:
    result = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert result["summary"]["object_role_count"] >= 5
    assert result["summary"]["visible_connector_count"] >= 3
    assert result["summary"]["forbidden_connector_count"] >= 2
    assert result["summary"]["label_ownership_count"] >= 2
    assert result["summary"]["visual_review_required"] is True
    assert result["publication_acceptance"] == "not_claimed"


def test_named_human_findings_bind_reviewed_revision_without_accepting_repair() -> None:
    findings = _yaml("review/human_findings.yaml")
    assert findings["schema"] == "figure-agent.human-reviewed-findings.v1"
    assert findings["reviewer"] == "moon"
    assert findings["reviewed_source"] == {
        "commit": "432a9573a188a79c720c204ceb3138aa29a7b5e2",
        "variant": "repaired",
        "receipt_sha256": (
            "2895ff9d57d19b083e7df313343f3a883e5aa9a20b5258c8ca92268c68b3729a"
        ),
        "review_input_hash": (
            "sha256:e28ada69677a60706505a9195f17a54a0b38ba8c9a8310f61bb02c7b5c79b877"
        ),
    }
    assert {item["id"] for item in findings["findings"]} == {
        "PF-ROLE-001",
        "PF-APPARATUS-001",
        "PF-CHARGE-001",
        "PF-LABEL-001",
        "PF-CONNECTOR-001",
    }
    assert all(
        item["review_outcome"] == "confirmed_defect"
        for item in findings["findings"]
    )
    apparatus = next(
        item for item in findings["findings"] if item["id"] == "PF-APPARATUS-001"
    )
    assert apparatus["required_correction"] == (
        "retain_an_applied_voltage_cue_without_the_incoherent_equipment_box"
    )
    assert apparatus["repair_family"] == "clarify_voltage_application"
    assert findings["revised_variant_acceptance"] == "pending"
    assert findings["publication_acceptance"] == "not_claimed"


def test_repaired_source_has_one_exact_jig_block_and_clear_voltage_cue() -> None:
    source = (FIXTURE / "fig1_failure_first_panel_f_pilot.tex").read_text(
        encoding="utf-8"
    )
    start = "% figure-agent:start panel_f.mechanism_scene"
    end = "% figure-agent:end panel_f.mechanism_scene"
    assert source.count(start) == 1
    assert source.count(end) == 1
    block = source.split(start, 1)[1].split(end, 1)[0]
    assert "small neutral mechanical jig" in block
    assert "ground" not in block.lower()
    assert "V_{\\mathrm{active}}" not in block
    assert "{bias}" not in block
    assert block.count("V_{\\mathrm{app}}") == 1
    assert "applied-voltage state cue" in block
    assert "source box" not in block.lower()
    assert "return path" not in block.lower()
    assert "(13.24, 3.76) -- (13.20, 3.38)" not in block
    assert "ball color" not in block
    assert "(11.08,2.48) .. controls" not in block
    assert "$q_{\\mathrm{tr}}$" not in block
    assert "flat trapped-charge markers" in block.lower()
    assert "{trapped charge}" in block
    assert "panelFCoulombRepulsionArrow" in source
    assert "{air gap}" in source
    assert "(13.23, 0.40) -- (13.37, 0.40)" not in source


def test_pilot_docs_require_voltage_application_without_false_circuit() -> None:
    briefing = (FIXTURE / "briefing.md").read_text(encoding="utf-8")
    caption = (FIXTURE / "caption.md").read_text(encoding="utf-8")
    assert "must show an applied-voltage cue" in briefing
    assert "does not require a full instrument box" in briefing
    assert "must not imply a ground or complete return path" in briefing
    assert "applied voltage" in caption
    assert "does not assert a grounded or complete circuit" in caption


def test_ablation_contract_is_comparable_and_stops_at_human_boundary() -> None:
    report = evaluate_ablation(
        {
            variant: FIXTURE / "review" / "ablation" / f"{variant}.yaml"
            for variant in ("raw", "verified", "repaired")
        }
    )
    assert report["variants"]["raw"]["confirmed_defect_count"] == 1
    assert report["variants"]["verified"]["confirmed_defect_count"] == 1
    assert report["variants"]["repaired"]["confirmed_defect_count"] == 0
    assert report["product_claim"] == "not_authorized"
    assert report["publication_acceptance"] == "not_claimed"
    for variant in ("raw", "verified", "repaired"):
        run = _yaml(f"review/ablation/{variant}.yaml")
        assert run["human_correction_minutes"] is None
        assert run["human_verdict"]["state"] == "pending"


def test_generated_receipt_binds_multiscale_pixel_evidence(tmp_path: Path) -> None:
    receipt = build_review_evidence_receipt(FIXTURE, tmp_path / "receipt.json")
    assert receipt["selector_id"] == "panel_f.mechanism_scene"
    assert receipt["attribution_state"] == "exact"
    assert receipt["render_geometry_hash"].startswith("sha256:")
    assert receipt["review_input_hash"].startswith("sha256:")
    assert receipt["evidence_scales"] == [
        "whole",
        "panel",
        "object_relation",
        "zoom",
    ]
    assert receipt["variants"] == ["raw", "verified", "repaired"]
    assert receipt["human_review_state"] == "pending"
    assert receipt["publication_acceptance"] == "not_claimed"
    assert json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8")) == receipt
    assert json.loads(
        (FIXTURE / "review" / "generated_receipt.json").read_text(encoding="utf-8")
    ) == receipt


def test_evidence_pack_keeps_verified_pixels_equal_to_raw(tmp_path: Path) -> None:
    fixture = tmp_path / "pilot"
    (fixture / "raw").mkdir(parents=True)
    (fixture / "repaired").mkdir()
    Image.new("RGB", (100, 80), "white").save(fixture / "raw" / "render.png")
    Image.new("RGB", (100, 80), "gray").save(
        fixture / "repaired" / "render.png"
    )
    (fixture / "evidence_regions.yaml").write_text(
        """schema: figure-agent.review-evidence-pack.v1
raw_render: raw/render.png
repaired_render: repaired/render.png
regions:
  panel: [0.1, 0.1, 0.9, 0.9]
  object_relation: [0.2, 0.2, 0.8, 0.8]
  zoom: [0.3, 0.3, 0.7, 0.7]
""",
        encoding="utf-8",
    )

    manifest = build_review_evidence_pack(fixture)

    records = {
        (item["variant"], item["role"]): item for item in manifest["artifacts"]
    }
    for role in ("whole", "panel", "object_relation", "zoom", "overlay"):
        assert records[("raw", role)]["sha256"] == records[("verified", role)][
            "sha256"
        ]
        assert records[("raw", role)]["sha256"] != records[("repaired", role)][
            "sha256"
        ]
    assert manifest["publication_acceptance"] == "not_claimed"
