from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image, ImageChops

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from panel_f_motif_svg import (  # noqa: E402
    ContractError,
    _normalize_content_boundary,
    audit_svg_semantics,
    render_pilot,
    render_svg,
    verify_pilot,
)

CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
PILOT = PLUGIN_ROOT / "examples/fig1_panel_f_svg_backend_pilot"
NS = {"svg": "http://www.w3.org/2000/svg"}
RENDER_TOOLS = ("rsvg-convert", "lualatex", "pdftoppm")
missing_render_tools = [tool for tool in RENDER_TOOLS if shutil.which(tool) is None]
requires_render_tools = pytest.mark.skipif(
    bool(missing_render_tools),
    reason=f"render test requires tools on PATH: {', '.join(missing_render_tools)}",
)


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
            "electrical",
        ),
        "source_return": (
            "relation-voltage-source",
            "relation-source-ground",
            "electrical",
        ),
    }
    ownership = root.find(".//svg:g[@data-relation-role='owned_by']", NS)
    assert ownership is not None
    assert ownership.attrib["data-relation"] == "trapped_charge_ownership"


def test_render_svg_declares_exact_contract_object_set() -> None:
    root = ET.fromstring(render_svg(CONTRACT, instance_id="objects"))
    assert {
        item.attrib["data-object"]
        for item in root.findall(".//svg:g[@data-object]", NS)
    } == {
        "fixed_mechanical_boundary",
        "floating_cantilever",
        "driven_electrode",
        "voltage_source",
        "ground",
        "gap_guides",
        "trapped_charge",
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
        (
            lambda data: data["relations"].update(
                unexpected={
                    "subject": "ground",
                    "role": "near",
                    "object": "driven_electrode",
                }
            ),
            "relation set",
        ),
        (lambda data: data["owns"].append("unexpected_object"), "owns set"),
        (lambda data: data.update(schema_version=2), "contract envelope"),
        (lambda data: data.update(motif="other"), "contract envelope"),
        (lambda data: data.update(renderer="svg"), "contract envelope"),
        (
            lambda data: data["forbidden_connections"].append(
                ["ground", "driven_electrode"]
            ),
            "forbidden connection set",
        ),
        (lambda data: data.update(forbidden_connections=[]), "forbidden connection"),
        (
            lambda data: data["objects"]["voltage_source"].update(electrical_state="floating"),
            "object states",
        ),
        (
            lambda data: data["objects"]["ground"].update(electrical_state="driven"),
            "object states",
        ),
        (
            lambda data: data["objects"]["trapped_charge"].update(electrical_state="floating"),
            "object states",
        ),
        (
            lambda data: data["connectors"].update(
                unexpected={
                    "role": "electrical",
                    "connects": ["ground", "driven_electrode"],
                }
            ),
            "connector set",
        ),
        (
            lambda data: data["connectors"].update(
                sample_ground={
                    "role": "electrical",
                    "connects": ["ground", "floating_cantilever"],
                }
            ),
            "forbidden connection",
        ),
    ],
)
def test_contract_drift_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    mutation(data)
    drifted = tmp_path / "contract.yaml"
    drifted.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ContractError, match=message):
        render_svg(drifted, instance_id="drift")


@pytest.mark.render
@requires_render_tools
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


@pytest.mark.render
@requires_render_tools
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
    assert authority["tikz_baseline"] == "isolated_approved_snippet_render"
    assert authority["tikz_snippet"] == ("styles/snippets/panel-f-floating-cantilever.tex")
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


def _foreground_bbox(path: Path) -> tuple[int, int, int, int] | None:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        background = Image.new("RGB", rgb.size, "white")
        difference = ImageChops.difference(rgb, background).convert("L")
        return difference.point(lambda value: 255 if value > 7 else 0).getbbox()


