"""Run a deterministic positive-path SVG polish harness."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fig_driver import build_driver_summary
from PIL import Image
from quality_manifest import REPO_ROOT, file_sha256
from status import infer_stage
from svg_polish_delta import build_svg_polish_delta_pack
from svg_polish_executor import apply_svg_polish
from svg_polish_handoff import write_handoff_files
from svg_polish_recipe import (
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    svg_polish_recipe_input_hash,
    write_svg_polish_recipe,
)
from svg_semantic_diff import build_svg_semantic_diff_report

SCHEMA = "figure-agent.svg-polish-positive-harness.v1"
FIXTURE = "svg_polish_positive_demo"
SEED_DIR = REPO_ROOT / "tests" / "fixtures" / FIXTURE
DEFAULT_WORK_DIR = REPO_ROOT / ".scratch" / "svg-polish-positive-harness"
MARKER_FILENAME = ".svg-polish-positive-harness.json"


def _copy_seed(work_dir: Path, *, force: bool) -> Path:
    if work_dir.exists():
        if not force:
            raise ValueError(f"work_dir already exists; pass --force to replace: {work_dir}")
        if work_dir.resolve() == REPO_ROOT.resolve():
            raise ValueError("refusing to replace repository root")
        if not _is_replaceable_work_dir(work_dir):
            marker = MARKER_FILENAME
            raise ValueError(f"refusing to replace unmarked work_dir; missing {marker}: {work_dir}")
        shutil.rmtree(work_dir)
    fixture = work_dir / "examples" / FIXTURE
    fixture.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SEED_DIR, fixture)
    _write_marker(work_dir)
    return fixture


def _is_replaceable_work_dir(work_dir: Path) -> bool:
    marker_path = work_dir / MARKER_FILENAME
    legacy_fixture = work_dir / "examples" / FIXTURE
    if work_dir.resolve() == DEFAULT_WORK_DIR.resolve() and legacy_fixture.is_dir():
        return True
    if not marker_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return marker.get("schema") == SCHEMA and marker.get("fixture") == FIXTURE


def _write_marker(work_dir: Path) -> None:
    marker_path = work_dir / MARKER_FILENAME
    marker_path.write_text(
        json.dumps({"schema": SCHEMA, "fixture": FIXTURE}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _materialize_exports(fixture: Path) -> None:
    name = fixture.name
    build = fixture / "build"
    exports = fixture / "exports"
    build.mkdir(exist_ok=True)
    exports.mkdir(exist_ok=True)
    pdf_bytes = _minimal_pdf_bytes()
    (build / f"{name}.pdf").write_bytes(pdf_bytes)
    (exports / f"{name}.pdf").write_bytes(pdf_bytes)
    Image.new("RGBA", (12, 12), (255, 255, 255, 255)).save(build / f"{name}.png")
    Image.new("RGBA", (12, 12), (255, 255, 255, 255)).save(exports / f"{name}.png")
    Image.new("RGBA", (12, 12), (255, 255, 255, 255)).save(exports / f"{name}.tif")
    (exports / f"{name}.svg").write_text(_minimal_svg_text(), encoding="utf-8")
    _materialize_audit_inputs(fixture)


def _materialize_audit_inputs(fixture: Path) -> None:
    name = fixture.name
    build = fixture / "build"
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": name,
                "render_pdf": f"build/{name}.pdf",
                "candidates": [],
                "total": 0,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    for filename in ("text_boundary_clash.json", "label_path_proximity.json"):
        (build / filename).write_text(
            json.dumps(
                {
                    "fixture": name,
                    "candidates": [],
                    "total": 0,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": name,
                "render_pdf": f"build/{name}.pdf",
                "source": "harness:empty",
                "candidates": [],
                "total": 0,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    crop_dir = build / "audit_crops"
    crop_dir.mkdir(parents=True, exist_ok=True)
    crop_path = crop_dir / "full_q1.png"
    Image.new("RGBA", (12, 12), (255, 255, 255, 255)).save(crop_path)
    (crop_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": name,
                "render_path": f"build/{name}.png",
                "required_crop_ids": ["full_q1"],
                "crops": [
                    {
                        "id": "full_q1",
                        "kind": "zoom_crop",
                        "source": "full_render",
                        "path": "build/audit_crops/full_q1.png",
                        "source_path": f"build/{name}.png",
                        "bbox_px": [0, 0, 12, 12],
                        "sha256": file_sha256(crop_path),
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _minimal_pdf_bytes() -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] /Resources << >> >>",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii"))
        chunks.append(payload + b"\n")
        chunks.append(b"endobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    chunks.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    chunks.append(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return b"".join(chunks)


def _minimal_svg_text() -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" '
        'viewBox="0 0 12 12">\n'
        '  <text id="label-main" x="2" y="8">demo</text>\n'
        "</svg>\n"
    )


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
            ),
            "operations": [
                {
                    "id": "R001",
                    "class": "label_micro_position",
                    "selector": {"kind": "element_id", "value": "label-main"},
                    "action": {"type": "translate", "dx": 1.5, "dy": -1.0, "unit": "px"},
                    "rationale": "Move the label by a bounded optical offset.",
                    "semantic_guard": {
                        "allowed": True,
                        "reason": "same label identity and same visual target",
                    },
                }
            ],
        },
    )
    return recipe_path


def _tiny_renderer(source_svg: Path, output_png: Path) -> None:
    color = (255, 255, 255, 255)
    if "polish" in source_svg.parts:
        color = (220, 230, 255, 255)
    Image.new("RGBA", (12, 12), color).save(output_png)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def run_positive_harness(
    *,
    work_dir: Path = DEFAULT_WORK_DIR,
    force: bool = False,
) -> dict[str, Any]:
    """Run the harness and return a JSON-serializable summary."""
    fixture = _copy_seed(work_dir, force=force)
    _materialize_exports(fixture)
    source_svg = fixture / "exports" / f"{FIXTURE}.svg"
    source_before = source_svg.read_text(encoding="utf-8")

    recipe_path = _write_recipe(fixture)
    polished_path = apply_svg_polish(recipe_path, example_dir=fixture, base_dir=REPO_ROOT)
    delta_manifest = build_svg_polish_delta_pack(
        fixture,
        recipe_path=recipe_path,
        renderer=_tiny_renderer,
        base_dir=REPO_ROOT,
    )
    semantic_diff = build_svg_semantic_diff_report(fixture)
    audit_path, manifest_path = write_handoff_files(
        fixture,
        reviewer="codex-harness",
        editor="agent_assisted",
        toolchain=[{"name": "svg_polish_positive_harness.py", "version": "v1"}],
        edit_classes=["label_micro_position"],
        reviewed_at="2026-06-01T00:00:00Z",
        notes="deterministic positive-path harness; visual-only label polish",
        semantic_change_declared=False,
        backport_required=False,
        force=False,
        base_dir=REPO_ROOT,
    )
    if source_svg.read_text(encoding="utf-8") != source_before:
        raise ValueError("source export SVG was mutated")

    status = infer_stage(fixture)
    driver = build_driver_summary(
        FIXTURE,
        mode="polish",
        goal="positive harness",
        repo_root=work_dir,
    )
    if status.get("final_artifact_state") != "FRESH":
        final_state = status.get("final_artifact_state")
        raise ValueError(f"expected final_artifact_state FRESH, got {final_state}")
    if driver.get("action") != "complete" or driver.get("stop_boundary") is not None:
        raise ValueError("expected polish driver complete with no stop boundary")

    return {
        "schema": SCHEMA,
        "fixture": FIXTURE,
        "work_dir": str(work_dir),
        "artifacts": {
            "recipe": _relative(recipe_path, work_dir),
            "polished_svg": _relative(polished_path, work_dir),
            "delta_manifest": _relative(delta_manifest, work_dir),
            "semantic_diff": _relative(semantic_diff, work_dir),
            "audit": _relative(audit_path, work_dir),
            "manifest": _relative(manifest_path, work_dir),
        },
        "status": {
            "render_state": status.get("render_state"),
            "export_state": status.get("export_state"),
            "final_artifact_kind": status.get("final_artifact_kind"),
            "final_artifact_state": status.get("final_artifact_state"),
            "final_ready": status.get("final_ready"),
        },
        "driver": {
            "action": driver.get("action"),
            "safe_command": driver.get("safe_command"),
            "stop_boundary": driver.get("stop_boundary"),
            "reason": driver.get("reason"),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_positive_harness(work_dir=args.work_dir, force=args.force)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
