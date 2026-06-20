from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import convention_receipt  # noqa: E402

REAL_FIXTURE = "fig1_overview_v2_pair_001_vault"


def _env_paths() -> dict[str, Path]:
    return {"plugin_root": PLUGIN_ROOT, "workspace_root": PLUGIN_ROOT}


def test_receipt_lists_project_conventions_with_source_quotes() -> None:
    payload = convention_receipt.build_convention_receipt(REAL_FIXTURE, **_env_paths())

    assert payload["schema"] == "figure-agent.convention-receipt.v1"
    assert payload["transfer_policy"] == "use_as_constraint"

    by_id = {rule["id"]: rule for rule in payload["conventions"]}
    cantilever = by_id["polymer_paper_project.cantilever-vertical-clip-top"]
    assert cantilever["scope"] == "project"
    assert cantilever["category"] == "instrument_standard"
    assert "vertical" in cantilever["rule"].lower()
    assert cantilever["source"]["locator"]
    assert cantilever["source"]["quote"] == "clip on TOP, polymer hangs down"
    assert cantilever["catalog"].endswith("authoring-rules-project.md")

    colour = by_id["polymer_paper_project.trap-colour-shallow-blue-deep-red"]
    assert colour["scope"] == "project"
    assert colour["source"]["quote"]


def test_receipt_payload_schema_and_structure() -> None:
    payload = convention_receipt.build_convention_receipt(REAL_FIXTURE, **_env_paths())

    assert payload["read_only"] is True
    assert payload["context_pack_schema"] == "figure-agent.authoring-context-pack.v1"
    assert payload["scope_boundary"]["render_verification"] is False
    assert payload["scope_boundary"]["injection_surface_only"] is True
    assert payload["scope_boundary"]["model_calls"] is False

    counts = payload["counts"]
    assert counts["total"] == counts["project"] + counts["fixture"]
    assert counts["total"] == len(payload["conventions"])
    assert counts["project"] >= 2
    assert counts["fixture"] >= 1

    for rule in payload["conventions"]:
        assert rule["transfer_policy"] == "use_as_constraint"
        assert rule["scope"] in {"project", "fixture"}
        assert rule["id"] and rule["category"] and rule["rule"]
        source = rule["source"]
        assert source["kind"] and source["locator"] and source["quote"]


def test_receipt_excludes_use_as_question_rules() -> None:
    payload = convention_receipt.build_convention_receipt(REAL_FIXTURE, **_env_paths())

    rule_ids = {rule["id"] for rule in payload["conventions"]}
    # pair001 carries use_as_question rules that must never reach the injection
    # receipt — only use_as_constraint conventions are propagated as constraints.
    assert "pair001.panel-c-reference-gap" not in rule_ids
    assert "pair001.panel-e-side-view-apparatus" not in rule_ids


def test_receipt_write_emits_build_artifacts(tmp_path: Path) -> None:
    name = "context_demo"
    fixture = tmp_path / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: context_demo\ntitle: Context Demo\npanels:\n  - id: C\n    caption: Trap\n",
        encoding="utf-8",
    )

    payload = convention_receipt.write_receipt(
        name,
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )

    receipt_json = fixture / "build" / "convention_receipt.json"
    receipt_md = fixture / "build" / "convention_receipt.md"
    assert receipt_json.is_file()
    assert receipt_md.is_file()

    on_disk = json.loads(receipt_json.read_text(encoding="utf-8"))
    assert on_disk == payload
    assert on_disk["schema"] == "figure-agent.convention-receipt.v1"
    # the project catalog is inherited by every fixture, so even a bare fixture
    # surfaces the cross-figure conventions in its receipt
    assert on_disk["counts"]["project"] >= 2

    text = receipt_md.read_text(encoding="utf-8")
    assert "Convention propagation receipt" in text
    assert "clip on TOP" in text


def test_receipt_cli_json(tmp_path: Path, capsys) -> None:
    name = "context_demo"
    fixture = tmp_path / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: context_demo\ntitle: Context Demo\npanels: []\n",
        encoding="utf-8",
    )
    os.environ.pop("FIGURE_AGENT_WORKSPACE", None)

    code = convention_receipt.main(
        [name, "--json"],
        plugin_root=PLUGIN_ROOT,
        workspace_root=tmp_path,
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["name"] == name
    assert out["schema"] == "figure-agent.convention-receipt.v1"