def test_normalization_preserves_aspect_ratio_and_centers_content(tmp_path: Path) -> None:
    source = tmp_path / "wide.png"
    destination = tmp_path / "normalized.png"
    Image.new("RGB", (400, 100), "black").save(source)
    _normalize_content_boundary(source, destination)
    bbox = _foreground_bbox(destination)
    assert bbox is not None
    assert pytest.approx((bbox[2] - bbox[0]) / (bbox[3] - bbox[1]), rel=0.01) == 4.0
    assert pytest.approx((bbox[0] + bbox[2]) / 2, abs=1) == 480
    assert pytest.approx((bbox[1] + bbox[3]) / 2, abs=1) == 320


@pytest.mark.render
@requires_render_tools
def test_tikz_baseline_is_isolated_to_the_same_content_boundary(tmp_path: Path) -> None:
    render_pilot(tmp_path)
    for name in ("tikz_baseline.png", "motif.png"):
        bbox = _foreground_bbox(tmp_path / name)
        assert bbox is not None
        assert 48 <= bbox[0] < bbox[2] <= 912
        assert 48 <= bbox[1] < bbox[3] <= 592
    with Image.open(tmp_path / "motif.png") as image:
        rgb = image.convert("RGB")
        assert rgb.getpixel((0, 0)) == (255, 255, 255)
        assert int(np.all(np.asarray(rgb) == 0, axis=2).sum()) < 100


@pytest.mark.render
@requires_render_tools
@pytest.mark.parametrize(
    "relative_path",
    [
        "authority.yaml",
        "contract.snapshot.yaml",
        "tikz_baseline.png",
        "comparison.png",
        "human_review.yaml",
    ],
)
def test_verify_rejects_missing_or_tampered_bound_artifacts(
    tmp_path: Path, relative_path: str
) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(PILOT, packet)
    target = packet / relative_path
    target.write_bytes(target.read_bytes() + b"tampered")
    with pytest.raises(ContractError):
        verify_pilot(packet)


@pytest.mark.render
@requires_render_tools
def test_verify_rejects_reencoded_motif_png(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(PILOT, packet)
    motif = packet / "motif.png"
    with Image.open(motif) as image:
        image.save(motif, format="PNG", optimize=True)
    with pytest.raises(ContractError, match="PNG byte hash"):
        verify_pilot(packet)


def test_svg_semantic_audit_rejects_object_and_role_mismatch() -> None:
    svg = render_svg(CONTRACT, instance_id="audit")
    assert audit_svg_semantics(svg, CONTRACT)["state"] == "passed"
    with pytest.raises(ContractError, match="semantic object mapping"):
        audit_svg_semantics(
            svg.replace('data-object="floating_cantilever"', 'data-object="unknown"'),
            CONTRACT,
        )
    with pytest.raises(ContractError, match="connector role mapping"):
        audit_svg_semantics(
            svg.replace('data-connector-role="mechanical"', 'data-connector-role="electrical"'),
            CONTRACT,
        )


@pytest.mark.render
@requires_render_tools
def test_comparison_labels_are_outside_equal_panes(tmp_path: Path) -> None:
    receipt = render_pilot(tmp_path)
    with Image.open(tmp_path / "comparison.png") as comparison:
        assert comparison.size == (1920, 700)
    assert receipt["comparison_labels"] == {
        "tikz": [0, 0, 960, 60],
        "svg": [960, 0, 1920, 60],
        "pane_top": 60,
    }


@pytest.mark.render
@requires_render_tools
def test_verify_allows_recorded_human_verdicts_without_machine_rewrite(
    tmp_path: Path,
) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(PILOT, packet)
    review_path = packet / "human_review.yaml"
    review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
    review["semantic_legibility_verdict"] = "accepted"
    review["visual_quality_vs_tikz"] = "worse"
    review_path.write_text(yaml.safe_dump(review, sort_keys=False), encoding="utf-8")
    assert verify_pilot(packet)["publication_acceptance"] == "not_claimed"


@pytest.mark.render
@requires_render_tools
def test_verify_rejects_review_claim_drift(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(PILOT, packet)
    review_path = packet / "human_review.yaml"
    review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
    review["backend_promotion"] = "authorized"
    review_path.write_text(yaml.safe_dump(review), encoding="utf-8")
    with pytest.raises(ContractError, match="backend promotion"):
        verify_pilot(packet)
