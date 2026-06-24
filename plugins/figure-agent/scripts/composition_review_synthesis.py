from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA: Final = "figure-agent.composition-review-synthesis.v1"


class CompositionReviewSynthesisError(ValueError):
    pass


def _load_review_packet(
    name: str,
    review_packet_path: str,
    workspace: Path,
) -> dict[str, Any]:
    path = candidate_contracts.fixture_local_output_path(workspace, name, review_packet_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompositionReviewSynthesisError("review_packet_invalid")
    if payload.get("schema") != "figure-agent.composition-review-packet.v1":
        raise CompositionReviewSynthesisError("review_packet_schema_invalid")
    return payload


def _markdown(packet: dict[str, Any]) -> str:
    candidate_id = str(packet.get("candidate_id") or "")
    apply_boundary = packet.get("apply_boundary")
    mutation_disabled = (
        isinstance(apply_boundary, dict)
        and apply_boundary.get("source_mutation_allowed") is False
    )
    confirmed = []
    if candidate_id and mutation_disabled:
        confirmed.append(
            f"- Candidate `{candidate_id}` is review-ready with source mutation disabled."
        )
    if packet.get("human_review_required") is True:
        confirmed.append("- Human review is required before acceptance or apply.")
    visual_evidence = packet.get("visual_evidence")
    if isinstance(visual_evidence, dict) and visual_evidence.get("visual_metrics"):
        confirmed.append("- Visual metrics were emitted as deterministic artifact evidence.")
    confirmed_text = "\n".join(confirmed) if confirmed else "- None."
    return "\n".join(
        [
            "# Composition Review Synthesis",
            "",
            "## Confirmed",
            "",
            confirmed_text,
            "",
            "## Refuted",
            "",
            "- None.",
            "",
            "## Unverified",
            "",
            "- Human visual preference remains unverified until acceptance.",
            "",
            "## Acceptance Recommendation",
            "",
            "Human review required before apply.",
            "",
        ]
    )


def write_review_synthesis(
    name: str,
    *,
    review_packet_path: str,
    output_path: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace_root)
    packet = _load_review_packet(name, review_packet_path, paths.workspace_root)
    output = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        output_path,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_markdown(packet), encoding="utf-8")
    return {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": packet.get("candidate_id"),
        "status": "review_synthesis_ready",
        "path": output.relative_to(paths.workspace_root / "examples" / name).as_posix(),
        "hard_refutations": [],
        "acceptance_recommendation": "human_review_required_before_apply",
    }
