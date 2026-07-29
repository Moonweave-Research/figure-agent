from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from generation_receipt import (  # noqa: E402
    GenerationReceiptError,
    record_generation_receipt,
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write_fixture(tmp_path: Path) -> dict[str, Path]:
    packet = tmp_path / "input_packet.json"
    budget = tmp_path / "budget_contract.yaml"
    starting = tmp_path / "starting.tex"
    generated = tmp_path / "generated.tex"
    run = tmp_path / "raw.yaml"
    neutral_task = "Author a neutral first-pass schematic for the declared topic.\n"
    prompt = (
        "# Bound raw authoring execution\n\n"
        "## Neutral authoring task\n"
        f"{neutral_task}"
        "\n## Provenance and publication boundary\n"
    )
    packet_payload = {
        "schema": "figure-agent.authoring-execution-packet.v1",
        "model_id": "codex-test",
        "context_pack": {
            "schema": "figure-agent.authoring-context-pack.v1",
            "base_sha256": "sha256:" + "a" * 64,
        },
        "prompt": {
            "utf8": prompt,
            "sha256": _sha256_bytes(prompt.encode("utf-8")),
        },
    }
    packet.write_text(json.dumps(packet_payload), encoding="utf-8")
    budget.write_text("budget: one repair\n", encoding="utf-8")
    starting.write_text("start\n", encoding="utf-8")
    generated.write_text("generated\n", encoding="utf-8")
    run.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.failure-ablation-run.v1",
                "variant": "raw",
                "shared_task_hash": _sha256_bytes(neutral_task.encode("utf-8")),
                "input_packet_hash": _sha256(packet),
                "budget_contract_hash": _sha256(budget),
            }
        ),
        encoding="utf-8",
    )
    return {
        "packet": packet,
        "budget": budget,
        "starting": starting,
        "generated": generated,
        "run": run,
    }


def _record(paths: dict[str, Path], *, model_id: str = "codex-test") -> dict[str, str]:
    return record_generation_receipt(
        paths["run"],
        model_id=model_id,
        source_commit="0123456789abcdef",
        input_packet=paths["packet"],
        budget_contract=paths["budget"],
        starting_artifact=paths["starting"],
        generated_artifact=paths["generated"],
    )


def test_record_generation_receipt_binds_packet_task_and_artifacts(
    tmp_path: Path,
) -> None:
    paths = _write_fixture(tmp_path)

    receipt = _record(paths)

    updated = yaml.safe_load(paths["run"].read_text(encoding="utf-8"))
    transcript = tmp_path / "raw.transcript.json"
    assert updated["generation_receipt"] == receipt
    assert receipt["schema"] == "figure-agent.generation-receipt.v2"
    assert receipt["input_packet_path"] == "input_packet.json"
    assert receipt["input_packet_sha256"] == _sha256(paths["packet"])
    assert receipt["shared_task_sha256"] == updated["shared_task_hash"]
    assert receipt["shared_task_binding_source"] == (
        "input_packet.prompt.neutral_authoring_task"
    )
    assert receipt["context_pack_base_sha256"] == "sha256:" + "a" * 64
    assert receipt["transcript_path"] == transcript.name
    assert receipt["transcript_sha256"] == _sha256(transcript)
    assert receipt["starting_artifact_sha256"] == _sha256(paths["starting"])
    assert receipt["generated_artifact_sha256"] == _sha256(paths["generated"])
    persisted = json.loads(transcript.read_text(encoding="utf-8"))
    assert persisted["model_id"] == "codex-test"
    assert persisted["shared_task_sha256"] == updated["shared_task_hash"]


def test_record_generation_receipt_rejects_model_mismatch(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)

    with pytest.raises(GenerationReceiptError, match="model_id_mismatch"):
        _record(paths, model_id="different-model")


def test_record_generation_receipt_rejects_shared_task_mismatch(
    tmp_path: Path,
) -> None:
    paths = _write_fixture(tmp_path)
    run = yaml.safe_load(paths["run"].read_text(encoding="utf-8"))
    run["shared_task_hash"] = "sha256:" + "b" * 64
    paths["run"].write_text(yaml.safe_dump(run), encoding="utf-8")

    with pytest.raises(GenerationReceiptError, match="shared_task_hash_mismatch"):
        _record(paths)


def test_record_generation_receipt_rejects_non_json_packet(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    paths["packet"].write_text("packet: legacy-yaml\n", encoding="utf-8")
    run = yaml.safe_load(paths["run"].read_text(encoding="utf-8"))
    run["input_packet_hash"] = _sha256(paths["packet"])
    paths["run"].write_text(yaml.safe_dump(run), encoding="utf-8")

    with pytest.raises(GenerationReceiptError, match="input_packet_json_invalid"):
        _record(paths)


def test_record_generation_receipt_rejects_non_adjacent_packet(
    tmp_path: Path,
) -> None:
    paths = _write_fixture(tmp_path)
    outside = tmp_path / "outside" / "outside.json"
    outside.parent.mkdir()
    outside.write_bytes(paths["packet"].read_bytes())

    with pytest.raises(GenerationReceiptError, match="input_packet_invalid"):
        record_generation_receipt(
            paths["run"],
            model_id="codex-test",
            source_commit="0123456789abcdef",
            input_packet=outside,
            budget_contract=paths["budget"],
            starting_artifact=paths["starting"],
            generated_artifact=paths["generated"],
        )
