"""Build blinded image reviews and aggregate non-compensating verdicts."""

from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path
from typing import Any

import yaml
from hybrid.comparison_report import aggregate_review_input_hash
from PIL import Image, ImageChops, ImageOps, PngImagePlugin, UnidentifiedImageError
from PIL import __version__ as PILLOW_VERSION

VISUAL_DIMENSIONS = {"composition", "illustration_quality", "typography"}
VISUAL_VALUES = {"better", "equivalent", "worse"}
PANEL_CLASSIFICATIONS = {
    "better",
    "equivalent",
    "worse",
    "rejected_scientific_fidelity",
}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EXACT_GEOMETRY_POLICY = "exact_authority_size.v1"
CONTAIN_GEOMETRY_POLICY = "contain_white_pad_authority_size.v1"
GEOMETRY_POLICIES = {EXACT_GEOMETRY_POLICY, CONTAIN_GEOMETRY_POLICY}


class DirectSvgReviewError(ValueError):
    """Raised when blinded evidence or a human verdict violates the protocol."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _opaque_sha256(path: Path, *, seed: str, purpose: str) -> str:
    digest = hashlib.sha256()
    digest.update(b"figure-agent.opaque-public-hash.v1\0")
    digest.update(seed.encode())
    digest.update(b"\0")
    digest.update(purpose.encode())
    digest.update(b"\0")
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DirectSvgReviewError(f"{field}_invalid")
    return value


def _normalize_image(
    source: Path,
    destination: Path,
    *,
    size: tuple[int, int],
    policy: str = EXACT_GEOMETRY_POLICY,
    packet_id: str | None = None,
) -> None:
    if policy not in GEOMETRY_POLICIES:
        raise DirectSvgReviewError("review_geometry_policy_invalid")
    try:
        with Image.open(source) as opened:
            if policy == EXACT_GEOMETRY_POLICY and opened.size != size:
                raise DirectSvgReviewError("review_geometry_mismatch")
            converted = opened.convert("RGB")
            if policy == CONTAIN_GEOMETRY_POLICY and converted.size != size:
                contained = ImageOps.contain(
                    converted,
                    size,
                    method=Image.Resampling.LANCZOS,
                )
                normalized = Image.new("RGB", size, "white")
                left = (size[0] - contained.width) // 2
                top = (size[1] - contained.height) // 2
                normalized.paste(contained, (left, top))
            else:
                normalized = converted
            png_info = PngImagePlugin.PngInfo()
            if packet_id is not None:
                png_info.add_text("packet_id", packet_id)
            normalized.save(destination, format="PNG", pnginfo=png_info)
    except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
        raise DirectSvgReviewError("review_image_invalid") from exc


def _write_diagnostics(
    option_a: Path,
    option_b: Path,
    output_dir: Path,
    *,
    seed: str,
) -> list[dict[str, Any]]:
    with Image.open(option_a) as first, Image.open(option_b) as second:
        difference = ImageChops.difference(first.convert("RGB"), second.convert("RGB"))
        difference_path = output_dir / "diagnostic-difference.png"
        difference.save(difference_path, format="PNG")
        flicker_path = output_dir / "diagnostic-flicker.gif"
        first.convert("RGB").save(
            flicker_path,
            format="GIF",
            save_all=True,
            append_images=[second.convert("RGB")],
            duration=500,
            loop=0,
            disposal=2,
        )
    return [
        {
            "kind": "difference",
            "path": difference_path.name,
            "sha256": _opaque_sha256(
                difference_path, seed=seed, purpose="diagnostic-difference"
            ),
            "diagnostic_only": True,
        },
        {
            "kind": "flicker",
            "path": flicker_path.name,
            "sha256": _opaque_sha256(
                flicker_path, seed=seed, purpose="diagnostic-flicker"
            ),
            "diagnostic_only": True,
        },
    ]


def build_review_packet(
    comparator_png: Path,
    candidate_png: Path,
    output_dir: Path,
    *,
    seed: str,
    private_manifest_path: Path,
    candidate_normalization_policy: str = EXACT_GEOMETRY_POLICY,
) -> dict[str, Any]:
    """Create opaque normalized options, private assignments, and diagnostics."""
    if not isinstance(seed, str) or not seed:
        raise DirectSvgReviewError("blinding_seed_required")
    if private_manifest_path.resolve().is_relative_to(output_dir.resolve()):
        raise DirectSvgReviewError("private_output_must_be_separate")
    try:
        with Image.open(comparator_png) as authority:
            authority_size = authority.size
    except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
        raise DirectSvgReviewError("review_image_invalid") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    sources = {"comparator": comparator_png, "candidate": candidate_png}
    assignments = ["comparator", "candidate"]
    random.Random(seed).shuffle(assignments)
    blinding_key = {letter: source for letter, source in zip(("A", "B"), assignments)}

    public_options: dict[str, dict[str, str]] = {}
    score_inputs: list[dict[str, str]] = []
    for letter in ("A", "B"):
        destination = output_dir / f"option-{letter.lower()}.png"
        policy = (
            candidate_normalization_policy
            if blinding_key[letter] == "candidate"
            else EXACT_GEOMETRY_POLICY
        )
        _normalize_image(
            sources[blinding_key[letter]],
            destination,
            size=authority_size,
            policy=policy,
            packet_id=hashlib.sha256(
                f"{seed}\0option-{letter}".encode()
            ).hexdigest(),
        )
        item = {
            "role": f"opaque_option_{letter}",
            "path": destination.name,
            "sha256": _opaque_sha256(
                destination, seed=seed, purpose=f"option-{letter}"
            ),
        }
        score_inputs.append(item)
        public_options[letter] = {"path": item["path"], "sha256": item["sha256"]}

    diagnostics = _write_diagnostics(
        output_dir / "option-a.png",
        output_dir / "option-b.png",
        output_dir,
        seed=seed,
    )
    toolchain = {
        "pillow": PILLOW_VERSION,
        "normalization": {
            "policy_set": [EXACT_GEOMETRY_POLICY, CONTAIN_GEOMETRY_POLICY],
            "application": "opaque",
            "resampling": "LANCZOS",
            "contain_mode": "aspect_preserving_centered_white_canvas",
        },
    }
    review_input_hash = aggregate_review_input_hash(score_inputs, toolchain)
    public_manifest = {
        "schema": "figure-agent.blind-review.v1",
        "options": public_options,
        "score_inputs": score_inputs,
        "diagnostics": diagnostics,
        "toolchain": toolchain,
        "review_input_hash": review_input_hash,
        "publication_acceptance": "not_claimed",
    }
    public_path = output_dir / "public-review-manifest.yaml"
    public_path.write_text(yaml.safe_dump(public_manifest, sort_keys=False), encoding="utf-8")

    private_manifest = {
        "schema": "figure-agent.blinding-key.v1",
        "assignments": blinding_key,
        "content_sha256": {
            letter: _sha256(output_dir / f"option-{letter.lower()}.png")
            for letter in ("A", "B")
        },
        "seed_sha256": f"sha256:{hashlib.sha256(seed.encode()).hexdigest()}",
        "public_manifest_sha256": _sha256(public_path),
        "review_input_hash": review_input_hash,
        "publication_acceptance": "not_claimed",
    }
    private_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    private_manifest_path.write_text(
        yaml.safe_dump(private_manifest, sort_keys=False), encoding="utf-8"
    )
    return {
        "public_options": public_options,
        "public_manifest": public_manifest,
        "blinding_key": private_manifest,
        "public_manifest_path": public_path,
        "private_blinding_key_path": private_manifest_path,
    }


def panel_verdict(
    *,
    scientific_fidelity: str,
    composition: str,
    illustration_quality: str,
    typography: str,
    scientific_evidence: str | None = None,
) -> dict[str, Any]:
    """Build one panel verdict without collapsing independent dimensions."""
    return {
        "scientific_fidelity": scientific_fidelity,
        "scientific_evidence": scientific_evidence,
        "composition": composition,
        "illustration_quality": illustration_quality,
        "typography": typography,
    }


def classify_panel_verdict(verdict: dict[str, Any]) -> str:
    """Apply a scientific hard gate and non-compensating visual aggregation."""
    if verdict.get("scientific_fidelity") == "fail":
        return "rejected_scientific_fidelity"
    if verdict.get("scientific_fidelity") != "pass":
        raise DirectSvgReviewError("scientific_fidelity_invalid")
    visual = {name: verdict.get(name) for name in VISUAL_DIMENSIONS}
    if any(value not in VISUAL_VALUES for value in visual.values()):
        raise DirectSvgReviewError("visual_verdict_invalid")
    if "worse" in visual.values():
        return "worse"
    if "better" in visual.values():
        return "better"
    return "equivalent"


def classify_quality_hypothesis(panel_results: dict[str, str]) -> str:
    """Require both C/F to be no worse and at least one to be better."""
    if set(panel_results) != {"C", "F"} or any(
        result not in PANEL_CLASSIFICATIONS for result in panel_results.values()
    ):
        raise DirectSvgReviewError("panel_results_invalid")
    if any(
        result in {"worse", "rejected_scientific_fidelity"}
        for result in panel_results.values()
    ):
        return "failed"
    if "better" in panel_results.values():
        return "passed"
    return "not_demonstrated"


def validate_review_verdict(verdict: dict[str, Any]) -> dict[str, Any]:
    """Validate named review evidence and derive the separate quality result."""
    if verdict.get("schema") != "figure-agent.direct-svg-review-verdict.v1":
        raise DirectSvgReviewError("review_verdict_schema_invalid")
    if not HASH_PATTERN.fullmatch(str(verdict.get("review_input_hash", ""))):
        raise DirectSvgReviewError("review_input_hash_invalid")
    reviewers = verdict.get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        raise DirectSvgReviewError("named_reviewer_required")
    for reviewer in reviewers:
        item = _mapping(reviewer, "reviewer")
        if not item.get("name") or not item.get("reviewed_at"):
            raise DirectSvgReviewError("named_reviewer_required")
    borderline = verdict.get("borderline")
    second_required = verdict.get("second_review_required")
    if not isinstance(borderline, bool) or not isinstance(second_required, bool):
        raise DirectSvgReviewError("review_escalation_state_invalid")
    if borderline and not second_required:
        raise DirectSvgReviewError("second_review_required_for_borderline")
    if second_required and len(reviewers) < 2:
        raise DirectSvgReviewError("second_reviewer_required")

    panels = _mapping(verdict.get("panels"), "panels")
    if set(panels) != {"C", "F"}:
        raise DirectSvgReviewError("panels_must_be_C_and_F")
    classifications: dict[str, str] = {}
    for panel, raw in panels.items():
        panel_data = _mapping(raw, f"panel_{panel}")
        if not panel_data.get("scientific_evidence"):
            raise DirectSvgReviewError("scientific_evidence_required")
        classifications[panel] = classify_panel_verdict(panel_data)

    editability = _mapping(verdict.get("editability_cost"), "editability_cost")
    if editability.get("verdict") not in VISUAL_VALUES or not editability.get("evidence"):
        raise DirectSvgReviewError("editability_cost_invalid")
    cold_runs = verdict.get("cold_run_count")
    if not isinstance(cold_runs, int) or isinstance(cold_runs, bool) or cold_runs < 0:
        raise DirectSvgReviewError("cold_run_count_invalid")
    if verdict.get("publication_acceptance") != "not_claimed":
        raise DirectSvgReviewError("publication_claim_forbidden")

    result = dict(verdict)
    result["panel_classifications"] = classifications
    result["quality_hypothesis"] = classify_quality_hypothesis(classifications)
    return result
