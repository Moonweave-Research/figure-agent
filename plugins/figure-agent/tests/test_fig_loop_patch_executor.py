from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_patch_executor import (  # noqa: E402
    PatchExecutorError,
    apply_patch_file,
    changed_paths_from_unified_diff,
    main,
)
from quality_manifest import file_sha256  # noqa: E402


def _write_latest_loop_run(
    repo_root: Path,
    *,
    patch_handoff: dict[str, Any] | None = None,
    auto_patch_eligibility: dict[str, Any] | None = None,
    adjudication: dict[str, Any] | None = None,
    fixture: str = "loop_demo",
) -> Path:
    run_dir = repo_root / ".scratch" / "fig-loop-runs" / f"20260521T000000Z-{fixture}"
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.fig-loop-run.v1",
                "fixture": fixture,
                "iterations": ["iteration_001.json"],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "iteration_001.json").write_text(
        json.dumps(
            {
                "patch_handoff": patch_handoff,
                "auto_patch_eligibility": auto_patch_eligibility,
                "adjudication": adjudication
                or {
                    "state": "fresh",
                    "decisions": [
                        {
                            "finding_id": "C001",
                            "decision": "apply",
                            "reason": "label overlap is local",
                            "patch_target": "panel A label cluster",
                            "evidence": "critique.md C001",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return run_dir


def _handoff(*, allowed: list[str] | None = None) -> dict[str, Any]:
    return {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": "panel A label cluster",
        "reason": "label overlap; move the label",
        "allowed_edit_scope": allowed
        or [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
            "examples/loop_demo/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            "examples/loop_demo/exports/",
            "examples/loop_demo/build/",
            "examples/loop_demo/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": ["/fig_compile loop_demo", "/fig_closeout loop_demo"],
    }


def _subregion_handoff() -> dict[str, Any]:
    payload = _handoff()
    payload["target_type"] = "subregion"
    payload["target_id"] = "D-2"
    payload["patch_target"] = "D-2"
    return payload


def _eligibility(**overrides: Any) -> dict[str, Any]:
    payload = {
        "level": "auto_patch_candidate",
        "target_type": "finding",
        "target_id": "C001",
        "allowed_reasons": ["label offset", "text overlap"],
        "blocked_reasons": [],
        "required_evidence": [
            "before compile/export evidence",
            "after compile/export evidence",
            "rollback path",
        ],
        "may_edit": False,
    }
    payload.update(overrides)
    return payload


def _fixture(repo_root: Path) -> Path:
    fixture = repo_root / "examples" / "loop_demo"
    fixture.mkdir(parents=True)
    (fixture / "loop_demo.tex").write_text(
        "\\node at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _patch_file(repo_root: Path, content: str) -> Path:
    patch_path = repo_root / "change.patch"
    patch_path.write_text(content, encoding="utf-8")
    return patch_path


def _single_file_patch(old: str = "Old Label", new: str = "New Label") -> str:
    return (
        "--- examples/loop_demo/loop_demo.tex\n"
        "+++ examples/loop_demo/loop_demo.tex\n"
        "@@ -1 +1 @@\n"
        f"-\\node at (0,0) {{{old}}};\n"
        f"+\\node at (0,0) {{{new}}};\n"
    )


def test_changed_paths_ignores_removed_content_that_looks_like_header(tmp_path: Path) -> None:
    patch_path = _patch_file(
        tmp_path,
        "--- examples/loop_demo/loop_demo.tex\n"
        "+++ examples/loop_demo/loop_demo.tex\n"
        "@@ -1 +1 @@\n"
        "--- label guide\n"
        "+-- label guide\n",
    )

    assert changed_paths_from_unified_diff(patch_path) == ["examples/loop_demo/loop_demo.tex"]


def _ready_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo_root = tmp_path
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    _fixture(repo_root)
    _write_latest_loop_run(
        repo_root,
        patch_handoff=_handoff(),
        auto_patch_eligibility=_eligibility(),
    )
    patch_path = _patch_file(repo_root, _single_file_patch())
    return repo_root, runs_root, patch_path


def test_executor_applies_one_allowed_patch_and_writes_closeout_evidence(
    tmp_path: Path,
) -> None:
    repo_root, runs_root, patch_path = _ready_repo(tmp_path)
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before_hash = file_sha256(tex_path)

    report = apply_patch_file(
        "loop_demo",
        repo_root=repo_root,
        runs_root=runs_root,
        patch_path=patch_path,
        apply=True,
    )

    assert tex_path.read_text(encoding="utf-8") == "\\node at (0,0) {New Label};\n"
    assert report["schema"] == "figure-agent.patch-apply.v1"
    assert report["fixture"] == "loop_demo"
    assert report["target_id"] == "C001"
    assert report["changed_paths"] == ["examples/loop_demo/loop_demo.tex"]
    assert report["pre_patch"]["allowed_edit_scope"][0]["sha256"] == before_hash
    assert report["post_patch"]["allowed_edit_scope"][0]["sha256"] == file_sha256(tex_path)
    assert report["closeout_required"] is True
    assert report["next_action"] == "/fig_closeout loop_demo"
    evidence_path = runs_root / "20260521T000000Z-loop_demo" / "patch_apply_001.json"
    assert json.loads(evidence_path.read_text(encoding="utf-8")) == report


def test_executor_refuses_without_explicit_apply_and_does_not_mutate(tmp_path: Path) -> None:
    repo_root, runs_root, patch_path = _ready_repo(tmp_path)
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    with pytest.raises(PatchExecutorError, match="explicit --apply"):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=False,
        )

    assert tex_path.read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("patch_handoff", "auto_patch_eligibility", "message"),
    [
        (None, _eligibility(), "patch_handoff"),
        (_handoff(), _eligibility(level="patch_assisted_only"), "auto_patch_candidate"),
        (_handoff(), _eligibility(target_id="C999"), "target_id"),
        (_handoff(), None, "auto_patch_eligibility"),
        (_handoff(), _eligibility(blocked_reasons=["physical mechanism"]), "blocked_reasons"),
        (_handoff(), _eligibility(allowed_reasons=[]), "allowed_reasons"),
        (_subregion_handoff(), _eligibility(target_id="D-2"), "finding target"),
    ],
)
def test_executor_refuses_invalid_latest_loop_state_without_mutation(
    tmp_path: Path,
    patch_handoff: dict[str, Any] | None,
    auto_patch_eligibility: dict[str, Any] | None,
    message: str,
) -> None:
    repo_root = tmp_path
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    _fixture(repo_root)
    _write_latest_loop_run(
        repo_root,
        patch_handoff=patch_handoff,
        auto_patch_eligibility=auto_patch_eligibility,
    )
    patch_path = _patch_file(repo_root, _single_file_patch())
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    with pytest.raises(PatchExecutorError, match=message):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )

    assert tex_path.read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("adjudication", "message"),
    [
        ({"state": "stale", "decisions": []}, "fresh adjudication"),
        (
            {
                "state": "fresh",
                "decisions": [
                    {"finding_id": "C001", "decision": "needs_human"},
                ],
            },
            "single apply decision",
        ),
        (
            {
                "state": "fresh",
                "decisions": [
                    {"finding_id": "C001", "decision": "apply"},
                    {"finding_id": "C002", "decision": "apply"},
                ],
            },
            "single apply decision",
        ),
    ],
)
def test_executor_requires_one_fresh_apply_decision_for_the_handoff_target(
    tmp_path: Path,
    adjudication: dict[str, Any],
    message: str,
) -> None:
    repo_root = tmp_path
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    _fixture(repo_root)
    _write_latest_loop_run(
        repo_root,
        patch_handoff=_handoff(),
        auto_patch_eligibility=_eligibility(),
        adjudication=adjudication,
    )
    patch_path = _patch_file(repo_root, _single_file_patch())
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    with pytest.raises(PatchExecutorError, match=message):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )

    assert tex_path.read_text(encoding="utf-8") == before


def test_executor_does_not_trust_may_edit_as_permission(tmp_path: Path) -> None:
    repo_root = tmp_path
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    _fixture(repo_root)
    _write_latest_loop_run(
        repo_root,
        patch_handoff=_handoff(),
        auto_patch_eligibility=_eligibility(level="human_review_required", may_edit=True),
    )
    patch_path = _patch_file(repo_root, _single_file_patch())

    with pytest.raises(PatchExecutorError, match="auto_patch_candidate"):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )


@pytest.mark.parametrize(
    ("patch_text", "message"),
    [
        (
            "--- examples/loop_demo/loop_demo.tex\n"
            "+++ examples/loop_demo/loop_demo.tex\n"
            "@@ -1 +1 @@\n"
            "-\\node at (0,0) {Old Label};\n"
            "+\\node at (0,0) {New Label};\n"
            "--- examples/loop_demo/authoring_plan.md\n"
            "+++ examples/loop_demo/authoring_plan.md\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "exactly one changed path",
        ),
        (
            "--- examples/other/other.tex\n"
            "+++ examples/other/other.tex\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "allowed_edit_scope",
        ),
        (
            "--- ../outside.tex\n"
            "+++ ../outside.tex\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "repo-relative",
        ),
        (
            "--- /tmp/outside.tex\n"
            "+++ /tmp/outside.tex\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "repo-relative",
        ),
        (
            "--- accepted/loop_demo.json\n"
            "+++ accepted/loop_demo.json\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        (
            "--- examples/loop_demo/golden_contract.yaml\n"
            "+++ examples/loop_demo/golden_contract.yaml\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        (
            "--- examples/loop_demo/exports/loop_demo.svg\n"
            "+++ examples/loop_demo/exports/loop_demo.svg\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        (
            "--- examples/loop_demo/build/loop_demo.png\n"
            "+++ examples/loop_demo/build/loop_demo.png\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        (
            "--- examples/loop_demo/critique.md\n"
            "+++ examples/loop_demo/critique.md\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        (
            "--- examples/loop_demo/polish/final_artifact.svg\n"
            "+++ examples/loop_demo/polish/final_artifact.svg\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n",
            "forbidden",
        ),
        ("not a unified diff\n", "unified diff"),
    ],
)
def test_executor_refuses_unsafe_patch_files_without_mutation(
    tmp_path: Path,
    patch_text: str,
    message: str,
) -> None:
    repo_root, runs_root, _patch_path = _ready_repo(tmp_path)
    patch_path = _patch_file(repo_root, patch_text)
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    with pytest.raises(PatchExecutorError, match=message):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )

    assert tex_path.read_text(encoding="utf-8") == before


def test_executor_refuses_malicious_allowed_scope_outside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path
    runs_root = repo_root / ".scratch" / "fig-loop-runs"
    _fixture(repo_root)
    _write_latest_loop_run(
        repo_root,
        patch_handoff=_handoff(allowed=["../outside.tex"]),
        auto_patch_eligibility=_eligibility(),
    )
    patch_path = _patch_file(
        repo_root,
        "--- ../outside.tex\n"
        "+++ ../outside.tex\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n",
    )

    with pytest.raises(PatchExecutorError, match="repo-relative"):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )


def test_executor_refuses_patch_command_failure_without_mutation(tmp_path: Path) -> None:
    repo_root, runs_root, _patch_path = _ready_repo(tmp_path)
    patch_path = _patch_file(repo_root, _single_file_patch(old="Missing Label"))
    tex_path = repo_root / "examples" / "loop_demo" / "loop_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    with pytest.raises(PatchExecutorError, match="patch command failed"):
        apply_patch_file(
            "loop_demo",
            repo_root=repo_root,
            runs_root=runs_root,
            patch_path=patch_path,
            apply=True,
        )

    assert tex_path.read_text(encoding="utf-8") == before


def test_executor_cli_requires_apply_flag_and_reports_controlled_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, runs_root, patch_path = _ready_repo(tmp_path)

    exit_code = main(
        [
            "loop_demo",
            "--repo-root",
            str(repo_root),
            "--runs-root",
            str(runs_root),
            "--patch-file",
            str(patch_path),
        ]
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "explicit --apply" in captured.err
