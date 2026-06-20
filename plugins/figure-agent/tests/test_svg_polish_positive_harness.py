from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import svg_polish_positive_harness as harness_mod  # noqa: E402
from svg_polish_positive_harness import run_positive_harness  # noqa: E402


def test_positive_harness_closes_polished_svg_route_without_mutating_source(
    tmp_path: Path,
) -> None:
    work_dir = tmp_path / "harness"

    result = run_positive_harness(work_dir=work_dir, force=False)

    assert result["schema"] == "figure-agent.svg-polish-positive-harness.v1"
    assert result["fixture"] == "svg_polish_positive_demo"
    assert result["status"]["final_artifact_kind"] == "polished_svg"
    assert result["status"]["final_artifact_state"] == "FRESH"
    assert result["driver"]["action"]
    assert "missing_input" not in result["driver"]["reason"]
    fixture = work_dir / "examples" / "svg_polish_positive_demo"
    assert (fixture / "polish" / "svg_polish_positive_demo.polished.svg").is_file()
    assert (fixture / "polish" / "aesthetic_delta" / "delta_manifest.json").is_file()
    assert (fixture / "polish" / "svg_semantic_diff.json").is_file()
    assert (fixture / "polish" / "svg_polish_manifest.yaml").is_file()
    for image_path in (
        fixture / "build" / "svg_polish_positive_demo.png",
        fixture / "exports" / "svg_polish_positive_demo.png",
        fixture / "exports" / "svg_polish_positive_demo.tif",
    ):
        with Image.open(image_path) as image:
            image.verify()
    source_svg = fixture / "exports" / "svg_polish_positive_demo.svg"
    assert 'id="label-main"' in source_svg.read_text(encoding="utf-8")
    assert "translate(1.5 -1)" not in source_svg.read_text(encoding="utf-8")
    json.dumps(result)


def test_positive_harness_requires_force_for_existing_workdir(tmp_path: Path) -> None:
    work_dir = tmp_path / "harness"
    run_positive_harness(work_dir=work_dir, force=False)

    try:
        run_positive_harness(work_dir=work_dir, force=False)
    except ValueError as exc:
        assert "--force" in str(exc)
    else:
        raise AssertionError("expected existing work_dir to require --force")


def test_positive_harness_refuses_to_force_replace_unmarked_workdir(tmp_path: Path) -> None:
    work_dir = tmp_path / "not-a-harness"
    work_dir.mkdir()
    (work_dir / "keep.txt").write_text("do not delete\n", encoding="utf-8")

    try:
        run_positive_harness(work_dir=work_dir, force=True)
    except ValueError as exc:
        assert "unmarked work_dir" in str(exc)
    else:
        raise AssertionError("expected unmarked work_dir replacement to fail")

    assert (work_dir / "keep.txt").read_text(encoding="utf-8") == "do not delete\n"


def test_positive_harness_cli_accepts_json_noop_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_positive_harness(*, work_dir: Path, force: bool) -> dict:
        return {
            "schema": "figure-agent.svg-polish-positive-harness.v1",
            "fixture": "svg_polish_positive_demo",
            "work_dir": str(work_dir),
            "force": force,
        }

    monkeypatch.setattr(harness_mod, "run_positive_harness", fake_run_positive_harness)

    exit_code = harness_mod.main(["--work-dir", str(tmp_path / "harness"), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.svg-polish-positive-harness.v1"


def test_positive_harness_cli_accepts_format_json_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_positive_harness(*, work_dir: Path, force: bool) -> dict:
        return {
            "schema": "figure-agent.svg-polish-positive-harness.v1",
            "fixture": "svg_polish_positive_demo",
            "work_dir": str(work_dir),
            "force": force,
        }

    monkeypatch.setattr(harness_mod, "run_positive_harness", fake_run_positive_harness)

    exit_code = harness_mod.main(
        ["--work-dir", str(tmp_path / "harness"), "--format", "json"]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.svg-polish-positive-harness.v1"
