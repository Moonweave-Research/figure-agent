from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reference_aesthetic_metrics import (  # noqa: E402
    METRICS_SCHEMA,
    ReferenceAestheticMetricsError,
    build_reference_aesthetic_metrics,
    main,
    reference_aesthetic_metrics_summary,
)


def _write_base_fixture(tmp_path: Path, *, with_learning: bool = True) -> Path:
    example_dir = tmp_path / "examples" / "demo"
    return _write_base_fixture_at(example_dir, with_learning=with_learning)


def _write_base_fixture_at(example_dir: Path, *, with_learning: bool = True) -> Path:
    name = example_dir.name
    build_dir = example_dir / "build"
    reference_dir = example_dir / "reference"
    build_dir.mkdir(parents=True)
    reference_dir.mkdir()
    Image.new("RGB", (80, 60), "white").save(build_dir / f"{name}.png")
    Image.new("RGB", (80, 60), "white").save(reference_dir / "style.png")
    pack = f"""
schema: figure-agent.critique-reference-pack.v1
fixture: {name}
target_journal: Nature Communications
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: reference/style.png
    role: journal_register
must_match_traits:
  - id: T001
    trait: compact editorial tone
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: poster-like palette
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Does this read as journal-grade?
"""
    if with_learning:
        pack += """
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/style.png
      roles:
        - style_anchor
        - density_reference
      allowed_transfer:
        - restrained palette
        - balanced ink density
        - compact typography hierarchy
        - mechanism abstraction level
        - clean line language
        - stage composition rhythm
      forbidden_transfer:
        - copy component topology
        - copy exact geometry or coordinates
        - copy label text
        - copy claim payload
        - copy panel semantics
      rationale: Use as style class only.
"""
    (example_dir / "critique_reference_pack.yaml").write_text(pack.lstrip(), encoding="utf-8")
    return example_dir


def test_reference_aesthetic_metrics_writes_deterministic_metric_pack(tmp_path: Path) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build = Image.new("RGB", (80, 60), "white")
    draw = ImageDraw.Draw(build)
    draw.rectangle((5, 5, 75, 55), fill=(220, 40, 40))
    build.save(example_dir / "build" / "demo.png")
    reference = Image.new("RGB", (80, 60), "white")
    draw = ImageDraw.Draw(reference)
    draw.rectangle((20, 15, 60, 45), fill=(80, 80, 80))
    reference.save(example_dir / "reference" / "style.png")

    first = build_reference_aesthetic_metrics(example_dir)
    second = build_reference_aesthetic_metrics(example_dir)

    assert first == second
    assert first is not None
    assert first["schema"] == METRICS_SCHEMA
    assert first["state"] == "measured"
    assert first["fixture"] == "demo"
    assert first["build_artifact"]["path"] == "build/demo.png"
    assert first["comparisons"][0]["reference_path"] == "reference/style.png"
    assert first["comparisons"][0]["roles"] == ["style_anchor", "density_reference"]
    metrics = first["comparisons"][0]["metrics"]
    assert metrics["palette_histogram_distance"] > 0
    assert metrics["ink_density_delta"] > 0
    assert "ssim" not in json.dumps(first).lower()
    output = example_dir / "build" / "reference_aesthetic_metrics.json"
    assert json.loads(output.read_text(encoding="utf-8")) == first


def test_reference_aesthetic_metrics_skips_when_reference_learning_missing(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path, with_learning=False)

    result = build_reference_aesthetic_metrics(example_dir)
    summary = reference_aesthetic_metrics_summary(example_dir)

    assert result is None
    assert summary is None
    assert not (example_dir / "build" / "reference_aesthetic_metrics.json").exists()


