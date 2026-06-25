from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

pytestmark = pytest.mark.quarantine

import fig_driver  # noqa: E402
import status as status_mod  # noqa: E402
import svg_polish_manifest as manifest_mod  # noqa: E402
from svg_polish_delta import build_svg_polish_delta_pack  # noqa: E402
from svg_polish_executor import apply_svg_polish  # noqa: E402
from svg_polish_handoff import write_handoff_files  # noqa: E402
from svg_polish_recipe import (  # noqa: E402
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    svg_polish_recipe_input_hash,
    write_svg_polish_recipe,
)
from svg_semantic_diff import build_svg_semantic_diff_report  # noqa: E402


def _write_clean_fixture(tmp_path: Path, name: str = "clean_polish_demo") -> tuple[Path, Path]:
    fixture = tmp_path / "examples" / name
    (fixture / "build").mkdir(parents=True)
    (fixture / "exports").mkdir()
    (fixture / "polish").mkdir()
    (fixture / f"{name}.tex").write_text(
        "\\begin{tikzpicture}\\node {demo};\\end{tikzpicture}\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Briefing\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        f"name: {name}\n"
        "panels: []\n"
        "final_artifact:\n"
        "  kind: polished_svg\n"
        "  manifest: polish/svg_polish_manifest.yaml\n",
        encoding="utf-8",
    )
    (fixture / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.11\n---\n",
        encoding="utf-8",
    )
    source_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">\n'
        '  <g id="label-a"><text>Label A</text></g>\n'
        '  <path id="guide-a" stroke-width="1.0" opacity="0.5" />\n'
        "</svg>\n"
    )
    (fixture / "exports" / f"{name}.svg").write_text(source_svg, encoding="utf-8")
    pdf_bytes = b"%PDF-1.4 clean polish demo\n"
    (fixture / "build" / f"{name}.pdf").write_bytes(pdf_bytes)
    (fixture / "exports" / f"{name}.pdf").write_bytes(pdf_bytes)
    (fixture / "exports" / f"{name}.png").write_bytes(b"\x89PNG")
    (fixture / "exports" / f"{name}.tif").write_bytes(b"TIFF")
    style_lock = tmp_path / "styles" / "style.sty"
    style_lock.parent.mkdir()
    style_lock.write_text("% test style\n", encoding="utf-8")
    old_time = time.time() - 200
    fresh_time = time.time() + 20
    for path in (
        fixture / f"{name}.tex",
        fixture / "briefing.md",
        fixture / "spec.yaml",
        fixture / "critique.md",
        style_lock,
    ):
        os.utime(path, (old_time, old_time))
    for path in [fixture / "build" / f"{name}.pdf", *list((fixture / "exports").iterdir())]:
        os.utime(path, (fresh_time, fresh_time))
    return fixture, style_lock


def _write_recipe(fixture: Path) -> Path:
    name = fixture.name
    recipe_path = fixture / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(
        recipe_path,
        {
            "schema": "figure-agent.svg-polish-recipe.v1",
            "fixture": name,
            "source_svg": f"exports/{name}.svg",
            "target_svg": f"polish/{name}.polished.svg",
            "recipe_input_hash": svg_polish_recipe_input_hash(
                fixture,
                name,
                source_svg=f"exports/{name}.svg",
                base_dir=fixture.parent.parent,
            ),
            "operations": [
                {
                    "id": "R001",
                    "class": "label_micro_position",
                    "selector": {"kind": "element_id", "value": "label-a"},
                    "action": {"type": "translate", "dx": 1.0, "dy": -1.0, "unit": "px"},
                    "rationale": "Move label by a bounded optical offset.",
                    "semantic_guard": {
                        "allowed": True,
                        "reason": "same label and target; visual-only movement",
                    },
                }
            ],
        },
    )
    return recipe_path


def _fake_renderer(source_svg: Path, output_png: Path) -> None:
    color = (255, 255, 255, 255)
    if "polish" in source_svg.parts:
        color = (220, 220, 255, 255)
    Image.new("RGBA", (8, 8), color).save(output_png)


def _stub_export_state(monkeypatch) -> None:
    def _stub(example_dir: Path, name: str) -> str:
        exports = example_dir / "exports"
        required = (
            exports / f"{name}.pdf",
            exports / f"{name}.svg",
            exports / f"{name}.png",
            exports / f"{name}.tif",
        )
        return "FRESH" if all(path.is_file() for path in required) else "MISSING"

    monkeypatch.setattr(status_mod, "compute_export_state", _stub)


def _stub_final_artifact_base_dir(monkeypatch, base_dir: Path) -> None:
    def _compute(
        example_dir: Path,
        name: str,
        spec: dict[str, Any],
        *,
        style_lock_path: Path,
        spec_parse_error: bool = False,
    ) -> dict[str, Any]:
        return manifest_mod.compute_final_artifact_state(
            example_dir,
            name,
            spec,
            style_lock_path=style_lock_path,
            base_dir=base_dir,
            spec_parse_error=spec_parse_error,
        )

    monkeypatch.setattr(status_mod, "compute_final_artifact_state", _compute)


def test_clean_polished_svg_route_closes_from_recipe_to_driver_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture, style_lock = _write_clean_fixture(tmp_path)
    _stub_export_state(monkeypatch)
    _stub_final_artifact_base_dir(monkeypatch, fixture.parent.parent)
    monkeypatch.setattr(status_mod, "STYLE_LOCK_PATH", style_lock)
    source_svg = fixture / "exports" / f"{fixture.name}.svg"
    source_before = source_svg.read_text(encoding="utf-8")
    recipe_path = _write_recipe(fixture)

    polished_path = apply_svg_polish(
        recipe_path,
        example_dir=fixture,
        base_dir=fixture.parent.parent,
    )
    delta_manifest = build_svg_polish_delta_pack(
        fixture,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fixture.parent.parent,
    )
    audit_path, manifest_path = write_handoff_files(
        fixture,
        reviewer="codex-ci",
        editor="agent_assisted",
        toolchain=[{"name": "svg_polish_executor.py", "version": "recipe-v1"}],
        edit_classes=["label_micro_position"],
        reviewed_at="2026-05-26T00:00:00Z",
        notes="deterministic clean dogfood visual-only polish",
        semantic_change_declared=False,
        backport_required=False,
        force=False,
        style_lock_path=style_lock,
        base_dir=fixture.parent.parent,
    )
    semantic_diff_path = build_svg_semantic_diff_report(fixture)

    status = status_mod.infer_stage(fixture)
    summary: dict[str, Any] = fig_driver.build_driver_summary(
        fixture.name,
        mode="polish",
        goal="clean dogfood",
        repo_root=fixture.parent.parent,
    )

    assert source_svg.read_text(encoding="utf-8") == source_before
    assert polished_path == fixture / "polish" / f"{fixture.name}.polished.svg"
    assert delta_manifest == fixture / "polish" / "aesthetic_delta" / "delta_manifest.json"
    assert audit_path == fixture / "polish" / "svg_polish_audit.md"
    assert manifest_path == fixture / "polish" / "svg_polish_manifest.yaml"
    assert semantic_diff_path == fixture / "polish" / "svg_semantic_diff.json"
    assert status["render_state"] == "FRESH"
    assert status["export_state"] == "FRESH"
    assert status["final_artifact_kind"] == "polished_svg"
    assert status["final_artifact_state"] == "FRESH"
    assert summary["action"] == "complete"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] is None
