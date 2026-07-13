#!/usr/bin/env python3
"""Compile hash-bound, renderer-neutral semantic legibility review evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from semantic_legibility_contract import (  # noqa: E402
    SemanticLegibilityContractError,
    validate_semantic_legibility_contract,
)
from visual_finding_artifacts import draw_attribution_box  # noqa: E402
from visual_finding_attribution import (  # noqa: E402
    VisualFindingAttributionError,
    attribute_visual_finding,
)

INPUT_SCHEMA = "figure-agent.semantic-legibility-evidence-input.v1"
OUTPUT_SCHEMA = "figure-agent.semantic-legibility-evidence.v1"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class SemanticLegibilityEvidenceError(ValueError):
    """Raised when the review input cannot be compiled safely."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _load_yaml(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise SemanticLegibilityEvidenceError(f"{label}_invalid") from exc
    if not isinstance(payload, dict):
        raise SemanticLegibilityEvidenceError(f"{label}_invalid")
    return payload


def _resolve(base: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise SemanticLegibilityEvidenceError(f"{label}_invalid")
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _normalized_claim(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SemanticLegibilityEvidenceError("authority_claim_invalid")
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split()).casefold()


def _authority_claims(payload: object) -> dict[str, list[str]]:
    if not isinstance(payload, list):
        raise SemanticLegibilityEvidenceError("authority_claims_invalid")
    claims: dict[str, set[str]] = {}
    for item in payload:
        if not isinstance(item, dict):
            raise SemanticLegibilityEvidenceError("authority_claim_invalid")
        semantic_id = item.get("semantic_id")
        authority_id = item.get("authority_id")
        if (
            not isinstance(semantic_id, str)
            or not _SAFE_ID.fullmatch(semantic_id)
            or not isinstance(authority_id, str)
            or not authority_id.strip()
        ):
            raise SemanticLegibilityEvidenceError("authority_claim_invalid")
        claims.setdefault(semantic_id, set()).add(_normalized_claim(item.get("claim")))
    return {semantic_id: sorted(values) for semantic_id, values in claims.items()}


def _bindings(payload: object) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, list):
        raise SemanticLegibilityEvidenceError("bindings_invalid")
    result: dict[str, list[dict[str, Any]]] = {}
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("semantic_id"), str):
            raise SemanticLegibilityEvidenceError("binding_invalid")
        result.setdefault(item["semantic_id"], []).append(item)
    return result


