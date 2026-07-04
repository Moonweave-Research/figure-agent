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


@pytest.fixture(autouse=True)
def _no_real_pre_mutation_compile(monkeypatch):
    # M3 added a best-effort pre-mutation compile when build/<name>.pdf is absent so
    # the value-preservation gate has a baseline; neutralize the shell-out here so
    # unit tests never invoke lualatex. Tests asserting the compile IS forced
    # re-override this with their own spy.
    monkeypatch.setattr(candidate_apply, "_compile_current_source", lambda *_a, **_k: None)


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


def _accepted_multiline_candidate_fixture(workspace: Path) -> tuple[Path, dict, str, str]:
    fixture, manifest = _rendered_candidate_fixture(workspace)
    source = "\n".join(
        [
            "% Panel F -- mechanical",
            "\\begin{scope}[shift={(9.5,0)}]",
            "\\draw[cGray!64!black, line width=0.34pt] (0,0) rectangle (1,1);",
            "\\node at (0.5,0.5) {Coulomb repulsion};",
            "\\end{scope}",
        ]
    ) + "\n"
    replacement = source.replace("line width=0.34pt", "line width=0.92pt").replace(
        "{Coulomb repulsion}",
        "{Coulomb repulsion strengthened}",
    )
    tex_path = fixture / "candidate_demo.tex"
    tex_path.write_text(source, encoding="utf-8")
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    operation_path = "examples/candidate_demo/candidate_demo.tex"
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored["operations"] = [
        {
            "kind": "replace_text",
            "path": operation_path,
            "source_sha256": _sha256_text(source),
            "line_start": 2,
            "line_end": 5,
            "original": "".join(source.splitlines(keepends=True)[1:5]),
            "replacement": "".join(replacement.splitlines(keepends=True)[1:5]),
        }
    ]
    stored["selectors"] = [
        {
            "kind": "tex_selector.v1",
            "path": operation_path,
            "source_hash": _sha256_text(source),
            "line_start": 2,
            "line_end": 5,
        }
    ]
    manifest_path.write_text(json.dumps(stored, sort_keys=True) + "\n", encoding="utf-8")
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
    return fixture, stored, source, replacement


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


