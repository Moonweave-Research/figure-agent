import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import recover_experience_records  # noqa: E402


def _record(record_id: str, fixture: str = "demo") -> dict[str, object]:
    return {
        "schema": "figure-agent.experience-record.v1",
        "record_id": record_id,
        "fixture": fixture,
    }


def _write(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def test_recovery_is_deduplicated_and_dry_run_safe(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    destination = plugin_root / "docs" / "experience-log" / "demo.jsonl"
    _write(destination, [_record("kept")])
    source = tmp_path / "source.jsonl"
    _write(source, [_record("kept"), _record("recovered"), _record("recovered")])

    records = recover_experience_records._json_lines(source.read_text(), "source")
    preview = recover_experience_records.recover_records(
        plugin_root, [("source", records)], execute=False
    )

    assert preview["recovered_total"] == 1
    assert preview["writes"] == []
    assert destination.read_text(encoding="utf-8").count("recovered") == 0

    applied = recover_experience_records.recover_records(
        plugin_root, [("source", records)], execute=True
    )
    assert applied["writes"] == ["docs/experience-log/demo.jsonl"]
    assert destination.read_text(encoding="utf-8").count("recovered") == 1


def test_recovery_rejects_same_record_id_with_different_payload(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    destination = plugin_root / "docs" / "experience-log" / "demo.jsonl"
    _write(destination, [_record("conflict")])
    changed = _record("conflict")
    changed["outcome"] = "different"

    with pytest.raises(recover_experience_records.RecoveryError, match="record_conflict"):
        recover_experience_records.recover_records(
            plugin_root, [("source", [changed])], execute=False
        )
