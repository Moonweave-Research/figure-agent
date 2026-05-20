from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_adjudication import write_adjudication  # noqa: E402
from fig_loop_adjudication import adjudication_state  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _write_valid_adjudication(example_dir: Path, critique_hash: str) -> None:
    write_adjudication(
        example_dir / "critique_adjudication.yaml",
        {
            "schema": "figure-agent.critique-adjudication.v1",
            "fixture": example_dir.name,
            "source_critique_hash": critique_hash,
            "decisions": [
                {
                    "finding_id": "C001",
                    "decision": "defer",
                    "reason": "requires visual confirmation",
                }
            ],
        },
    )


def test_adjudication_state_reports_missing_file(tmp_path: Path) -> None:
    state = adjudication_state(tmp_path)

    assert state == {
        "state": "missing",
        "path": str(tmp_path / "critique_adjudication.yaml"),
        "decision_count": 0,
    }


def test_adjudication_state_reports_fresh_adjudication(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_valid_adjudication(tmp_path, file_sha256(critique))

    state = adjudication_state(tmp_path)

    assert state["state"] == "fresh"
    assert state["decision_count"] == 1
    assert state["decisions"][0]["finding_id"] == "C001"
    assert state["source_critique_hash"] == file_sha256(critique)


def test_adjudication_state_reports_stale_hash(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    _write_valid_adjudication(tmp_path, file_sha256(critique))
    critique.write_text("# critique v2\n", encoding="utf-8")

    state = adjudication_state(tmp_path)

    assert state["state"] == "stale"
    assert state["decision_count"] == 1


def test_adjudication_state_reports_invalid_without_traceback(tmp_path: Path) -> None:
    (tmp_path / "critique_adjudication.yaml").write_text(
        "schema: [unterminated\n",
        encoding="utf-8",
    )

    state = adjudication_state(tmp_path)

    assert state["state"] == "invalid"
    assert state["decision_count"] == 0
    assert "invalid YAML" in state["error"]
