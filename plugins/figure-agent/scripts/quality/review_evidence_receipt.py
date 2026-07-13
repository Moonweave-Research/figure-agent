from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from hybrid.comparison_report import aggregate_review_input_hash  # noqa: E402
from semantic_region_contract import render_geometry_hash  # noqa: E402

SCHEMA = "figure-agent.review-evidence-receipt.v1"
VARIANTS = ("raw", "verified", "repaired")
SCALES = ("whole", "panel", "object_relation", "zoom")


class ReviewEvidenceReceiptError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReviewEvidenceReceiptError(f"mapping_required: {path.name}")
    return payload


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_file(root: Path, relative_value: object) -> Path:
    relative = Path(str(relative_value or ""))
    candidate = (root / relative).resolve()
    if (
        not relative.parts
        or relative.is_absolute()
        or ".." in relative.parts
        or not candidate.is_relative_to(root)
        or candidate.is_symlink()
        or not candidate.is_file()
    ):
        raise ReviewEvidenceReceiptError(f"unsafe_review_input: {relative}")
    return candidate


def _page_geometry(pdf_path: Path, page_index: int) -> dict[str, Any]:
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover - runtime dependency contract
        raise ReviewEvidenceReceiptError("pdfplumber_required") from exc
    with pdfplumber.open(pdf_path) as pdf:
        if page_index >= len(pdf.pages):
            raise ReviewEvidenceReceiptError("page_index_out_of_range")
        page = pdf.pages[page_index]
        width_cm = round(float(page.width) * 2.54 / 72.0, 6)
        height_cm = round(float(page.height) * 2.54 / 72.0, 6)
    geometry = {
        "coordinate_space": "pdf_cm",
        "page_index": page_index,
        "origin": "bottom_left",
        "media_box_pdf_cm": [0.0, 0.0, width_cm, height_cm],
        "crop_box_pdf_cm": [0.0, 0.0, width_cm, height_cm],
        "rotation_deg": 0,
    }
    return {**geometry, "render_geometry_hash": render_geometry_hash(geometry)}


def human_review_binding(
    verdict: dict[str, Any], current_panel_hash: str, current_review_hash: str
) -> dict[str, Any]:
    reviewed_source = verdict.get("reviewed_source")
    reviewed_panel_hash = (
        str(reviewed_source.get("panel_render_sha256") or "")
        if isinstance(reviewed_source, dict)
        else ""
    )
    if reviewed_panel_hash and not reviewed_panel_hash.startswith("sha256:"):
        reviewed_panel_hash = "sha256:" + reviewed_panel_hash
    reviewed_review_hash = (
        str(reviewed_source.get("review_input_hash") or "")
        if isinstance(reviewed_source, dict)
        else ""
    )
    if reviewed_review_hash and not reviewed_review_hash.startswith("sha256:"):
        reviewed_review_hash = "sha256:" + reviewed_review_hash
    panel_matches = reviewed_panel_hash == current_panel_hash
    review_input_matches = reviewed_review_hash == current_review_hash
    return {
        "reviewed_panel_sha256": reviewed_panel_hash or None,
        "current_panel_sha256": current_panel_hash,
        "panel_matches": panel_matches,
        "reviewed_review_input_hash": reviewed_review_hash or None,
        "current_review_input_hash": current_review_hash,
        "review_input_matches": review_input_matches,
        "matches": panel_matches and review_input_matches,
    }


def build_review_evidence_receipt(fixture_dir: Path, output_path: Path) -> dict[str, Any]:
    fixture = fixture_dir.resolve()
    authority = _load_yaml(fixture / "authority.yaml")
    protocol = _load_yaml(fixture / "comparison_protocol.yaml")
    verdict = _load_yaml(fixture / "review" / "human_verdict.yaml")
    selector = authority.get("selector")
    if not isinstance(selector, dict) or selector.get("hash_authority") != "generated_receipt":
        raise ReviewEvidenceReceiptError("generated_hash_authority_required")
    if (
        selector.get("render_geometry_hash") is not None
        or selector.get("review_input_hash") is not None
    ):
        raise ReviewEvidenceReceiptError("tracked_manifest_hash_must_be_null")

    selector_id = str(selector.get("selector_id") or "")
    source_path = _safe_file(fixture, protocol.get("repaired_source"))
    source = source_path.read_text(encoding="utf-8")
    start = str(selector.get("anchor_start") or "")
    end = str(selector.get("anchor_end") or "")
    if not selector_id or source.count(start) != 1 or source.count(end) != 1:
        raise ReviewEvidenceReceiptError("selector_binding_not_exact")
    if source.index(start) >= source.index(end):
        raise ReviewEvidenceReceiptError("selector_order_invalid")

    render_pdf = _safe_file(fixture, protocol.get("repaired_render_pdf"))
    geometry = _page_geometry(render_pdf, int(selector.get("page_index", -1)))
    if geometry["coordinate_space"] != selector.get("coordinate_space"):
        raise ReviewEvidenceReceiptError("coordinate_space_mismatch")

    raw_inputs = protocol.get("review_inputs")
    if not isinstance(raw_inputs, dict) or set(raw_inputs) != set(VARIANTS):
        raise ReviewEvidenceReceiptError("review_variant_set_invalid")
    inputs: list[dict[str, str]] = []
    for variant in VARIANTS:
        entries = raw_inputs[variant]
        if not isinstance(entries, dict) or set(entries) != {*SCALES, "overlay"}:
            raise ReviewEvidenceReceiptError(f"review_scale_set_invalid: {variant}")
        for role, relative in sorted(entries.items()):
            path = _safe_file(fixture, relative)
            inputs.append(
                {
                    "role": f"{variant}.{role}",
                    "path": path.relative_to(fixture).as_posix(),
                    "sha256": _sha256(path),
                }
            )
    toolchain = protocol.get("toolchain")
    if not isinstance(toolchain, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in toolchain.items()
    ):
        raise ReviewEvidenceReceiptError("toolchain_invalid")
    review_hash = aggregate_review_input_hash(inputs, toolchain)
    current_panel_hash = next(item["sha256"] for item in inputs if item["role"] == "repaired.panel")
    review_binding = human_review_binding(verdict, current_panel_hash, review_hash)

    receipt = {
        "schema": SCHEMA,
        "fixture": fixture.name,
        "selector_id": selector_id,
        "source_sha256": _sha256(source_path),
        "attribution_state": "exact",
        "page_geometry": geometry,
        "render_geometry_hash": geometry["render_geometry_hash"],
        "review_inputs": inputs,
        "review_input_hash": review_hash,
        "evidence_scales": list(SCALES),
        "variants": list(VARIANTS),
        "human_review_state": (
            verdict.get("state") if review_binding["matches"] else "pending_revalidation"
        ),
        "human_review_binding": review_binding,
        "publication_acceptance": "not_claimed",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
