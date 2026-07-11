from __future__ import annotations

import hashlib
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml
from direct_svg_candidate import validate_candidate
from direct_svg_packet import validate_packet

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_direct_svg_cleanroom_baseline"
RUN_ROOT = FIXTURE / "runs" / "test-b"
PACKET_PATH = FIXTURE / "packets" / "test-b-synthesis.yaml"
SEMANTIC_PATH = FIXTURE / "contract" / "semantic-packet.yaml"
PANEL_CONTRACTS = {
    "c": {
        "ids": {
            "c_polymer_film",
            "c_shallow_trap_population",
            "c_deep_trap_population",
            "c_mobility_edge",
            "c_conduction_band",
            "c_valence_band",
            "c_trap_depth",
        },
        "text": {
            "C",
            "localized traps",
            "poly(S-r-DIB) thin film",
            "d ≈ 1 μm",
            "Energy",
            "E_C",
            "mobility edge",
            "E_V",
            "shallow",
            "deep",
            "ΔE_t^d",
        },
    },
    "f": {
        "ids": {
            "f_polymer_cantilever",
            "f_fixed_support",
            "f_planar_electrode",
            "f_active_bias",
            "f_trapped_charge",
            "f_coulomb_repulsion",
            "f_air_gap",
        },
        "text": {
            "F",
            "mechanical",
            "V_active",
            "q_tr",
            "Coulomb",
            "repulsion",
            "electrode",
            "air gap",
        },
    },
}


def _load(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _panel_relations(semantic: dict[str, Any], panel: str) -> set[tuple[str, str, str, str]]:
    prefix = f"{panel}_"
    result = set()
    for relation in semantic["object_relations"]:
        subject = str(relation["subject"])
        if subject.startswith(prefix):
            result.add(
                (
                    subject,
                    str(relation["predicate"]),
                    str(relation["object"]),
                    str(relation.get("qualification", "")),
                )
            )
    return result


def _svg_relations(root: ET.Element) -> set[tuple[str, str, str, str]]:
    return {
        (
            element.attrib["data-relation-subject"],
            element.attrib["data-relation-predicate"],
            element.attrib["data-relation-object"],
            element.attrib.get("data-qualification", ""),
        )
        for element in root.iter()
        if element.attrib.get("data-coverage") == "declared-not-spatially-verified"
    }


def _assert_svg_contract(
    svg: Path,
    *,
    contract: dict[str, set[str]],
    semantic: dict[str, Any],
    panel: str,
) -> None:
    validate_candidate(svg, required_ids=contract["ids"])
    root = ET.parse(svg).getroot()
    live_text = {
        "".join(element.itertext()).strip()
        for element in root.iter()
        if _local_name(element.tag) == "text"
    }
    assert contract["text"].issubset(live_text)
    assert _svg_relations(root) == _panel_relations(semantic, panel)


def test_test_b_run_is_reproducible_semantically_complete_and_review_ready() -> None:
    packet = validate_packet(PACKET_PATH)
    semantic = _load(SEMANTIC_PATH)
    state = _load(RUN_ROOT / "run-state.yaml")

    assert packet["test_kind"] == "synthesis"
    assert state["state"] == "machine_review_ready"
    assert state["execution_started"] is True
    assert state["human_scientific_acceptance"] == "pending"
    assert state["human_visual_acceptance"] == "pending"
    assert state["publication_acceptance"] == "not_claimed"
    environment_receipt = RUN_ROOT / state["environment_receipt"]["path"]
    assert state["environment_receipt"]["sha256"] == _sha256(environment_receipt)

    artifacts_by_panel = {item["panel"].lower(): item for item in state["candidate_artifacts"]}
    assert set(artifacts_by_panel) == set(PANEL_CONTRACTS)
    for panel, contract in PANEL_CONTRACTS.items():
        panel_root = RUN_ROOT / f"panel-{panel}"
        ledger = _load(panel_root / "ledger.yaml")
        artifact = artifacts_by_panel[panel]
        assert artifact["ledger_sha256"] == _sha256(RUN_ROOT / artifact["ledger_path"])
        assert ledger["schema"] == "figure-agent.direct-svg-iteration-ledger.v1"
        assert ledger["budget"] == {"cycles": 3, "wall_minutes_per_panel": 30}
        assert ledger["publication_acceptance"] == "not_claimed"
        assert len(ledger["iterations"]) == 3

        source_hashes: set[str] = set()
        render_hashes: set[str] = set()
        for cycle, receipt in enumerate(ledger["iterations"], start=1):
            svg = RUN_ROOT / receipt["svg_path"]
            png = RUN_ROOT / receipt["png_path"]
            assert receipt["cycle"] == cycle
            assert receipt["source_sha256"] == _sha256(svg)
            assert receipt["render_sha256"] == _sha256(png)
            assert receipt["publication_acceptance"] == "not_claimed"
            assert receipt["correction_reason"]
            assert receipt["command"]
            assert all(not str(token).startswith("/") for token in receipt["command"])
            assert receipt["tool_model_receipt"]["task"] == "Task 20 Step 2 Test B"
            assert receipt["tool_model_receipt"]["method"] == "manual_llm_direct_svg"
            assert receipt["tool_model_receipt"]["tools"] == ["apply_patch", "render_candidate"]
            assert receipt["tool_model_receipt"]["reference_pixels_available"] is False
            _assert_svg_contract(
                svg,
                contract=contract,
                semantic=semantic,
                panel=panel,
            )
            source_hashes.add(receipt["source_sha256"])
            render_hashes.add(receipt["render_sha256"])
        assert len(source_hashes) == 3
        assert len(render_hashes) == 3

        final_svg = RUN_ROOT / artifacts_by_panel[panel]["svg_path"]
        final_png = RUN_ROOT / artifacts_by_panel[panel]["png_path"]
        assert artifacts_by_panel[panel]["source_sha256"] == _sha256(final_svg)
        assert artifacts_by_panel[panel]["render_sha256"] == _sha256(final_png)
        assert artifacts_by_panel[panel]["cycles"] == 3

    replay = subprocess.run(
        ["uv", "run", "python", str(RUN_ROOT / "replay.py"), "--verify"],
        cwd=PLUGIN_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert "replay verified: 6/6 deterministic renders" in replay.stdout
