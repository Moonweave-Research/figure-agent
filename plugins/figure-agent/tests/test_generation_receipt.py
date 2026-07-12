from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from generation_receipt import record_generation_receipt  # noqa: E402


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_record_generation_receipt_binds_local_inputs_and_artifacts(tmp_path: Path) -> None:
    packet = tmp_path / "input_packet.yaml"
    budget = tmp_path / "budget_contract.yaml"
    starting = tmp_path / "starting.tex"
    generated = tmp_path / "generated.tex"
    run = tmp_path / "raw.yaml"
    packet.write_text("packet: Fig3\n", encoding="utf-8")
    budget.write_text("budget: one repair\n", encoding="utf-8")
    starting.write_text("start\n", encoding="utf-8")
    generated.write_text("generated\n", encoding="utf-8")
    run.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-ablation-run.v1",
                "variant": "raw",
                "input_packet_hash": _sha256(packet),
                "budget_contract_hash": _sha256(budget),
            }
        ),
        encoding="utf-8",
    )

    receipt = record_generation_receipt(
        run,
        model_id="codex-test",
        source_commit="0123456789abcdef",
        input_packet=packet,
        budget_contract=budget,
        starting_artifact=starting,
        generated_artifact=generated,
    )

    updated = yaml.safe_load(run.read_text(encoding="utf-8"))
    transcript = tmp_path / "raw.transcript.json"
    assert updated["generation_receipt"] == receipt
    assert receipt["transcript_path"] == transcript.name
    assert receipt["transcript_sha256"] == _sha256(transcript)
    assert receipt["starting_artifact_sha256"] == _sha256(starting)
    assert receipt["generated_artifact_sha256"] == _sha256(generated)
    assert json.loads(transcript.read_text(encoding="utf-8"))["model_id"] == "codex-test"
