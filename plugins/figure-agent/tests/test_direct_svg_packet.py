from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
import yaml
from direct_svg_packet import DirectSvgPacketError, validate_packet

DENIED_SOURCE_FAMILIES = [
    "tex",
    "whole_figure_svg",
    "candidate_patch",
    "experience_log",
    "illustration_grammar",
]


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_input(root: Path, name: str, content: bytes) -> dict[str, str]:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"path": name, "sha256": _sha256(path)}


def _write_packet(
    tmp_path: Path,
    *,
    test_kind: str = "reconstruction",
    include_target_crops: bool | None = None,
) -> Path:
    if include_target_crops is None:
        include_target_crops = test_kind == "reconstruction"

    allowed_inputs: list[dict[str, str]] = []
    semantic = _write_input(tmp_path, "inputs/semantic.yaml", b"objects: []\n")
    allowed_inputs.append({"role": "semantic_packet", **semantic})
    font = _write_input(tmp_path, "inputs/font.woff2", b"licensed-font")
    allowed_inputs.append({"role": "licensed_font", **font})
    if include_target_crops:
        panel_c = _write_input(tmp_path, "inputs/panel-c.png", b"panel-c")
        panel_f = _write_input(tmp_path, "inputs/panel-f.png", b"panel-f")
        allowed_inputs.extend(
            [
                {"role": "panel_c_target_crop", **panel_c},
                {"role": "panel_f_target_crop", **panel_f},
            ]
        )

    packet: dict[str, Any] = {
        "schema": "figure-agent.direct-svg-packet.v1",
        "test_kind": test_kind,
        "panels": ["C", "F"],
        "denied_source_families": DENIED_SOURCE_FAMILIES.copy(),
        "allowed_inputs": allowed_inputs,
        "budgets": {
            "utility": {"cycles": 3, "wall_minutes_per_panel": 30},
            "ceiling": {"cycles": 8, "wall_minutes_per_panel": 120},
        },
        "model_contract": {
            "provider": "openai",
            "model": "gpt-test",
            "snapshot": None,
            "reasoning": "high",
            "prompt_paths": ["inputs/semantic.yaml"],
            "tools": ["apply_patch", "rsvg-convert"],
            "token_cap": 20000,
            "compute_cap": None,
        },
        "font": {
            "role": "licensed_font",
            "license": "OFL-1.1",
            "sha256": font["sha256"],
        },
        "publication_acceptance": "not_claimed",
    }
    packet_path = tmp_path / "packet.yaml"
    packet_path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    return packet_path


def _load_packet(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _rewrite_packet(path: Path, packet: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")


def test_reconstruction_packet_accepts_hash_bound_inputs(tmp_path: Path) -> None:
    result = validate_packet(_write_packet(tmp_path))

    assert result["schema"] == "figure-agent.direct-svg-packet.v1"
    assert result["test_kind"] == "reconstruction"
    assert result["publication_acceptance"] == "not_claimed"


def test_reconstruction_requires_target_crops(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path, include_target_crops=False)

    with pytest.raises(DirectSvgPacketError, match="target_crop_required"):
        validate_packet(packet_path)


def test_synthesis_rejects_target_or_geometry_derivatives(tmp_path: Path) -> None:
    packet_path = _write_packet(
        tmp_path,
        test_kind="synthesis",
        include_target_crops=True,
    )

    with pytest.raises(DirectSvgPacketError, match="target_crop_forbidden"):
        validate_packet(packet_path)


@pytest.mark.parametrize("family", DENIED_SOURCE_FAMILIES)
def test_packet_requires_every_denied_source_family(tmp_path: Path, family: str) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    packet["denied_source_families"].remove(family)
    _rewrite_packet(packet_path, packet)

    with pytest.raises(DirectSvgPacketError, match="denied_source_families_incomplete"):
        validate_packet(packet_path)


def test_packet_rejects_parent_path_escape(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    packet["allowed_inputs"][0]["path"] = "../semantic.yaml"
    _rewrite_packet(packet_path, packet)

    with pytest.raises(DirectSvgPacketError, match="unsafe_input_path"):
        validate_packet(packet_path)


def test_packet_rejects_input_hash_mismatch(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    packet["allowed_inputs"][0]["sha256"] = "sha256:" + "0" * 64
    _rewrite_packet(packet_path, packet)

    with pytest.raises(DirectSvgPacketError, match="input_hash_mismatch"):
        validate_packet(packet_path)


def test_packet_rejects_changed_budget(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    packet["budgets"]["utility"]["cycles"] = 4
    _rewrite_packet(packet_path, packet)

    with pytest.raises(DirectSvgPacketError, match="budget_contract_invalid"):
        validate_packet(packet_path)


def test_packet_requires_complete_model_contract(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    del packet["model_contract"]["snapshot"]
    _rewrite_packet(packet_path, packet)

    with pytest.raises(DirectSvgPacketError, match="model_contract_incomplete"):
        validate_packet(packet_path)


def test_packet_allows_additional_model_receipt_fields(tmp_path: Path) -> None:
    packet_path = _write_packet(tmp_path)
    packet = _load_packet(packet_path)
    packet["model_contract"]["runtime_version"] = "codex-test"
    _rewrite_packet(packet_path, packet)

    result = validate_packet(packet_path)

    assert result["model_contract"]["runtime_version"] == "codex-test"


def test_packet_can_resolve_declared_fixture_root_inputs(tmp_path: Path) -> None:
    packets = tmp_path / "packets"
    packets.mkdir()
    packet_path = _write_packet(packets)
    packet = _load_packet(packet_path)
    packet["path_base"] = "fixture_root"
    for item in packet["allowed_inputs"]:
        item["path"] = f"packets/{item['path']}"
    _rewrite_packet(packet_path, packet)

    result = validate_packet(packet_path)

    assert result["path_base"] == "fixture_root"
