from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import status as status_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_export_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace qpdf-dependent compute_export_state with a filesystem-only stub.

    Same pattern as tests/test_status.py: stub PDFs cannot be hashed via qpdf,
    so freshness is inferred from artifact presence alone.
    """

    def _stub(example_dir: Path, name: str) -> str:
        exports_dir = example_dir / "exports"
        pdf = exports_dir / f"{name}.pdf"
        if not pdf.is_file():
            return "MISSING"
        svg = exports_dir / f"{name}.svg"
        png = exports_dir / f"{name}.png"
        tif = (exports_dir / f"{name}.tif").is_file() or (exports_dir / f"{name}.tiff").is_file()
        if not (svg.is_file() and png.is_file() and tif):
            return "STALE"
        return "FRESH"

    monkeypatch.setattr(status_mod, "compute_export_state", _stub)


def _write_basic_fixture(root: Path, name: str = "driver_demo") -> Path:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("% tikz\n", encoding="utf-8")
    return fixture


def _write_fresh_build_and_exports(fixture: Path, name: str = "driver_demo") -> None:
    pdf_bytes = b"%PDF-1.4 driver"
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / f"{name}.pdf").write_bytes(pdf_bytes)
    exports = fixture / "exports"
    exports.mkdir(exist_ok=True)
    (exports / f"{name}.pdf").write_bytes(pdf_bytes)
    (exports / f"{name}.svg").write_text("<svg/>\n", encoding="utf-8")
    (exports / f"{name}.png").write_bytes(b"\x89PNG")
    (exports / f"{name}.tif").write_bytes(b"TIFF")
    old_time = time.time() - 100
    fresh_time = time.time() - 10
    for path in (fixture / "spec.yaml", fixture / "briefing.md", fixture / f"{name}.tex"):
        os.utime(path, (old_time, old_time))
    for path in [build / f"{name}.pdf", *exports.iterdir()]:
        os.utime(path, (fresh_time, fresh_time))


def _run_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
    return fig_driver.build_driver_summary(name, mode=mode, goal=goal, repo_root=repo_root)


# --- CLI + JSON contract -----------------------------------------------------


def test_main_requires_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(
        ["driver_demo", "--mode", "review", "--goal", "review"], repo_root=tmp_path
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "--dry-run is required" in captured.err
    assert captured.out == ""


def test_main_emits_json_summary_in_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(
        [
            "driver_demo",
            "--mode",
            "authoring",
            "--goal",
            "tighten layout",
            "--dry-run",
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.driver.v1"
    assert payload["fixture"] == "driver_demo"
    assert payload["mode"] == "authoring"
    assert payload["goal"] == "tighten layout"
    assert payload["may_execute"] is False
    assert isinstance(payload["status"], dict)
    assert isinstance(payload["forbidden_actions"], list)
    for key in ("action", "safe_command", "stop_boundary", "reason"):
        assert key in payload


def test_unsupported_mode_fails_cleanly(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        fig_driver.main(
            [
                "driver_demo",
                "--mode",
                "executive",
                "--goal",
                "x",
                "--dry-run",
            ],
            repo_root=tmp_path,
        )

    assert exc_info.value.code == 2


# --- authoring mode ----------------------------------------------------------


def test_authoring_mode_recommends_compile_when_render_missing(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "bash scripts/compile.sh examples/driver_demo/driver_demo.tex"
    assert summary["stop_boundary"] is None


def test_authoring_mode_completes_when_render_fresh(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


# --- review mode -------------------------------------------------------------


def test_review_mode_stops_for_reference_missing(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/missing.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "reference_missing"
    assert summary["safe_command"] is None


def test_review_mode_stops_for_host_critique_when_critique_missing(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    reference = fixture / "reference" / "ref.png"
    reference.parent.mkdir()
    reference.write_bytes(b"\x89PNG")
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/ref.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert summary["safe_command"] == "/fig_critique driver_demo"


def test_review_mode_recommends_adjudicate_when_critique_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: True)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_adjudicate"
    assert summary["stop_boundary"] is None
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/critique_adjudication.py scaffold driver_demo"
    )


def test_review_mode_runs_fig_loop_when_prerequisites_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/fig_loop.py driver_demo --goal review --json"
    )
    assert summary["stop_boundary"] is None


def test_review_mode_fig_loop_goal_is_shell_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="it's a goal", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/fig_loop.py driver_demo --goal 'it'\"'\"'s a goal' --json"
    )


# --- release mode ------------------------------------------------------------


def test_release_mode_reports_release_blocked_without_mutation(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert summary["may_execute"] is False
    assert summary["safe_command"] is None


# --- polish mode -------------------------------------------------------------


def test_polish_mode_requires_current_export_before_polish(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_compile"


def test_polish_mode_stops_for_polish_handoff_when_export_current(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None


def test_polish_mode_reports_semantic_backport_required_for_blocked_final_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "BLOCKED",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "polish/driver_demo.polished.svg",
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] == "semantic_backport_required"


def test_polish_mode_completes_when_polished_svg_is_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "FRESH",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "polish/driver_demo.polished.svg",
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


# --- stage 0 / 1 -------------------------------------------------------------


def test_create_or_fix_source_when_directory_missing(tmp_path: Path) -> None:
    (tmp_path / "examples").mkdir()

    summary = _run_driver("driver_demo", mode="review", goal="scaffold", repo_root=tmp_path)

    assert summary["action"] == "create_or_fix_source"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] is None


def test_create_or_fix_source_when_tex_missing(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "driver_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: driver_demo\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "create_or_fix_source"


# --- release-mode critique recommendation (Review 1 HIGH regression test) ----


def test_release_mode_recommends_critique_without_self_contradicting_forbidden_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Release mode hitting MISSING critique must not forbid the action it returns."""
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": ["critique_missing"],
        "render_state": "FRESH",
        "critique_state": "MISSING",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert summary["safe_command"] == "/fig_critique driver_demo"
    assert summary["action"] not in summary["forbidden_actions"]


# --- no-mutation guarantee ---------------------------------------------------


def test_driver_dry_run_does_not_mutate_fixture_files(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    before = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }

    _run_driver("driver_demo", mode="review", goal="dry", repo_root=tmp_path)

    after = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }
    assert after == before
