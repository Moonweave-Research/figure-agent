from __future__ import annotations

import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
SOURCE_TEXT = (
    "% fig-agent:start object=carrier_walk\n"
    "old walk\n"
    "% fig-agent:end object=carrier_walk\n"
)
AFTER_TEXT = SOURCE_TEXT.replace("old walk", "smoothed walk")


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "candidate_demo"
    fixture.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text(SOURCE_TEXT, encoding="utf-8")
    return fixture


def _candidate_set(fixture: Path, source_hash: str) -> Path:
    path = fixture / "build" / "candidates" / "composition_candidate_set.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "figure-agent.composition-candidate-set.v1",
                "fixture": fixture.name,
                "candidates": [
                    {
                        "id": "CCAND001",
                        "family": "freeform_structural",
                        "operations": [
                            {
                                "kind": "replace_semantic_block",
                                "path": f"examples/{fixture.name}/{fixture.name}.tex",
                                "base_source_hash": source_hash,
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
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _render_artifacts(fixture: Path) -> None:
    sandbox = fixture / "build" / "candidates" / "CCAND001"
    source_copy = sandbox / "source" / "candidate.tex"
    source_copy.parent.mkdir(parents=True)
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


def test_fig_agent_compose_apply_mutates_after_explicit_acceptance(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    candidate_set_path = _candidate_set(fixture, _sha256_text(SOURCE_TEXT))
    _render_artifacts(fixture)

    accept = _run(
        workspace,
        "compose-accept",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--reviewer",
        "local-user",
        "--rationale",
        "Reviewed before apply.",
        "--permission",
        "apply_to_fixture_source",
        "--permission",
        "accept_freeform_structural",
        "--json",
    )
    assert accept.returncode == 0, accept.stderr

    result = _run(
        workspace,
        "compose-apply",
        fixture.name,
        "--candidate-set",
        candidate_set_path.relative_to(fixture).as_posix(),
        "--candidate-id",
        "CCAND001",
        "--json",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert payload["schema"] == "figure-agent.composition-apply-result.v1"
    assert payload["status"] == "applied_unverified"
    assert source.read_text(encoding="utf-8") == AFTER_TEXT
    assert (fixture / "build" / "candidates" / "CCAND001" / "rollback.patch").is_file()
