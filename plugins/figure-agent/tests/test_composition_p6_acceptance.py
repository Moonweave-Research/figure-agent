from __future__ import annotations

import importlib
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


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _module(name: str):
    return importlib.import_module(name)


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    (fixture / "build" / "candidates" / "CCAND001").mkdir(parents=True)
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, source


def _candidate_set(workspace: Path, source: Path, *, stale: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": "fig3_resistance_mechanism",
        "authority": "creative_review_only",
        "base": {"tex_hash": _sha256_text(source.read_text(encoding="utf-8"))},
        "candidates": [
            {
                "id": "CCAND001",
                "family": "freeform_structural",
                "permissions_required": ["apply_to_fixture_source", "accept_freeform_structural"],
                "operations": [
                    {
                        "schema": "figure-agent.composition-candidate-operation.v1",
                        "kind": "replace_semantic_block",
                        "path": source.relative_to(workspace).as_posix(),
                        "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
                        "selector": {
                            "kind": "semantic_block",
                            "object_id": "carrier_walk",
                            "start_marker": "% fig-agent:start object=carrier_walk",
                            "end_marker": "% fig-agent:end object=carrier_walk",
                        },
                        "replacement_text": SOURCE_TEXT.replace("old walk", "smoothed walk"),
                    }
                ],
            }
        ],
    }
    if stale:
        payload["freshness_vector"] = {
            "schema": "figure-agent.freshness-vector.v1",
            "status": {"source": "stale"},
            "stale_fields": ["source"],
            "blocking_for": ["rank", "apply"],
        }
    return payload


def _render_artifacts(fixture: Path, *, symlink: bool = False) -> tuple[Path, Path]:
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        outside = fixture.parent / "outside.tex"
        outside.write_text(SOURCE_TEXT.replace("old walk", "smoothed walk"), encoding="utf-8")
        source_copy.symlink_to(outside)
    else:
        source_copy.write_text(SOURCE_TEXT.replace("old walk", "smoothed walk"), encoding="utf-8")
    render_manifest = sandbox / "composition_render_manifest.json"
    render_manifest.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": "CCAND001",
                "sandbox_path": "build/candidates/CCAND001",
                "artifacts": {
                    "source_copy": "build/candidates/CCAND001/source/candidate.tex"
                },
                "hash_evidence": {
                    "source_copy": _sha256_text(SOURCE_TEXT.replace("old walk", "smoothed walk"))
                },
                "stages": {
                    "prepare": {"status": "success"},
                    "compile": {"status": "not_run"},
                    "export": {"status": "not_run"},
                    "crop": {"status": "not_run"},
                    "evaluate": {"status": "not_run"},
                },
                "human_review_required": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return render_manifest, source_copy


