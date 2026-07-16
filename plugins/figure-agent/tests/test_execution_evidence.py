from __future__ import annotations

import hashlib
import json
from pathlib import Path

import execution_evidence
import pytest


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_compile_evidence_uses_content_fingerprints_and_sorted_allowlisted_paths(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "examples" / "demo"
    build_dir = fixture_dir / "build"
    build_dir.mkdir(parents=True)
    pdf_path = build_dir / "demo.pdf"
    json_path = build_dir / "collisions.json"
    pdf_path.write_bytes(b"before")
    json_path.write_bytes(b"same")

    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_compile",
    )

    pdf_path.write_bytes(b"after")
    png_path = build_dir / "demo.png"
    png_path.write_bytes(b"png")
    visual_manifest = (
        build_dir / "perception" / "visual_findings" / "manifest.json"
    )
    visual_manifest.parent.mkdir(parents=True)
    visual_manifest.write_bytes(b"{}")
    (build_dir / "demo.aux").write_bytes(b"transient")

    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert evidence == {
        "schema": "figure-agent.step-execution-evidence.v1",
        "fixture": "demo",
        "action": "run_compile",
        "state": "captured",
        "artifacts": [
            {
                "role": "compile_report",
                "path": "examples/demo/build/collisions.json",
                "change": "unchanged",
                "size_bytes": 4,
                "sha256": _sha256(b"same"),
            },
            {
                "role": "render_pdf",
                "path": "examples/demo/build/demo.pdf",
                "change": "modified",
                "size_bytes": 5,
                "sha256": _sha256(b"after"),
            },
            {
                "role": "render_png",
                "path": "examples/demo/build/demo.png",
                "change": "created",
                "size_bytes": 3,
                "sha256": _sha256(b"png"),
            },
            {
                "role": "visual_finding_artifact",
                "path": (
                    "examples/demo/build/perception/visual_findings/manifest.json"
                ),
                "change": "created",
                "size_bytes": 2,
                "sha256": _sha256(b"{}"),
            },
        ],
        "diagnostics": [],
    }


def test_compile_evidence_ignores_symlinks_and_reports_success_missing_outputs(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / "examples" / "demo" / "build"
    build_dir.mkdir(parents=True)
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    (build_dir / "demo.pdf").symlink_to(outside)

    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_compile",
    )
    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert evidence["artifacts"] == []
    assert evidence["state"] == "captured_with_diagnostics"
    assert evidence["diagnostics"] == [
        "artifact_symlink_ignored:examples/demo/build/demo.pdf",
        "required_artifact_missing:examples/demo/build/demo.pdf",
        "required_artifact_missing:examples/demo/build/demo.png",
    ]


def test_compile_evidence_does_not_follow_symlinked_output_directory(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "examples" / "demo"
    fixture_dir.mkdir(parents=True)
    outside_build = tmp_path / "outside-build"
    outside_build.mkdir()
    (outside_build / "demo.pdf").write_bytes(b"outside")
    (outside_build / "demo.png").write_bytes(b"outside")
    (fixture_dir / "build").symlink_to(outside_build, target_is_directory=True)

    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_compile",
    )
    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert evidence["artifacts"] == []
    assert all("outside-build" not in diagnostic for diagnostic in evidence["diagnostics"])
    assert (
        "artifact_symlink_ignored:examples/demo/build"
        in evidence["diagnostics"]
    )


def test_failed_adjudication_preserves_partial_artifact_without_missing_diagnostic(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "examples" / "demo"
    fixture_dir.mkdir(parents=True)
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_adjudicate",
    )
    adjudication = fixture_dir / "critique_adjudication.yaml"
    adjudication.write_text("schema: partial\n", encoding="utf-8")

    evidence = execution_evidence.finish_step_capture(capture, returncode=3)

    assert evidence["state"] == "captured"
    assert evidence["diagnostics"] == []
    assert evidence["artifacts"][0]["role"] == "critique_adjudication"
    assert evidence["artifacts"][0]["change"] == "created"


def _write_loop_run(run_dir: Path, *, fixture: str) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps({"fixture": fixture}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "iteration_001.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "stop_report.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "decision.md").write_text("# Decision\n", encoding="utf-8")


