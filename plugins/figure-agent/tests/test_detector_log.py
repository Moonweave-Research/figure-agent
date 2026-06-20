from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


from detector_log import log_detector_run  # noqa: E402


def _read_records(log_path: Path) -> list[dict]:
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]


def test_writes_one_record_with_expected_keys_and_values(tmp_path: Path):
    log_path = tmp_path / "detector_log.jsonl"
    wrote = log_detector_run(
        "label_hyphenation",
        fired=True,
        finding_count=3,
        duration_ms=1.5,
        log_path=log_path,
    )
    assert wrote is True
    records = _read_records(log_path)
    assert len(records) == 1
    record = records[0]
    assert set(record) == {"name", "fired", "finding_count", "duration_ms", "ts"}
    assert record["name"] == "label_hyphenation"
    assert record["fired"] is True
    assert record["finding_count"] == 3


def test_appends_rather_than_overwrites(tmp_path: Path):
    log_path = tmp_path / "detector_log.jsonl"
    log_detector_run("a", fired=False, finding_count=0, log_path=log_path)
    log_detector_run("b", fired=True, finding_count=2, log_path=log_path)
    records = _read_records(log_path)
    assert [r["name"] for r in records] == ["a", "b"]


def test_clean_run_records_fired_false_and_omits_duration(tmp_path: Path):
    log_path = tmp_path / "detector_log.jsonl"
    log_detector_run("clean", fired=False, finding_count=0, log_path=log_path)
    record = _read_records(log_path)[0]
    assert record["fired"] is False
    assert record["finding_count"] == 0
    assert record["duration_ms"] is None


def test_noop_when_directory_missing(tmp_path: Path):
    log_path = tmp_path / "absent" / "detector_log.jsonl"
    wrote = log_detector_run("x", fired=True, finding_count=1, log_path=log_path)
    assert wrote is False
    assert not log_path.exists()
    assert not log_path.parent.exists()
