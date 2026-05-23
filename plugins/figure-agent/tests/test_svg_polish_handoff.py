from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_polish_handoff import (  # noqa: E402
    SvgPolishHandoffError,
    main,
    write_handoff_files,
)
from svg_polish_manifest import (  # noqa: E402
    FINAL_ARTIFACT_BLOCKED,
    compute_final_artifact_state,
    load_svg_polish_manifest,
    svg_polish_manifest_is_stale,
)


def _make_fixture(tmp_path: Path, name: str = "demo_fig") -> tuple[Path, Path]:
    fig_dir = tmp_path / "examples" / name
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "polish").mkdir()
    (fig_dir / f"{name}.tex").write_text(
        "\\begin{tikzpicture}\\node {demo};\\end{tikzpicture}\n",
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("# Briefing\n", encoding="utf-8")
    (fig_dir / "spec.yaml").write_text("name: demo_fig\n", encoding="utf-8")
    (fig_dir / "exports" / f"{name}.svg").write_text(
        "<svg><text>base</text></svg>\n",
        encoding="utf-8",
    )
    (fig_dir / "exports" / f"{name}.pdf").write_bytes(b"%PDF base\n")
    (fig_dir / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.10\n---\n",
        encoding="utf-8",
    )
    (fig_dir / "polish" / f"{name}.polished.svg").write_text(
        "<svg><text>polished</text></svg>\n",
        encoding="utf-8",
    )
    style_lock = fig_dir / "style.sty"
    style_lock.write_text("% style\n", encoding="utf-8")
    return fig_dir, style_lock


def _write_default_handoff(
    fig_dir: Path,
    style_lock: Path,
    *,
    backport_required: bool = False,
) -> tuple[Path, Path]:
    return write_handoff_files(
        fig_dir,
        reviewer="author",
        editor="human",
        toolchain=[{"name": "Inkscape", "version": "1.4"}],
        edit_classes=["label_micro_position", "stroke_polish"],
        reviewed_at="2026-05-23T00:00:00Z",
        notes="visual-only polish",
        semantic_change_declared=False,
        backport_required=backport_required,
        force=False,
        style_lock_path=style_lock,
        base_dir=fig_dir.parent.parent,
    )


def test_write_handoff_files_creates_audit_and_fresh_manifest(tmp_path: Path) -> None:
    fig_dir, style_lock = _make_fixture(tmp_path)

    audit_path, manifest_path = _write_default_handoff(fig_dir, style_lock)

    audit = audit_path.read_text(encoding="utf-8")
    assert "components: pass" in audit
    assert "labels/material identity: pass" in audit
    assert "mechanism directions: pass" in audit
    assert "panel/storyline meaning: pass" in audit
    assert "scale/proximity meaning: pass" in audit
    assert "unresolved critique findings: visible" in audit
    manifest = load_svg_polish_manifest(manifest_path, example_dir=fig_dir)
    assert manifest["polished"]["edit_classes"] == ["label_micro_position", "stroke_polish"]
    assert not svg_polish_manifest_is_stale(
        manifest_path,
        example_dir=fig_dir,
        style_lock_path=style_lock,
        base_dir=fig_dir.parent.parent,
    )


def test_write_handoff_files_rejects_unknown_edit_class_before_writing(tmp_path: Path) -> None:
    fig_dir, style_lock = _make_fixture(tmp_path)

    try:
        write_handoff_files(
            fig_dir,
            reviewer="author",
            editor="human",
            toolchain=[{"name": "Inkscape", "version": "1.4"}],
            edit_classes=["component_rename"],
            reviewed_at="2026-05-23T00:00:00Z",
            notes="bad class",
            semantic_change_declared=False,
            backport_required=False,
            force=False,
            style_lock_path=style_lock,
            base_dir=fig_dir.parent.parent,
        )
    except SvgPolishHandoffError as exc:
        assert "component_rename" in str(exc)
    else:
        raise AssertionError("expected SvgPolishHandoffError")

    assert not (fig_dir / "polish" / "svg_polish_audit.md").exists()
    assert not (fig_dir / "polish" / "svg_polish_manifest.yaml").exists()


def test_write_handoff_files_rejects_empty_reviewer_before_writing(tmp_path: Path) -> None:
    fig_dir, style_lock = _make_fixture(tmp_path)

    try:
        write_handoff_files(
            fig_dir,
            reviewer="",
            editor="human",
            toolchain=[{"name": "Inkscape", "version": "1.4"}],
            edit_classes=["label_micro_position"],
            reviewed_at="2026-05-23T00:00:00Z",
            notes="visual-only polish",
            semantic_change_declared=False,
            backport_required=False,
            force=False,
            style_lock_path=style_lock,
            base_dir=fig_dir.parent.parent,
        )
    except SvgPolishHandoffError as exc:
        assert "reviewer" in str(exc)
    else:
        raise AssertionError("expected SvgPolishHandoffError")

    assert not (fig_dir / "polish" / "svg_polish_audit.md").exists()
    assert not (fig_dir / "polish" / "svg_polish_manifest.yaml").exists()


def test_backport_required_manifest_is_blocked_by_existing_final_artifact_state(
    tmp_path: Path,
) -> None:
    fig_dir, style_lock = _make_fixture(tmp_path)
    spec_path = fig_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8")
        + "final_artifact:\n"
        + "  kind: polished_svg\n"
        + "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    _write_default_handoff(fig_dir, style_lock, backport_required=True)
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    state = compute_final_artifact_state(
        fig_dir,
        fig_dir.name,
        spec,
        style_lock_path=style_lock,
        base_dir=fig_dir.parent.parent,
    )

    assert state["state"] == FINAL_ARTIFACT_BLOCKED
    assert "semantic backport required" in state["error"]


def test_cli_dry_run_does_not_write_outputs(tmp_path: Path, capsys) -> None:
    fig_dir, style_lock = _make_fixture(tmp_path)

    exit_code = main(
        [
            str(fig_dir),
            "--reviewer",
            "author",
            "--editor",
            "human",
            "--toolchain",
            "Inkscape:1.4",
            "--edit-class",
            "label_micro_position",
            "--reviewed-at",
            "2026-05-23T00:00:00Z",
            "--style-lock-path",
            str(style_lock),
            "--base-dir",
            str(fig_dir.parent.parent),
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "dry-run" in output
    assert "polish/svg_polish_audit.md" in output
    assert "polish/svg_polish_manifest.yaml" in output
    assert not (fig_dir / "polish" / "svg_polish_audit.md").exists()
    assert not (fig_dir / "polish" / "svg_polish_manifest.yaml").exists()
