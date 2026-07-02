from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

import pytest

pytestmark = pytest.mark.quarantine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)
AFTER_TEXT = SOURCE_TEXT.replace("old walk", "smoothed walk")


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path, name: str = "candidate_demo") -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    (fixture / "build" / "candidates" / "CCAND001").mkdir(parents=True)
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, source


def _candidate_set(workspace: Path, source: Path) -> dict[str, object]:
    return {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": source.stem,
        "candidates": [
            {
                "id": "CCAND001",
                "family": "freeform_structural",
                "operations": [
                    {
                        "schema": "figure-agent.composition-candidate-operation.v1",
                        "kind": "replace_semantic_block",
                        "path": source.relative_to(workspace).as_posix(),
                        "base_source_hash": _sha256_text(SOURCE_TEXT),
                        "selector": {
                            "kind": "semantic_block",
                            "start_marker": "% fig-agent:start object=carrier_walk",
                            "end_marker": "% fig-agent:end object=carrier_walk",
                        },
                        "replacement_text": AFTER_TEXT,
                    }
                ],
            }
        ],
    }


def _render_artifacts(fixture: Path) -> None:
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    source_copy.write_text(AFTER_TEXT, encoding="utf-8")
    (sandbox / "composition_render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": "CCAND001",
                "artifacts": {"source_copy": "build/candidates/CCAND001/source/candidate.tex"},
                "hash_evidence": {"source_copy": _sha256_text(AFTER_TEXT)},
                "stages": {
                    "prepare": {"status": "success"},
                    "compile": {"status": "not_run"},
                    "export": {"status": "not_run"},
                    "crop": {"status": "not_run"},
                    "evaluate": {"status": "not_run"},
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _accepted(workspace: Path, source: Path) -> tuple[dict[str, object], dict[str, object]]:
    import composition_acceptance

    fixture = source.parent
    candidate_set = _candidate_set(workspace, source)
    _render_artifacts(fixture)
    result = composition_acceptance.write_composition_acceptance(
        fixture.name,
        "CCAND001",
        candidate_set=candidate_set,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
        reviewer="local-user",
        rationale="Reviewed before apply.",
        permissions_granted=["apply_to_fixture_source", "accept_freeform_structural"],
        workspace_root=workspace,
    )
    return candidate_set, result["acceptance"]


def test_apply_acceptance_mutates_only_source_and_writes_rollback(tmp_path: Path) -> None:
    import composition_apply

    workspace, source = _fixture(tmp_path)
    fixture = source.parent
    candidate_set, acceptance = _accepted(workspace, source)
    before = {path.relative_to(fixture).as_posix() for path in fixture.rglob("*") if path.is_file()}

    result = composition_apply.apply_composition_acceptance(
        fixture.name,
        "CCAND001",
        candidate_set=candidate_set,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
        acceptance=acceptance,
        workspace_root=workspace,
    )

    after = {path.relative_to(fixture).as_posix() for path in fixture.rglob("*") if path.is_file()}
    assert result["schema"] == "figure-agent.composition-apply-result.v1"
    assert result["status"] == "applied_unverified"
    assert result["source_mutation_allowed"] is True
    assert source.read_text(encoding="utf-8") == AFTER_TEXT
    assert after - before == {
        "build/candidates/CCAND001/composition_apply_result.json",
        "build/candidates/CCAND001/rollback.patch",
    }
    assert result["changed_files"][0]["path"] == "candidate_demo.tex"
    assert "old walk" in (fixture / result["rollback_patch"]).read_text(encoding="utf-8")


def test_apply_acceptance_blocks_hash_drift_before_mutation(tmp_path: Path) -> None:
    import composition_apply

    workspace, source = _fixture(tmp_path)
    fixture = source.parent
    candidate_set, acceptance = _accepted(workspace, source)
    source.write_text(SOURCE_TEXT.replace("old walk", "changed walk"), encoding="utf-8")

    result = composition_apply.apply_composition_acceptance(
        fixture.name,
        "CCAND001",
        candidate_set=candidate_set,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
        acceptance=acceptance,
        workspace_root=workspace,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "acceptance_not_current"
    assert source.read_text(encoding="utf-8") != AFTER_TEXT


def test_apply_acceptance_requires_source_mutation_permission(tmp_path: Path) -> None:
    import composition_apply

    workspace, source = _fixture(tmp_path)
    fixture = source.parent
    candidate_set, acceptance = _accepted(workspace, source)
    acceptance["permissions_granted"] = ["accept_freeform_structural"]

    with pytest.raises(composition_apply.CompositionApplyError, match="apply_to_fixture_source"):
        composition_apply.apply_composition_acceptance(
            fixture.name,
            "CCAND001",
            candidate_set=candidate_set,
            candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
            acceptance=acceptance,
            workspace_root=workspace,
        )
