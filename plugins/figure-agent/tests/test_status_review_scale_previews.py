from __future__ import annotations

from pathlib import Path

import render_input_manifest
import status as status_mod
from PIL import Image
from review_scale_previews import build_scale_previews
from status import infer_stage


def _source_fixture(root: Path) -> Path:
    fixture = root / "preview_status_demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    name = fixture.name
    (fixture / f"{name}.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("briefing\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        f"name: {name}\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "review_scale_previews: required\n",
        encoding="utf-8",
    )
    (build / f"{name}.pdf").write_bytes(b"%PDF")
    Image.new("RGB", (300, 150), color="red").save(build / f"{name}.png", "PNG")
    render_input_manifest.write_manifest(
        fixture=name,
        render_pdf=build / f"{name}.pdf",
        inputs=status_mod._render_input_paths(fixture, name),
        output=render_input_manifest.manifest_path(build / f"{name}.pdf"),
    )
    return fixture


def test_status_fails_closed_when_required_scale_preview_is_missing(tmp_path: Path) -> None:
    fixture = _source_fixture(tmp_path)

    result = infer_stage(fixture)

    assert result["render_state"] == "STALE"
    assert result["review_scale_previews"]["state"] == "MISSING"
    assert result["status_explanation"]["first_blocker"]["code"] == "review_scale_previews_missing"


def test_status_recovers_only_after_preview_manifest_binds_current_render(tmp_path: Path) -> None:
    fixture = _source_fixture(tmp_path)
    render = fixture / "build" / f"{fixture.name}.png"
    build_scale_previews(render)

    result = infer_stage(fixture)

    assert result["render_state"] == "FRESH"
    assert result["review_scale_previews"]["state"] == "FRESH"
    assert result["stage"] == 3


def test_status_marks_changed_render_stale_even_when_pdf_is_fresh(tmp_path: Path) -> None:
    fixture = _source_fixture(tmp_path)
    render = fixture / "build" / f"{fixture.name}.png"
    build_scale_previews(render)
    Image.new("RGB", (300, 150), color="blue").save(render, "PNG")

    result = infer_stage(fixture)

    assert result["render_state"] == "STALE"
    assert result["review_scale_previews"]["state"] == "STALE"
    assert result["status_explanation"]["first_blocker"]["code"] == "review_scale_previews_stale"
