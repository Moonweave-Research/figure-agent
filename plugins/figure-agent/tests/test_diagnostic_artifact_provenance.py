from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import diagnostic_artifact_provenance  # noqa: E402
from diagnostic_artifact_provenance import classify_artifact, provenance_report  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _write_fixture(tmp_path: Path) -> Path:
    example_dir = tmp_path / "examples" / "demo"
    build_dir = example_dir / "build"
    crop_dir = build_dir / "audit_crops"
    crop_dir.mkdir(parents=True)
    (build_dir / "demo.png").write_bytes(b"current render\n")
    (build_dir / "demo.pdf").write_bytes(b"current pdf\n")
    crop_path = crop_dir / "full_q1.png"
    crop_path.write_bytes(b"manifest crop\n")
    manifest = {
        "schema": "figure-agent.audit-crop-manifest.v1",
        "fixture": "demo",
        "render_path": "build/demo.png",
        "required_crop_ids": ["full_q1"],
        "crops": [
            {
                "id": "full_q1",
                "kind": "zoom_crop",
                "source": "full_render",
                "path": "build/audit_crops/full_q1.png",
                "source_path": "build/demo.png",
                "bbox_px": [0, 0, 10, 10],
                "sha256": file_sha256(crop_path),
            }
        ],
    }
    (crop_dir / "manifest.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    return example_dir


def test_manifest_bound_crop_is_authoritative_when_hash_matches(tmp_path: Path) -> None:
    example_dir = _write_fixture(tmp_path)

    result = classify_artifact(example_dir, example_dir / "build/audit_crops/full_q1.png")

    assert result["classification"] == "manifest_bound_current"
    assert result["authoritative"] is True
    assert result["manifest_crop_id"] == "full_q1"


def test_build_render_is_authoritative_artifact_but_points_to_status_freshness(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)

    result = classify_artifact(example_dir, example_dir / "build/demo.png")

    assert result["classification"] == "build_render_current"
    assert result["authoritative"] is True
    assert "/fig_status" in result["reason"]


def test_manifest_bound_crop_is_not_authoritative_when_hash_mismatches(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    crop = example_dir / "build/audit_crops/full_q1.png"
    crop.write_bytes(b"edited crop\n")

    result = classify_artifact(example_dir, crop)

    assert result["classification"] == "stale_or_mismatched"
    assert result["authoritative"] is False
    assert result["reason"] == "path is in audit manifest but file hash differs"


def test_scratch_crop_older_than_current_render_is_stale_or_unbound(tmp_path: Path) -> None:
    example_dir = _write_fixture(tmp_path)
    scratch_crop = tmp_path / ".scratch" / "debug" / "old_panel.png"
    scratch_crop.parent.mkdir(parents=True)
    scratch_crop.write_bytes(b"old crop\n")
    import os

    os.utime(example_dir / "build/demo.png", (200, 200))
    os.utime(scratch_crop, (100, 100))

    result = classify_artifact(example_dir, scratch_crop)

    assert result["classification"] == "stale_or_unbound"
    assert result["authoritative"] is False
    assert result["reason"] == "diagnostic artifact is older than current build render"


def test_unmanifested_current_crop_is_diagnostic_only(tmp_path: Path) -> None:
    example_dir = _write_fixture(tmp_path)
    debug_crop = example_dir / "build" / "manual_crop.png"
    debug_crop.write_bytes(b"manual crop\n")

    result = classify_artifact(example_dir, debug_crop)

    assert result["classification"] == "diagnostic_only"
    assert result["authoritative"] is False
    assert "not manifest-bound" in result["reason"]


def test_report_summarizes_authoritative_and_diagnostic_paths(tmp_path: Path) -> None:
    example_dir = _write_fixture(tmp_path)
    debug_crop = example_dir / "build" / "manual_crop.png"
    debug_crop.write_bytes(b"manual crop\n")

    report = provenance_report(
        example_dir,
        [
            example_dir / "build/audit_crops/full_q1.png",
            debug_crop,
        ],
    )

    assert report["schema"] == "figure-agent.diagnostic-artifact-provenance.v1"
    assert report["authoritative_count"] == 1
    assert report["diagnostic_count"] == 1
    assert [item["classification"] for item in report["artifacts"]] == [
        "manifest_bound_current",
        "diagnostic_only",
    ]


def test_cli_accepts_examples_fixture_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path
    example_dir = _write_fixture(repo_root)

    result = diagnostic_artifact_provenance.main(
        [
            "examples/demo",
            "build/demo.png",
            "--repo-root",
            str(repo_root),
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["fixture"] == "demo"
    assert payload["artifacts"][0]["classification"] == "build_render_current"
    assert str(example_dir) in payload["example_dir"]


def test_cli_rejects_parent_relative_fixture_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root = tmp_path / "repo"
    outside = repo_root / "outside"
    outside_build = outside / "build"
    outside_build.mkdir(parents=True)
    (repo_root / "examples").mkdir()
    (outside_build / "outside.png").write_bytes(b"outside render\n")

    result = diagnostic_artifact_provenance.main(
        [
            "examples/../outside",
            "build/outside.png",
            "--repo-root",
            str(repo_root),
        ]
    )

    assert result == 2
    captured = capsys.readouterr()
    assert "fixture path must be a fixture name or examples/<name> path" in captured.err
    assert captured.out == ""