def test_reference_aesthetic_metrics_records_missing_reference_as_skipped(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    (example_dir / "reference" / "style.png").unlink()

    result = build_reference_aesthetic_metrics(example_dir)

    assert result is not None
    assert result["state"] == "skipped"
    assert "reference/style.png" in result["skip_reasons"][0]
    assert result["comparisons"] == []


def test_reference_aesthetic_metrics_raises_on_corrupt_build_render(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    (example_dir / "build" / "demo.png").write_bytes(b"")

    with pytest.raises(ReferenceAestheticMetricsError) as exc_info:
        build_reference_aesthetic_metrics(example_dir)

    assert "build/demo.png" in str(exc_info.value)


def test_reference_aesthetic_metrics_records_corrupt_reference_as_skipped(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    (example_dir / "reference" / "style.png").write_bytes(b"")

    result = build_reference_aesthetic_metrics(example_dir)

    assert result is not None
    assert result["state"] == "skipped"
    assert "reference/style.png" in result["skip_reasons"][0]
    assert result["comparisons"] == []


def test_reference_aesthetic_metrics_summary_reports_unsafe_reference_path_invalid(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    pack_path = example_dir / "critique_reference_pack.yaml"
    pack_path.write_text(
        pack_path.read_text(encoding="utf-8").replace(
            "path: reference/style.png",
            "path: ../outside.png",
        ),
        encoding="utf-8",
    )

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "invalid"
    assert "path" in summary["reason"]


def test_reference_aesthetic_metrics_detects_silhouette_difference(tmp_path: Path) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(build).rectangle((0, 0, 79, 59), fill=(40, 40, 40))
    build.save(example_dir / "build" / "demo.png")
    reference = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(reference).rectangle((30, 20, 50, 40), fill=(40, 40, 40))
    reference.save(example_dir / "reference" / "style.png")

    result = build_reference_aesthetic_metrics(example_dir)

    assert result is not None
    occupancy = result["comparisons"][0]["metrics"]["coarse_silhouette_occupancy_delta"]
    assert occupancy > 0.5


def test_reference_aesthetic_metrics_summary_reports_missing_metrics(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "missing"
    assert summary["next_action"].startswith("run scripts/reference_aesthetic_metrics.py")


def test_reference_aesthetic_metrics_summary_reports_passed_metrics(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build_reference_aesthetic_metrics(example_dir)

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "passed"
    assert summary["next_action"] == "no reference aesthetic metric action required"


def test_reference_aesthetic_metrics_summary_reports_warning_metrics(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build_reference_aesthetic_metrics(example_dir)
    output = example_dir / "build" / "reference_aesthetic_metrics.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["comparisons"][0]["metrics"]["palette_histogram_distance"] = 0.3
    output.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "warning"
    assert summary["warning_metric_count"] == 1
    assert summary["severe_metric_count"] == 0


def test_reference_aesthetic_metrics_summary_reports_stale_build_hash(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build_reference_aesthetic_metrics(example_dir)
    Image.new("RGB", (80, 60), "black").save(example_dir / "build" / "demo.png")

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "stale"
    assert "build/demo.png" in summary["blocking_items"]


def test_reference_aesthetic_metrics_summary_reports_stale_when_reference_readded(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    (example_dir / "reference" / "style.png").unlink()
    payload = build_reference_aesthetic_metrics(example_dir)
    assert payload is not None
    assert payload["state"] == "skipped"
    Image.new("RGB", (80, 60), "white").save(example_dir / "reference" / "style.png")

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "stale"
    assert "reference/style.png" in summary["blocking_items"]
    assert summary["next_action"].startswith("rerun scripts/reference_aesthetic_metrics.py")


def test_reference_aesthetic_metrics_summary_keeps_skipped_when_readded_reference_corrupt(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    (example_dir / "reference" / "style.png").unlink()
    build_reference_aesthetic_metrics(example_dir)
    (example_dir / "reference" / "style.png").write_bytes(b"")

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "skipped"
    assert summary["next_action"] == "provide at least one readable reference-learning image"


def test_reference_aesthetic_metrics_summary_reports_invalid_metrics_json(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    output = example_dir / "build" / "reference_aesthetic_metrics.json"
    output.write_text("{not yaml json", encoding="utf-8")

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "invalid"
    assert summary["next_action"].startswith("rerun scripts/reference_aesthetic_metrics.py")


def test_reference_aesthetic_metrics_summary_reports_severe_divergence(
    tmp_path: Path,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    build = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(build).rectangle((0, 0, 79, 59), fill=(255, 0, 0))
    build.save(example_dir / "build" / "demo.png")
    reference = Image.new("RGB", (80, 60), "white")
    ImageDraw.Draw(reference).rectangle((35, 25, 45, 35), fill=(40, 40, 40))
    reference.save(example_dir / "reference" / "style.png")
    build_reference_aesthetic_metrics(example_dir)

    summary = reference_aesthetic_metrics_summary(example_dir)

    assert summary is not None
    assert summary["evaluation_state"] == "severe_divergence"
    assert summary["severe_metric_count"] >= 1
    assert summary["next_action"].startswith("review reference_aesthetic_metrics.json")


def test_reference_aesthetic_metrics_cli_accepts_fixture_name_and_absolute_examples_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    example_dir = _write_base_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert main(["demo"]) == 0
    assert "measured: wrote build/reference_aesthetic_metrics.json" in capsys.readouterr().out

    (example_dir / "build" / "reference_aesthetic_metrics.json").unlink()
    assert main(["examples/demo"]) == 0
    assert "measured: wrote build/reference_aesthetic_metrics.json" in capsys.readouterr().out

    (example_dir / "build" / "reference_aesthetic_metrics.json").unlink()
    assert main([str(example_dir.resolve())]) == 0
    assert "measured: wrote build/reference_aesthetic_metrics.json" in capsys.readouterr().out


def test_reference_aesthetic_metrics_cli_rejects_traversal_or_outside_relative_path(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    outside = _write_base_fixture_at(tmp_path / "outside")
    _write_base_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert main(["examples/../outside"]) == 1
    assert "invalid fixture path" in capsys.readouterr().err

    assert main(["outside"]) == 1
    assert "relative fixture names must resolve under examples/" in capsys.readouterr().err
    assert not (outside / "build" / "reference_aesthetic_metrics.json").exists()
