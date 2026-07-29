from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from review_scale_previews import (
    FRESH,
    INVALID,
    MISSING,
    STALE,
    build_scale_previews,
    manifest_path,
    preview_path,
    preview_status,
)


def _render(path: Path, color: str = "red") -> None:
    Image.new("RGB", (300, 150), color=color).save(path, "PNG")


def test_preview_manifest_binds_every_scale_to_current_render(tmp_path: Path) -> None:
    render = tmp_path / "figure.png"
    _render(render)

    payload = build_scale_previews(render)

    assert preview_status(render)["state"] == FRESH
    assert payload["render"]["path"] == "figure.png"
    actual_sizes = [
        (item["label"], item["width_px"], item["height_px"])
        for item in payload["previews"]
    ]
    assert actual_sizes == [
        ("100pct", 300, 150),
        ("50pct", 150, 75),
        ("33pct", 99, 50),
    ]
    assert preview_path(render, "33pct").is_file()


def test_changed_render_makes_old_preview_evidence_stale(tmp_path: Path) -> None:
    render = tmp_path / "figure.png"
    _render(render, "red")
    build_scale_previews(render)

    _render(render, "blue")

    result = preview_status(render)
    assert result["state"] == STALE
    assert result["reason"] == "render_hash_mismatch"


def test_regeneration_rebinds_previews_after_render_change(tmp_path: Path) -> None:
    render = tmp_path / "figure.png"
    _render(render, "red")
    build_scale_previews(render)
    _render(render, "blue")

    payload = build_scale_previews(render)

    assert preview_status(render)["state"] == FRESH
    assert payload["previews"][-1]["sha256"].startswith("sha256:")


def test_partial_or_malformed_manifest_is_never_fresh(tmp_path: Path) -> None:
    render = tmp_path / "figure.png"
    _render(render)
    build_scale_previews(render)
    preview_path(render, "33pct").unlink()

    assert preview_status(render)["state"] == MISSING

    manifest_path(render).write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
    assert preview_status(render)["state"] == INVALID
