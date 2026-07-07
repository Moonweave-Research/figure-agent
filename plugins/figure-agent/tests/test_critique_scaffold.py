from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

import critique_scaffold  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _fresh_status(path: Path) -> dict[str, object]:
    return {
        "stage": 4,
        "render_state": "FRESH",
        "critique_state": "MISSING",
        "exports_substate": "FRESH",
    }


def _write_fixture(workspace: Path, name: str = "critique_demo") -> Path:
    fixture = workspace / "examples" / name
    build = fixture / "build"
    crops = build / "audit_crops"
    crops.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"""
name: {name}
panels: []
style_profile: polymer-default
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("\\node at (0,0) {demo};\n", encoding="utf-8")
    (build / f"{name}.png").write_bytes(b"png demo\n")
    (build / f"{name}.pdf").write_bytes(b"%PDF demo\n")
    crop_path = crops / "full_q1.png"
    crop_path.write_bytes(b"crop\n")
    (crops / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": name,
                "render_path": f"build/{name}.png",
                "required_crop_ids": ["full_q1"],
                "crops": [
                    {
                        "id": "full_q1",
                        "path": "build/audit_crops/full_q1.png",
                        "kind": "zoom_crop",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return fixture


def test_critique_scaffold_writes_only_build_scaffold(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    monkeypatch.setattr(critique_scaffold.status, "infer_stage", _fresh_status)

    payload = critique_scaffold.build_critique_scaffold(
        "critique_demo",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    output = fixture / "build" / "critique_scaffold.md"
    assert payload["schema"] == critique_scaffold.SCHEMA
    assert payload["state"] == "ready"
    assert payload["crop_audit"]["required_crop_ids"] == ["full_q1"]
    assert payload["mutation_boundary"] == (
        "writes_build_scaffold_only_no_critique_or_acceptance_state"
    )
    assert output.is_file()
    assert "verdict: TODO" in output.read_text(encoding="utf-8")
    assert not (fixture / "critique.md").exists()
    assert not (fixture / "human_attestation.json").exists()


def test_critique_scaffold_requires_fresh_render(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    def stale_status(path: Path) -> dict[str, object]:
        return {**_fresh_status(path), "render_state": "STALE"}

    monkeypatch.setattr(critique_scaffold.status, "infer_stage", stale_status)

    result = critique_scaffold.main(
        ["critique_demo", "--json"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert result == 1
    output = workspace / "examples" / "critique_demo" / "build" / "critique_scaffold.md"
    assert not output.exists()


def test_critique_scaffold_no_write_keeps_workspace_unchanged(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    monkeypatch.setattr(critique_scaffold.status, "infer_stage", _fresh_status)

    payload = critique_scaffold.build_critique_scaffold(
        "critique_demo",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
        write=False,
    )

    assert payload["output_path"] == "build/critique_scaffold.md"
    assert not (fixture / "build" / "critique_scaffold.md").exists()


def test_critique_scaffold_cli_outputs_json(tmp_path: Path) -> None:
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
            "critique-scaffold",
            "critique_demo",
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
    assert payload["schema"] == critique_scaffold.SCHEMA
    assert payload["crop_audit"]["required_count"] == 1
