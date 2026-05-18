from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quality_manifest import file_sha256  # noqa: E402
from svg_polish_manifest import (  # noqa: E402
    SvgPolishManifestError,
    final_artifact_source_set_hash,
    load_svg_polish_manifest,
    svg_polish_manifest_is_stale,
    validate_svg_polish_manifest,
    write_svg_polish_manifest,
)


def _make_fixture(tmp_path: Path, name: str = "demo_fig") -> Path:
    fig_dir = tmp_path / "examples" / name
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "polish").mkdir()
    (fig_dir / "reference").mkdir()
    (fig_dir / f"{name}.tex").write_text(
        "\\begin{tikzpicture}\\end{tikzpicture}\n",
        encoding="utf-8",
    )
    (fig_dir / "briefing.md").write_text("# Briefing\n", encoding="utf-8")
    (fig_dir / "spec.yaml").write_text(
        "name: demo_fig\n"
        "reference_image: reference/figure.png\n"
        "panels:\n"
        "  - id: A\n"
        "    bbox_pdf_cm: [0, 0, 1, 1]\n"
        "    reference_image: reference/panel_a.png\n",
        encoding="utf-8",
    )
    (fig_dir / "coordinate_hints.yaml").write_text("metadata: {}\n", encoding="utf-8")
    (fig_dir / "authoring_plan.md").write_text("# Plan\n", encoding="utf-8")
    (fig_dir / "theory_guard.md").write_text(
        "| ID | severity | claim | method | evidence |\n",
        encoding="utf-8",
    )
    (fig_dir / "subregion_iteration_log.md").write_text("# Log\n", encoding="utf-8")
    (fig_dir / "reference" / "reference_pack.md").write_text("# Pack\n", encoding="utf-8")
    (fig_dir / "reference" / "figure.png").write_bytes(b"figure-ref")
    (fig_dir / "reference" / "panel_a.png").write_bytes(b"panel-ref")
    (fig_dir / "exports" / f"{name}.svg").write_text(
        "<svg><text>base</text></svg>\n",
        encoding="utf-8",
    )
    (fig_dir / "exports" / f"{name}.pdf").write_bytes(b"%PDF base\n")
    (fig_dir / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.2\n---\n",
        encoding="utf-8",
    )
    (fig_dir / "polish" / f"{name}.polished.svg").write_text(
        "<svg><text>polished</text></svg>\n",
        encoding="utf-8",
    )
    (fig_dir / "polish" / "svg_polish_audit.md").write_text("# Audit\n", encoding="utf-8")
    return fig_dir


def _valid_manifest(fig_dir: Path, *, style_lock_path: Path | None = None) -> dict:
    name = fig_dir.name
    style_lock = style_lock_path or (fig_dir / "style.sty")
    if not style_lock.exists():
        style_lock.write_text("% style\n", encoding="utf-8")
    return {
        "schema": "figure-agent.svg-polish-manifest.v1",
        "fixture": name,
        "base": {
            "source_set_hash": final_artifact_source_set_hash(
                fig_dir,
                name,
                style_lock_path=style_lock,
                base_dir=fig_dir.parent.parent,
            ),
            "source_tex_hash": file_sha256(fig_dir / f"{name}.tex"),
            "briefing_hash": file_sha256(fig_dir / "briefing.md"),
            "spec_hash": file_sha256(fig_dir / "spec.yaml"),
            "generated_svg_hash": file_sha256(fig_dir / "exports" / f"{name}.svg"),
            "export_pdf_hash": file_sha256(fig_dir / "exports" / f"{name}.pdf"),
            "critique_hash": file_sha256(fig_dir / "critique.md"),
        },
        "polished": {
            "path": f"polish/{name}.polished.svg",
            "polished_svg_hash": file_sha256(fig_dir / "polish" / f"{name}.polished.svg"),
            "audit_hash": file_sha256(fig_dir / "polish" / "svg_polish_audit.md"),
            "editor": "human",
            "toolchain": [{"name": "Inkscape", "version": "1.4"}],
            "edit_classes": ["label_micro_position", "stroke_polish"],
            "semantic_change_declared": False,
            "backport_required": False,
        },
        "provenance": {
            "reviewer": "author",
            "reviewed_at": "2026-05-19T00:00:00Z",
            "notes": "visual-only polish",
        },
    }


def _is_stale(fig_dir: Path, manifest: Path, *, style_lock_path: Path | None = None) -> bool:
    style_lock = style_lock_path or (fig_dir / "style.sty")
    return svg_polish_manifest_is_stale(
        manifest,
        example_dir=fig_dir,
        style_lock_path=style_lock,
        base_dir=fig_dir.parent.parent,
    )


def test_valid_manifest_loads_successfully(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))

    loaded = load_svg_polish_manifest(manifest, example_dir=fig_dir)

    assert loaded["fixture"] == "demo_fig"
    assert loaded["polished"]["path"] == "polish/demo_fig.polished.svg"