def test_apply_readiness_reports_ready_for_local_acceptance(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    _render_artifacts(workspace / "examples" / "fig3_resistance_mechanism")

    readiness = _module("composition_acceptance").build_composition_apply_readiness(
        "fig3_resistance_mechanism",
        candidate_set=_candidate_set(workspace, source),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    assert readiness["schema"] == "figure-agent.composition-apply-readiness.v1"
    assert readiness["status"] == "ready_for_local_acceptance"
    assert readiness["source_mutation_allowed"] is False
    assert readiness["blocking_reasons"] == []
    assert readiness["required_commands"][0].startswith("fig-agent compose-accept")


def test_apply_readiness_blocks_stale_freshness(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    _render_artifacts(workspace / "examples" / "fig3_resistance_mechanism")

    readiness = _module("composition_acceptance").build_composition_apply_readiness(
        "fig3_resistance_mechanism",
        candidate_set=_candidate_set(workspace, source, stale=True),
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    assert readiness["status"] == "blocked"
    assert readiness["blocking_reasons"] == ["refresh_required"]


def test_apply_readiness_blocks_source_hash_drift(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    _render_artifacts(workspace / "examples" / "fig3_resistance_mechanism")
    candidate_set = _candidate_set(workspace, source)
    source.write_text(SOURCE_TEXT.replace("old walk", "changed walk"), encoding="utf-8")

    readiness = _module("composition_acceptance").build_composition_apply_readiness(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        candidate_id="CCAND001",
        workspace_root=workspace,
    )

    assert readiness["status"] == "blocked"
    assert readiness["blocking_reasons"][0] == "source_hash_drift"


def test_apply_readiness_rejects_missing_manifest_and_symlinked_source_copy(
    tmp_path: Path,
) -> None:
    workspace, source = _fixture(tmp_path)
    fixture = workspace / "examples" / "fig3_resistance_mechanism"
    render_manifest, source_copy = _render_artifacts(fixture)
    module = _module("composition_acceptance")

    render_manifest.unlink()
    with pytest.raises(module.CompositionAcceptanceError, match="render_manifest_missing"):
        module.build_composition_apply_readiness(
            "fig3_resistance_mechanism",
            candidate_set=_candidate_set(workspace, source),
            candidate_id="CCAND001",
            workspace_root=workspace,
        )

    render_manifest, source_copy = _render_artifacts(fixture)
    source_copy.unlink()
    source_copy.symlink_to(fixture.parent / "outside.tex")
    with pytest.raises(module.CompositionAcceptanceError, match="sandbox_symlink_forbidden"):
        module.build_composition_apply_readiness(
            "fig3_resistance_mechanism",
            candidate_set=_candidate_set(workspace, source),
            candidate_id="CCAND001",
            workspace_root=workspace,
        )


def test_write_acceptance_records_hash_evidence_and_permissions_only(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    fixture = workspace / "examples" / "fig3_resistance_mechanism"
    render_manifest, source_copy = _render_artifacts(fixture)
    before = {
        path.relative_to(fixture).as_posix()
        for path in fixture.rglob("*")
        if path.is_file()
    }

    payload = _module("composition_acceptance").write_composition_acceptance(
        "fig3_resistance_mechanism",
        "CCAND001",
        candidate_set=_candidate_set(workspace, source),
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        permissions_granted=["apply_to_fixture_source", "accept_freeform_structural"],
        workspace_root=workspace,
    )

    acceptance_path = fixture / "build" / "candidates" / "CCAND001" / "composition_acceptance.json"
    after = {
        path.relative_to(fixture).as_posix()
        for path in fixture.rglob("*")
        if path.is_file()
    }
    data = json.loads(acceptance_path.read_text(encoding="utf-8"))
    assert payload["path"] == "build/candidates/CCAND001/composition_acceptance.json"
    assert after - before == {"build/candidates/CCAND001/composition_acceptance.json"}
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert data["schema"] == "figure-agent.composition-acceptance.v1"
    assert data["reviewer"] == "local-user"
    assert data["rationale"] == "Rendered evidence reviewed."
    assert data["permissions_granted"] == ["apply_to_fixture_source", "accept_freeform_structural"]
    assert data["hash_evidence"]["source"] == _sha256_text(SOURCE_TEXT)
    assert data["hash_evidence"]["render_manifest"] == _sha256_text(
        render_manifest.read_text(encoding="utf-8")
    )
    assert source_copy.read_text(encoding="utf-8") == SOURCE_TEXT.replace(
        "old walk",
        "smoothed walk",
    )


def test_write_acceptance_rejects_missing_freeform_permission(tmp_path: Path) -> None:
    workspace, source = _fixture(tmp_path)
    fixture = workspace / "examples" / "fig3_resistance_mechanism"
    _render_artifacts(fixture)

    with pytest.raises(
        _module("composition_acceptance").CompositionAcceptanceError,
        match="accept_freeform_structural",
    ):
        _module("composition_acceptance").write_composition_acceptance(
            "fig3_resistance_mechanism",
            "CCAND001",
            candidate_set=_candidate_set(workspace, source),
            candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
            reviewer="local-user",
            rationale="Rendered evidence reviewed.",
            permissions_granted=["apply_to_fixture_source"],
            workspace_root=workspace,
        )
