from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import evidence_hash  # noqa: E402
import golden_acceptance  # noqa: E402
from test_evidence_index import _fixture  # noqa: E402


def _decision_record_text(*, packet_timestamp: str, note: str) -> str:
    return (
        json.dumps(
            {
                "schema": "figure-agent.human-decision-record.v1",
                "fixture": "candidate_demo",
                "packet_schema": "figure-agent.release-decision-packet.v1",
                "packet_path": "docs/decision-packets/candidate_demo.json",
                "packet_recommendation": "accept_current_generated_export",
                "packet_timestamp": packet_timestamp,
                "decision_kind": "accept_current_generated_export",
                "agent_recommendation": "Record explicit acceptance separately.",
                "human_decision": "accept_current_generated_export",
                "human_note": note,
                "follow_up": {"implementation_slice": "run explicit release operation"},
                "mutation_boundary": "no_source_mutation",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _commit_everything(plugin_root: Path) -> None:
    """An authorization must be committed, so the tmp plugin root is a real repo."""
    subprocess.run(["git", "init", "-q"], cwd=plugin_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=plugin_root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "authorization",
        ],
        cwd=plugin_root,
        check=True,
        capture_output=True,
    )


def _write_release_decision_record(
    plugin_root: Path,
    *,
    stem: str = "candidate_demo_accept_current_generated_export",
    packet_timestamp: str = "2026-07-01T00:00:00Z",
    note: str = "Authorizes naming the release operation only.",
    commit: bool = True,
) -> Path:
    records_root = plugin_root / "docs" / "decision-records" / "tests"
    records_root.mkdir(parents=True, exist_ok=True)
    path = records_root / f"{stem}.json"
    path.write_text(
        _decision_record_text(packet_timestamp=packet_timestamp, note=note),
        encoding="utf-8",
    )
    if commit:
        _commit_everything(plugin_root)
    return plugin_root


def _write_authorizing_decision_record(plugin_root: Path) -> Path:
    return _write_release_decision_record(plugin_root)


def _ready_payload(*, critique_state: str = "passed") -> dict:
    checks = [
        {"id": "candidate_apply", "state": "passed", "reason": "", "command": None},
        {"id": "compile", "state": "passed", "reason": "", "command": None},
        {
            "id": "critique",
            "state": critique_state,
            "reason": "critique_state is STALE" if critique_state != "passed" else "",
            "command": "/fig_critique demo" if critique_state != "passed" else None,
        },
        {
            "id": "export",
            "state": "blocked",
            "reason": "tracked golden export requires deliberate manual approval",
            "command": None,
        },
        {
            "id": "golden_acceptance",
            "state": "blocked",
            "reason": "tracked golden export requires current golden acceptance",
            "command": None,
        },
        {
            "id": "loop_rerun",
            "state": "blocked",
            "reason": "closeout prerequisites are incomplete: export",
            "evidence": {"blocked_by": ["export"]},
        },
    ]
    return {
        "schema": "figure-agent.closeout-readiness.v1",
        "figure_name": "candidate_demo",
        "status": "blocked",
        "checks": checks,
        "next_action": "tracked golden export requires deliberate manual approval",
        "evidence_index": {
            "source": {"tex_sha256": "sha256:" + "1" * 64},
            "candidate": {
                "apply_result_path": "build/candidates/CAND001/apply_result.json",
            },
            "status": {"export_state": "TRACKED_GOLDEN"},
        },
    }


def test_closeout_accept_writes_golden_acceptance_for_tracked_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    result = golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale="Reviewed tracked golden export.",
        accept_golden=True,
        workspace_root=workspace,
        plugin_root=_write_release_decision_record(workspace),
    )

    path = fixture / "build" / "closeout" / "golden_acceptance.json"
    assert result["path"] == "build/closeout/golden_acceptance.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "figure-agent.golden-acceptance.v1"
    assert payload["decision"] == "accept"
    assert payload["accept_golden"] is True
    assert payload["exports"]["pdf"].startswith("sha256:")


def test_closeout_reject_writes_non_accept_decision_without_release_authority(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")

    result = golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="reject",
        reviewer="local-user",
        rationale="Do not promote this generated export.",
        accept_golden=False,
        workspace_root=workspace,
        plugin_root=workspace,
    )

    path = fixture / "build" / "closeout" / "golden_acceptance.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert result["path"] == "build/closeout/golden_acceptance.json"
    assert payload["schema"] == "figure-agent.golden-acceptance.v1"
    assert payload["decision"] == "reject"
    assert payload["accept_golden"] is False
    assert payload["source_sha256"].startswith("sha256:")
    assert payload["exports"]["pdf"].startswith("sha256:")


def test_closeout_accept_requires_human_release_decision_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(
        golden_acceptance.GoldenAcceptanceError,
        match="release_decision_record_required",
    ):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=workspace,
        )


