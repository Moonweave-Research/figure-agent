from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quality_manifest import (  # noqa: E402
    CRITIQUE_RUBRIC_VERSION,
    CRITIQUE_RUBRIC_VERSION_V1_14,
    CRITIQUE_RUBRIC_VERSION_V1_17,
    critique_freshness_diagnostics,
    critique_generator_version,
    critique_manifest_paths,
    expected_critique_rubric_version,
    input_manifest_hash,
)


def test_input_manifest_hash_changes_when_file_content_changes(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("first\n", encoding="utf-8")

    before = input_manifest_hash((source,), base_dir=tmp_path)
    source.write_text("second\n", encoding="utf-8")
    after = input_manifest_hash((source,), base_dir=tmp_path)

    assert before.startswith("sha256:")
    assert after.startswith("sha256:")
    assert before != after


def test_input_manifest_hash_is_stable_for_path_order(tmp_path: Path) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("a\n", encoding="utf-8")
    second.write_text("b\n", encoding="utf-8")

    assert input_manifest_hash((first, second), base_dir=tmp_path) == input_manifest_hash(
        (second, first), base_dir=tmp_path
    )


def _write_basic_critique_fixture(tmp_path: Path) -> tuple[Path, Path]:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "polymer-paper-preamble.sty"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    return example_dir, style_lock


def _write_metadata_critique(
    critique_path: Path,
    *,
    critique_input_hash: str,
    generator_version: str,
    rubric_version: str,
    schema: str = "figure-agent.critique.v1",
) -> None:
    critique_path.write_text(
        "---\n"
        f"schema: {schema}\n"
        "fixture: demo\n"
        f"generator_version: {generator_version}\n"
        f"rubric_version: {rubric_version}\n"
        f"critique_input_hash: {critique_input_hash}\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )


def test_critique_freshness_diagnostics_reports_no_mismatch_for_fresh_metadata(
    tmp_path: Path,
) -> None:
    example_dir, style_lock = _write_basic_critique_fixture(tmp_path)
    spec = {"name": "demo"}
    expected_hash = input_manifest_hash(
        critique_manifest_paths(example_dir, "demo", spec, style_lock_path=style_lock),
        base_dir=tmp_path,
    )
    generator_path = tmp_path / "critique_brief.py"
    generator_path.write_text("generator\n", encoding="utf-8")
    _write_metadata_critique(
        example_dir / "critique.md",
        critique_input_hash=expected_hash,
        generator_version=critique_generator_version(generator_path),
        rubric_version=CRITIQUE_RUBRIC_VERSION,
    )

    diagnostics = critique_freshness_diagnostics(
        example_dir / "critique.md",
        example_dir,
        "demo",
        spec,
        style_lock_path=style_lock,
        base_dir=tmp_path,
        generator_path=generator_path,
    )

    assert diagnostics["metadata_complete"] is True
    assert diagnostics["is_fresh"] is True
    assert diagnostics["mismatch_reasons"] == []


def test_critique_freshness_diagnostics_reports_generator_mismatch(tmp_path: Path) -> None:
    example_dir, style_lock = _write_basic_critique_fixture(tmp_path)
    spec = {"name": "demo"}
    expected_hash = input_manifest_hash(
        critique_manifest_paths(example_dir, "demo", spec, style_lock_path=style_lock),
        base_dir=tmp_path,
    )
    generator_path = tmp_path / "critique_brief.py"
    generator_path.write_text("generator\n", encoding="utf-8")
    _write_metadata_critique(
        example_dir / "critique.md",
        critique_input_hash=expected_hash,
        generator_version="sha256:stale",
        rubric_version=CRITIQUE_RUBRIC_VERSION,
    )

    diagnostics = critique_freshness_diagnostics(
        example_dir / "critique.md",
        example_dir,
        "demo",
        spec,
        style_lock_path=style_lock,
        base_dir=tmp_path,
        generator_path=generator_path,
    )

    assert diagnostics["is_fresh"] is False
    assert diagnostics["mismatch_reasons"] == ["generator_version"]


def test_critique_freshness_diagnostics_reports_missing_metadata(tmp_path: Path) -> None:
    example_dir, style_lock = _write_basic_critique_fixture(tmp_path)
    (example_dir / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1\nfixture: demo\n---\n# critique\n",
        encoding="utf-8",
    )

    diagnostics = critique_freshness_diagnostics(
        example_dir / "critique.md",
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
        base_dir=tmp_path,
        generator_path=tmp_path / "missing_generator.py",
    )

    assert diagnostics["metadata_complete"] is False
    assert diagnostics["is_fresh"] is None
    assert diagnostics["mismatch_reasons"] == ["missing_hash_metadata"]


def test_critique_freshness_diagnostics_reports_schema_rubric_mismatch(
    tmp_path: Path,
) -> None:
    example_dir, style_lock = _write_basic_critique_fixture(tmp_path)
    spec = {"name": "demo"}
    intent_path = example_dir / "aesthetic_intent.yaml"
    intent_path.write_text(
        "schema: figure-agent.aesthetic-intent.v2\nfixture: demo\n",
        encoding="utf-8",
    )
    expected_hash = input_manifest_hash(
        critique_manifest_paths(example_dir, "demo", spec, style_lock_path=style_lock),
        base_dir=tmp_path,
    )
    generator_path = tmp_path / "critique_brief.py"
    generator_path.write_text("generator\n", encoding="utf-8")
    _write_metadata_critique(
        example_dir / "critique.md",
        critique_input_hash=expected_hash,
        generator_version=critique_generator_version(generator_path),
        rubric_version=CRITIQUE_RUBRIC_VERSION_V1_14,
        schema="figure-agent.critique.v1",
    )

    diagnostics = critique_freshness_diagnostics(
        example_dir / "critique.md",
        example_dir,
        "demo",
        spec,
        style_lock_path=style_lock,
        base_dir=tmp_path,
        generator_path=generator_path,
    )

    assert diagnostics["is_fresh"] is False
    assert diagnostics["mismatch_reasons"] == ["schema_rubric"]


def test_critique_manifest_includes_audit_crop_manifest_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"schema":"figure-agent.audit-crop-manifest.v1"}\n')

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    manifest_path.write_text('{"schema":"figure-agent.audit-crop-manifest.v1","n":1}\n')
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert manifest_path in paths
    assert before != after


def test_critique_manifest_includes_text_boundary_report_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    report_path = example_dir / "build" / "text_boundary_clash.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        '{"schema":"figure-agent.text-boundary-clash.v1","total":0}\n',
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    report_path.write_text(
        '{"schema":"figure-agent.text-boundary-clash.v1","total":1}\n',
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert report_path in paths
    assert before != after


def test_critique_manifest_includes_label_path_proximity_report_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    report_path = example_dir / "build" / "label_path_proximity.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        '{"schema":"figure-agent.label-path-proximity.v1","total":0}\n',
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    report_path.write_text(
        '{"schema":"figure-agent.label-path-proximity.v1","total":1}\n',
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert report_path in paths
    assert before != after


def test_critique_manifest_includes_undeclared_geometry_report_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    report_path = example_dir / "build" / "undeclared_geometry.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        '{"schema":"figure-agent.undeclared-geometry.v1","candidates":['
        '{"id":"UG001","kind":"path","nearest_text":"foo","distance_pt":2.0}]}\n',
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    report_path.write_text(
        '{"schema":"figure-agent.undeclared-geometry.v1","candidates":['
        '{"id":"UG001","kind":"path","nearest_text":"BAR","distance_pt":9.0},'
        '{"id":"UG002","kind":"node","nearest_text":"baz","distance_pt":1.0}]}\n',
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert report_path in paths
    assert before != after


def test_critique_manifest_includes_critique_reference_pack_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    pack_path = example_dir / "critique_reference_pack.yaml"
    pack_path.write_text(
        "schema: figure-agent.critique-reference-pack.v1\nfixture: demo\n",
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    pack_path.write_text(
        "schema: figure-agent.critique-reference-pack.v1\nfixture: demo\nchanged: true\n",
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert pack_path in paths
    assert before != after


def test_critique_manifest_includes_reference_aesthetic_metrics_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    (example_dir / "build").mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    metrics_path = example_dir / "build" / "reference_aesthetic_metrics.json"
    metrics_path.write_text(
        '{"schema":"figure-agent.reference-aesthetic-metrics.v1"}\n',
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    metrics_path.write_text(
        '{"schema":"figure-agent.reference-aesthetic-metrics.v1","changed":true}\n',
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert metrics_path in paths
    assert before != after


def test_critique_manifest_includes_aesthetic_intent_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    intent_path = example_dir / "aesthetic_intent.yaml"
    intent_path.write_text(
        "schema: figure-agent.aesthetic-intent.v1\nfixture: demo\n",
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    intent_path.write_text(
        "schema: figure-agent.aesthetic-intent.v1\nfixture: demo\nchanged: true\n",
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert intent_path in paths
    assert before != after


def test_critique_manifest_includes_declared_paper_aesthetic_context(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text(
        "name: demo\npaper_aesthetic_context: paper-demo\n",
        encoding="utf-8",
    )
    pack_dir = example_dir.parent / "_paper_aesthetic_contexts"
    pack_dir.mkdir()
    pack_path = pack_dir / "paper-demo.yaml"
    pack_path.write_text(
        "schema: figure-agent.paper-aesthetic-context.v1\n"
        "paper_id: paper-demo\n"
        "target_journal: Nature Communications\n"
        "visual_maturity: editorial\n"
        "density: balanced\n"
        "shared_visual_language:\n"
        "  - id: restrained_palette\n"
        "    dimension: palette\n"
        "    instruction: keep palette restrained\n"
        "    priority: required\n"
        "    positive_signals:\n"
        "      - muted shared accents\n"
        "    anti_patterns:\n"
        "      - poster-like saturation\n"
        "figure_roles:\n"
        "  - fixture: demo\n"
        "    role: overview_mechanism\n"
        "    must_align_with:\n"
        "      - restrained_palette\n"
        "must_avoid:\n"
        "  - id: series_drift\n"
        "    pattern: inconsistent design system\n"
        "    severity: MAJOR\n",
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo", "paper_aesthetic_context": "paper-demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    pack_path.write_text(pack_path.read_text(encoding="utf-8") + "changed: true\n")
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert pack_path in paths
    assert before != after


def test_critique_manifest_omits_paper_aesthetic_context_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    pack_dir = example_dir.parent / "_paper_aesthetic_contexts"
    pack_dir.mkdir()
    pack_path = pack_dir / "paper-demo.yaml"
    pack_path.write_text("schema: figure-agent.paper-aesthetic-context.v1\n")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )

    assert pack_path not in paths


def test_critique_manifest_includes_declared_journal_art_direction_playbook(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text(
        "name: demo\njournal_art_direction_playbook: nc-main-text\n",
        encoding="utf-8",
    )
    pack_dir = example_dir.parent / "_journal_art_direction_playbooks"
    pack_dir.mkdir()
    pack_path = pack_dir / "nc-main-text.yaml"
    pack_path.write_text("schema: figure-agent.journal-art-direction-playbook.v1\n")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo", "journal_art_direction_playbook": "nc-main-text"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    pack_path.write_text(
        "schema: figure-agent.journal-art-direction-playbook.v1\nchanged: true\n",
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert pack_path in paths
    assert before != after


def test_critique_manifest_omits_journal_playbook_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    pack_dir = example_dir.parent / "_journal_art_direction_playbooks"
    pack_dir.mkdir()
    pack_path = pack_dir / "nc-main-text.yaml"
    pack_path.write_text("schema: figure-agent.journal-art-direction-playbook.v1\n")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )

    assert pack_path not in paths


def test_critique_manifest_does_not_crash_on_invalid_paper_context_id(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        "name: demo\npaper_aesthetic_context: ../escape\n",
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo", "paper_aesthetic_context": "../escape"},
        style_lock_path=style_lock,
    )

    assert spec_path in paths


def test_critique_manifest_ignores_generated_export_svg_without_polish_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    export_svg = example_dir / "exports" / "demo.svg"
    export_svg.parent.mkdir()
    export_svg.write_text("<svg>generated export</svg>\n", encoding="utf-8")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    export_svg.write_text("<svg>changed generated export</svg>\n", encoding="utf-8")
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert export_svg not in paths
    assert before == after
def test_critique_manifest_ignores_external_vision_review_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    review_path = example_dir / "external_vision_review.yaml"
    review_path.write_text("schema: figure-agent.external-vision-review.v1\n", encoding="utf-8")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )

    assert review_path not in paths


def test_critique_manifest_includes_external_vision_review_when_opted_in(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    review_path = example_dir / "external_vision_review.yaml"
    review_path.write_text("schema: figure-agent.external-vision-review.v1\n", encoding="utf-8")

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo", "external_vision_review": True},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    review_path.write_text(
        "schema: figure-agent.external-vision-review.v1\nreviewer: changed\n",
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert review_path in paths
    assert before != after


def test_expected_critique_rubric_version_uses_v1_14_for_aesthetic_intent_v2(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v2\nfixture: demo\n",
        encoding="utf-8",
    )

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_14


def test_expected_critique_rubric_version_uses_v1_14_for_journal_playbook(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "spec.yaml").write_text(
        "name: demo\njournal_art_direction_playbook: nc-main-text\n",
        encoding="utf-8",
    )

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_14


def test_expected_critique_rubric_version_uses_v1_14_for_reference_learning(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "critique_reference_pack.yaml").write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: demo
target_journal: Nature Communications
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references: []
must_match_traits: []
must_avoid_traits: []
calibration_questions: []
reference_learning:
  schema: figure-agent.reference-learning.v1
  references: []
""".lstrip(),
        encoding="utf-8",
    )

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_14


def test_expected_critique_rubric_version_uses_v1_14_for_journal_playbook_and_intent_v2(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "spec.yaml").write_text(
        "name: demo\njournal_art_direction_playbook: nc-main-text\n",
        encoding="utf-8",
    )
    (example_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v2\nfixture: demo\n",
        encoding="utf-8",
    )

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_14


def test_expected_critique_rubric_version_uses_v1_17_for_crop_manifest(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"schema":"figure-agent.audit-crop-manifest.v1"}\n')

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_17


def test_expected_critique_rubric_version_uses_v1_17_for_undeclared_geometry(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    report_path = example_dir / "build" / "undeclared_geometry.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"schema":"figure-agent.undeclared-geometry.v1"}\n')

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION_V1_17


def test_expected_critique_rubric_version_keeps_v1_10_for_legacy_intent(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    (example_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v1\nfixture: demo\n",
        encoding="utf-8",
    )

    assert expected_critique_rubric_version(example_dir) == CRITIQUE_RUBRIC_VERSION