def test_apply_candidate_rejects_recommendation_packet_as_acceptance(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    acceptance_path = sandbox / "acceptance.json"
    acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
    recommendation_packet = {
        **acceptance,
        "schema": "figure-agent.candidate-review-packet.v1",
        "recommended_next_action": "human_review_required",
        "apply_readiness": {
            "status": "ready_for_local_acceptance",
            "blocking_reasons": [],
        },
    }
    acceptance_path.write_text(
        json.dumps(recommendation_packet, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=False,
    )

    assert result["status"] == "blocked"
    assert result["diagnostics"][0]["code"] == "acceptance_schema_invalid"


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


def test_apply_candidate_multiline_exact_replace_writes_source_and_result(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest, _source, replacement = _accepted_multiline_candidate_fixture(workspace)

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
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == replacement
    assert result["changed_files"][0]["path"] == "candidate_demo.tex"


def test_apply_candidate_blocks_multiline_replace_when_range_does_not_match(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest, source, _replacement = _accepted_multiline_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored["operations"][0]["line_end"] = 4
    manifest_path.write_text(json.dumps(stored, sort_keys=True) + "\n", encoding="utf-8")
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
    assert result["diagnostics"][0]["code"] == "original_text_line_mismatch"
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == source


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
    # Give the value-preservation gate a stable label baseline so the ONLY failure
    # is the mocked export, not a missing baseline (M3).
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

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
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

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


def _semantic_recheck_fakes(monkeypatch, pre, post):
    # Robust pre/post ledger fake: any ledger call before _post_apply_checks runs
    # (semantic review, the pre-mutation snapshot) returns `pre`; the post-apply
    # recheck (after _post_apply_checks flips the flag) returns `post`.
    state = {"applied": False}

    def fake_post_apply(_name, _paths):
        state["applied"] = True
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "success", "returncode": 0},
            "status": {"status": "success", "returncode": 0},
        }

    def fake_ledger(_name, **_kwargs):
        return {"defects": post} if state["applied"] else {"defects": pre}

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)
    monkeypatch.setitem(
        sys.modules,
        "quality_defect_ledger",
        types.SimpleNamespace(build_quality_defect_ledger=fake_ledger),
    )


def _set_source_defect(fixture: Path, defect_id: str = "QD001") -> None:
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored["source_defect"] = {"id": defect_id}
    manifest_path.write_text(json.dumps(stored, sort_keys=True) + "\n", encoding="utf-8")


def _ledger_defect(did: str, panel: str = "A", cls: str = "text_overlap", severity: str = "action"):
    return {
        "id": did,
        "defect_class": cls,
        "severity": severity,
        "target": {"panel": panel, "subregion": f"sel:{did.lower()}"},
    }


def test_apply_candidate_records_failed_recheck_when_defect_persists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Anti-gaming: the applied edit shifts the line (so the fingerprint AND the
    # sel: sub-region key change), but the same (panel, defect_class, severity)
    # defect persists. The old fingerprint-equality recheck wrongly passed this;
    # the semantic recheck must report it unresolved.
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    _semantic_recheck_fakes(
        monkeypatch,
        pre=[_ledger_defect("QD001")],
        post=[_ledger_defect("QD777")],  # same (A, text_overlap, action) signature
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

    assert result["status"] == "rolled_back"
    recheck = result["post_apply"]["detector_recheck"]
    assert recheck["status"] == "failed"
    assert recheck["reason"] == "source_defect_unresolved"
    assert recheck["source_defect_id"] == "QD001"


def test_apply_candidate_rolls_back_on_failed_detector_recheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Autonomy safety: a fix the recheck reports as failed must be UNDONE, not
    # left applied and merely flagged — the verifier replaces the human gate, so
    # it must roll the .tex back so a known-ineffective fix never persists.
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    _semantic_recheck_fakes(
        monkeypatch,
        pre=[_ledger_defect("QD001")],
        post=[_ledger_defect("QD777")],  # same signature persists -> recheck failed
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

    assert result["status"] == "rolled_back"
    assert result["post_apply"]["detector_recheck"]["status"] == "failed"
    assert result["post_apply"]["class_verifiers"]["rolled_back"] is True
    # The ineffective edit is reverted to the pre-apply source, not left applied.
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == "source\n"


def test_apply_candidate_semantic_recheck_success_when_resolved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The applied edit removes the target defect (its (panel, defect_class,
    # severity) signature is gone from the post-apply ledger) -> recheck success.
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    _semantic_recheck_fakes(
        monkeypatch,
        pre=[_ledger_defect("QD001")],
        post=[],  # target resolved, nothing new
    )
    # No build/<name>.pdf in the fixture, so M3 must force a pre-mutation compile to
    # obtain a value-preservation baseline; spy on it and give a stable baseline.
    compile_calls: list[str] = []
    monkeypatch.setattr(
        candidate_apply, "_compile_current_source", lambda name, _paths: compile_calls.append(name)
    )
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

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
    assert compile_calls == ["candidate_demo"]  # baseline absent -> forced compile
    recheck = result["post_apply"]["detector_recheck"]
    assert recheck["status"] == "success"
    assert recheck["reason"] == "source_defect_resolved"
    assert recheck["source_defect_id"] == "QD001"


def test_verify_labels_unchanged_equal_passes_and_differ_fails():
    assert candidate_apply._verify_labels_unchanged({"S": 1, "x": 2}, {"S": 1, "x": 2})[0] is True
    ok, reason = candidate_apply._verify_labels_unchanged({"S": 1}, {"S": 1, "NEW": 1})
    assert ok is False
    assert reason == "labels_changed"


def test_verify_labels_unchanged_blocks_without_baseline():
    # No pre-mutation baseline => value-preservation is unverifiable => FAIL CLOSED.
    # (M3: an absent baseline must not silently pass the safety gate.)
    ok, reason = candidate_apply._verify_labels_unchanged({}, {"S": 1})
    assert ok is False
    assert reason == "no_label_baseline"


def test_verify_palette_locked_flags_definecolor(tmp_path: Path):
    clean = tmp_path / "clean.tex"
    clean.write_text("\\node (a) at (0,0) {Label};\n", encoding="utf-8")
    assert candidate_apply._verify_palette_locked(clean)[0] is True
    dirty = tmp_path / "dirty.tex"
    dirty.write_text("\\definecolor{foo}{rgb}{0.1,0.2,0.3}\n", encoding="utf-8")
    ok, reason = candidate_apply._verify_palette_locked(dirty)
    assert ok is False
    assert reason.startswith("palette_violation:")


def test_run_class_verifiers_fails_on_changed_labels(tmp_path: Path):
    tex = tmp_path / "fig.tex"
    tex.write_text("\\node (a) at (0,0) {Label};\n", encoding="utf-8")
    changes = [{"path": tex, "before": "x", "after": "y", "relative": "fig.tex"}]
    result = candidate_apply._run_class_verifiers(changes, {"S": 1}, {"S": 1, "NEW": 1})
    assert result["status"] == "failed"
    assert any(
        v["verifier"] == "labels_unchanged" and v["status"] == "failed" for v in result["verifiers"]
    )


def test_apply_candidate_rolls_back_on_value_preservation_violation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A value-preservation verifier fails => the .tex must be auto-rolled-back to
    # its pre-mutation content and the result recorded as a non-terminal rollback.
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    # Semantic recheck passes (target resolved), so the ONLY failure is the
    # value-preservation gate, which we force to fail.
    _semantic_recheck_fakes(monkeypatch, pre=[_ledger_defect("QD001")], post=[])
    monkeypatch.setattr(
        candidate_apply,
        "_run_class_verifiers",
        lambda *_args, **_kwargs: {
            "status": "failed",
            "verifiers": [
                {"verifier": "labels_unchanged", "status": "failed", "reason": "labels_changed"}
            ],
        },
    )
    tex_path = fixture / "candidate_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "rolled_back"
    cv = result["post_apply"]["class_verifiers"]
    assert cv["status"] == "failed"
    assert cv["rolled_back"] is True
    # the source .tex was restored to its pre-mutation content
    assert tex_path.read_text(encoding="utf-8") == before


def test_apply_candidate_allows_reapply_after_rollback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    _semantic_recheck_fakes(
        monkeypatch,
        pre=[_ledger_defect("QD001")],
        post=[_ledger_defect("QD777")],
    )
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

    rolled_back = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )
    ready = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=False,
        post_apply=True,
    )

    assert rolled_back["status"] == "rolled_back"
    assert ready["status"] == "ready"
    assert "source\n" == (fixture / "candidate_demo.tex").read_text(encoding="utf-8")


def test_apply_candidate_rollback_recompiles_or_removes_stale_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    build_pdf = fixture / "build" / "candidate_demo.pdf"
    build_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf.write_bytes(b"mutated-pdf")
    compile_calls: list[str] = []

    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )
    _semantic_recheck_fakes(
        monkeypatch,
        pre=[_ledger_defect("QD001")],
        post=[_ledger_defect("QD777")],
    )
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

    def fail_compile(name: str, _paths) -> None:
        compile_calls.append(name)
        raise RuntimeError("compile failed")

    monkeypatch.setattr(candidate_apply, "_compile_current_source", fail_compile)

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "rolled_back"
    assert compile_calls == ["candidate_demo"]
    assert not build_pdf.exists()
    assert result["post_apply"]["rollback_compile"]["status"] == "failed"


def test_apply_candidate_rollback_restores_or_removes_generated_exports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture, manifest = _accepted_candidate_fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    original_svg = exports / "candidate_demo.svg"
    original_svg.write_bytes(b"original-svg")

    _set_source_defect(fixture)
    candidate_acceptance.write_acceptance(
        "candidate_demo",
        "CAND001",
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        decision="accept",
        reviewer="local-user",
        rationale="Rendered evidence reviewed.",
        workspace_root=workspace,
    )

    state = {"applied": False}

    def fake_post_apply(_name, _paths):
        state["applied"] = True
        original_svg.write_bytes(b"mutated-svg")
        (exports / "candidate_demo.png").write_bytes(b"new-png")
        return {
            "compile": {"status": "success", "returncode": 0},
            "export": {"status": "success", "returncode": 0},
            "status": {"status": "success", "returncode": 0},
        }

    def fake_ledger(_name, **_kwargs):
        if state["applied"]:
            return {"defects": [_ledger_defect("QD777")]}
        return {"defects": [_ledger_defect("QD001")]}

    monkeypatch.setattr(candidate_apply, "_post_apply_checks", fake_post_apply)
    monkeypatch.setitem(
        sys.modules,
        "quality_defect_ledger",
        types.SimpleNamespace(build_quality_defect_ledger=fake_ledger),
    )
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

    result = candidate_apply.apply_candidate(
        "candidate_demo",
        manifest,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/candidate_set.json"),
        acceptance_path=Path("build/candidates/CAND001/acceptance.json"),
        apply=True,
        post_apply=True,
    )

    assert result["status"] == "rolled_back"
    assert original_svg.read_bytes() == b"original-svg"
    assert not (exports / "candidate_demo.png").exists()
    assert result["post_apply"]["rollback_exports"]["status"] == "success"


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
    monkeypatch.setattr(candidate_apply, "_pdf_words", lambda _p: {"L": 1})

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


def _defect(did, panel, cls="text_overlap", severity="action", fp=None, sub="sel:aaa", anchor=None):
    d = {
        "id": did,
        "defect_class": cls,
        "severity": severity,
        "target": {"panel": panel, "subregion": sub},
    }
    if fp is not None:
        d["source_fingerprint"] = fp
    if anchor is not None:
        d["selector_hint"] = {"kind": "node_name", "value": anchor}
    return d


def test_semantic_recheck_resolved_is_success():
    pre = [_defect("QD001", "A")]
    post: list = []
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "success"
    assert verdict["reason"] == "source_defect_resolved"


def test_semantic_recheck_persisting_defect_is_failed_despite_changed_fingerprint():
    # Anti-gaming: a coordinate nudge changes the line (so the fingerprint AND the
    # sel: sub-region key shift), but the same (panel, defect_class, severity)
    # defect persists. The old fingerprint-equality recheck wrongly passed this.
    pre = [_defect("QD001", "A", fp="sha256:" + "a" * 64, sub="sel:aaa")]
    post = [_defect("QD001", "A", fp="sha256:" + "b" * 64, sub="sel:bbb")]
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "source_defect_unresolved"


def test_semantic_recheck_new_equal_severity_defect_is_failed():
    pre = [_defect("QD001", "A")]
    # target resolved, but a NEW equal-severity defect appeared in panel B
    post = [_defect("QD050", "B", sub="sel:zzz")]
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "new_defect_introduced"


def test_semantic_recheck_new_lower_severity_defect_is_allowed():
    # A new LOWER-severity defect does not fail the recheck (only equal/higher).
    pre = [_defect("QD001", "A", severity="blocker")]
    post = [_defect("QD050", "B", severity="action")]
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "success"


def test_semantic_recheck_source_absent_pre_is_failed():
    verdict = candidate_apply._semantic_recheck_verdict("QD404", [], [])
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "source_defect_absent_pre_apply"


def test_semantic_recheck_flags_resolving_the_wrong_same_signature_instance():
    # Two same-(panel, class, severity) defects told apart by their stable anchor.
    # The edit clears the OTHER one; the target persists -> must NOT be credited as
    # resolved just because the (panel, class, severity) COUNT dropped (M4).
    pre = [_defect("QD001", "A", anchor="PDMS"), _defect("QD002", "A", anchor="PET")]
    post = [_defect("QD001", "A", anchor="PDMS")]  # target QD001/PDMS still present
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "source_defect_unresolved"


def test_semantic_recheck_flags_severity_downgrade_as_unresolved():
    # The target element is only downgraded (major -> action) at the same anchor,
    # not removed -> the signature count for 'major' drops to 0 but the defect is
    # not resolved (M4).
    pre = [_defect("QD001", "A", severity="major", anchor="PDMS")]
    post = [_defect("QD001", "A", severity="action", anchor="PDMS")]
    verdict = candidate_apply._semantic_recheck_verdict("QD001", pre, post)
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "source_defect_unresolved"


def test_finding_recheck_fails_when_a_target_text_still_crosses():
    # The verifier ledger is undeclared_geometry-grounded and blind to the
    # visual_clash crossings a critique finding catches, so a finding-sourced
    # fix verifies against the post-apply crossing texts directly.
    verdict = candidate_apply._finding_recheck_verdict(
        ["PI,", "PDMS,", "PET"], ["PI,", "PET", "(shallow,"]
    )
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "finding_crossing_unresolved"
    assert "PI," in verdict["unresolved_texts"]


def test_finding_recheck_succeeds_when_no_target_text_crosses():
    verdict = candidate_apply._finding_recheck_verdict(["PI,", "PDMS,", "PET"], ["Origin", "S85"])
    assert verdict["status"] == "success"
    assert verdict["reason"] == "finding_crossing_resolved"


def test_finding_recheck_fails_when_fix_clears_target_but_introduces_new_crossing():
    # Destination-unaware fix: the targets are cleared but the move pushed the
    # label onto another element (a NEW crossing absent pre-apply).
    verdict = candidate_apply._finding_recheck_verdict(
        ["PI,", "PDMS,", "PET"],
        ["S85", "(shallow,"],
        pre_crossing_texts=["PI,", "PDMS,", "PET", "S85"],
    )
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "finding_new_crossing_introduced"
    assert "(shallow," in verdict["introduced_texts"]


def test_finding_recheck_success_ignores_stable_baseline_crossings():
    # Baseline false-positive crossings present both pre and post must not count
    # as newly introduced.
    verdict = candidate_apply._finding_recheck_verdict(
        ["PI,", "PDMS,", "PET"],
        ["Origin", "S85"],
        pre_crossing_texts=["PI,", "PDMS,", "PET", "Origin", "S85"],
    )
    assert verdict["status"] == "success"


def test_post_apply_recheck_finding_sourced_uses_post_visual_clash(tmp_path: Path) -> None:
    import runtime_paths

    workspace = tmp_path / "workspace"
    build = workspace / "examples" / "demo" / "build"
    build.mkdir(parents=True)
    (build / "visual_clash.json").write_text(
        json.dumps({"candidates": [{"id": "VC001", "kind": "text_on_path", "text": "PI,"}]}),
        encoding="utf-8",
    )
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace)
    manifest = {
        "source_defect": {
            "id": "C001",
            "source": "adjudicated_finding",
            "target_texts": ["PI,", "PET"],
        }
    }
    verdict = candidate_apply._post_apply_semantic_recheck("demo", paths, manifest, [])
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "finding_crossing_unresolved"
    assert "PI," in verdict["unresolved_texts"]


def test_post_apply_recheck_finding_sourced_without_target_texts_is_failed(tmp_path: Path) -> None:
    import runtime_paths

    workspace = tmp_path / "workspace"
    (workspace / "examples" / "demo" / "build").mkdir(parents=True)
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace)
    manifest = {"source_defect": {"id": "C001", "source": "adjudicated_finding"}}
    verdict = candidate_apply._post_apply_semantic_recheck("demo", paths, manifest, [])
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "finding_target_texts_missing"


def test_post_apply_recheck_finding_sourced_flags_new_crossing(tmp_path: Path) -> None:
    import runtime_paths

    workspace = tmp_path / "workspace"
    build = workspace / "examples" / "demo" / "build"
    build.mkdir(parents=True)
    # Post state: the targeted texts cleared, but the move introduced a new
    # crossing "(shallow," that was not present pre-apply.
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {"id": "VC001", "kind": "text_on_path", "text": "(shallow,"},
                    {"id": "VC002", "kind": "text_on_fill", "text": "S85"},
                ]
            }
        ),
        encoding="utf-8",
    )
    paths = runtime_paths.resolve_runtime_paths(workspace_root=workspace)
    manifest = {
        "source_defect": {
            "id": "C001",
            "source": "adjudicated_finding",
            "target_texts": ["PI,", "PET"],
        }
    }
    verdict = candidate_apply._post_apply_semantic_recheck(
        "demo", paths, manifest, [], ["PI,", "PET", "S85"]
    )
    assert verdict["status"] == "failed"
    assert verdict["reason"] == "finding_new_crossing_introduced"
    assert "(shallow," in verdict["introduced_texts"]
