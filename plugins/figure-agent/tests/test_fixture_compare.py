from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

import fixture_compare  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _tree(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))


def _write_fixture(workspace: Path, name: str, *, with_critique: bool = False) -> Path:
    fixture = workspace / "examples" / name
    build = fixture / "build"
    exports = fixture / "exports"
    build.mkdir(parents=True)
    exports.mkdir()
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
    for path, content in (
        (build / f"{name}.pdf", b"%PDF demo\n"),
        (build / f"{name}.png", b"png demo\n"),
        (exports / f"{name}.pdf", b"%PDF export\n"),
        (exports / f"{name}.svg", b"<svg />\n"),
        (exports / f"{name}.png", b"png export\n"),
        (exports / f"{name}.tif", b"tif export\n"),
    ):
        path.write_bytes(content)
    (build / "visual_clash.json").write_text(
        json.dumps({"fixture": name, "total": 0, "candidates": []}) + "\n",
        encoding="utf-8",
    )
    (build / "text_boundary_clash.json").write_text(
        json.dumps({"fixture": name, "total": 0, "candidates": []}) + "\n",
        encoding="utf-8",
    )
    (build / "label_path_proximity.json").write_text(
        json.dumps({"fixture": name, "total": 0, "candidates": []}) + "\n",
        encoding="utf-8",
    )
    (build / "visual_quality_metrics.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.fixture-visual-quality-metrics.v1",
                "state": "measured",
                "image": {"ink_density": 0.12, "edge_density": 0.03},
                "scaffold_load": {"score": 4, "level": "low"},
                "crop_audit": {"required_count": 2},
                "print_scale": {"state": "present"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    if with_critique:
        (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    old = time.time() - 100
    for source in (fixture / "spec.yaml", fixture / "briefing.md", fixture / f"{name}.tex"):
        os.utime(source, (old, old))
    return fixture


def _fresh_status(path: Path) -> dict[str, object]:
    return {
        "stage": 4,
        "render_state": "FRESH",
        "export_state": "FRESH",
        "exports_substate": "FRESH",
        "critique_state": "MISSING",
        "acceptance_state": "NOT_DECLARED",
        "accepted": None,
        "final_ready": False,
        "release_ready": False,
        "next": f"run /fig_critique {path.name}",
        "notes": ["critique_missing"],
    }


def test_compare_packet_is_read_only_and_blocks_on_missing_critique(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(fixture_compare.status, "infer_stage", _fresh_status)
    _write_fixture(workspace, "candidate_a")
    _write_fixture(workspace, "candidate_b")
    before = _tree(workspace)

    packet = fixture_compare.build_fixture_compare_packet(
        ["candidate_a", "candidate_b"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert packet["schema"] == fixture_compare.SCHEMA
    assert packet["mutation_boundary"] == "read_only_no_source_or_state_mutation"
    assert packet["recommendation"]["bucket"] == "needs_human_critique"
    assert packet["recommendation"]["fixtures"] == ["candidate_a", "candidate_b"]
    assert packet["fixtures"][0]["artifacts"]["exports"][1]["kind"] == "export_svg"
    assert packet["fixtures"][0]["artifacts"]["exports"][1]["sha256"].startswith("sha256:")
    assert packet["fixtures"][0]["audit_counts"]["visual_clash"] == {
        "present": True,
        "candidate_count": 0,
    }
    assert packet["fixtures"][0]["visual_metrics"] == {
        "state": "measured",
        "schema": "figure-agent.fixture-visual-quality-metrics.v1",
        "image": {"ink_density": 0.12, "edge_density": 0.03},
        "scaffold_load": {"score": 4, "level": "low"},
        "crop_audit": {"required_count": 2},
        "print_scale": {"state": "present"},
    }
    assert _tree(workspace) == before


def test_compare_packet_blocks_stale_or_incomplete_candidate(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"

    def status_for(path: Path) -> dict[str, object]:
        payload = _fresh_status(path)
        if path.name == "candidate_b":
            payload = {**payload, "render_state": "STALE", "notes": ["stale_render"]}
        return payload

    monkeypatch.setattr(fixture_compare.status, "infer_stage", status_for)
    _write_fixture(workspace, "candidate_a")
    _write_fixture(workspace, "candidate_b")

    packet = fixture_compare.build_fixture_compare_packet(
        ["candidate_a", "candidate_b"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert packet["recommendation"]["bucket"] == "blocked_stale_evidence"
    assert packet["recommendation"]["fixtures"] == ["candidate_b"]


def test_compare_fixtures_cli_outputs_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace, "candidate_a")
    _write_fixture(workspace, "candidate_b")

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "compare-fixtures",
            "candidate_a",
            "candidate_b",
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
    assert payload["schema"] == fixture_compare.SCHEMA
    assert [item["name"] for item in payload["fixtures"]] == ["candidate_a", "candidate_b"]


def test_compare_requires_two_fixtures(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace, "candidate_a")

    result = fixture_compare.main(
        ["candidate_a", "--json"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert result == 1
