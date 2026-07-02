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


def _proposal(fixture: Path, source_hash: str, *, generation: bool = False) -> Path:
    payload = {
        "schema": "figure-agent.composition-candidate-set.v1",
        "fixture": fixture.name,
        "authority": "creative_review_only",
        "base": {"tex_hash": source_hash},
        "candidates": [
            {
                "id": "CCAND001",
                "family": "freeform_structural",
                "proposal_source": "host",
            }
        ],
    }
    if generation:
        payload["model_prompt"] = "generate a candidate"
    path = fixture / "proposal.json"
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _candidate_set(fixture: Path, source_hash: str) -> Path:
    path = fixture / "build" / "candidates" / "composition_candidate_set.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": fixture.name,
                "status": "proposed_unranked",
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


def test_fig_agent_compose_capture_outputs_json_without_model_call(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    proposal_path = _proposal(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = _run(
        workspace,
        "compose-capture",
        "candidate_demo",
        "--proposal",
        proposal_path.relative_to(workspace).as_posix(),
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.composition-candidate-set.v1"
    assert payload["fixture"] == "candidate_demo"
    assert payload["capture_policy"]["model_calls_allowed"] is False
    assert payload["capture_policy"]["executable_payload_allowed"] is False


def test_fig_agent_compose_capture_output_is_fixture_local(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    proposal_path = _proposal(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = _run(
        workspace,
        "compose-capture",
        "candidate_demo",
        "--proposal",
        proposal_path.relative_to(workspace).as_posix(),
        "--output",
        "build/candidates/composition_candidate_set.json",
        "--json",
    )

    output = fixture / "build" / "candidates" / "composition_candidate_set.json"
    assert result.returncode == 0, result.stderr
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == (
        "figure-agent.composition-candidate-set.v1"
    )


def test_fig_agent_compose_capture_rejects_generation_payload_cleanly(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    proposal_path = _proposal(
        fixture,
        _sha256_text(source.read_text(encoding="utf-8")),
        generation=True,
    )

    result = _run(
        workspace,
        "compose-capture",
        "candidate_demo",
        "--proposal",
        proposal_path.relative_to(workspace).as_posix(),
        "--json",
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "goal_generation_forbidden" in result.stderr


def test_fig_agent_compose_render_outputs_prepare_manifest_without_tex_execution(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(source.read_text(encoding="utf-8")))

    result = _run(
        workspace,
        "compose-render",
        "candidate_demo",
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )

    manifest = fixture / "build" / "candidates" / "CCAND001" / "composition_render_manifest.json"
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.composition-render-result.v1"
    assert payload["status"] == "prepared"
    assert payload["rendered"][0]["render_manifest"] == (
        "build/candidates/CCAND001/composition_render_manifest.json"
    )
    assert manifest.is_file()
    assert not (fixture / "build" / "candidates" / "CCAND001" / "render").exists()