def test_invalid_schema_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    payload["schema"] = "figure-agent.svg-polish-manifest.v0"

    with pytest.raises(SvgPolishManifestError, match="schema"):
        validate_svg_polish_manifest(payload, example_dir=fig_dir)


@pytest.mark.parametrize("field", ("schema", "fixture", "base", "polished", "provenance"))
def test_missing_required_top_level_fields_fail(tmp_path: Path, field: str) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    del payload[field]

    with pytest.raises(SvgPolishManifestError, match=field):
        validate_svg_polish_manifest(payload, example_dir=fig_dir)


def test_invalid_polished_path_outside_polish_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    payload["polished"]["path"] = "../exports/demo_fig.svg"

    with pytest.raises(SvgPolishManifestError, match="polished.path"):
        validate_svg_polish_manifest(payload, example_dir=fig_dir)


def test_invalid_editor_enum_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    payload["polished"]["editor"] = "robot"

    with pytest.raises(SvgPolishManifestError, match="editor"):
        validate_svg_polish_manifest(payload, example_dir=fig_dir)


def test_unknown_edit_class_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    payload["polished"]["edit_classes"].append("semantic_rewrite")

    with pytest.raises(SvgPolishManifestError, match="edit_classes"):
        validate_svg_polish_manifest(payload, example_dir=fig_dir)


def test_malformed_yaml_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    manifest.write_text("schema: [unterminated\n", encoding="utf-8")

    with pytest.raises(SvgPolishManifestError, match="invalid YAML"):
        load_svg_polish_manifest(manifest, example_dir=fig_dir)


def test_matching_hashes_are_fresh(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))

    assert _is_stale(fig_dir, manifest) is False


@pytest.mark.parametrize(
    "relative_path",
    (
        "demo_fig.tex",
        "exports/demo_fig.svg",
        "exports/demo_fig.pdf",
        "critique.md",
        "polish/demo_fig.polished.svg",
        "polish/svg_polish_audit.md",
    ),
)
def test_changed_direct_hash_inputs_are_stale(tmp_path: Path, relative_path: str) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))

    target = fig_dir / relative_path
    if target.suffix == ".pdf":
        target.write_bytes(b"%PDF changed\n")
    else:
        target.write_text(target.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

    assert _is_stale(fig_dir, manifest) is True


@pytest.mark.parametrize(
    "relative_path",
    (
        "coordinate_hints.yaml",
        "authoring_plan.md",
        "theory_guard.md",
        "subregion_iteration_log.md",
        "reference/reference_pack.md",
        "reference/figure.png",
        "reference/panel_a.png",
    ),
)
def test_changed_source_set_inputs_are_stale(tmp_path: Path, relative_path: str) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))

    target = fig_dir / relative_path
    if target.suffix == ".png":
        target.write_bytes(target.read_bytes() + b"changed")
    else:
        target.write_text(target.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")

    assert _is_stale(fig_dir, manifest) is True


def test_changed_style_lock_is_stale(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    style_lock = fig_dir / "style.sty"
    style_lock.write_text("% style\n", encoding="utf-8")
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir, style_lock_path=style_lock))

    style_lock.write_text("% style changed\n", encoding="utf-8")

    assert _is_stale(fig_dir, manifest, style_lock_path=style_lock) is True


def test_missing_polished_svg_fails_cleanly_during_stale_check(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))
    (fig_dir / "polish" / "demo_fig.polished.svg").unlink()

    with pytest.raises(SvgPolishManifestError, match="missing"):
        _is_stale(fig_dir, manifest)


def test_invalid_spec_fails_cleanly_during_source_set_hash(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    (fig_dir / "spec.yaml").write_text(
        "name: demo_fig\n"
        "panels:\n"
        "  - id: A\n"
        "    bbox_pdf_cm: [1, 1, 0, 0]\n",
        encoding="utf-8",
    )

    with pytest.raises(SvgPolishManifestError, match="invalid spec.yaml"):
        final_artifact_source_set_hash(fig_dir, "demo_fig", style_lock_path=fig_dir / "style.sty")


def test_unknown_future_fields_survive_load_write(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_manifest(fig_dir)
    payload["future"] = {"review_model": "human-v2"}
    payload["polished"]["future_detail"] = "kept"
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"

    write_svg_polish_manifest(manifest, payload)
    loaded = load_svg_polish_manifest(manifest, example_dir=fig_dir)
    rewrite = fig_dir / "polish" / "rewritten.yaml"
    write_svg_polish_manifest(rewrite, loaded)

    reloaded = load_svg_polish_manifest(rewrite, example_dir=fig_dir)
    assert reloaded["future"]["review_model"] == "human-v2"
    assert reloaded["polished"]["future_detail"] == "kept"


def test_writer_emits_reloadable_yaml(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    manifest = fig_dir / "polish" / "svg_polish_manifest.yaml"
    write_svg_polish_manifest(manifest, _valid_manifest(fig_dir))

    reloaded = load_svg_polish_manifest(manifest, example_dir=fig_dir)

    assert validate_svg_polish_manifest(reloaded, example_dir=fig_dir) == reloaded
