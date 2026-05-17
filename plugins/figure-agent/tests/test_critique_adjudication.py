from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    load_adjudication,
    validate_adjudication,
    write_adjudication,
)
from quality_manifest import file_sha256  # noqa: E402


def _valid_payload(critique_hash: str = "sha256:" + "a" * 64) -> dict:
    return {
        "schema": "figure-agent.critique-adjudication.v1",
        "fixture": "demo_fig",
        "source_critique_hash": critique_hash,
        "decisions": [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps the trap lobe",
                "patch_target": "panel A label cluster",
                "evidence": "critique C001 and build/demo_fig.png",
            }
        ],
    }


def test_valid_adjudication_loads_successfully(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    write_adjudication(path, _valid_payload())

    data = load_adjudication(path)

    assert data["fixture"] == "demo_fig"
    assert data["decisions"][0]["finding_id"] == "C001"


def test_invalid_schema_fails() -> None:
    payload = _valid_payload()
    payload["schema"] = "figure-agent.critique-adjudication.v0"

    with pytest.raises(CritiqueAdjudicationError, match="schema"):
        validate_adjudication(payload)


def test_invalid_decision_value_fails() -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = "maybe"

    with pytest.raises(CritiqueAdjudicationError, match="decision"):
        validate_adjudication(payload)


def test_missing_required_fields_fail() -> None:
    payload = _valid_payload()
    del payload["source_critique_hash"]

    with pytest.raises(CritiqueAdjudicationError, match="source_critique_hash"):
        validate_adjudication(payload)


@pytest.mark.parametrize("field", ("fixture", "decisions"))
def test_missing_top_level_required_fields_fail(field: str) -> None:
    payload = _valid_payload()
    del payload[field]

    with pytest.raises(CritiqueAdjudicationError, match=field):
        validate_adjudication(payload)


@pytest.mark.parametrize("field", ("finding_id", "reason"))
def test_missing_decision_required_fields_fail(field: str) -> None:
    payload = _valid_payload()
    del payload["decisions"][0][field]

    with pytest.raises(CritiqueAdjudicationError, match=field):
        validate_adjudication(payload)


def test_invalid_source_critique_hash_prefix_fails() -> None:
    payload = _valid_payload("md5:" + "a" * 32)

    with pytest.raises(CritiqueAdjudicationError, match="sha256"):
        validate_adjudication(payload)


def test_malformed_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    path.write_text("schema: [unterminated\n", encoding="utf-8")

    with pytest.raises(CritiqueAdjudicationError, match="invalid YAML"):
        load_adjudication(path)


def test_matching_critique_hash_is_fresh(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload(file_sha256(critique)))

    assert adjudication_is_stale(adjudication, critique) is False


def test_stale_adjudication_is_detected_when_critique_changes(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload(file_sha256(critique)))

    critique.write_text("# critique v2\n", encoding="utf-8")

    assert adjudication_is_stale(adjudication, critique) is True


def test_stale_check_fails_cleanly_when_critique_is_missing(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload())

    with pytest.raises(CritiqueAdjudicationError, match="missing critique"):
        adjudication_is_stale(adjudication, critique)


def test_unknown_future_fields_survive_load_write(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["reviewer"] = "host-llm"
    payload["decisions"][0]["confidence"] = "medium"
    path = tmp_path / "critique_adjudication.yaml"

    write_adjudication(path, payload)
    loaded = load_adjudication(path)
    rewrite_path = tmp_path / "rewritten.yaml"
    write_adjudication(rewrite_path, loaded)

    rewritten = load_adjudication(rewrite_path)
    assert rewritten["reviewer"] == "host-llm"
    assert rewritten["decisions"][0]["confidence"] == "medium"


def test_writer_emits_reloadable_yaml(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    write_adjudication(path, _valid_payload())

    reloaded = load_adjudication(path)

    assert validate_adjudication(reloaded) == reloaded


@pytest.mark.parametrize("decision", ("apply", "resolved"))
def test_apply_and_resolved_require_patch_target_and_evidence(decision: str) -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = decision
    payload["decisions"][0]["patch_target"] = ""
    payload["decisions"][0]["evidence"] = ""

    with pytest.raises(CritiqueAdjudicationError, match="patch_target"):
        validate_adjudication(payload)


def test_apply_requires_evidence_when_patch_target_is_present() -> None:
    payload = _valid_payload()
    payload["decisions"][0]["evidence"] = ""

    with pytest.raises(CritiqueAdjudicationError, match="evidence"):
        validate_adjudication(payload)


@pytest.mark.parametrize("decision", ("dismiss", "defer", "needs_human"))
def test_non_patch_decisions_allow_empty_patch_target_and_evidence(decision: str) -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = decision
    payload["decisions"][0]["patch_target"] = ""
    payload["decisions"][0]["evidence"] = ""

    assert validate_adjudication(payload) == payload
