from __future__ import annotations

import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

pytestmark = pytest.mark.quarantine

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: candidate_demo\npanels:\n  - id: C\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(SOURCE_TEXT, encoding="utf-8")
    return fixture


def _candidate_set(fixture: Path, source_hash: str) -> Path:
    path = fixture / "build" / "candidates" / "composition_candidate_set.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": fixture.name,
                "authority": "creative_review_only",
                "base": {"tex_hash": source_hash},
                "candidates": [
                    {
                        "id": "CCAND001",
                        "family": "freeform_structural",
                        "operations": [
                            {
                                "schema": "figure-agent.composition-candidate-operation.v1",
                                "kind": "replace_semantic_block",
                                "path": f"examples/{fixture.name}/{fixture.name}.tex",
                                "base_source_hash": source_hash,
                                "selector": {
                                    "kind": "semantic_block",
                                    "start_marker": "% fig-agent:start object=carrier_walk",
                                    "end_marker": "% fig-agent:end object=carrier_walk",
                                },
                                "replacement_text": SOURCE_TEXT.replace(
                                    "old walk",
                                    "smoothed walk",
                                ),
                            }
                        ],
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _prepare_render_artifacts(fixture: Path) -> Path:
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
    source_copy.write_text(SOURCE_TEXT.replace("old walk", "smoothed walk"), encoding="utf-8")
    (sandbox / "composition_render_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-render-manifest.v1",
                "fixture": fixture.name,
                "candidate_id": "CCAND001",
                "sandbox_path": "build/candidates/CCAND001",
                "artifacts": {"source_copy": "build/candidates/CCAND001/source/candidate.tex"},
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
    return source_copy


def test_fig_agent_compose_apply_ready_reports_ready_for_local_acceptance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    _prepare_render_artifacts(fixture)
    _candidate_set(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = _run(
        workspace,
        "compose-apply-ready",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/composition_candidate_set.json",
        "--candidate-id",
        "CCAND001",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.composition-apply-readiness.v1"
    assert payload["status"] == "ready_for_local_acceptance"
    assert payload["source_mutation_allowed"] is False
    assert payload["blocking_reasons"] == []
    assert payload["required_commands"][0].startswith("fig-agent compose-accept")
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT


def test_fig_agent_compose_accept_writes_composition_acceptance_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    source_copy = _prepare_render_artifacts(fixture)
    candidate_set_path = _candidate_set(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = _run(
        workspace,
        "compose-accept",
        "candidate_demo",
        "CCAND001",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--reviewer",
        "local-user",
        "--rationale",
        "Rendered evidence reviewed.",
        "--permissions-granted",
        "apply_to_fixture_source",
        "accept_freeform_structural",
        "--json",
    )

    acceptance_path = fixture / "build" / "candidates" / "CCAND001" / "composition_acceptance.json"
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.composition-acceptance-write-result.v1"
    assert payload["path"] == "build/candidates/CCAND001/composition_acceptance.json"
    assert acceptance_path.is_file()
    assert payload["acceptance"]["schema"] == "figure-agent.composition-acceptance.v1"
    assert json.loads(acceptance_path.read_text(encoding="utf-8"))["reviewer"] == "local-user"
    assert source.read_text(encoding="utf-8") == SOURCE_TEXT
    assert source_copy.read_text(encoding="utf-8") == SOURCE_TEXT.replace(
        "old walk",
        "smoothed walk",
    )
