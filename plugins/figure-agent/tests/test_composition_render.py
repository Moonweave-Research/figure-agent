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
    "% fig-agent:start object=current_sparkline\n"
    "old spark\n"
    "% fig-agent:end object=current_sparkline\n"
)
REPLACEMENT_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "smoothed walk\n"
    "% fig-agent:end object=carrier_walk\n"
)
SPARKLINE_REPLACEMENT_TEXT = (
    "% fig-agent:start object=current_sparkline\n"
    "anchored spark\n"
    "% fig-agent:end object=current_sparkline\n"
)
ORIGINAL_SPARKLINE_TEXT = (
    "% fig-agent:start object=current_sparkline\n"
    "old spark\n"
    "% fig-agent:end object=current_sparkline\n"
)


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path, name: str = "fig3_resistance_mechanism") -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        "name: fig3_resistance_mechanism\npanels:\n  - id: A\n",
        encoding="utf-8",
    )
    source = fixture / f"{name}.tex"
    source.write_text(SOURCE_TEXT, encoding="utf-8")
    return workspace, fixture, source


def _candidate_set(workspace: Path, source: Path, name: str = "fig3_resistance_mechanism") -> dict:
    return {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": name,
        "status": "proposed_unranked",
        "candidates": [
            {
                "id": "CCAND001",
                "family": "freeform_structural",
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
                        "replacement_text": REPLACEMENT_TEXT,
                        "rollback": {"kind": "restore_original_text", "original_text": SOURCE_TEXT},
                    }
                ],
            }
        ],
    }


def _sparkline_operation(workspace: Path, source: Path) -> dict:
    return {
        "schema": "figure-agent.composition-candidate-operation.v1",
        "kind": "replace_semantic_block",
        "path": source.relative_to(workspace).as_posix(),
        "base_source_hash": _sha256_text(source.read_text(encoding="utf-8")),
        "selector": {
            "kind": "semantic_block",
            "object_id": "current_sparkline",
            "start_marker": "% fig-agent:start object=current_sparkline",
            "end_marker": "% fig-agent:end object=current_sparkline",
        },
        "replacement_text": SPARKLINE_REPLACEMENT_TEXT,
        "rollback": {"kind": "restore_original_text", "original_text": "old spark\n"},
    }


def test_prepare_compose_render_writes_candidate_source_copy_only_in_sandbox(
    tmp_path: Path,
) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    candidate_set = _candidate_set(workspace, source)

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/composition_candidate_set.json"),
        candidate_id="CCAND001",
    )

    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    manifest = sandbox / "composition_render_manifest.json"
    assert result["schema"] == "figure-agent.composition-render-result.v1"
    assert result["status"] == "prepared"
    assert result["rendered"][0]["render_manifest"] == (
        "build/candidates/CCAND001/composition_render_manifest.json"
    )
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert source_copy.read_text(encoding="utf-8") == REPLACEMENT_TEXT + ORIGINAL_SPARKLINE_TEXT
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-agent.composition-render-manifest.v1"
    assert data["artifacts"]["source_copy"] == "build/candidates/CCAND001/source/candidate.tex"
    assert data["stages"] == {
        "prepare": {"status": "success"},
        "compile": {"status": "not_run"},
        "export": {"status": "not_run"},
        "crop": {"status": "not_run"},
        "evaluate": {"status": "not_run"},
    }
    assert data["render_policy"] == {
        "tex_execution_allowed": False,
        "model_calls_allowed": False,
        "executable_payload_allowed": False,
    }
    assert not (sandbox / "render" / "candidate.pdf").exists()


def test_prepare_compose_render_rejects_source_hash_drift_as_rebase_required(
    tmp_path: Path,
) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    candidate_set = _candidate_set(workspace, source)
    source.write_text(SOURCE_TEXT.replace("old walk", "changed walk"), encoding="utf-8")

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_id="CCAND001",
    )

    assert result["status"] == "rebase_required"
    assert result["diagnostics"][0]["code"] == "source_hash_drift"
    assert result["diagnostics"][0]["action"] == "rebase_required"
    assert not (fixture / "build" / "candidates" / "CCAND001" / "source").exists()


def test_prepare_compose_render_reuses_path_and_symlink_preflight(tmp_path: Path) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    candidate_set = _candidate_set(workspace, source)
    outside = tmp_path / "outside.tex"
    outside.write_text(SOURCE_TEXT, encoding="utf-8")
    source.unlink()
    source.symlink_to(outside)

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_id="CCAND001",
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "sandbox_symlink_forbidden"
    assert result["diagnostics"][0]["stage"] == "pre_tex"


def test_prepare_compose_render_resolves_object_id_semantic_selector_without_line_ranges(
    tmp_path: Path,
) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    candidate_set = _candidate_set(workspace, source)
    operation = candidate_set["candidates"][0]["operations"][0]
    operation["selector"] = {"kind": "semantic_block", "object_id": "carrier_walk"}

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_id="CCAND001",
    )

    source_copy = fixture / "build" / "candidates" / "CCAND001" / "source" / "candidate.tex"
    assert result["status"] == "prepared"
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert source_copy.read_text(encoding="utf-8") == REPLACEMENT_TEXT + ORIGINAL_SPARKLINE_TEXT


def test_prepare_compose_render_applies_multiple_semantic_block_operations(
    tmp_path: Path,
) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    candidate_set = _candidate_set(workspace, source)
    candidate = candidate_set["candidates"][0]
    candidate["id"] = "CCAND_COMBO"
    candidate["operations"].append(_sparkline_operation(workspace, source))

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_id="CCAND_COMBO",
    )

    source_copy = fixture / "build" / "candidates" / "CCAND_COMBO" / "source" / "candidate.tex"
    assert result["status"] == "prepared"
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert source_copy.read_text(encoding="utf-8") == REPLACEMENT_TEXT + SPARKLINE_REPLACEMENT_TEXT


def test_prepare_compose_render_preserves_separator_after_replacement_without_trailing_newline(
    tmp_path: Path,
) -> None:
    import composition_render

    workspace, fixture, source = _fixture(tmp_path)
    source.write_text(
        "% fig-agent:start object=carrier_walk\n"
        "old walk\n"
        "% fig-agent:end object=carrier_walk\n"
        "\\node[sub] {following label};\n",
        encoding="utf-8",
    )
    candidate_set = _candidate_set(workspace, source)
    operation = candidate_set["candidates"][0]["operations"][0]
    operation["base_source_hash"] = _sha256_text(source.read_text(encoding="utf-8"))
    operation["replacement_text"] = REPLACEMENT_TEXT.rstrip("\n")

    result = composition_render.prepare_composition_render(
        "fig3_resistance_mechanism",
        candidate_set=candidate_set,
        workspace_root=workspace,
        candidate_id="CCAND001",
    )

    source_copy = fixture / "build" / "candidates" / "CCAND001" / "source" / "candidate.tex"
    assert result["status"] == "prepared"
    assert (
        "% fig-agent:end object=carrier_walk\n"
        "\\node[sub] {following label};\n"
    ) in source_copy.read_text(encoding="utf-8")
