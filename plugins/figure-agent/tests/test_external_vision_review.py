from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from external_vision_review import (  # noqa: E402
    EXTERNAL_VISION_REVIEW_SCHEMA,
    ExternalVisionReviewError,
    external_vision_review_freshness,
    external_vision_review_template,
    load_external_vision_review,
    load_optional_external_vision_review,
    main,
)
from fig_loop_assessments import external_vision_review_summary  # noqa: E402


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_artifact(example_dir: Path, *, content: bytes = b"png") -> Path:
    path = example_dir / "build" / f"{example_dir.name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _write_crop(example_dir: Path, *, crop_id: str = "VC001") -> Path:
    path = example_dir / "build" / "audit_crops" / f"{crop_id}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"crop")
    return path


def _write_crop_manifest(example_dir: Path, crops: list[Path]) -> None:
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": example_dir.name,
                "render_path": f"build/{example_dir.name}.png",
                "required_crop_ids": [path.stem for path in crops],
                "crops": [
                    {
                        "id": path.stem,
                        "path": str(path.relative_to(example_dir)),
                        "sha256": _sha256(path),
                    }
                    for path in crops
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_review(
    example_dir: Path,
    *,
    fixture: str | None = None,
    confidence: str = "medium",
    suggested_action: str = "human_review",
    conflict: bool = True,
    artifact_hash: str | None = None,
) -> Path:
    artifact_path = _write_artifact(example_dir)
    crop_path = _write_crop(example_dir)
    if artifact_hash is None:
        artifact_hash = _sha256(artifact_path)
    conflicts = (
        """
conflicts:
  - external_finding_id: EV001
    host_finding_id: C001
    summary: external review sees a label-target issue that host critique dismissed
""".rstrip()
        if conflict
        else "conflicts: []"
    )
    path = example_dir / "external_vision_review.yaml"
    path.write_text(
        f"""
schema: {EXTERNAL_VISION_REVIEW_SCHEMA}
fixture: {fixture or example_dir.name}
reviewer: Gemini manual second pass
reviewed_at: 2026-05-28T12:00:00Z
confidence: {confidence}
reviewed_artifact:
  path: build/{example_dir.name}.png
  hash: {artifact_hash}
reviewed_crops:
  - crop_id: VC001
    path: build/audit_crops/VC001.png
    hash: {_sha256(crop_path)}
findings:
  - id: EV001
    severity: MAJOR
    observation: label appears visually attached to the wrong object in the crop
    evidence_ref: VC001
    suggested_action: {suggested_action}
{conflicts}
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_load_external_vision_review_accepts_valid_review(tmp_path: Path) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    path = _write_review(example_dir)

    review = load_external_vision_review(path)

    assert review["schema"] == EXTERNAL_VISION_REVIEW_SCHEMA
    assert review["fixture"] == "demo"
    assert review["reviewer"] == "Gemini manual second pass"
    assert review["findings"][0]["id"] == "EV001"
    assert review["conflicts"][0]["host_finding_id"] == "C001"


def test_load_optional_external_vision_review_returns_none_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_review(example_dir)

    assert load_optional_external_vision_review(example_dir, {"name": "demo"}) is None


def test_load_optional_external_vision_review_rejects_missing_opted_review(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()

    with pytest.raises(ExternalVisionReviewError, match="missing"):
        load_optional_external_vision_review(
            example_dir,
            {"name": "demo", "external_vision_review": True},
        )


def test_load_external_vision_review_rejects_malformed_yaml(tmp_path: Path) -> None:
    path = tmp_path / "external_vision_review.yaml"
    path.write_text("schema: [", encoding="utf-8")

    with pytest.raises(ExternalVisionReviewError, match="malformed YAML"):
        load_external_vision_review(path)


def test_load_optional_external_vision_review_rejects_fixture_mismatch(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_review(example_dir, fixture="other")

    with pytest.raises(ExternalVisionReviewError, match="fixture"):
        load_optional_external_vision_review(
            example_dir,
            {"name": "demo", "external_vision_review": True},
        )


def test_load_external_vision_review_rejects_invalid_enums(tmp_path: Path) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    path = _write_review(example_dir, confidence="certain")

    with pytest.raises(ExternalVisionReviewError, match="confidence"):
        load_external_vision_review(path)

    path = _write_review(example_dir, suggested_action="auto_patch")
    with pytest.raises(ExternalVisionReviewError, match="suggested_action"):
        load_external_vision_review(path)


def test_external_vision_review_freshness_detects_stale_artifact_hash(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_review(example_dir)
    review = load_external_vision_review(example_dir / "external_vision_review.yaml")

    fresh = external_vision_review_freshness(example_dir, review)
    assert fresh["state"] == "fresh"
    assert fresh["stale_paths"] == []

    (example_dir / "build" / "demo.png").write_bytes(b"changed")
    stale = external_vision_review_freshness(example_dir, review)
    assert stale["state"] == "stale"
    assert stale["stale_paths"] == ["build/demo.png"]


def test_external_vision_review_summary_marks_conflicts_needs_human(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        "name: demo\nexternal_vision_review: true\n",
        encoding="utf-8",
    )
    _write_review(example_dir, conflict=True)

    summary = external_vision_review_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "needs_human"
    assert summary["conflict_count"] == 1
    assert summary["active_conflicts"] == ["EV001 vs C001"]


def test_external_vision_review_summary_gates_unresolved_major_findings(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        "name: demo\nexternal_vision_review: true\n",
        encoding="utf-8",
    )
    _write_review(example_dir, conflict=False)

    summary = external_vision_review_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "needs_human"
    assert summary["unresolved_finding_count"] == 1
    assert summary["active_findings"] == ["EV001:MAJOR"]


def test_external_vision_review_summary_accept_simplification_findings_pass(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        "name: demo\nexternal_vision_review: true\n",
        encoding="utf-8",
    )
    _write_review(
        example_dir,
        conflict=False,
        suggested_action="accept_simplification",
    )

    summary = external_vision_review_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "passed"
    assert summary["unresolved_finding_count"] == 0
    assert summary["active_findings"] == []


def test_external_vision_review_summary_marks_stale_review(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        "name: demo\nexternal_vision_review: true\n",
        encoding="utf-8",
    )
    _write_review(example_dir, conflict=False)
    (example_dir / "build" / "demo.png").write_bytes(b"changed")

    summary = external_vision_review_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "stale"
    assert summary["freshness"]["stale_paths"] == ["build/demo.png"]


def test_external_vision_review_summary_reports_spec_parse_error(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        "name: demo\nstyle_profile: unknown\nexternal_vision_review: true\n",
        encoding="utf-8",
    )

    summary = external_vision_review_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "invalid"
    assert "Unknown style_profile" in summary["error"]


def test_external_vision_review_template_uses_current_artifact_and_manifest_crops(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    artifact_path = _write_artifact(example_dir, content=b"render")
    full_crop = _write_crop(example_dir, crop_id="full_q1")
    clash_crop = _write_crop(example_dir, crop_id="VC001_A")
    _write_crop_manifest(example_dir, [full_crop, clash_crop])

    template = external_vision_review_template(
        example_dir,
        reviewer="Gemini manual second pass",
        reviewed_at="2026-06-02T00:00:00Z",
    )
    review_path = example_dir / "external_vision_review.yaml"
    review_path.write_text(template, encoding="utf-8")

    review = load_external_vision_review(review_path)

    assert review["fixture"] == "demo"
    assert review["reviewer"] == "Gemini manual second pass"
    assert review["reviewed_artifact"] == {
        "path": "build/demo.png",
        "hash": _sha256(artifact_path),
    }
    assert [crop["crop_id"] for crop in review["reviewed_crops"]] == [
        "VC001_A",
        "full_q1",
    ]
    assert review["findings"] == []
    assert review["conflicts"] == []
    assert external_vision_review_freshness(example_dir, review)["state"] == "fresh"


def test_external_vision_review_freshness_detects_manifest_crop_set_drift(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_artifact(example_dir, content=b"render")
    first_crop = _write_crop(example_dir, crop_id="full_q1")
    _write_crop_manifest(example_dir, [first_crop])
    review_path = example_dir / "external_vision_review.yaml"
    review_path.write_text(
        external_vision_review_template(example_dir),
        encoding="utf-8",
    )
    review = load_external_vision_review(review_path)

    second_crop = _write_crop(example_dir, crop_id="VC002_B")
    _write_crop_manifest(example_dir, [first_crop, second_crop])

    freshness = external_vision_review_freshness(example_dir, review)

    assert freshness["state"] == "stale"
    assert freshness["stale_paths"] == ["build/audit_crops/VC002_B.png"]


def test_external_vision_review_template_cli_emits_reloadable_yaml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_artifact(example_dir)
    crop = _write_crop(example_dir, crop_id="full_q1")
    _write_crop_manifest(example_dir, [crop])

    exit_code = main(
        [
            "--template",
            str(example_dir),
            "--reviewer",
            "external reviewer",
            "--reviewed-at",
            "2026-06-02T00:00:00Z",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    review_path = example_dir / "external_vision_review.yaml"
    review_path.write_text(output, encoding="utf-8")
    review = load_external_vision_review(review_path)
    assert review["fixture"] == "demo"
    assert review["reviewed_crops"][0]["crop_id"] == "full_q1"


def test_external_vision_review_template_cli_can_write_canonical_file(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_artifact(example_dir)

    exit_code = main(
        [
            "--template",
            str(example_dir),
            "--write-template",
            "--reviewed-at",
            "2026-06-02T00:00:00Z",
        ]
    )

    assert exit_code == 0
    review = load_external_vision_review(example_dir / "external_vision_review.yaml")
    assert review["reviewed_artifact"]["path"] == "build/demo.png"


def test_external_vision_review_template_cli_refuses_overwrite_without_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_artifact(example_dir)
    (example_dir / "external_vision_review.yaml").write_text("existing\n", encoding="utf-8")

    exit_code = main(["--template", str(example_dir), "--write-template"])

    assert exit_code == 1
    assert "already exists" in capsys.readouterr().err


def test_template_write_rejects_parent_relative_fixture_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    _write_artifact(outside_dir)
    review_path = outside_dir / "external_vision_review.yaml"
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--template",
            "examples/../outside",
            "--write-template",
            "--reviewed-at",
            "2026-06-02T00:00:00Z",
        ]
    )

    assert exit_code == 1
    assert "invalid fixture path" in capsys.readouterr().err
    assert not review_path.exists()


def test_template_write_rejects_existing_relative_dir_outside_examples(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    _write_artifact(outside_dir)
    review_path = outside_dir / "external_vision_review.yaml"
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--template",
            "outside",
            "--write-template",
            "--reviewed-at",
            "2026-06-02T00:00:00Z",
        ]
    )

    assert exit_code == 1
    assert "invalid fixture path" in capsys.readouterr().err
    assert not review_path.exists()


def test_external_vision_review_template_rejects_unsafe_manifest_crop_path(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "demo"
    example_dir.mkdir()
    _write_artifact(example_dir)
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": "demo",
                "render_path": "build/demo.png",
                "required_crop_ids": ["escape"],
                "crops": [
                    {
                        "id": "escape",
                        "path": "../outside.png",
                        "sha256": _sha256(outside),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ExternalVisionReviewError, match="safe path"):
        external_vision_review_template(example_dir)
