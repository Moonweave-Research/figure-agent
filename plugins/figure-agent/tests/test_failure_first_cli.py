from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CLI = PLUGIN_ROOT / "bin" / "fig-agent"


def test_failure_corpus_cli_is_read_only() -> None:
    before = {
        path.relative_to(PLUGIN_ROOT): path.stat().st_mtime_ns
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file()
    }
    result = subprocess.run(
        [str(CLI), "failure-corpus", "--json"],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.llm-failure-corpus.v1"
    after = {
        path.relative_to(PLUGIN_ROOT): path.stat().st_mtime_ns
        for path in PLUGIN_ROOT.rglob("*")
        if path.is_file()
    }
    assert after == before


def _write_run(root: Path, variant: str, defect_count: int) -> Path:
    path = root / f"{variant}.yaml"
    payload = {
        "schema": "figure-agent.failure-ablation-run.v1",
        "variant": variant,
        "model_contract_hash": "sha256:" + "1" * 64,
        "input_packet_hash": "sha256:" + "2" * 64,
        "budget_contract_hash": "sha256:" + "3" * 64,
        "figure_family": "synthetic-cli",
        "findings": [
            {
                "id": f"TYPO-{index}",
                "failure_class": "typography",
                "review_outcome": "confirmed_defect",
            }
            for index in range(defect_count)
        ],
        "human_correction_minutes": None,
        "intervention_count": 0,
        "clean_reproduction": True,
        "human_verdict": {"state": "pending"},
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_failure_ablation_cli_keeps_acceptance_unclaimed(tmp_path: Path) -> None:
    paths = {
        "raw": _write_run(tmp_path, "raw", 2),
        "verified": _write_run(tmp_path, "verified", 2),
        "repaired": _write_run(tmp_path, "repaired", 1),
    }
    result = subprocess.run(
        [
            str(CLI),
            "failure-ablation",
            "--raw",
            str(paths["raw"]),
            "--verified",
            str(paths["verified"]),
            "--repaired",
            str(paths["repaired"]),
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.failure-ablation-report.v1"
    assert payload["publication_acceptance"] == "not_claimed"
