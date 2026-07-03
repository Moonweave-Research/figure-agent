from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import visual_quality_metrics  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _write_fixture(workspace: Path, name: str = "metrics_demo") -> Path:
    fixture = workspace / "examples" / name
    build = fixture / "build"
    crops = build / "audit_crops"
    crops.mkdir(parents=True)
    image = Image.new("RGB", (80, 60), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 40, 30), fill=(30, 30, 30))
    draw.line((0, 55, 79, 55), fill=(200, 0, 0), width=2)
    image.save(build / f"{name}.png")
    (build / "visual_clash.json").write_text(
        json.dumps({"total": 2, "candidates": [{"id": "VC001"}, {"id": "VC002"}]}) + "\n",
        encoding="utf-8",
    )
    (build / "text_boundary_clash.json").write_text(
        json.dumps({"candidates": [{"id": "TB001"}]}) + "\n",
        encoding="utf-8",
    )
    (build / "label_path_proximity.json").write_text(
        json.dumps({"total": 0, "candidates": []}) + "\n",
        encoding="utf-8",
    )
    (crops / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "required_crop_ids": ["full_q1", "print_thumbnail", "print_178mm"],
                "crops": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def test_visual_quality_metrics_writes_advisory_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)

    payload = visual_quality_metrics.build_visual_quality_metrics(
        "metrics_demo",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    output = fixture / "build" / "visual_quality_metrics.json"
    assert payload["schema"] == visual_quality_metrics.SCHEMA
    assert payload["policy"] == "advisory_only"
    assert payload["image"]["size_px"] == [80, 60]
    assert payload["image"]["ink_density"] > 0
    assert payload["detectors"]["visual_clash"]["candidate_count"] == 2
    assert payload["detectors"]["text_boundary"]["candidate_count"] == 1
    assert payload["crop_audit"]["required_count"] == 3
    assert payload["print_scale"]["state"] == "present"
    assert payload["scaffold_load"]["score"] == 6
    assert output.is_file()


def test_visual_quality_metrics_no_write(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)

    payload = visual_quality_metrics.build_visual_quality_metrics(
        "metrics_demo",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
        write=False,
    )

    assert payload["state"] == "measured"
    assert not (fixture / "build" / "visual_quality_metrics.json").exists()


def test_visual_quality_metrics_requires_build_png(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    (fixture / "build" / "metrics_demo.png").unlink()

    result = visual_quality_metrics.main(
        ["metrics_demo", "--json"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert result == 1


def test_visual_metrics_cli_outputs_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "visual-metrics",
            "metrics_demo",
            "--json",
        ],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == visual_quality_metrics.SCHEMA
    assert payload["mutation_boundary"] == "writes_build_metrics_only_no_gate_state"
