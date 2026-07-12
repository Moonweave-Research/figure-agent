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
from pathlib import Path

import yaml
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
APPROVED_SNIPPET = PLUGIN_ROOT / "styles/snippets/panel-f-floating-cantilever.tex"
CANVAS = (960, 640)
CONTENT_BOX = (48, 48, 912, 592)


class ContractError(ValueError):
    """Raised when the neutral motif contract drifts from the supported shape."""


def _validate_contract(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    expected_states = {
        "voltage_source": "driven",
        "ground": "reference",
        "floating_cantilever": "floating",
        "trapped_charge": "trapped",
    }
    if not isinstance(data, dict) or set(data.get("objects", {})) != set(expected_states):
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
    forbidden = {frozenset(connection) for connection in data.get("forbidden_connections", [])}
    if frozenset(("floating_cantilever", "ground")) not in forbidden:
        raise ContractError("forbidden connection floating_cantilever-to-ground is missing")
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
  <g id="{prefix}-electrical-leads" data-object="electrical_leads">
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
  <g id="{prefix}-electrode-drive" data-relation="electrode_drive" data-from="{prefix}-voltage-source" data-to="{prefix}-driven-electrode" data-connector-role="electrical-drive"/>
  <g id="{prefix}-source-return" data-relation="source_return" data-from="{prefix}-voltage-source" data-to="{prefix}-source-ground" data-connector-role="electrical-return"/>
  <g id="{prefix}-charge-ownership" data-relation="trapped_charge_ownership" data-from="{prefix}-trapped-charge" data-to="{prefix}-floating-cantilever" data-connector-role="ownership"/>
</svg>
'''


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
        content = rgb.crop(bbox).resize(
            (CONTENT_BOX[2] - CONTENT_BOX[0], CONTENT_BOX[3] - CONTENT_BOX[1]),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGB", CANVAS, "white")
        canvas.paste(content, CONTENT_BOX[:2])
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
        sheet = Image.new("RGB", (CANVAS[0] * 2, CANVAS[1]), "white")
        sheet.paste(tikz.convert("RGB"), (0, 0))
        sheet.paste(svg.convert("RGB"), (CANVAS[0], 0))
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
            "normalization": "foreground_crop_resampled_to_equal_box",
        },
        "approved_tikz_snippet_unchanged": True,
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "authority.yaml").write_text(
        yaml.safe_dump(authority, sort_keys=False), encoding="utf-8"
    )
    review = {
        "schema": "figure-agent.panel-f-svg-human-review.v1",
        "comparison_artifact": "comparison.png",
        "semantic_legibility_verdict": "pending",
        "visual_quality_vs_tikz": "pending",
        "backend_promotion": "not_authorized",
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "human_review.yaml").write_text(
        yaml.safe_dump(review, sort_keys=False), encoding="utf-8"
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
        "authority_sha256": _sha256(output_dir / "authority.yaml"),
        "contract_snapshot_sha256": _sha256(output_dir / "contract.snapshot.yaml"),
        "tikz_baseline_sha256": _sha256(output_dir / "tikz_baseline.png"),
        "human_review_sha256": _sha256(output_dir / "human_review.yaml"),
        "backend_promotion": "not_authorized",
        "semantic_legibility_verdict": "pending",
        "visual_quality_vs_tikz": "pending",
        "publication_acceptance": "not_claimed",
    }
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
    if review.get("backend_promotion") != "not_authorized":
        raise ContractError("backend promotion must remain not_authorized")
    if review.get("publication_acceptance") != "not_claimed":
        raise ContractError("review publication acceptance drifted")
    if (
        review.get("semantic_legibility_verdict") != "pending"
        or review.get("visual_quality_vs_tikz") != "pending"
    ):
        raise ContractError("human comparison fields must remain pending")
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
            "human_review_sha256": "human_review.yaml",
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
