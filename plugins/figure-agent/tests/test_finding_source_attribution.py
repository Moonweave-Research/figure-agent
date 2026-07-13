from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import finding_source_attribution  # noqa: E402


def _sha256(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode()).hexdigest()}"


def _fixture(tmp_path: Path) -> tuple[Path, dict, dict]:
    source_text = (
        "\\node[title] {during conduction};\n"
        "% material:start\n"
        "\\node[note] {disordered sulfur polymer film};\n"
        "% material:end\n"
    )
    source = tmp_path / "figure.tex"
    source.write_text(source_text, encoding="utf-8")
    report = {
        "schema": "figure-agent.text-collisions.v1",
        "fixture": "demo",
        "collisions": [
            {
                "id": "TC001",
                "texts": ["disordered", "conduction"],
                "source_mapping": None,
            }
        ],
    }
    registry = {
        "schema": "figure-agent.source-selector-registry.v1",
        "source_path": "figure.tex",
        "source_sha256": _sha256(source_text),
        "selectors": [
            {
                "selector_id": "panel-a-title",
                "anchor_start": "\\node[title] {during conduction};",
                "anchor_end": "% material:start",
                "rendered_aliases": ["conduction"],
                "repair_role": "fixed",
            },
            {
                "selector_id": "panel-a-material-label",
                "anchor_start": "% material:start",
                "anchor_end": "% material:end",
                "rendered_aliases": ["disordered", "sulfur", "polymer", "film"],
                "repair_role": "movable",
                "repair_family": "local_reposition",
                "protected_invariants": ["during conduction"],
            },
        ],
    }
    return source, report, registry


def test_attributes_collision_to_only_declared_movable_selector(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)

    result = finding_source_attribution.attribute_findings(
        report,
        registry,
        source_path=source,
    )

    assert result["schema"] == "figure-agent.finding-source-attribution.v1"
    assert result["findings"] == [
        {
            "finding_id": "TC001",
            "state": "exact",
            "reason_code": "one_declared_movable_selector",
            "matched_selectors": [
                {
                    "selector_id": "panel-a-material-label",
                    "matched_texts": ["disordered"],
                    "repair_role": "movable",
                },
                {
                    "selector_id": "panel-a-title",
                    "matched_texts": ["conduction"],
                    "repair_role": "fixed",
                },
            ],
            "selected_selector_id": "panel-a-material-label",
        }
    ]


def test_fails_closed_when_two_movable_selectors_match(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    registry["selectors"][0]["repair_role"] = "movable"

    result = finding_source_attribution.attribute_findings(
        report,
        registry,
        source_path=source,
    )

    assert result["findings"][0]["state"] == "ambiguous"
    assert result["findings"][0]["selected_selector_id"] is None


def test_fails_closed_when_no_alias_matches(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    report["collisions"][0]["texts"] = ["unknown", "tokens"]

    result = finding_source_attribution.attribute_findings(
        report,
        registry,
        source_path=source,
    )

    assert result["findings"][0]["state"] == "unbound"
    assert result["findings"][0]["reason_code"] == "no_declared_alias_match"


def test_rejects_source_hash_drift(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    registry["source_sha256"] = "sha256:" + "0" * 64

    with pytest.raises(
        finding_source_attribution.SourceAttributionError,
        match="source hash",
    ):
        finding_source_attribution.attribute_findings(
            report,
            registry,
            source_path=source,
        )


def test_builds_existing_repair_target_contract_for_one_exact_finding(
    tmp_path: Path,
) -> None:
    source, report, registry = _fixture(tmp_path)
    attribution = finding_source_attribution.attribute_findings(
        report,
        registry,
        source_path=source,
    )

    contract = finding_source_attribution.build_repair_target_contract(
        report_path="reports/collisions.json",
        report=report,
        registry=registry,
        attribution=attribution,
        finding_id="TC001",
    )

    assert contract["schema"] == "figure-agent.repair-target-contract.v1"
    assert contract["source_path"] == "figure.tex"
    assert contract["targets"][0]["finding"] == {
        "report_path": "reports/collisions.json",
        "id": "TC001",
    }
    assert contract["targets"][0]["selector"]["selector_id"] == (
        "panel-a-material-label"
    )
    assert contract["targets"][0]["attribution"] == {"state": "exact"}


def test_cli_writes_attribution_and_target_contract(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    report_path = tmp_path / "collisions.json"
    registry_path = tmp_path / "selectors.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    rc = finding_source_attribution.main(
        [
            "--report",
            str(report_path),
            "--registry",
            str(registry_path),
            "--source",
            str(source),
            "--finding-id",
            "TC001",
            "--attribution-out",
            str(tmp_path / "attribution.json"),
            "--target-contract-out",
            str(tmp_path / "targets.json"),
        ]
    )

    assert rc == 0
    assert json.loads((tmp_path / "attribution.json").read_text())["summary"] == {
        "ambiguous": 0,
        "exact": 1,
        "unbound": 0,
    }
    assert json.loads((tmp_path / "targets.json").read_text())["targets"][0][
        "repair_family"
    ] == "local_reposition"


def test_fig_agent_routes_finding_attribution_command(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    report_path = tmp_path / "collisions.json"
    registry_path = tmp_path / "selectors.json"
    attribution_path = tmp_path / "attribution.json"
    target_path = tmp_path / "targets.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = subprocess.run(
        [
            str(Path(__file__).resolve().parents[1] / "bin" / "fig-agent"),
            "finding-attribution",
            "--report",
            str(report_path),
            "--registry",
            str(registry_path),
            "--source",
            str(source),
            "--finding-id",
            "TC001",
            "--attribution-out",
            str(attribution_path),
            "--target-contract-out",
            str(target_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert attribution_path.is_file()
    assert target_path.is_file()


def test_cli_refuses_to_overwrite_existing_attribution_artifact(tmp_path: Path) -> None:
    source, report, registry = _fixture(tmp_path)
    report_path = tmp_path / "collisions.json"
    registry_path = tmp_path / "selectors.json"
    attribution_path = tmp_path / "attribution.json"
    target_path = tmp_path / "targets.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    attribution_path.write_text("historical\n", encoding="utf-8")

    rc = finding_source_attribution.main(
        [
            "--report",
            str(report_path),
            "--registry",
            str(registry_path),
            "--source",
            str(source),
            "--finding-id",
            "TC001",
            "--attribution-out",
            str(attribution_path),
            "--target-contract-out",
            str(target_path),
        ]
    )

    assert rc == 1
    assert attribution_path.read_text(encoding="utf-8") == "historical\n"
    assert not target_path.exists()
