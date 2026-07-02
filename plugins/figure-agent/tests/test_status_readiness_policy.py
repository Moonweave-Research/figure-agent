"""Focused regression tests for /fig_status readiness policy."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_freshness import EXPORT_FRESH, EXPORT_TRACKED_GOLDEN  # noqa: E402
from status_readiness_policy import build_status_vector  # noqa: E402


def _vector(
    *,
    stage: int = 4,
    notes: list[str] | None = None,
    accepted: bool | None = True,
    exports_substate: str = EXPORT_FRESH,
    render_state: str = "FRESH",
    critique_state: str = "FRESH",
    final_artifact: dict | None = None,
    publication_gate: dict | None = None,
) -> dict:
    return build_status_vector(
        stage=stage,
        notes=notes or [],
        accepted=accepted,
        exports_substate=exports_substate,
        render_state=render_state,
        critique_state=critique_state,
        final_artifact=final_artifact
        or {
            "state": "NONE",
            "kind": "generated_export",
            "path": "exports/demo.svg",
        },
        publication_gate=publication_gate,
    )


def test_spec_parse_note_blocks_workflow_and_release_readiness() -> None:
    vector = _vector(notes=["spec_parse_error"])

    assert vector["workflow_ready"] is False
    assert vector["golden_ready"] is False
    assert vector["release_ready"] is False
    assert vector["final_ready"] is False


def test_tracked_golden_is_golden_ready_but_not_release_ready() -> None:
    vector = _vector(exports_substate=EXPORT_TRACKED_GOLDEN)

    assert vector["workflow_ready"] is True
    assert vector["golden_ready"] is True
    assert vector["release_ready"] is False
    assert vector["final_ready"] is False
def test_publication_gate_fields_are_preserved_in_status_vector() -> None:
    publication_gate = {
        "publication_gate_state": "PROVENANCE_REQUIRED",
        "publication_gate_failures": [{"code": "missing_submission_safe_true"}],
    }

    vector = _vector(publication_gate=publication_gate)

    assert vector["publication_gate_state"] == "PROVENANCE_REQUIRED"
    assert vector["publication_gate_failures"] == [
        {"code": "missing_submission_safe_true"}
    ]


def test_accepted_stale_vector_preserves_history_but_blocks_current_readiness() -> None:
    vector = _vector(notes=["stale_export"], accepted=True)

    assert vector["acceptance_state"] == "ACCEPTED"
    assert vector["acceptance_freshness_state"] == "accepted_but_stale"
    assert vector["workflow_ready"] is False
    assert vector["golden_ready"] is False
    assert vector["release_ready"] is False
    assert vector["final_ready"] is False
