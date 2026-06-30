from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from human_decision_record import validate_decision_record  # noqa: E402


def test_documented_human_decision_records_validate() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    record_paths = sorted((plugin_root / "docs" / "decision-records").glob("**/*.json"))

    assert record_paths
    for record_path in record_paths:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        validated = validate_decision_record(record)
        assert validated["fixture"] == record["fixture"]
