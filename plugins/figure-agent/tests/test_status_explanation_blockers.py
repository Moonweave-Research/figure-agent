from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from publication_gate import PublicationGateFailure  # noqa: E402
from status_explanation import build_status_explanation  # noqa: E402


def _status_with_two_gate_failures() -> dict[str, object]:
    return {
        "name": "fig",
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "acceptance_state": "ACCEPTED",
        "publication_gate_state": "PROVENANCE_REQUIRED",
        "publication_gate_failures": [
            PublicationGateFailure(
                code="missing_submission_safe_true",
                category="provenance",
                actor="human",
                message="submission-safe not declared",
                required_action="declare submission-safe",
            ),
            {
                "code": "invalid_human_attestation",
                "category": "provenance",
                "actor": "human",
                "message": "attestation hash is stale",
                "required_action": "run fig-agent attest",
            },
        ],
        "stage": 4,
        "release_ready": False,
    }


def test_publication_gate_blocker_lists_every_failure() -> None:
    explanation = build_status_explanation(_status_with_two_gate_failures())

    entry = next(
        item
        for item in explanation["buckets"]["human_blockers"]
        if item["code"] == "publication_gate_required"
    )
    assert [item["code"] for item in entry["blockers"]] == [
        "missing_submission_safe_true",
        "invalid_human_attestation",
    ]
    assert "invalid_human_attestation: run fig-agent attest" in entry["message"]
    assert "blockers (2)" in entry["message"]


def test_publication_gate_blocker_without_failure_list_stays_generic() -> None:
    status = _status_with_two_gate_failures()
    status["publication_gate_failures"] = []

    explanation = build_status_explanation(status)

    entry = next(
        item
        for item in explanation["buckets"]["human_blockers"]
        if item["code"] == "publication_gate_required"
    )
    assert entry["blockers"] == []
    assert "blockers (" not in entry["message"]
