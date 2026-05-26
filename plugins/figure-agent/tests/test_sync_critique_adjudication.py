from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_adjudication  # noqa: E402
from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    load_adjudication,
    main,
    sync_adjudication,
)
from inputs import parse_spec  # noqa: E402
from quality_manifest import (  # noqa: E402
    CRITIQUE_RUBRIC_VERSION,
    CRITIQUE_RUBRIC_VERSION_V1_11,
    compute_critique_input_hash,
    file_sha256,
)


def _write_repo_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    example = repo / "examples" / "demo_fig"
    (repo / "scripts").mkdir(parents=True)
    (repo / "styles").mkdir()
    example.mkdir(parents=True)
    (repo / "scripts" / "critique_brief.py").write_text("# generator\n", encoding="utf-8")
    (repo / "styles" / "polymer-paper-preamble.sty").write_text("% style\n", encoding="utf-8")
    (example / "reference").mkdir()
    (example / "reference" / "golden.png").write_bytes(b"\x89PNG")
    (example / "spec.yaml").write_text(
        "name: demo_fig\n"
        "reference_image: reference/golden.png\n"
        "panels: []\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    (example / "briefing.md").write_text("briefing\n", encoding="utf-8")
    (example / "demo_fig.tex").write_text("% tikz\n", encoding="utf-8")
    return repo, example


def _write_fresh_critique(
    repo: Path,
    example: Path,
    *,
    generator_version: str | None = None,
    critique_input_hash: str | None = None,
    schema: str = "figure-agent.critique.v1",
    rubric_version: str = CRITIQUE_RUBRIC_VERSION,
    finding_status: str = "open",
    finding_severity: str | None = None,
    finding_category: str | None = None,
    suggested_fix: str | None = None,
) -> Path:
    spec = parse_spec((example / "spec.yaml").read_text(encoding="utf-8"))
    generator_path = repo / "scripts" / "critique_brief.py"
    style_lock_path = repo / "styles" / "polymer-paper-preamble.sty"
    critique_input_hash = critique_input_hash or compute_critique_input_hash(
        example,
        "demo_fig",
        spec,
        style_lock_path=style_lock_path,
        base_dir=repo,
    )
    generator_version = generator_version or file_sha256(generator_path)
    severity_yaml = f"    severity: {finding_severity}\n" if finding_severity else ""
    category_yaml = f"    category: {finding_category}\n" if finding_category else ""
    suggested_fix_yaml = f"    suggested_fix: {suggested_fix}\n" if suggested_fix else ""
    critique = example / "critique.md"
    critique.write_text(
        "---\n"
        f"schema: {schema}\n"
        "fixture: demo_fig\n"
        "generator: critique_brief.py\n"
        f"generator_version: {generator_version}\n"
        f"rubric_version: {rubric_version}\n"
        f"critique_input_hash: {critique_input_hash}\n"
        "findings:\n"
        "  - id: C001\n"
        f"    status: {finding_status}\n"
        f"{severity_yaml}"
        f"{category_yaml}"
        "    tex_lines: [10, 20]\n"
        "    observation: label needs review\n"
        f"{suggested_fix_yaml}"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def _write_aesthetic_intent_v2(example: Path) -> None:
    (example / "aesthetic_intent.yaml").write_text(
        """schema: figure-agent.aesthetic-intent.v2
fixture: demo_fig
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: Prefer restrained publication-grade hierarchy.
must_avoid:
  - id: toy_diagram
    pattern: Avoid cartoon-like oversized labels.
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: Semantic TikZ is correct but optical finish is limiting.
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: maturity_restraint
    dimension: maturity
    intent: Mature publication-grade restraint.
    priority: required
    positive_signals:
      - Quiet hierarchy.
    anti_patterns:
      - Toy-like label scale.
    allowed_adjustments:
      - Reduce label weight.
    forbidden_adjustments:
      - Add decorative effects.
    default_route: tikz_patch
""",
        encoding="utf-8",
    )


def _write_adjudication(example: Path, source_hash: str = "sha256:old") -> Path:
    path = example / "critique_adjudication.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": "demo_fig",
                "source_critique_hash": source_hash,
                "decisions": [
                    {
                        "finding_id": "C001",
                        "decision": "dismiss",
                        "reason": "human reviewed current defect",
                        "patch_target": "",
                        "evidence": "",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_sync_adjudication_refreshes_hash_for_fresh_critique(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    critique = _write_fresh_critique(repo, example)
    adjudication = _write_adjudication(example)

    result = sync_adjudication(example, repo_root=repo)

    assert result == adjudication
    payload = load_adjudication(adjudication)
    assert payload["source_critique_hash"] == file_sha256(critique)
    assert payload["decisions"][0]["decision"] == "dismiss"


def test_sync_adjudication_accepts_v1_11_rubric_for_aesthetic_intent_v2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_aesthetic_intent_v2(example)
    monkeypatch.setattr(critique_adjudication, "validate_critique_schema", lambda _: None)
    critique = _write_fresh_critique(
        repo,
        example,
        schema="figure-agent.critique.v1.11",
        rubric_version=CRITIQUE_RUBRIC_VERSION_V1_11,
    )
    _write_adjudication(example)

    sync_adjudication(example, repo_root=repo)

    payload = load_adjudication(example / "critique_adjudication.yaml")
    assert payload["source_critique_hash"] == file_sha256(critique)


def test_sync_adjudication_refuses_stale_generator_metadata(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(repo, example, generator_version="sha256:bad")

    with pytest.raises(CritiqueAdjudicationError, match="generator_version mismatch"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_refuses_stale_input_hash(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    spec = parse_spec((example / "spec.yaml").read_text(encoding="utf-8"))
    old_hash = compute_critique_input_hash(
        example,
        "demo_fig",
        spec,
        style_lock_path=repo / "styles" / "polymer-paper-preamble.sty",
        base_dir=repo,
    )
    _write_fresh_critique(repo, example, critique_input_hash=old_hash)
    (example / "briefing.md").write_text("changed briefing\n", encoding="utf-8")

    with pytest.raises(CritiqueAdjudicationError, match="critique_input_hash mismatch"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_reports_missing_critique(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)

    with pytest.raises(CritiqueAdjudicationError, match="/fig_critique demo_fig"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_refuses_malformed_existing_adjudication(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(repo, example)
    (example / "critique_adjudication.yaml").write_text("decisions: [", encoding="utf-8")

    with pytest.raises(CritiqueAdjudicationError, match="invalid YAML"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_refuses_changed_finding_ids_without_force(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(repo, example)
    _write_adjudication(example)
    payload = load_adjudication(example / "critique_adjudication.yaml")
    payload["decisions"][0]["finding_id"] = "C999"
    (example / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(CritiqueAdjudicationError, match="finding ids differ"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_force_recreates_changed_finding_ids(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    critique = _write_fresh_critique(repo, example)
    _write_adjudication(example)
    payload = load_adjudication(example / "critique_adjudication.yaml")
    payload["decisions"][0]["finding_id"] = "C999"
    (example / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )

    sync_adjudication(example, repo_root=repo, force=True)

    updated = load_adjudication(example / "critique_adjudication.yaml")
    assert updated["source_critique_hash"] == file_sha256(critique)
    assert [decision["finding_id"] for decision in updated["decisions"]] == ["C001"]


def test_sync_adjudication_cli_supports_conservative_policy(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(
        repo,
        example,
        finding_severity="MINOR",
        finding_category="style",
        suggested_fix="accept_simplification - no edit required",
    )

    exit_code = main(
        [
            "sync",
            "demo_fig",
            "--force",
            "--policy",
            "conservative-v1",
            "--repo-root",
            str(repo),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "synced" in captured.out
    adjudication = load_adjudication(example / "critique_adjudication.yaml")
    assert adjudication["decisions"][0]["decision"] == "dismiss"


def test_sync_adjudication_refuses_same_id_shape_change_without_force(tmp_path: Path) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(repo, example, finding_status="resolved")
    _write_adjudication(example)

    with pytest.raises(CritiqueAdjudicationError, match="adjudication decisions differ"):
        sync_adjudication(example, repo_root=repo)


def test_sync_adjudication_cli_reports_controlled_stale_error(
    tmp_path: Path,
    capsys,
) -> None:
    repo, example = _write_repo_fixture(tmp_path)
    _write_fresh_critique(repo, example, generator_version="sha256:bad")

    exit_code = main(["sync", "demo_fig", "--repo-root", str(repo)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "generator_version mismatch" in captured.err
    assert f"/fig_critique {example.name}" in captured.err
