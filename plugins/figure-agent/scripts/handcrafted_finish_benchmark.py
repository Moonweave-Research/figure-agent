"""Validate and crop the cross-figure handcrafted-finish benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

MANIFEST_SCHEMA = "figure-agent.handcrafted-finish-benchmark.v1"
REVIEW_SCHEMA = "figure-agent.handcrafted-finish-host-review.v1"
EVIDENCE_SCHEMA = "figure-agent.handcrafted-finish-render-evidence.v1"
CANDIDATE_ROLES = frozenset(
    {"current_baseline", "free_llm_redraw", "editorial_refinement"}
)


class HandcraftedFinishBenchmarkError(ValueError):
    """Raised when benchmark evidence overstates or breaks its contract."""


def _mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HandcraftedFinishBenchmarkError("yaml_mapping_required")
    return payload


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise HandcraftedFinishBenchmarkError(f"{key}_invalid")
    return list(value)


def _bbox(value: object) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        raise HandcraftedFinishBenchmarkError("candidate_bbox_invalid")
    if not all(isinstance(item, (int, float)) for item in value):
        raise HandcraftedFinishBenchmarkError("candidate_bbox_invalid")
    bbox = [float(item) for item in value]
    if bbox[2] <= 0 or bbox[3] <= 0:
        raise HandcraftedFinishBenchmarkError("candidate_bbox_invalid")
    return bbox


def load_manifest(path: Path) -> dict[str, Any]:
    payload = _mapping(path)
    if payload.get("schema") != MANIFEST_SCHEMA:
        raise HandcraftedFinishBenchmarkError("manifest_schema_invalid")
    if payload.get("publication_acceptance") != "not_claimed":
        raise HandcraftedFinishBenchmarkError("publication_acceptance_overclaim")
    if payload.get("learning_state") != "prospective_host_evidence_only":
        raise HandcraftedFinishBenchmarkError("learning_state_invalid")
    canvas = payload.get("canvas_cm")
    if not isinstance(canvas, list) or len(canvas) != 2 or not all(
        isinstance(item, (int, float)) and item > 0 for item in canvas
    ):
        raise HandcraftedFinishBenchmarkError("canvas_cm_invalid")
    canvas_width, canvas_height = (float(canvas[0]), float(canvas[1]))
    motifs = payload.get("motifs")
    if not isinstance(motifs, list) or len(motifs) < 3:
        raise HandcraftedFinishBenchmarkError("three_motifs_required")
    motif_ids: set[str] = set()
    option_ids: set[str] = set()
    for motif in motifs:
        if not isinstance(motif, dict):
            raise HandcraftedFinishBenchmarkError("motif_invalid")
        motif_id = motif.get("id")
        if not isinstance(motif_id, str) or not motif_id or motif_id in motif_ids:
            raise HandcraftedFinishBenchmarkError("motif_id_invalid")
        motif_ids.add(motif_id)
        _string_list(motif, "scientific_invariants")
        candidates = motif.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != 3:
            raise HandcraftedFinishBenchmarkError("candidate_triplet_required")
        roles: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise HandcraftedFinishBenchmarkError("candidate_invalid")
            role = candidate.get("role")
            option_id = candidate.get("option_id")
            if role not in CANDIDATE_ROLES:
                raise HandcraftedFinishBenchmarkError("candidate_role_invalid")
            if role in roles:
                raise HandcraftedFinishBenchmarkError("candidate_role_duplicate")
            roles.add(role)
            if (
                not isinstance(option_id, str)
                or not option_id
                or option_id in option_ids
            ):
                raise HandcraftedFinishBenchmarkError("candidate_option_id_invalid")
            option_ids.add(option_id)
            if candidate.get("meaning_preserved") is not True:
                raise HandcraftedFinishBenchmarkError("candidate_meaning_not_preserved")
            _string_list(candidate, "observable_finish_choices")
            x, y, width, height = _bbox(candidate.get("bbox_cm"))
            if x < 0 or y < 0 or x + width > canvas_width or y + height > canvas_height:
                raise HandcraftedFinishBenchmarkError("candidate_bbox_outside_canvas")
        if roles != CANDIDATE_ROLES:
            raise HandcraftedFinishBenchmarkError("candidate_roles_incomplete")
    return payload


def load_review(path: Path, *, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = _mapping(path)
    if payload.get("schema") != REVIEW_SCHEMA:
        raise HandcraftedFinishBenchmarkError("review_schema_invalid")
    if payload.get("review_authority") != "host_advisory_only":
        raise HandcraftedFinishBenchmarkError("host_review_authority_invalid")
    if payload.get("blinding_strength") != "masked_but_authorship_confounded":
        raise HandcraftedFinishBenchmarkError("blinding_strength_overclaim")
    if payload.get("creates_quality_reward") is not False:
        raise HandcraftedFinishBenchmarkError("host_review_cannot_create_reward")
    if payload.get("authorizes_rule_promotion") is not False:
        raise HandcraftedFinishBenchmarkError("host_review_cannot_promote_rule")
    if payload.get("publication_acceptance") != "not_claimed":
        raise HandcraftedFinishBenchmarkError("publication_acceptance_overclaim")
    motif_ids = {motif["id"] for motif in manifest["motifs"]}
    options_by_motif = {
        motif["id"]: {candidate["option_id"] for candidate in motif["candidates"]}
        for motif in manifest["motifs"]
    }
    results = payload.get("results")
    if not isinstance(results, list) or {result.get("motif_id") for result in results} != motif_ids:
        raise HandcraftedFinishBenchmarkError("review_results_incomplete")
    for result in results:
        if not isinstance(result, dict) or result.get("human_verdict") != "not_recorded":
            raise HandcraftedFinishBenchmarkError("human_verdict_overclaim")
        verdict = result.get("host_verdict")
        preference = result.get("host_preference")
        if verdict == "preferred_option":
            if preference not in options_by_motif[result["motif_id"]]:
                raise HandcraftedFinishBenchmarkError("host_preference_invalid")
        elif verdict == "no_viable_candidate":
            if preference is not None:
                raise HandcraftedFinishBenchmarkError("failed_set_cannot_name_preference")
        elif verdict == "repair_candidate_pending_human":
            if preference is not None:
                raise HandcraftedFinishBenchmarkError(
                    "pending_repair_cannot_name_preference"
                )
            if result.get("repair_candidate") not in options_by_motif[result["motif_id"]]:
                raise HandcraftedFinishBenchmarkError("repair_candidate_invalid")
        else:
            raise HandcraftedFinishBenchmarkError("host_verdict_invalid")
        _string_list(result, "observed_strengths")
        _string_list(result, "observed_risks")
    return payload


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_render_evidence(
    manifest_path: Path,
    render_path: Path,
    crop_dir: Path,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    source_path = manifest_path.parent / str(manifest["source"])
    if not source_path.is_file() or not render_path.is_file():
        raise HandcraftedFinishBenchmarkError("source_or_render_missing")
    crop_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(render_path) as image:
        rgb = image.convert("RGB")
        image_width, image_height = rgb.size
        canvas_width, canvas_height = (float(value) for value in manifest["canvas_cm"])
        crops: list[dict[str, Any]] = []
        for motif in manifest["motifs"]:
            for candidate in motif["candidates"]:
                x, y, width, height = candidate["bbox_cm"]
                left = round(float(x) / canvas_width * image_width)
                right = round((float(x) + float(width)) / canvas_width * image_width)
                top = round(
                    (canvas_height - float(y) - float(height))
                    / canvas_height
                    * image_height
                )
                bottom = round((canvas_height - float(y)) / canvas_height * image_height)
                crop = rgb.crop((left, top, right, bottom))
                original_path = crop_dir / f"{candidate['option_id']}_100.png"
                crop.save(original_path)
                scale_paths: dict[str, str] = {"100": original_path.as_posix()}
                for scale in (50, 33):
                    scaled = crop.resize(
                        (
                            max(1, round(crop.width * scale / 100)),
                            max(1, round(crop.height * scale / 100)),
                        ),
                        Image.Resampling.LANCZOS,
                    )
                    scaled_path = crop_dir / f"{candidate['option_id']}_{scale}.png"
                    scaled.save(scaled_path)
                    scale_paths[str(scale)] = scaled_path.as_posix()
                crops.append(
                    {
                        "motif_id": motif["id"],
                        "option_id": candidate["option_id"],
                        "bbox_px": [left, top, right, bottom],
                        "images": scale_paths,
                    }
                )
    return {
        "schema": EVIDENCE_SCHEMA,
        "fixture": manifest["fixture"],
        "manifest_sha256": _sha256(manifest_path),
        "source_sha256": _sha256(source_path),
        "render_sha256": _sha256(render_path),
        "render_size_px": [image_width, image_height],
        "publication_acceptance": "not_claimed",
        "crops": crops,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--render", type=Path)
    parser.add_argument("--crop-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    payload: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "fixture": manifest["fixture"],
        "motif_count": len(manifest["motifs"]),
        "candidate_count": sum(len(motif["candidates"]) for motif in manifest["motifs"]),
        "state": "contract_valid",
    }
    if args.review:
        review = load_review(args.review, manifest=manifest)
        payload["review_authority"] = review["review_authority"]
    if args.render or args.crop_dir or args.output:
        if not args.render or not args.crop_dir:
            parser.error("--render and --crop-dir are required together")
        payload = build_render_evidence(args.manifest, args.render, args.crop_dir)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
