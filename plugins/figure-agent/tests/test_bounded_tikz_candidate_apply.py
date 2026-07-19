# ruff: noqa: E402, I001

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import bounded_tikz_candidate_apply  # noqa: E402
import bounded_tikz_candidate_packet  # noqa: E402


FIXTURE = "fig3_trapping_concept"


def _fixture(workspace: Path, name: str = FIXTURE) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / f"{name}.tex").write_text(
        "\n".join(
            [
                "% fixture",
                r"      at (3.50, 2.85) {$kT \ll E_t$\\[-1pt](escape negligible)};",
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


def _candidate_packet(workspace: Path) -> dict[str, object]:
    return bounded_tikz_candidate_packet.build_bounded_tikz_candidate_packet(
        FIXTURE,
        workspace_root=workspace,
        request_packet=_request_packet(),
    )


def _source_mutation_decision(candidate_packet: dict[str, object]) -> dict[str, object]:
    candidate = candidate_packet["candidate"]
    assert isinstance(candidate, dict)
    return {
        "schema": "figure-agent.human-decision-record.v1",
        "fixture": FIXTURE,
        "packet_schema": "figure-agent.release-decision-packet.v1",
        "packet_path": "docs/decision-packets/example-bounded-tikz-apply.json",
        "packet_recommendation": "apply_bounded_tikz_candidate",
        "queue_run_id": "bounded-tikz-apply-001",
        "decision_kind": "apply_bounded_tikz_candidate",
        "agent_recommendation": "Apply exactly one hash-bound bounded TikZ source patch.",
        "human_decision": "approve source mutation for this exact bounded TikZ patch",
        "human_note": "Source mutation is authorized only for this candidate id and hash.",
        "follow_up": {
            "command": (
                "fig-agent bounded-tikz-apply fig3_trapping_concept "
                "--apply --authorization decision.json"
            )
        },
        "mutation_boundary": "source_mutation_allowed",
        "authorized_candidate_id": candidate["id"],
        "authorized_candidate_hash": candidate["candidate_hash"],
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


def test_dry_run_reports_ready_without_mutating_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / f"{FIXTURE}.tex"
    before = source.read_text(encoding="utf-8")

    result = bounded_tikz_candidate_apply.apply_bounded_tikz_candidate(
        FIXTURE,
        workspace_root=workspace,
        candidate_packet=_candidate_packet(workspace),
        apply=False,
    )

    assert result["schema"] == bounded_tikz_candidate_apply.SCHEMA
    assert result["status"] == "ready"
    assert result["applied"] is False
    assert result["changed_files"][0]["path"] == f"examples/{FIXTURE}/{FIXTURE}.tex"
    assert source.read_text(encoding="utf-8") == before


def test_apply_blocks_without_source_mutation_decision(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / f"{FIXTURE}.tex"
    before = source.read_text(encoding="utf-8")

    result = bounded_tikz_candidate_apply.apply_bounded_tikz_candidate(
        FIXTURE,
        workspace_root=workspace,
        candidate_packet=_candidate_packet(workspace),
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["applied"] is False
    assert result["diagnostics"][0]["code"] == "source_mutation_decision_missing"
    assert source.read_text(encoding="utf-8") == before


def test_apply_exact_hash_bound_replacement_with_source_mutation_decision(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / f"{FIXTURE}.tex"
    candidate_packet = _candidate_packet(workspace)

    result = bounded_tikz_candidate_apply.apply_bounded_tikz_candidate(
        FIXTURE,
        workspace_root=workspace,
        candidate_packet=candidate_packet,
        source_mutation_decision=_source_mutation_decision(candidate_packet),
        apply=True,
    )

    assert result["status"] == "applied"
    assert result["applied"] is True
    text = source.read_text(encoding="utf-8")
    assert "3.62, 2.82" in text
    assert "3.50, 2.85" not in text
    assert result["required_commands"] == [
        f"fig-agent compile {FIXTURE} --strict",
        f"fig-agent status {FIXTURE} --json",
    ]


def test_apply_blocks_source_hash_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    packet = _candidate_packet(workspace)
    source = fixture / f"{FIXTURE}.tex"
    source.write_text(source.read_text(encoding="utf-8") + "% drift\n", encoding="utf-8")

    result = bounded_tikz_candidate_apply.apply_bounded_tikz_candidate(
        FIXTURE,
        workspace_root=workspace,
        candidate_packet=packet,
        source_mutation_decision=_source_mutation_decision(packet),
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["applied"] is False
    assert result["diagnostics"][0]["code"] == "source_hash_mismatch"


def test_apply_preserves_candidate_hash_mismatch_diagnostic_code(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    packet = _candidate_packet(workspace)
    decision = _source_mutation_decision(packet)
    decision["authorized_candidate_hash"] = "sha256:" + "0" * 64

    result = bounded_tikz_candidate_apply.apply_bounded_tikz_candidate(
        FIXTURE,
        workspace_root=workspace,
        candidate_packet=packet,
        source_mutation_decision=decision,
        apply=True,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == (
        "source_mutation_decision_candidate_hash_mismatch"
    )


def test_fig_agent_bounded_tikz_apply_dry_run_reads_workspace_source(
    tmp_path: Path,
) -> None:
    workspace = _baseline_workspace(tmp_path)

    result = _run_fig_agent(
        "bounded-tikz-apply",
        FIXTURE,
        "--dry-run",
        "--json",
        workspace=workspace,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == bounded_tikz_candidate_apply.SCHEMA
    assert payload["status"] == "ready"
    assert payload["applied"] is False


def test_fig_agent_bounded_tikz_apply_blocks_apply_without_decision(
    tmp_path: Path,
) -> None:
    workspace = _baseline_workspace(tmp_path)

    result = _run_fig_agent(
        "bounded-tikz-apply",
        FIXTURE,
        "--apply",
        "--json",
        workspace=workspace,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["diagnostics"][0]["code"] == "source_mutation_decision_missing"


def test_fig_agent_bounded_tikz_apply_uses_hash_bound_decision(
    tmp_path: Path,
) -> None:
    workspace = _baseline_workspace(tmp_path)
    source = workspace / "examples" / FIXTURE / f"{FIXTURE}.tex"
    candidate_packet = _candidate_packet(workspace)
    decision_path = tmp_path / "source-mutation-decision.json"
    decision_path.write_text(
        json.dumps(_source_mutation_decision(candidate_packet)),
        encoding="utf-8",
    )

    result = _run_fig_agent(
        "bounded-tikz-apply",
        FIXTURE,
        "--apply",
        "--authorization",
        str(decision_path),
        "--json",
        workspace=workspace,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "applied"
    assert payload["applied"] is True
    assert "3.62, 2.82" in source.read_text(encoding="utf-8")
