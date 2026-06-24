from __future__ import annotations

import json
import sys
import types
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_acceptance  # noqa: E402
import candidate_apply  # noqa: E402


def _sha256_text(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _rendered_candidate_fixture(workspace: Path) -> tuple[Path, dict]:
    fixture = workspace / "examples" / "candidate_demo"
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (fixture / "candidate_demo.tex").write_text("source\n", encoding="utf-8")
    candidate_hash = "sha256:" + "1" * 64
    operation_path = "examples/candidate_demo/candidate_demo.tex"
    candidate_set = {
        "schema": "figure-agent.candidate-set.v1",
        "candidates": [{"id": "CAND001", "candidate_hash": candidate_hash}],
    }
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "fixture": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "effective_apply_authority": "review_only",
        "verification": {"hard_gate_state": "human_required"},
        "operations": [
            {
                "kind": "replace_text",
                "path": operation_path,
                "source_sha256": _sha256_text("source\n"),
                "original": "source\n",
                "replacement": "candidate\n",
            }
        ],
        "selectors": [
            {
                "kind": "tex_selector.v1",
                "path": operation_path,
                "source_hash": _sha256_text("source\n"),
            }
        ],
    }
    render_manifest = {
        "schema": "figure-agent.candidate-render-manifest.v1",
        "figure_name": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": candidate_hash,
        "candidate_set_path": "build/candidates/candidate_set.json",
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
    }
    (fixture / "build" / "candidates" / "candidate_set.json").write_text(
        json.dumps(candidate_set, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "candidate_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sandbox / "render_manifest.json").write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return fixture, manifest


def _accepted_candidate_fixture(workspace: Path) -> tuple[Path, dict]:
    fixture, manifest = _rendered_candidate_fixture(workspace)
    _write_semantic_review(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    return fixture, manifest


def _write_semantic_review(fixture: Path) -> None:
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest = json.loads((sandbox / "candidate_manifest.json").read_text(encoding="utf-8"))
    render_manifest_path = sandbox / "render_manifest.json"
    payload = {
        "schema": "figure-agent.semantic-candidate-review.v1",
        "fixture": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": manifest["candidate_hash"],
        "reviewed_artifacts": [
            {
                "path": render_manifest_path.relative_to(fixture).as_posix(),
                "sha256": _sha256_file(render_manifest_path),
            }
        ],
        "semantic_invariants": [],
        "findings": [],
        "conflicts": [],
        "verdict": "pass",
        "human_required": False,
        "reviewed_at": "2026-06-22T00:00:00Z",
        "reviewer": "host",
    }
    (sandbox / "semantic_review.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_apply_candidate_requires_acceptance_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture, manifest = _rendered_candidate_fixture(workspace)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["schema"] == "figure-agent.candidate-apply-result.v1"
    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "acceptance_missing"


def test_apply_candidate_blocks_required_missing_semantic_review(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture, manifest = _rendered_candidate_fixture(workspace)
    sandbox = _fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    stored_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_manifest["semantic_risks"] = ["candidate changes a semantic claim"]
    manifest_path.write_text(json.dumps(stored_manifest, sort_keys=True) + "\n", encoding="utf-8")
    acceptance = {
        "schema": "figure-agent.candidate-acceptance.v1",
        "figure_name": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": stored_manifest["candidate_hash"],
        "candidate_set_path": "build/candidates/candidate_set.json",
        "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
        "render_manifest_sha256": _sha256_file(sandbox / "render_manifest.json"),
        "decision": "accept",
        "reviewer": "local-user",
        "reviewed_at": "2026-06-08T00:00:00Z",
        "rationale": "crafted fixture",
        "human_review_required": True,
    }
    (sandbox / "acceptance.json").write_text(
        json.dumps(acceptance, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "semantic_review"
    assert result["diagnostics"][0]["message"] == "semantic_risk"


def test_apply_candidate_exact_replace_writes_source_and_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "applied_unverified"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "candidate\n"
    assert result["changed_files"][0]["path"] == "candidate_demo.tex"
    assert result["post_apply"] == {}
    assert result["required_commands"] == [
        "/fig_compile candidate_demo",
        "/fig_export candidate_demo --skip-critique",
        "/fig_status candidate_demo --json",
    ]
    assert (fixture / "build" / "candidates" / "CAND001" / "rollback.patch").is_file()
    assert (fixture / "build" / "candidates" / "CAND001" / "apply_result.json").is_file()


def test_apply_candidate_refuses_already_applied_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    apply_result = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result.write_text(
        json.dumps({"schema": "figure-agent.candidate-apply-result.v1", "status": "applied"})
        + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "already_applied"


def test_apply_candidate_refuses_unverified_apply_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    apply_result = fixture / "build" / "candidates" / "CAND001" / "apply_result.json"
    apply_result.write_text(
        json.dumps(
            {
                "schema": "figure-agent.candidate-apply-result.v1",
                "status": "applied_unverified",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "already_applied"


def test_apply_candidate_refuses_existing_mcp_or_quality_lock(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    lock = fixture / "build" / ".mcp-locks" / "mutation.lock"
    lock.parent.mkdir()
    lock.write_text("{}", encoding="utf-8")

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "mutation_lock_active"


def test_apply_candidate_uses_shared_mcp_mutation_lock(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    lock_path = fixture / "build" / ".mcp-locks" / "mutation.lock"
    lock_path.parent.mkdir()

    original_lock = candidate_apply._candidate_apply_lock

    @contextmanager
    def observing_lock(example_dir: Path):
        with original_lock(example_dir) as active:
            assert lock_path.exists()
            yield active

    candidate_apply._candidate_apply_lock = observing_lock
    try:
        result = candidate_apply.apply_candidate(
            "candidate_demo",
            manifest,
            workspace_root=workspace,
            candidate_set_path=Path("build/candidates/candidate_set.json"),
            acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
            apply=True,
        post_apply=False,
        )
    finally:
        candidate_apply._candidate_apply_lock = original_lock

    assert result["status"] == "applied_unverified"
    assert not lock_path.exists()


def test_apply_candidate_rejects_source_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    (fixture / "candidate_demo.tex").write_text("changed\n", encoding="utf-8")

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "source_drift_hash_mismatch"


def test_apply_candidate_rejects_empty_operations_with_crafted_acceptance(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _rendered_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"] = []
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    acceptance = {
        "schema": "figure-agent.candidate-acceptance.v1",
        "figure_name": "candidate_demo",
        "candidate_id": "CAND001",
        "candidate_hash": manifest["candidate_hash"],
        "candidate_set_path": "build/candidates/candidate_set.json",
        "candidate_manifest_path": "build/candidates/CAND001/candidate_manifest.json",
        "candidate_manifest_sha256": _sha256_file(manifest_path),
        "render_manifest_path": "build/candidates/CAND001/render_manifest.json",
        "render_manifest_sha256": _sha256_file(sandbox / "render_manifest.json"),
        "decision": "accept",
        "reviewer": "local-user",
        "reviewed_at": "2026-06-08T00:00:00Z",
        "rationale": "crafted fixture",
        "human_review_required": True,
    }
    (sandbox / "acceptance.json").write_text(
        json.dumps(acceptance, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "operations_empty"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "source\n"


def test_apply_candidate_uses_stored_manifest_not_caller_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    tampered_manifest = dict(manifest)
    tampered_manifest["operations"] = []

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        tampered_manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=False,
    )

    assert result["status"] == "applied_unverified"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "candidate\n"


def test_apply_candidate_records_failed_post_apply_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)

    def fake_post_apply(_name, _paths):
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "failed", "returncode": 1},
            "status": {"status": "success", "returncode": 0},
        }

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "applied_with_failed_verification"
    assert result["post_apply"]["export"]["status"] == "failed"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "candidate\n"


def test_apply_candidate_runs_post_apply_verification_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture, manifest = _accepted_candidate_fixture(workspace)
    calls: list[str] = []

    def fake_post_apply(name, _paths):
        calls.append(name)
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "success", "returncode": 0},
            "status": {"status": "success", "returncode": 0},
        }

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] == "applied"
    assert calls == ["candidate_demo"]
    assert result["post_apply"]["compile"]["status"] == "success"


def test_apply_candidate_records_failed_detector_recheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_fingerprint = "sha256:" + "a" * 64
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    stored_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_manifest["source_defect"] = {
        "id": "QD001",
        "source_fingerprint": source_fingerprint,
    }
    manifest_path.write_text(json.dumps(stored_manifest, sort_keys=True) + "\n", encoding="utf-8")
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )

    def fake_post_apply(_name, _paths):
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "success", "returncode": 0},
            "status": {"status": "success", "returncode": 0},
        }

    def fake_ledger(_name, **_kwargs):
        return {"defects": [{"id": "QD999", "source_fingerprint": source_fingerprint}]}

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)
    monkeypatch.setitem(
        sys.modules,
        "quality_defect_ledger",
        types.SimpleNamespace(build_quality_defect_ledger=fake_ledger),
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "applied_with_failed_verification"
    assert result["post_apply"]["detector_recheck"] == {
        "status": "failed",
        "reason": "source_defect_still_detected",
        "source_defect_id": "QD001",
        "source_defect_fingerprint": source_fingerprint,
    }


def test_apply_candidate_detector_recheck_ignores_colliding_source_defect_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    stored_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_manifest["source_defect"] = {
        "id": "QD001",
        "source_fingerprint": "sha256:" + "a" * 64,
    }
    manifest_path.write_text(json.dumps(stored_manifest, sort_keys=True) + "\n", encoding="utf-8")
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )

    def fake_post_apply(_name, _paths):
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "success", "returncode": 0},
            "status": {"status": "success", "returncode": 0},
        }

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {"id": "QD001", "source_fingerprint": "sha256:" + "b" * 64},
            ]
        }

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)
    monkeypatch.setitem(
        sys.modules,
        "quality_defect_ledger",
        types.SimpleNamespace(build_quality_defect_ledger=fake_ledger),
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "applied"
    assert result["post_apply"]["detector_recheck"] == {
        "status": "success",
        "reason": "source_defect_not_detected",
        "source_defect_id": "QD001",
        "source_defect_fingerprint": "sha256:" + "a" * 64,
    }


def test_post_apply_export_does_not_force_golden_roll_forward(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture, manifest = _accepted_candidate_fixture(workspace)
    commands: list[list[str]] = []

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **_kwargs):
        commands.append([str(item) for item in command])
        return Completed()

    monkeypatch.setattr(candidate_apply.subprocess, "run", fake_run)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
    )

    assert result["status"] == "applied"
    export_command = commands[1]
    assert "run_export.py" in export_command[1]
    assert "--skip-critique" in export_command
    assert "--force-golden" not in export_command


def test_apply_validates_fixture_name_before_result(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _rendered_candidate_fixture(workspace)

    with pytest.raises(ValueError, match="fixture name"):
        candidate_apply.apply_candidate(
            "../candidate_demo",
            {"candidate_id": "CAND001"},
            workspace_root=workspace,
            apply=True,
        post_apply=False,
        )
