# ruff: noqa: E402, I001

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import bounded_tikz_candidate_packet  # noqa: E402


FIXTURE = "fig3_trapping_concept"


def _fixture(workspace: Path, name: str = FIXTURE) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\n".join(
            [
                "% fixture",
                r"  \node[font=\textsf{\fontsize{6.5}{8}\selectfont}, cGray!70!black,",
                r"        anchor=west, align=left]",
                r"      at (3.50, 2.85) {$kT \ll E_t$\\[-1pt](escape negligible)};",
                r"  \node at (0,0) {other};",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def _request_packet() -> dict[str, object]:
    return {
        "schema": "figure-agent.bounded-tikz-refinement-packet.v1",
        "fixture": FIXTURE,
        "state": "ready_for_human_source_mutation_choice",
        "mutation_boundary": "no_source_mutation",
        "authorizes_source_mutation": False,
        "candidate_family": {
            "id": "restrained_tikz_refinement",
            "source_mutation_boundary": "source_mutation_requires_separate_approval",
        },
    }


def _run_fig_agent(*args: str, workspace: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace or PLUGIN_ROOT)
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=PLUGIN_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _baseline_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    fixture_dir = workspace / "examples" / FIXTURE
    shutil.copytree(PLUGIN_ROOT / "examples" / FIXTURE, fixture_dir)
    (fixture_dir / f"{FIXTURE}.tex").write_text(
        "\n".join(
            [
                "% fixture",
                r"      at (3.50, 2.85) {$kT \ll E_t$\\[-1pt](escape negligible)};",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return workspace


def test_candidate_packet_contains_hash_bound_patch_without_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = (workspace / "examples" / FIXTURE / f"{FIXTURE}.tex").read_text(
        encoding="utf-8"
    )

    packet = bounded_tikz_candidate_packet.build_bounded_tikz_candidate_packet(
        FIXTURE,
        workspace_root=workspace,
        request_packet=_request_packet(),
    )

    assert packet["schema"] == bounded_tikz_candidate_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "candidate_packet_ready_for_human_review"
    assert packet["mutation_boundary"] == "no_source_mutation"
    assert packet["authorizes_source_mutation"] is False
    assert packet["candidate"]["id"] == "BTIKZ001"
    assert packet["candidate"]["family"] == "restrained_tikz_refinement"
    assert packet["candidate"]["edit_class"] == "label_spacing"
    assert packet["candidate"]["source_hash"].startswith("sha256:")
    assert packet["candidate"]["selector"]["original_hash"].startswith("sha256:")
    assert packet["candidate"]["operations"][0]["kind"] == "replace_text"
    assert "3.62, 2.82" in packet["candidate"]["operations"][0]["replacement"]
    assert packet["candidate"]["rollback"]["strategy"] == "reverse_operations"
    assert packet["candidate"]["verification"]["required_commands"] == [
        f"fig-agent compile {FIXTURE} --strict",
        f"fig-agent status {FIXTURE} --json",
        f"fig-agent bounded-tikz-candidate {FIXTURE} --json",
    ]
    after = (workspace / "examples" / FIXTURE / f"{FIXTURE}.tex").read_text(
        encoding="utf-8"
    )
    assert after == before


def test_candidate_packet_blocks_when_request_does_not_authorize_preparation(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    request = _request_packet()
    request["state"] = "blocked_missing_style_benchmark_pack"

    packet = bounded_tikz_candidate_packet.build_bounded_tikz_candidate_packet(
        FIXTURE,
        workspace_root=workspace,
        request_packet=request,
    )

    assert packet["state"] == "blocked_refinement_request_not_ready"
    assert packet["candidate"] is None
    assert packet["authorizes_source_mutation"] is False


def test_candidate_packet_reports_when_candidate_is_already_reflected(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / f"{FIXTURE}.tex"
    source.write_text(
        source.read_text(encoding="utf-8").replace("3.50, 2.85", "3.62, 2.82"),
        encoding="utf-8",
    )

    packet = bounded_tikz_candidate_packet.build_bounded_tikz_candidate_packet(
        FIXTURE,
        workspace_root=workspace,
        request_packet=_request_packet(),
    )

    assert packet["state"] == "blocked_candidate_already_reflected"
    assert packet["candidate"] is None
    assert packet["next_agent_action"] == "refresh_benchmark_evidence_for_current_source"


def test_candidate_packet_rejects_unsafe_fixture(tmp_path: Path) -> None:
    with pytest.raises(
        bounded_tikz_candidate_packet.BoundedTikzCandidatePacketError,
        match="fixture_invalid",
    ):
        bounded_tikz_candidate_packet.build_bounded_tikz_candidate_packet(
            "../escape",
            workspace_root=tmp_path,
            request_packet=_request_packet(),
        )


def test_fig_agent_bounded_tikz_candidate_cli_reads_workspace_source(
    tmp_path: Path,
) -> None:
    workspace = _baseline_workspace(tmp_path)

    result = _run_fig_agent("bounded-tikz-candidate", FIXTURE, "--json", workspace=workspace)

    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    assert packet["schema"] == bounded_tikz_candidate_packet.SCHEMA
    assert packet["fixture"] == FIXTURE
    assert packet["state"] == "candidate_packet_ready_for_human_review"
    assert packet["authorizes_source_mutation"] is False
    assert packet["candidate"]["source_hash"].startswith("sha256:")
    assert packet["candidate"]["operations"][0]["path"] == (
        f"examples/{FIXTURE}/{FIXTURE}.tex"
    )
