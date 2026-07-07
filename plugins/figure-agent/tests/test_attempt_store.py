from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import attempt_store  # noqa: E402


def _attempt(attempt_id: str, parent_attempt_id: str | None = None) -> dict[str, object]:
    return {
        "schema": "figure-agent.figure-attempt.v1",
        "attempt_id": attempt_id,
        "parent_attempt_id": parent_attempt_id,
        "figure_id": "demo",
        "user_goal": "improve figure",
        "target_medium": "journal_paper",
        "target_journal": "Nature Communications",
        "figure_type": "mechanism_schematic",
        "spec_hash": "sha256:" + "1" * 64,
        "journal_guide_hash": "sha256:" + "2" * 64,
        "render_backend": "tikz_lualatex",
        "outputs": {
            "editable": "examples/demo/demo.tex",
            "preview_png": "examples/demo/build/demo.png",
            "pdf": "examples/demo/build/demo.pdf",
        },
        "journal_constraints": {"passed": True, "violations": []},
        "semantic_score": {
            "complete": True,
            "missing_elements": [],
            "incorrect_relations": [],
        },
        "aesthetic_score": {
            "overall": 0.8,
            "clarity": 0.8,
            "visual_hierarchy": 0.8,
            "balance": 0.8,
            "readability": 0.8,
            "density_control": 0.8,
            "restraint": 0.8,
            "journal_elegance": 0.8,
        },
        "issues": [],
        "edit_plan": [],
        "decision": "accept",
    }


def test_append_and_read_attempts_preserves_parent_chain(tmp_path: Path) -> None:
    result1 = attempt_store.append_attempt(
        "demo",
        _attempt("attempt-001"),
        plugin_root=tmp_path,
    )
    result2 = attempt_store.append_attempt(
        "demo",
        _attempt("attempt-002", parent_attempt_id="attempt-001"),
        plugin_root=tmp_path,
    )

    assert result1["writes"] == ["docs/attempts/demo.jsonl"]
    assert result2["writes"] == ["docs/attempts/demo.jsonl"]
    rows = attempt_store.read_attempts("demo", plugin_root=tmp_path)
    assert [row["attempt_id"] for row in rows] == ["attempt-001", "attempt-002"]
    assert rows[1]["parent_attempt_id"] == "attempt-001"
    raw_rows = (tmp_path / "docs" / "attempts" / "demo.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(raw_rows) == 2
    assert json.loads(raw_rows[0])["record_hash"].startswith("sha256:")


def test_append_attempt_refuses_unsafe_fixture_name(tmp_path: Path) -> None:
    with pytest.raises(attempt_store.AttemptStoreError):
        attempt_store.append_attempt("../escape", _attempt("attempt-001"), plugin_root=tmp_path)


def test_append_attempt_refuses_symlinked_log(tmp_path: Path) -> None:
    log_dir = tmp_path / "docs" / "attempts"
    log_dir.mkdir(parents=True)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("", encoding="utf-8")
    (log_dir / "demo.jsonl").symlink_to(outside)

    with pytest.raises(attempt_store.AttemptStoreError, match="attempt_log_symlink"):
        attempt_store.append_attempt("demo", _attempt("attempt-001"), plugin_root=tmp_path)
