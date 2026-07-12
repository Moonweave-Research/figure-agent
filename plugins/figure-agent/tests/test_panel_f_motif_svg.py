from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from panel_f_motif_svg import ContractError, render_pilot, render_svg  # noqa: E402

CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
PILOT = PLUGIN_ROOT / "examples/fig1_panel_f_svg_backend_pilot"
NS = {"svg": "http://www.w3.org/2000/svg"}


def _normalized_png_hash(path: Path) -> str:
    with Image.open(path) as image:
        pixels = image.convert("RGBA").tobytes()
        header = f"{image.width}x{image.height}:RGBA:".encode()
    return hashlib.sha256(header + pixels).hexdigest()


def test_render_svg_is_editable_semantic_fragment() -> None:
    svg = render_svg(CONTRACT, instance_id="pilot")
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["data-fragment-role"] == "panel-f-motif"

    required = {
        "fixed-boundary",
        "floating-cantilever",
        "driven-electrode",
        "voltage-source",
        "source-ground",
        "electrical-leads",
        "gap-guides",
        "trapped-charge",
    }
    groups = {item.attrib["id"] for item in root.findall(".//svg:g", NS)}
    assert {f"pilot-{name}" for name in required} <= groups
    assert all(item.startswith("pilot-") for item in groups)

    serialized = svg.lower()
    for forbidden in ("<image", "<script", "<filter"):
        assert forbidden not in serialized
    assert not root.findall(".//*[@href]")
    assert not root.findall(".//*[@{http://www.w3.org/1999/xlink}href]")
    for forbidden in ("coulomb", "force-arrow", "panel-letter", "whole-panel"):
        assert forbidden not in serialized


def test_render_svg_declares_relation_endpoints_and_connector_roles() -> None:
    root = ET.fromstring(render_svg(CONTRACT, instance_id="relation"))
    connectors = root.findall(".//svg:g[@data-connector-role]", NS)
    records = {
        item.attrib["data-relation"]: (
            item.attrib["data-from"],
            item.attrib["data-to"],
            item.attrib["data-connector-role"],
        )
        for item in connectors
    }
    assert records == {
        "mechanical_attachment": (
            "relation-fixed-boundary",
            "relation-floating-cantilever",
            "mechanical",
        ),
        "electrode_drive": (
            "relation-voltage-source",
            "relation-driven-electrode",
            "electrical-drive",
        ),
        "source_return": (
            "relation-voltage-source",
            "relation-source-ground",
            "electrical-return",
        ),
        "trapped_charge_ownership": (
            "relation-trapped-charge",
            "relation-floating-cantilever",
            "ownership",
        ),
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda data: data["objects"].pop("floating_cantilever"), "required objects"),
        (
            lambda data: data["connectors"]["electrode_drive"].update(role="mechanical"),
            "connector roles",
        ),
        (lambda data: data["relations"].clear(), "required relations"),
        (lambda data: data.update(forbidden_connections=[]), "forbidden connection"),
    ],
)
def test_contract_drift_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    mutation(data)
    drifted = tmp_path / "contract.yaml"
    drifted.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ContractError, match=message):
        render_svg(drifted, instance_id="drift")


def test_pilot_replays_are_byte_and_pixel_deterministic(tmp_path: Path) -> None:
    first = render_pilot(tmp_path / "first")
    second = render_pilot(tmp_path / "second")
    assert first["svg_sha256"] == second["svg_sha256"]
    assert first["png_pixel_sha256"] == second["png_pixel_sha256"]
    assert (tmp_path / "first/motif.svg").read_bytes() == (
        tmp_path / "second/motif.svg"
    ).read_bytes()
    assert _normalized_png_hash(tmp_path / "first/motif.png") == _normalized_png_hash(
        tmp_path / "second/motif.png"
    )


def test_committed_pilot_is_complete_and_verifiable() -> None:
    required = {
        "authority.yaml",
        "motif.svg",
        "motif.png",
        "tikz_baseline.png",
        "comparison.png",
        "receipt.json",
        "human_review.yaml",
    }
    assert required <= {path.name for path in PILOT.iterdir()}
    authority = yaml.safe_load((PILOT / "authority.yaml").read_text(encoding="utf-8"))
    assert authority["contract"] == "styles/snippets/panel-f-floating-cantilever.contract.yaml"
    assert authority["tikz_baseline"] == (
        "examples/fig1_failure_first_panel_f_pilot/build/panel_crops/F.png"
    )
    review = yaml.safe_load((PILOT / "human_review.yaml").read_text(encoding="utf-8"))
    assert review["semantic_legibility_verdict"] == "pending"
    assert review["visual_quality_vs_tikz"] == "pending"
    assert review["publication_acceptance"] == "not_claimed"
    receipt = json.loads((PILOT / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["publication_acceptance"] == "not_claimed"
    assert receipt["comparison_boundary"] == "equal_pixel_canvas"

    result = subprocess.run(
        [sys.executable, "scripts/panel_f_motif_svg.py", "verify", str(PILOT)],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "verified" in result.stdout.lower()