def test_direct_fig_loop_requires_one_new_fixture_bound_immediate_child(
    tmp_path: Path,
) -> None:
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_fig_loop",
    )
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    _write_loop_run(runs_root / "run-a", fixture="demo")
    _write_loop_run(runs_root / "run-b", fixture="demo")

    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert evidence["artifacts"] == []
    assert evidence["diagnostics"] == ["fig_loop_run_ambiguous"]
    assert evidence["state"] == "captured_with_diagnostics"


def test_direct_fig_loop_reports_missing_new_run_without_guessing_latest(
    tmp_path: Path,
) -> None:
    existing = tmp_path / ".scratch" / "fig-loop-runs" / "old"
    _write_loop_run(existing, fixture="demo")
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_fig_loop",
    )

    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert evidence["artifacts"] == []
    assert evidence["diagnostics"] == ["fig_loop_run_missing"]


def test_queue_bound_fig_loop_uses_exact_returned_run_and_recursive_allowlist(
    tmp_path: Path,
) -> None:
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_fig_loop",
    )
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    returned = runs_root / "run-returned"
    _write_loop_run(returned, fixture="demo")
    command_logs = returned / "command_logs"
    command_logs.mkdir()
    (command_logs / "compile.stdout.log").write_text("ok\n", encoding="utf-8")
    (command_logs / "secret.bin").write_bytes(b"ignore")
    _write_loop_run(runs_root / "run-unrelated", fixture="demo")

    evidence = execution_evidence.finish_step_capture(
        capture,
        returncode=0,
        loop_run_dir=returned,
    )

    assert evidence["diagnostics"] == []
    assert [item["role"] for item in evidence["artifacts"]] == [
        "fig_loop_command_log",
        "fig_loop_decision",
        "fig_loop_iteration",
        "fig_loop_manifest",
        "fig_loop_stop_report",
    ]
    assert all("run-unrelated" not in item["path"] for item in evidence["artifacts"])
    assert all(not item["path"].endswith("secret.bin") for item in evidence["artifacts"])


def test_export_evidence_is_limited_to_four_named_formats(tmp_path: Path) -> None:
    exports_dir = tmp_path / "examples" / "demo" / "exports"
    exports_dir.mkdir(parents=True)
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_export",
    )
    for suffix in (".pdf", ".png", ".svg", ".tif"):
        (exports_dir / f"demo{suffix}").write_bytes(suffix.encode())
    (exports_dir / "other.svg").write_bytes(b"other")

    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert [item["role"] for item in evidence["artifacts"]] == [
        "export_pdf",
        "export_png",
        "export_svg",
        "export_tiff",
    ]
    assert all(
        item["path"].startswith("examples/demo/exports/demo.")
        for item in evidence["artifacts"]
    )


def test_unexpected_programming_error_is_not_converted_to_capture_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_dir = tmp_path / "examples" / "demo"
    fixture_dir.mkdir(parents=True)
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_adjudicate",
    )
    path = fixture_dir / "critique_adjudication.yaml"
    path.write_text("schema: test\n", encoding="utf-8")
    original_lstat = Path.lstat

    def _broken_lstat(self: Path):
        if self == path:
            raise RuntimeError("programming defect with /private/raw/path")
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", _broken_lstat)

    with pytest.raises(RuntimeError, match="programming defect"):
        execution_evidence.finish_step_capture(capture, returncode=0)


def test_collection_oserror_is_sanitized_and_other_artifacts_survive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_dir = tmp_path / "examples" / "demo" / "build"
    build_dir.mkdir(parents=True)
    pdf_path = build_dir / "demo.pdf"
    png_path = build_dir / "demo.png"
    pdf_path.write_bytes(b"pdf")
    png_path.write_bytes(b"png")
    original_lstat = Path.lstat

    def _denied_lstat(self: Path):
        if self == pdf_path:
            raise PermissionError("raw private path /do/not/expose")
        return original_lstat(self)

    monkeypatch.setattr(Path, "lstat", _denied_lstat)
    capture = execution_evidence.begin_step_capture(
        tmp_path,
        fixture="demo",
        action="run_compile",
    )
    evidence = execution_evidence.finish_step_capture(capture, returncode=0)

    assert [item["path"] for item in evidence["artifacts"]] == [
        "examples/demo/build/demo.png"
    ]
    assert evidence["diagnostics"] == [
        "artifact_lstat_failed:examples/demo/build/demo.pdf",
        "required_artifact_missing:examples/demo/build/demo.pdf",
    ]
    assert "/do/not/expose" not in json.dumps(evidence)