def test_closeout_accept_allows_first_time_tracked_golden_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")

    def realistic_readiness(*args, **kwargs):
        return {
            **_ready_payload(),
            "checks": [
                check
                for check in _ready_payload()["checks"]
                if check["id"] in {"candidate_apply", "compile", "critique"}
            ]
            + [
                {
                    "id": "export",
                    "state": "blocked",
                    "reason": ("tracked golden export acceptance is invalid: missing"),
                    "command": None,
                },
                {
                    "id": "golden_acceptance",
                    "state": "blocked",
                    "reason": "tracked golden export requires current golden acceptance",
                    "command": None,
                },
                {
                    "id": "final_artifact",
                    "state": "passed",
                    "reason": "final_artifact_state is NONE",
                    "command": None,
                },
                {
                    "id": "release",
                    "state": "passed",
                    "reason": "publication gate passed",
                    "command": None,
                    "evidence": {
                        "release_ready": False,
                        "publication_gate_state": "PASS",
                        "publication_gate_failures": [],
                    },
                },
                {
                    "id": "loop_rerun",
                    "state": "blocked",
                    "reason": "closeout prerequisites are incomplete: export",
                    "command": None,
                    "evidence": {"blocked_by": ["export"]},
                },
            ],
        }

    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        realistic_readiness,
    )

    result = golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale="Reviewed tracked golden export.",
        accept_golden=True,
        workspace_root=workspace,
        plugin_root=_write_release_decision_record(workspace),
    )

    assert result["path"] == "build/closeout/golden_acceptance.json"


