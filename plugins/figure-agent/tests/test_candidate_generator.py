from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def test_candidates_include_required_provenance_fields(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert payload["schema"] == "figure-agent.candidate-set.v1"
    assert payload["base"]["tex_hash"].startswith("sha256:")
    assert candidate["affected_files"] == ["examples/candidate_demo/candidate_demo.tex"]
    assert candidate["selector"]["original_hash"].startswith("sha256:")
    assert candidate["rollback"]["strategy"] == "reverse_operations"
    assert candidate["verification"]["required_commands"] == [
        "fig-agent compile candidate_demo --strict",
        "fig-agent status candidate_demo --json",
    ]
    assert candidate["apply_authority"] == "apply_eligible"


def test_candidates_do_not_emit_for_missing_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples" / "candidate_demo").mkdir(parents=True)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"][0]["code"] == "source_missing"


def test_candidate_output_rejects_fixture_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
            output_path=workspace / "outside.json",
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "path_escape" in str(exc)
    else:
        raise AssertionError("expected output path escape to be rejected")


def test_candidate_output_accepts_fixture_relative_output_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
        output_path=Path("build/candidates/candidate_set.json"),
    )

    assert payload["candidates"][0]["id"] == "CAND001"


def test_candidate_generator_refuses_symlinked_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside.tex"
    outside.write_text("\\node (label-a) at (0,0) {External};\n", encoding="utf-8")
    (fixture / "candidate_demo.tex").unlink()
    (fixture / "candidate_demo.tex").symlink_to(outside)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "source_symlink_forbidden" in str(exc)
    else:
        raise AssertionError("expected source symlink to be rejected")


def test_candidates_downgrade_apply_authority_from_intent_floor(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: missing.png
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"][0]["apply_authority"] == "review_only"
