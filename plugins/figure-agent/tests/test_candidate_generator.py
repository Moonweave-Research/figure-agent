from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402
import quality_defect_ledger  # noqa: E402


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


def _write_undeclared_candidate_defect(fixture: Path, source_line: int = 1) -> None:
    build_dir = fixture / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": source_line,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_candidates_include_required_provenance_fields(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)

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
    source_defect = candidate["source_defect"]
    assert source_defect.pop("source_fingerprint").startswith("sha256:")
    assert source_defect == {
        "id": "QD001",
        "source": "deterministic_audit",
        "defect_class": "text_overlap",
        "evidence": [
            {
                "uri": "figure://candidate_demo/audit/undeclared-geometry",
                "node_id": "UG001",
            }
        ],
    }


def test_candidates_do_not_emit_blind_first_offsettable_fallback(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "no_supported_candidate"}]


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
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)

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


def test_candidate_generator_refuses_symlinked_fixture_dir(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    external_workspace = tmp_path / "external"
    external_fixture = _fixture(external_workspace)
    fixture_link = workspace / "examples" / "candidate_demo"
    fixture_link.parent.mkdir(parents=True)
    fixture_link.symlink_to(external_fixture)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "fixture_symlink_forbidden" in str(exc)
    else:
        raise AssertionError("expected fixture directory symlink to be rejected")


def test_candidates_downgrade_apply_authority_from_intent_floor(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)
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


def test_candidate_targets_ledger_defect_line_not_first_offsettable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    # First offsettable line is line 1 (the panel-letter node); the real defect is line 3.
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {a};\n"
        "\\node (title) {Origin of traps};\n"
        "\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    build_dir = fixture / "build"
    build_dir.mkdir()
    (build_dir / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 3,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "candidate_demo",
        workspace_root=workspace,
    )
    first_defect = ledger["defects"][0]
    assert first_defect["patchability"]["state"] == "safe_candidate"
    assert first_defect["selector_hint"] == {"kind": "line_range", "value": "3:3"}

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert candidate["id"] == "CAND001"
    assert candidate["selector"]["kind"] == "line_range_with_hash"
    assert candidate["selector"]["start_line"] == 3
    assert candidate["selector"]["end_line"] == 3


def test_candidate_generator_skips_line_weight_style_safe_defect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {
                    "id": "QD001",
                    "source": "critique_adjudication",
                    "defect_class": "line_weight_style",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "C001"}],
                    "selector_hint": {"kind": "line_range", "value": "1:1"},
                    "patchability": {"state": "safe_candidate"},
                }
            ]
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "no_supported_candidate"}]
