from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_defect_ledger  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(workspace: Path, name: str = "quality_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: quality_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _write_text_boundary_report(fixture: Path, candidate_id: str = "TB001") -> None:
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": fixture.name,
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_vertical_boundary",
                        "text": "Old Label",
                        "boundary_id": "column_rule",
                    }
                ],
                "total": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_quality_defect_ledger_is_read_only_and_deterministic(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    _write_text_boundary_report(fixture)
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    first = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    second = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert first == second
    assert first["schema"] == "figure-agent.quality-defect-ledger.v1"
    assert first["fixture"] == "quality_demo"
    assert first["defects"][0]["id"] == "QD001"
    assert first["defects"][0]["evidence"] == [
        {
            "uri": "figure://quality_demo/audit/text-boundary",
            "node_id": "checker:text_boundary",
        }
    ]
    assert first["defects"][0]["patchability"]["state"] == "safe_candidate"
    assert first["defects"][0]["freshness"]["audit_evidence_graph_hash"].startswith(
        "sha256:"
    )
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_quality_defect_ledger_handles_missing_critique_without_raising(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert ledger["defects"]
    assert ledger["defects"][0]["defect_class"] == "render_missing"
    assert ledger["defects"][0]["owner"] == "human"
    assert ledger["defects"][0]["patchability"]["state"] == "human_required"


def test_quality_defect_ledger_blocks_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_fixture(workspace)
    outside = tmp_path / "outside.tex"
    outside.write_text("secret", encoding="utf-8")
    (fixture / "quality_demo.tex").unlink()
    (fixture / "quality_demo.tex").symlink_to(outside)

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "quality_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert ledger["defects"][0]["patchability"]["state"] == "unsupported"
    assert "path_escape" in ledger["defects"][0]["patchability"]["blocked_codes"]
