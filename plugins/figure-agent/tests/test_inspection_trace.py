from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from inspection_trace import (  # noqa: E402
    InspectionTraceError,
    load_optional_inspection_trace,
    main,
)
from quality_manifest import file_sha256  # noqa: E402


def _write_fixture(tmp_path: Path) -> Path:
    fixture = tmp_path / "examples" / "demo_fig"
    (fixture / "build" / "audit_crops").mkdir(parents=True)
    (fixture / "build" / "audit_crops" / "full_q1.png").write_bytes(b"crop")
    return fixture


def _write_trace(fixture: Path, *, artifact_hash: str | None = None) -> Path:
    crop = fixture / "build" / "audit_crops" / "full_q1.png"
    trace = fixture / "inspection_trace.yaml"
    trace.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.inspection-trace.v1",
                "fixture": fixture.name,
                "source": "subagent",
                "inspected_artifacts": [
                    {
                        "id": "full_q1",
                        "path": "build/audit_crops/full_q1.png",
                        "sha256": artifact_hash or file_sha256(crop),
                        "verdict": "inspected",
                        "note": "subagent read this crop",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return trace


def test_load_optional_inspection_trace_reports_missing_as_not_applicable(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(tmp_path)

    result = load_optional_inspection_trace(fixture)

    assert result["state"] == "not_applicable"
    assert result["trace"] is None


def test_load_optional_inspection_trace_validates_artifact_hash(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    _write_trace(fixture)

    result = load_optional_inspection_trace(fixture)

    assert result["state"] == "pass"
    assert result["trace"]["schema"] == "figure-agent.inspection-trace.v1"
    assert result["trace"]["inspected_artifacts"][0]["id"] == "full_q1"


def test_load_optional_inspection_trace_rejects_duplicate_ids(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    trace = _write_trace(fixture)
    payload = yaml.safe_load(trace.read_text(encoding="utf-8"))
    payload["inspected_artifacts"].append(dict(payload["inspected_artifacts"][0]))
    trace.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(InspectionTraceError, match="duplicate id: full_q1"):
        load_optional_inspection_trace(fixture)


def test_load_optional_inspection_trace_rejects_empty_artifact_list(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    trace = _write_trace(fixture)
    payload = yaml.safe_load(trace.read_text(encoding="utf-8"))
    payload["inspected_artifacts"] = []
    trace.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(InspectionTraceError, match="must be a non-empty list"):
        load_optional_inspection_trace(fixture)


def test_load_optional_inspection_trace_rejects_path_traversal(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    trace = _write_trace(fixture)
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    payload = yaml.safe_load(trace.read_text(encoding="utf-8"))
    payload["inspected_artifacts"][0]["path"] = "../../outside.png"
    payload["inspected_artifacts"][0]["sha256"] = file_sha256(outside)
    trace.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(InspectionTraceError, match="must stay inside"):
        load_optional_inspection_trace(fixture)


def test_load_optional_inspection_trace_rejects_missing_artifact(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    trace = _write_trace(fixture)
    payload = yaml.safe_load(trace.read_text(encoding="utf-8"))
    payload["inspected_artifacts"][0]["path"] = "build/audit_crops/missing.png"
    trace.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(InspectionTraceError, match="missing inspected artifact"):
        load_optional_inspection_trace(fixture)


def test_load_optional_inspection_trace_rejects_stale_hash(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    _write_trace(fixture, artifact_hash="sha256:bad")

    with pytest.raises(InspectionTraceError, match="hash mismatch"):
        load_optional_inspection_trace(fixture)


def test_load_optional_inspection_trace_rejects_malformed_yaml(tmp_path: Path) -> None:
    fixture = _write_fixture(tmp_path)
    (fixture / "inspection_trace.yaml").write_text("inspected_artifacts: [", encoding="utf-8")

    with pytest.raises(InspectionTraceError, match="invalid YAML"):
        load_optional_inspection_trace(fixture)


def test_inspection_trace_cli_validates_fixture_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write_fixture(tmp_path)
    _write_trace(fixture)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["validate", str(fixture)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "inspection_trace.py: valid" in captured.out


def test_inspection_trace_cli_reports_controlled_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = _write_fixture(tmp_path)
    _write_trace(fixture, artifact_hash="sha256:bad")
    monkeypatch.chdir(tmp_path)

    exit_code = main(["validate", str(fixture)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "hash mismatch" in captured.err


def test_inspection_trace_cli_rejects_traversal_or_outside_relative_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    outside = tmp_path / "outside"
    (outside / "build" / "audit_crops").mkdir(parents=True)
    (outside / "build" / "audit_crops" / "full_q1.png").write_bytes(b"crop")
    _write_trace(outside)
    _write_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert main(["validate", "examples/../outside"]) == 1
    assert "invalid fixture path" in capsys.readouterr().err

    assert main(["validate", "outside"]) == 1
    assert "relative fixture names must resolve under examples/" in capsys.readouterr().err