def _declared_subjects(
    contract: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    section = contract["semantic_legibility"]
    objects = {item["object_id"]: item for item in section["object_roles"]}
    relations = {item["connector_id"]: item for item in section["visible_connectors"]}
    return objects, relations


def _binding_failure(
    records: list[dict[str, Any]],
    *,
    full_render_sha256: str,
    page_sha256: str,
) -> str | None:
    if not records:
        return "binding_missing"
    if len(records) != 1:
        return "binding_duplicate"
    binding = records[0]
    state = binding.get("binding_state")
    if state != "exact":
        return f"binding_{state or 'missing'}"
    if binding.get("full_render_sha256") != full_render_sha256:
        return "full_render_hash_mismatch"
    if binding.get("page_sha256") != page_sha256:
        return "page_hash_mismatch"
    return None


def _crop_box(bbox: list[float], size: tuple[int, int], padding: int = 12) -> list[int]:
    rounded = [int(round(item)) for item in bbox]
    value = [
        max(0, rounded[0] - padding),
        max(0, rounded[1] - padding),
        min(size[0], rounded[2] + padding),
        min(size[1], rounded[3] + padding),
    ]
    if value[2] <= value[0] or value[3] <= value[1]:
        raise SemanticLegibilityEvidenceError("subject_bbox_outside_render")
    return value


def _review_questions(
    payload: dict[str, Any], subject_states: dict[str, str]
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for key, question_kind in (
        ("required_distinctions", "required_visual_distinction"),
        ("human_review_questions", "named_human_review_question"),
    ):
        values = payload.get(key, [])
        if not isinstance(values, list):
            raise SemanticLegibilityEvidenceError(f"{key}_invalid")
        for item in values:
            if not isinstance(item, dict):
                raise SemanticLegibilityEvidenceError(f"{key}_invalid")
            semantic_ids = item.get("semantic_ids")
            if (
                not isinstance(item.get("question_id"), str)
                or not isinstance(item.get("question"), str)
                or not isinstance(semantic_ids, list)
                or not semantic_ids
                or not all(isinstance(value, str) for value in semantic_ids)
            ):
                raise SemanticLegibilityEvidenceError(f"{key}_invalid")
            blocked = [
                semantic_id
                for semantic_id in semantic_ids
                if subject_states.get(semantic_id) != "exact"
            ]
            questions.append(
                {
                    "question_id": item["question_id"],
                    "question_kind": question_kind,
                    "semantic_ids": semantic_ids,
                    "question": item["question"],
                    "status": "pending" if not blocked else "blocked",
                    **({"blocked_semantic_ids": blocked} if blocked else {}),
                }
            )
    return questions


def compile_semantic_legibility_evidence(input_path: Path, output_dir: Path) -> dict[str, Any]:
    """Compile review evidence without making a visual or publication verdict."""
    input_path = input_path.resolve()
    base = input_path.parent
    payload = _load_yaml(input_path, label="input")
    if payload.get("schema") != INPUT_SCHEMA:
        raise SemanticLegibilityEvidenceError("schema_invalid")
    if payload.get("semantic_preservation") != "not_claimed_pending_human_review":
        raise SemanticLegibilityEvidenceError("semantic_preservation_invalid")
    if payload.get("publication_acceptance") != "not_claimed":
        raise SemanticLegibilityEvidenceError("publication_acceptance_invalid")

    fixture_dir = _resolve(base, payload.get("fixture_dir"), label="fixture_dir")
    semantic_contract_path = _resolve(
        base, payload.get("semantic_contract"), label="semantic_contract"
    )
    semantic_regions_path = _resolve(
        base, payload.get("semantic_regions"), label="semantic_regions"
    )
    try:
        semantic_contract = validate_semantic_legibility_contract(
            _load_yaml(semantic_contract_path, label="semantic_contract")
        )
    except SemanticLegibilityContractError as exc:
        raise SemanticLegibilityEvidenceError(str(exc)) from exc
    semantic_regions = _load_yaml(semantic_regions_path, label="semantic_regions")
    region_index = {
        region["id"]: region
        for region in semantic_regions.get("regions", [])
        if isinstance(region, dict) and isinstance(region.get("id"), str)
    }

    render = payload.get("render")
    if not isinstance(render, dict):
        raise SemanticLegibilityEvidenceError("render_invalid")
    full_render_path = _resolve(base, render.get("full_render_path"), label="full_render_path")
    page_path = _resolve(base, render.get("page_path"), label="page_path")
    try:
        full_render_sha256 = _sha256(full_render_path)
        page_sha256 = _sha256(page_path)
    except OSError as exc:
        raise SemanticLegibilityEvidenceError("render_input_missing") from exc
    declared_full_hash = render.get("full_render_sha256")
    declared_page_hash = render.get("page_sha256")
    global_hash_failure = None
    if declared_full_hash != full_render_sha256:
        global_hash_failure = "full_render_hash_mismatch"
    elif declared_page_hash != page_sha256:
        global_hash_failure = "page_hash_mismatch"

    subjects = payload.get("subjects")
    if not isinstance(subjects, list) or not subjects:
        raise SemanticLegibilityEvidenceError("subjects_invalid")
    binding_index = _bindings(payload.get("bindings"))
    claims = _authority_claims(payload.get("authority_claims"))
    declared_objects, declared_relations = _declared_subjects(semantic_contract)

    output_dir = output_dir.resolve()
    crops_dir = output_dir / "crops"
    if crops_dir.exists():
        shutil.rmtree(crops_dir)
    crops_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(full_render_path) as opened:
        source_image = opened.convert("RGB")

    records: list[dict[str, Any]] = []
    seen_subjects: set[str] = set()
    for subject in subjects:
        if not isinstance(subject, dict):
            raise SemanticLegibilityEvidenceError("subject_invalid")
        semantic_id = subject.get("semantic_id")
        kind = subject.get("kind")
        if (
            not isinstance(semantic_id, str)
            or not _SAFE_ID.fullmatch(semantic_id)
            or semantic_id in seen_subjects
            or kind not in {"object", "relation"}
        ):
            raise SemanticLegibilityEvidenceError("subject_invalid")
        seen_subjects.add(semantic_id)
        expected = subject.get("expected_readings")
        forbidden = subject.get("forbidden_readings")
        if (
            not isinstance(expected, list)
            or not expected
            or not all(isinstance(value, str) and value.strip() for value in expected)
            or not isinstance(forbidden, list)
            or not all(isinstance(value, str) and value.strip() for value in forbidden)
        ):
            raise SemanticLegibilityEvidenceError("subject_readings_invalid")
        base_record = {
            "semantic_id": semantic_id,
            "kind": kind,
            "expected_readings": expected,
            "forbidden_readings": forbidden,
        }
        normalized_claims = claims.get(semantic_id, [])
        if len(normalized_claims) > 1:
            records.append(
                {
                    **base_record,
                    "state": "blocked_authority_conflict",
                    "review_disposition": "review_only",
                    "reason": "conflicting_normalized_authority_claims",
                    "normalized_authority_claims": normalized_claims,
                }
            )
            continue
        declarations = declared_objects if kind == "object" else declared_relations
        declaration = declarations.get(semantic_id)
        declared = declaration is not None
        reason = global_hash_failure
        if not declared:
            reason = "semantic_declaration_missing"
        if reason is None:
            reason = _binding_failure(
                binding_index.get(semantic_id, []),
                full_render_sha256=full_render_sha256,
                page_sha256=page_sha256,
            )
        if reason is not None:
            records.append(
                {
                    **base_record,
                    "state": "unbound",
                    "review_disposition": "review_only",
                    "reason": reason,
                }
            )
            continue

        binding = binding_index[semantic_id][0]
        try:
            attribution = attribute_visual_finding(
                {
                    "id": semantic_id,
                    "bbox_px": subject.get("bbox_px"),
                    "confidence": None,
                },
                detector_render=render.get("detector_render"),
                semantic_contract=semantic_regions,
                fixture_dir=fixture_dir,
            )
        except VisualFindingAttributionError as exc:
            records.append(
                {
                    **base_record,
                    "state": "unbound",
                    "review_disposition": "review_only",
                    "reason": str(exc),
                }
            )
            continue
        if attribution.get("state") != "exact" or attribution.get("region_candidates") != [
            binding.get("region_id")
        ]:
            records.append(
                {
                    **base_record,
                    "state": "unbound",
                    "review_disposition": "review_only",
                    "reason": attribution.get("reason", "region_binding_mismatch"),
                }
            )
            continue

        bbox = [float(value) for value in attribution["detector_bbox_px"]]
        image = source_image.copy()
        draw_attribution_box(
            ImageDraw.Draw(image),
            [round(value) for value in bbox],
            attribution_state="exact",
        )
        crop_box = _crop_box(bbox, image.size)
        crop_relative = Path("crops") / f"{semantic_id}.png"
        crop_path = output_dir / crop_relative
        image.crop(crop_box).save(crop_path, format="PNG", optimize=False)
        records.append(
            {
                **base_record,
                "state": "exact",
                "review_disposition": "human_review_required",
                "human_verdict": "pending",
                "panel_id": region_index[binding["region_id"]].get("panel_id"),
                "semantic_declaration": declaration,
                "selector_snapshot": attribution["source_selector"],
                "coordinate_space": {
                    "name": "pdf_cm",
                    "origin": semantic_regions["page_geometry"]["origin"],
                    "page_index": semantic_regions["page_geometry"]["page_index"],
                    "bbox_pdf_cm": attribution["bbox_pdf_cm"],
                    "bbox_px": bbox,
                    "pixel_origin": render["detector_render"]["pixel_origin"],
                },
                "crop": {"path": crop_relative.as_posix(), "bbox_px": crop_box},
                "hashes": {
                    "full_render_sha256": full_render_sha256,
                    "page_sha256": page_sha256,
                    "crop_sha256": _sha256(crop_path),
                    "render_geometry_hash": semantic_regions["page_geometry"][
                        "render_geometry_hash"
                    ],
                },
            }
        )

    subject_states = {item["semantic_id"]: item["state"] for item in records}
    packet = {
        "schema": OUTPUT_SCHEMA,
        "subjects": records,
        "human_review_questions": _review_questions(payload, subject_states),
        "human_verdict": "pending",
        "semantic_preservation": "not_claimed_pending_human_review",
        "publication_acceptance": "not_claimed",
        "input_hashes": {
            "input_sha256": _sha256(input_path),
            "semantic_contract_sha256": _sha256(semantic_contract_path),
            "semantic_regions_sha256": _sha256(semantic_regions_path),
            "full_render_sha256": full_render_sha256,
            "page_sha256": page_sha256,
        },
    }
    packet["review_input_hash"] = _canonical_hash(packet)
    (output_dir / "packet.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        packet = compile_semantic_legibility_evidence(args.input, args.output_dir)
    except SemanticLegibilityEvidenceError as exc:
        print(f"ERROR semantic_legibility_evidence: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        exact = sum(subject["state"] == "exact" for subject in packet["subjects"])
        print(
            "OK semantic_legibility_evidence: "
            f"exact={exact} total={len(packet['subjects'])} "
            "human_verdict=pending publication_acceptance=not_claimed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
