#!/usr/bin/env python3
"""Render the contract-bound Panel F motif as an editable SVG fragment."""

# The literal SVG keeps each editable primitive on one source line.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
APPROVED_SNIPPET = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.tex"
CANVAS = (960, 640)
CONTENT_BOX = (48, 48, 912, 592)


class ContractError(ValueError):
    """Raised when the neutral motif contract drifts from the supported shape."""


def _validate_contract(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or (
        data.get("schema_version") != 1
        or data.get("motif") != "panel-f-floating-cantilever"
        or data.get("renderer") != "neutral"
    ):
        raise ContractError("contract envelope drifted")
    expected_states = {
        "voltage_source": "driven",
        "ground": "reference",
        "floating_cantilever": "floating",
        "trapped_charge": "trapped",
    }
    if set(data.get("objects", {})) != set(expected_states):
        raise ContractError("required objects are missing")
    if any(
        data["objects"][name].get("electrical_state") != state
        for name, state in expected_states.items()
    ):
        raise ContractError("object states drifted")

    connectors = data.get("connectors", {})
    expected_connectors = {
        "mechanical_attachment": (
            "mechanical",
            ["fixed_mechanical_boundary", "floating_cantilever"],
        ),
        "electrode_drive": ("electrical", ["voltage_source", "driven_electrode"]),
        "source_return": ("electrical", ["voltage_source", "ground"]),
    }
    forbidden_connections = data.get("forbidden_connections", [])
    if forbidden_connections != [["floating_cantilever", "ground"]]:
        raise ContractError("forbidden connection set drifted")
    forbidden = {frozenset(connection) for connection in forbidden_connections}
    for connector in connectors.values():
        endpoints = connector.get("connects", [])
        if len(endpoints) == 2 and frozenset(endpoints) in forbidden:
            raise ContractError("actual connector matches forbidden connection")
    if set(connectors) != set(expected_connectors):
        raise ContractError("connector set drifted")
    if any(
        connectors.get(name, {}).get("role") != role
        or connectors.get(name, {}).get("connects") != endpoints
        for name, (role, endpoints) in expected_connectors.items()
    ):
        raise ContractError("connector roles or endpoints drifted")

    relations = data.get("relations", {})
    if "trapped_charge_ownership" not in relations:
        raise ContractError("required relations drifted")
    if set(relations) != {"trapped_charge_ownership"}:
        raise ContractError("relation set drifted")
    relation = relations.get("trapped_charge_ownership", {})
    if relation != {
        "subject": "trapped_charge",
        "role": "owned_by",
        "object": "floating_cantilever",
    }:
        raise ContractError("required relations drifted")
    required_owns = {
        "fixed_mechanical_boundary",
        "floating_cantilever",
        "driven_electrode",
        "source_return",
        "gap_guides",
        "trapped_charge",
    }
    if set(data.get("owns", [])) != required_owns:
        raise ContractError("owns set drifted")
    return data


def render_svg(contract_path: Path = DEFAULT_CONTRACT, *, instance_id: str = "panel-f") -> str:
    """Return deterministic SVG bytes as text after fail-closed contract validation."""
    _validate_contract(Path(contract_path))
    if not instance_id or any(
        char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        for char in instance_id
    ):
        raise ValueError("instance_id must contain only letters, digits, underscores, and hyphens")

    prefix = instance_id
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 640" width="960" height="640" data-fragment-role="panel-f-motif">
  <title>Floating cantilever and driven electrode motif</title>
  <desc>Editable semantic SVG fragment; the cantilever is electrically floating and the voltage-source return is grounded.</desc>
  <g id="{prefix}-fixed-boundary" data-object="fixed_mechanical_boundary">
    <rect x="94" y="116" width="70" height="304" rx="8" fill="#d9dde3" stroke="#343a40" stroke-width="6"/>
    <path d="M108 146l42-24M108 196l42-24M108 246l42-24M108 296l42-24M108 346l42-24M108 396l42-24" fill="none" stroke="#77808b" stroke-width="4"/>
  </g>
  <g id="{prefix}-floating-cantilever" data-object="floating_cantilever" data-electrical-state="floating">
    <path d="M164 244 C330 244 450 250 604 276 L604 326 C450 300 330 294 164 294 Z" fill="#e5a449" stroke="#4a3422" stroke-width="6"/>
  </g>
  <g id="{prefix}-driven-electrode" data-object="driven_electrode" data-electrical-state="driven">
    <rect x="580" y="420" width="246" height="34" rx="8" fill="#78a8d8" stroke="#274d73" stroke-width="6"/>
  </g>
  <g id="{prefix}-voltage-source" data-object="voltage_source" data-electrical-state="driven">
    <circle cx="768" cy="160" r="55" fill="#fff" stroke="#27323d" stroke-width="6"/>
    <path d="M748 142h40M768 122v40M750 184h36" stroke="#27323d" stroke-width="5"/>
  </g>
  <g id="{prefix}-source-ground" data-object="ground" data-electrical-state="reference">
    <path d="M768 540v30M730 570h76M740 584h56M752 598h32" fill="none" stroke="#27323d" stroke-width="6"/>
  </g>
  <g id="{prefix}-electrical-leads" data-visual-role="electrical_leads">
    <path d="M768 215v84h-64v121" fill="none" stroke="#315d8a" stroke-width="6"/>
    <path d="M823 160h42v380h-97" fill="none" stroke="#315d8a" stroke-width="6"/>
  </g>
  <g id="{prefix}-gap-guides" data-object="gap_guides">
    <path d="M540 340v64M526 340h28M526 404h28" fill="none" stroke="#6c757d" stroke-width="3" stroke-dasharray="8 7"/>
  </g>
  <g id="{prefix}-trapped-charge" data-object="trapped_charge" data-electrical-state="trapped">
    <circle cx="410" cy="270" r="9" fill="#b73535"/><circle cx="448" cy="276" r="9" fill="#b73535"/><circle cx="486" cy="283" r="9" fill="#b73535"/>
  </g>
  <g id="{prefix}-mechanical-attachment" data-relation="mechanical_attachment" data-from="{prefix}-fixed-boundary" data-to="{prefix}-floating-cantilever" data-connector-role="mechanical">
    <rect x="154" y="230" width="28" height="78" rx="5" fill="#6f7780" stroke="#343a40" stroke-width="4"/>
  </g>
  <g id="{prefix}-electrode-drive" data-relation="electrode_drive" data-from="{prefix}-voltage-source" data-to="{prefix}-driven-electrode" data-connector-role="electrical" data-style-role="electrical-drive"/>
  <g id="{prefix}-source-return" data-relation="source_return" data-from="{prefix}-voltage-source" data-to="{prefix}-source-ground" data-connector-role="electrical" data-style-role="electrical-return"/>
  <g id="{prefix}-charge-ownership" data-relation="trapped_charge_ownership" data-from="{prefix}-trapped-charge" data-to="{prefix}-floating-cantilever" data-relation-role="owned_by"/>
</svg>
'''


def audit_svg_semantics(svg: str, contract_path: Path = DEFAULT_CONTRACT) -> dict:
    """Validate the renderer's semantic groups against the closed motif contract."""
    contract = _validate_contract(Path(contract_path))
    root = ET.fromstring(svg)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    rendered_objects = {
        group.attrib["data-object"]
        for group in root.findall(".//svg:g[@data-object]", namespace)
    }
    expected_objects = set(contract["owns"]) - {"source_return"}
    expected_objects |= set(contract["objects"])
    if rendered_objects != expected_objects:
        raise ContractError("semantic object mapping drifted")
    rendered_roles = {
        group.attrib["data-relation"]: group.attrib["data-connector-role"]
        for group in root.findall(".//svg:g[@data-connector-role]", namespace)
    }
    expected_roles = {
        "mechanical_attachment": "mechanical",
        "electrode_drive": "electrical",
        "source_return": "electrical",
    }
    if rendered_roles != expected_roles:
        raise ContractError("connector role mapping drifted")
    rendered_relations = {
        group.attrib["data-relation"]: group.attrib["data-relation-role"]
        for group in root.findall(".//svg:g[@data-relation-role]", namespace)
    }
    expected_relations = {
        name: relation["role"] for name, relation in contract["relations"].items()
    }
    if rendered_relations != expected_relations:
        raise ContractError("relation role mapping drifted")
    return {"state": "passed", "object_count": len(rendered_objects)}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pixel_hash(path: Path) -> str:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        header = f"{rgba.width}x{rgba.height}:RGBA:".encode()
        return hashlib.sha256(header + rgba.tobytes()).hexdigest()


def _normalize_content_boundary(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        white = Image.new("RGBA", rgba.size, "white")
        white.alpha_composite(rgba)
        rgb = white.convert("RGB")
        mask = rgb.convert("L").point(lambda value: 255 if value < 248 else 0)
        bbox = mask.getbbox()
        if bbox is None:
            raise ContractError(f"render has no foreground content: {source}")
        content = rgb.crop(bbox)
        content.thumbnail(
            (CONTENT_BOX[2] - CONTENT_BOX[0], CONTENT_BOX[3] - CONTENT_BOX[1]),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGB", CANVAS, "white")
        position = (
            CONTENT_BOX[0] + (CONTENT_BOX[2] - CONTENT_BOX[0] - content.width) // 2,
            CONTENT_BOX[1] + (CONTENT_BOX[3] - CONTENT_BOX[1] - content.height) // 2,
        )
        canvas.paste(content, position)
        canvas.save(destination, format="PNG", optimize=False)


def _render_tikz_motif(destination: Path) -> None:
    source = rf"""\documentclass[border=0pt]{{standalone}}
\usepackage{{polymer-paper-preamble}}
\input{{{APPROVED_SNIPPET.as_posix()}}}
\begin{{document}}
\begin{{tikzpicture}}
\PanelFFloatingCantilever{{baseline}}{{0,0}}
\end{{tikzpicture}}
\end{{document}}
"""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "motif.tex").write_text(source, encoding="utf-8")
        env = os.environ.copy()
        env["TEXINPUTS"] = f"{PLUGIN_ROOT / 'styles'}:{env.get('TEXINPUTS', '')}"
        try:
            subprocess.run(
                ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "motif.tex"],
                cwd=work,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as error:
            raise ContractError(f"isolated TikZ motif failed to compile: {error.stdout}") from error
        subprocess.run(
            ["pdftoppm", "-singlefile", "-png", "-r", "300", "motif.pdf", "motif"],
            cwd=work,
            check=True,
            capture_output=True,
        )
        _normalize_content_boundary(work / "motif.png", destination)


def render_pilot(output_dir: Path) -> dict:
    """Write the bounded SVG/TikZ comparison packet into ``output_dir``."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_path = output_dir / "motif.svg"
    svg_path.write_text(render_svg(DEFAULT_CONTRACT, instance_id="panel-f-svg"), encoding="utf-8")
    audit_svg_semantics(svg_path.read_text(encoding="utf-8"), DEFAULT_CONTRACT)
    raw_png = output_dir / ".motif-raw.png"
    subprocess.run(
        [
            "rsvg-convert",
            "--width",
            str(CANVAS[0]),
            "--height",
            str(CANVAS[1]),
            "--output",
            str(raw_png),
            str(svg_path),
        ],
        check=True,
        capture_output=True,
    )
    _normalize_content_boundary(raw_png, output_dir / "motif.png")
    raw_png.unlink()
    _render_tikz_motif(output_dir / "tikz_baseline.png")

    with (
        Image.open(output_dir / "tikz_baseline.png") as tikz,
        Image.open(output_dir / "motif.png") as svg,
    ):
        sheet = Image.new("RGB", (CANVAS[0] * 2, CANVAS[1] + 60), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((CANVAS[0] // 2, 30), "TikZ", fill="black", anchor="mm")
        draw.text((CANVAS[0] + CANVAS[0] // 2, 30), "SVG", fill="black", anchor="mm")
        sheet.paste(tikz.convert("RGB"), (0, 60))
        sheet.paste(svg.convert("RGB"), (CANVAS[0], 60))
        sheet.save(output_dir / "comparison.png", format="PNG", optimize=False)

    shutil.copy2(DEFAULT_CONTRACT, output_dir / "contract.snapshot.yaml")
    authority = {
        "schema": "figure-agent.panel-f-svg-authority.v1",
        "contract": "styles/snippets/panel-f-floating-cantilever.contract.yaml",
        "contract_sha256": _sha256(DEFAULT_CONTRACT),
        "tikz_baseline": "isolated_approved_snippet_render",
        "tikz_snippet": "styles/snippets/panel-f-floating-cantilever.tex",
        "tikz_snippet_sha256": _sha256(APPROVED_SNIPPET),
        "comparison_boundary": {
            "canvas": list(CANVAS),
            "content_box": list(CONTENT_BOX),
            "normalization": "foreground_crop_uniform_contain_centered",
        },
        "approved_tikz_snippet_unchanged": True,
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "authority.yaml").write_text(
        yaml.safe_dump(authority, sort_keys=False), encoding="utf-8"
    )
    receipt = {
        "schema": "figure-agent.panel-f-svg-receipt.v1",
        "comparison_boundary": "equal_pixel_canvas",
        "canvas": {"width": CANVAS[0], "height": CANVAS[1]},
        "svg_sha256": _sha256(svg_path),
        "png_sha256": _sha256(output_dir / "motif.png"),
        "png_pixel_sha256": _pixel_hash(output_dir / "motif.png"),
        "tikz_pixel_sha256": _pixel_hash(output_dir / "tikz_baseline.png"),
        "comparison_sha256": _sha256(output_dir / "comparison.png"),
        "comparison_labels": {
            "tikz": [0, 0, 960, 60],
            "svg": [960, 0, 1920, 60],
            "pane_top": 60,
        },
        "authority_sha256": _sha256(output_dir / "authority.yaml"),
        "contract_snapshot_sha256": _sha256(output_dir / "contract.snapshot.yaml"),
        "tikz_baseline_sha256": _sha256(output_dir / "tikz_baseline.png"),
        "backend_promotion": "not_authorized",
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    review = {
        "schema": "figure-agent.panel-f-svg-human-review.v1",
        "comparison_artifact": "comparison.png",
        "machine_receipt_sha256": _sha256(output_dir / "receipt.json"),
        "comparison_sha256": receipt["comparison_sha256"],
        "semantic_legibility_verdict": "pending",
        "visual_quality_vs_tikz": "pending",
        "backend_promotion": "not_authorized",
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "human_review.yaml").write_text(
        yaml.safe_dump(review, sort_keys=False), encoding="utf-8"
    )
    return receipt


def verify_pilot(pilot_dir: Path) -> dict:
    """Fail closed unless a packet matches two fresh deterministic replays."""
    pilot_dir = Path(pilot_dir)
    try:
        receipt = json.loads((pilot_dir / "receipt.json").read_text(encoding="utf-8"))
        authority = yaml.safe_load((pilot_dir / "authority.yaml").read_text(encoding="utf-8"))
        review = yaml.safe_load((pilot_dir / "human_review.yaml").read_text(encoding="utf-8"))
        _validate_contract(pilot_dir / "contract.snapshot.yaml")
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid or missing pilot artifact: {error}") from error
    if receipt.get("publication_acceptance") != "not_claimed":
        raise ContractError("publication acceptance must remain not_claimed")
    if receipt.get("backend_promotion") != "not_authorized":
        raise ContractError("backend promotion must remain not_authorized")
    if authority.get("publication_acceptance") != "not_claimed":
        raise ContractError("authority publication acceptance drifted")
    if review.get("schema") != "figure-agent.panel-f-svg-human-review.v1" or review.get(
        "comparison_artifact"
    ) != "comparison.png":
        raise ContractError("human review binding drifted")
    if review.get("machine_receipt_sha256") != _sha256(pilot_dir / "receipt.json") or review.get(
        "comparison_sha256"
    ) != receipt.get("comparison_sha256"):
        raise ContractError("human review binding drifted")
    semantic_verdict = review.get("semantic_legibility_verdict")
    visual_verdict = review.get("visual_quality_vs_tikz")
    if semantic_verdict not in {"pending", "accepted", "rejected"} or visual_verdict not in {
        "pending",
        "better",
        "equivalent",
        "worse",
    }:
        raise ContractError("human comparison verdict vocabulary is invalid")
    promotion = review.get("backend_promotion")
    promotion_supported = semantic_verdict == "accepted" and visual_verdict in {
        "better",
        "equivalent",
    }
    if promotion not in {"not_authorized", "authorized"}:
        raise ContractError("backend promotion state is invalid")
    if promotion == "authorized" and not promotion_supported:
        raise ContractError("backend promotion requires both verdicts accepted")
    if review.get("publication_acceptance") != "not_claimed":
        raise ContractError("review publication acceptance drifted")
    if _sha256(pilot_dir / "motif.png") != receipt.get("png_sha256"):
        raise ContractError("committed PNG byte hash differs from receipt")
    with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
        first = render_pilot(Path(first_tmp))
        second = render_pilot(Path(second_tmp))
        if (
            first["svg_sha256"] != second["svg_sha256"]
            or first["png_pixel_sha256"] != second["png_pixel_sha256"]
        ):
            raise ContractError("fresh replays are not deterministic")
        if (pilot_dir / "motif.svg").read_bytes() != (Path(first_tmp) / "motif.svg").read_bytes():
            raise ContractError("committed SVG differs from fresh replay")
        if _pixel_hash(pilot_dir / "motif.png") != first["png_pixel_sha256"]:
            raise ContractError("committed PNG differs from fresh replay")
        if receipt != first:
            raise ContractError("committed receipt differs from fresh replay")
        bound_hashes = {
            "authority_sha256": "authority.yaml",
            "contract_snapshot_sha256": "contract.snapshot.yaml",
            "tikz_baseline_sha256": "tikz_baseline.png",
            "comparison_sha256": "comparison.png",
        }
        for field, filename in bound_hashes.items():
            if receipt.get(field) != _sha256(pilot_dir / filename):
                raise ContractError(f"bound artifact hash mismatch: {filename}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("output_dir", type=Path)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("pilot_dir", type=Path)
    args = parser.parse_args()
    result = (
        render_pilot(args.output_dir) if args.command == "render" else verify_pilot(args.pilot_dir)
    )
    print(f"{args.command} verified: {result['svg_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