def test_closeout_accept_blocks_auto_detected_stale_candidate_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    def fake_closeout(_name, repo_root, runs_root=None):
        return {
            "schema": "figure-agent.closeout.v1",
            "fixture": "candidate_demo",
            "closeout_complete": True,
            "next_action": "closeout complete",
            "blocking_step_ids": [],
            "status": {
                "render_state": "FRESH",
                "critique_state": "FRESH",
                "export_state": "FRESH",
                "workflow_ready": True,
                "release_ready": True,
                "final_ready": True,
                "final_artifact_state": "NONE",
                "final_artifact_kind": "generated_export",
                "final_artifact_path": "exports/candidate_demo.svg",
                "publication_gate_state": "NOT_APPLICABLE",
                "publication_gate_failures": [],
            },
            "steps": [],
        }

    monkeypatch.setattr(golden_acceptance.closeout_readiness, "_compute_closeout", fake_closeout)

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="closeout_not_ready"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_requires_accept_golden_for_tracked_golden(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="accept_golden_required"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=False,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_stale_critique(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(critique_state="needs_action"),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="closeout_not_ready"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_symlinked_output(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir()
    outside = tmp_path / "golden_acceptance.json"
    outside.write_text("{}", encoding="utf-8")
    (closeout_dir / "golden_acceptance.json").symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_symlinked_export(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    (exports / "candidate_demo.pdf").symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_symlinked_source(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    source = fixture / "candidate_demo.tex"
    source.unlink()
    outside = tmp_path / "outside.tex"
    outside.write_text("outside\n", encoding="utf-8")
    source.symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_symlinked_build_dir(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    build_dir = fixture / "build"
    outside = tmp_path / "outside-build"
    outside.mkdir()
    for path in sorted(build_dir.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink()
        else:
            path.rmdir()
    build_dir.rmdir()
    build_dir.symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_closeout_accept_rejects_symlinked_closeout_dir(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    closeout_dir = fixture / "build" / "closeout"
    outside = tmp_path / "outside-closeout"
    outside.mkdir()
    closeout_dir.symlink_to(outside)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    with pytest.raises(golden_acceptance.GoldenAcceptanceError, match="sandbox_symlink"):
        golden_acceptance.write_golden_acceptance(
            "candidate_demo",
            decision="accept",
            reviewer="local-user",
            rationale="Reviewed tracked golden export.",
            accept_golden=True,
            workspace_root=workspace,
            plugin_root=_write_release_decision_record(workspace),
        )


def test_pre_acceptance_waivers_are_keyed_on_evidence_not_reason_prose() -> None:
    """The waivers used to match reason sentences. _release_check stopped
    producing the string the release waiver looked for in 3ae90b60, which left
    golden acceptance unreachable, and the loop_rerun waiver matched any path
    under exports/. Both now read structured evidence."""
    readiness = {
        "checks": [
            {
                "id": "release",
                "state": "blocked",
                "reason": "release is waiting on the acceptance itself",
                "evidence": {
                    "release_ready": False,
                    "publication_gate_state": "PASS",
                    "publication_gate_failures": [],
                },
            },
            {
                "id": "loop_rerun",
                "state": "blocked",
                "reason": "exports/demo.pdf is newer than latest loop record",
                "evidence": {"newest_input_is_export_artifact": True},
            },
        ]
    }

    waived = golden_acceptance._allowed_pre_acceptance_blocks(readiness)

    assert [check["id"] for check in waived] == ["release", "loop_rerun"]


def test_release_blocked_by_the_publication_gate_is_never_waived() -> None:
    """`release_ready is False` alone waived every blocked release check,
    including one blocked because no human attested, so the check could never
    block an accept."""

    def readiness(gate_state: str, failures: list[dict[str, str]]) -> dict:
        return {
            "checks": [
                {
                    "id": "release",
                    "state": "blocked",
                    "reason": f"publication gate state is {gate_state}",
                    "evidence": {
                        "release_ready": False,
                        "publication_gate_state": gate_state,
                        "publication_gate_failures": failures,
                    },
                }
            ]
        }

    forged = [{"code": "invalid_human_attestation"}]
    assert (
        golden_acceptance._allowed_pre_acceptance_blocks(readiness("PROVENANCE_REQUIRED", forged))
        == []
    )
    assert (
        golden_acceptance._allowed_pre_acceptance_blocks(readiness("HUMAN_ACCEPTANCE_REQUIRED", []))
        == []
    )
    assert golden_acceptance._allowed_pre_acceptance_blocks(readiness("NOT_APPLICABLE", [])) == []


def test_stale_loop_record_is_not_waived_without_export_evidence() -> None:
    """A source edit that outdates the loop record says "export" nowhere and
    must not be waived — but the old substring test saw exports/ in the path
    of any export artifact and waived every stale record after /fig_export."""
    readiness = {
        "checks": [
            {
                "id": "loop_rerun",
                "state": "blocked",
                "reason": "examples/demo/demo.tex is newer than latest loop record",
                "evidence": {"newest_input_is_export_artifact": False},
            },
            {
                "id": "release",
                "state": "blocked",
                "reason": "publication gate reports 1 failure(s)",
                "evidence": {"release_ready": True},
            },
        ]
    }

    assert golden_acceptance._allowed_pre_acceptance_blocks(readiness) == []


def test_acceptance_names_the_authorization_it_rode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The decision kind says "accept_current_generated_export" but nothing
    pins which export was current, so one authorization stays valid for every
    later export. The receipt at least has to name the one it used."""
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_authorizing_decision_record(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )

    golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale="Reviewed tracked golden export.",
        accept_golden=True,
        workspace_root=workspace,
        plugin_root=_write_release_decision_record(workspace),
    )

    payload = json.loads(
        (fixture / "build" / "closeout" / "golden_acceptance.json").read_text(encoding="utf-8")
    )
    authorization = payload["release_authorization"]
    assert authorization["path"].endswith("candidate_demo_accept_current_generated_export.json")
    assert authorization["sha256"].startswith("sha256:")
    assert authorization["packet_timestamp"] == "2026-07-01T00:00:00Z"


def test_reject_records_no_authorization_when_none_exists(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"pdf")

    golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="reject",
        reviewer="local-user",
        rationale="Do not promote this generated export.",
        accept_golden=False,
        workspace_root=workspace,
        plugin_root=workspace,
    )

    payload = json.loads(
        (fixture / "build" / "closeout" / "golden_acceptance.json").read_text(encoding="utf-8")
    )
    assert payload["release_authorization"] is None


def _accept(workspace: Path, *, rationale: str = "Reviewed tracked golden export.") -> dict:
    return golden_acceptance.write_golden_acceptance(
        "candidate_demo",
        decision="accept",
        reviewer="local-user",
        rationale=rationale,
        accept_golden=True,
        workspace_root=workspace,
        plugin_root=workspace,
    )


def _accept_ready_fixture(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    pdf: bytes = b"pdf",
) -> Path:
    fixture = _fixture(workspace)
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "exports").mkdir()
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(pdf)
    monkeypatch.setattr(
        golden_acceptance.closeout_readiness,
        "build_closeout_readiness",
        lambda *args, **kwargs: _ready_payload(),
    )
    return fixture


def test_an_uncommitted_decision_record_cannot_authorize_an_accept(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An agent that can write JSON could otherwise author its own release
    authorization: the review wrote docs/decision-records/adversarial/*.json
    and the real closeout-accept honoured it."""
    workspace = tmp_path / "workspace"
    _accept_ready_fixture(workspace, monkeypatch)
    _commit_everything(workspace)
    _write_release_decision_record(workspace, commit=False)

    with pytest.raises(
        golden_acceptance.GoldenAcceptanceError,
        match="release_decision_record_required",
    ):
        _accept(workspace)


def test_committing_the_same_decision_record_authorizes_the_accept(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Positive control for the test above: only the commit differs."""
    workspace = tmp_path / "workspace"
    fixture = _accept_ready_fixture(workspace, monkeypatch)
    _write_release_decision_record(workspace, commit=True)

    _accept(workspace)

    payload = json.loads(
        (fixture / "build" / "closeout" / "golden_acceptance.json").read_text(encoding="utf-8")
    )
    assert payload["release_authorization"]["packet_timestamp"] == "2026-07-01T00:00:00Z"


def test_the_newest_authorization_wins_not_the_lexicographically_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Records live in date-prefixed directories, so sorted(glob(...)) named
    the oldest authorization in the receipt — the opposite of the intent."""
    workspace = tmp_path / "workspace"
    fixture = _accept_ready_fixture(workspace, monkeypatch)
    _write_release_decision_record(
        workspace,
        stem="aaa_first_alphabetically",
        packet_timestamp="2026-07-01T00:00:00Z",
        commit=False,
    )
    _write_release_decision_record(
        workspace,
        stem="zzz_last_alphabetically",
        packet_timestamp="2026-08-30T00:00:00Z",
        commit=True,
    )

    _accept(workspace)

    payload = json.loads(
        (fixture / "build" / "closeout" / "golden_acceptance.json").read_text(encoding="utf-8")
    )
    authorization = payload["release_authorization"]
    assert authorization["packet_timestamp"] == "2026-08-30T00:00:00Z"
    assert authorization["path"].endswith("zzz_last_alphabetically.json")


def test_one_authorization_cannot_accept_a_second_different_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The review accepted fig3's PDF as fig5 by swapping the export and
    re-running the accept: release_authorization stayed byte-identical while
    the export hash moved."""
    workspace = tmp_path / "workspace"
    fixture = _accept_ready_fixture(workspace, monkeypatch)
    _write_release_decision_record(workspace)

    _accept(workspace)
    receipt = fixture / "build" / "closeout" / "golden_acceptance.json"
    first_export = json.loads(receipt.read_text(encoding="utf-8"))["exports"]["pdf"]
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"a different figure entirely")

    with pytest.raises(
        golden_acceptance.GoldenAcceptanceError,
        match="release_authorization_predates_export_change",
    ):
        _accept(workspace)

    payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert payload["exports"]["pdf"] == first_export


def test_a_newer_authorization_can_accept_the_changed_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Positive control: the same second accept succeeds once a human signs
    again after the export changed."""
    workspace = tmp_path / "workspace"
    fixture = _accept_ready_fixture(workspace, monkeypatch)
    _write_release_decision_record(workspace)

    _accept(workspace)
    (fixture / "exports" / "candidate_demo.pdf").write_bytes(b"a different figure entirely")
    _write_release_decision_record(
        workspace,
        stem="zzz_signed_after_the_export_changed",
        packet_timestamp="2099-01-01T00:00:00Z",
        commit=True,
    )

    _accept(workspace)

    payload = json.loads(
        (fixture / "build" / "closeout" / "golden_acceptance.json").read_text(encoding="utf-8")
    )
    assert payload["release_authorization"]["packet_timestamp"] == "2099-01-01T00:00:00Z"
    assert payload["exports"]["pdf"] == evidence_hash.sha256_file(
        fixture / "exports" / "candidate_demo.pdf"
    )
