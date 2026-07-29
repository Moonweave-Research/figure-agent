"""Write an auditable generation receipt for one failure-ablation run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
PACKET_SCHEMA = "figure-agent.authoring-execution-packet.v1"
RECEIPT_SCHEMA = "figure-agent.generation-receipt.v2"
NEUTRAL_TASK_START = "- Shared neutral authoring task (verbatim):\n\n"
NEUTRAL_TASK_END_MARKERS = (
    "\n\n- Required panels:",
    "\n\n## Provenance and publication boundary",
)


class GenerationReceiptError(ValueError):
    """Expected user-facing errors for invalid generation evidence."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _regular_file(path: Path, *, error: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise GenerationReceiptError(error)
    return path


def _adjacent_artifact(run_path: Path, artifact: Path, *, error: str) -> Path:
    _regular_file(artifact, error=error)
    if artifact.parent.resolve() != run_path.parent.resolve():
        raise GenerationReceiptError(error)
    return artifact


def _load_run(path: Path) -> dict[str, Any]:
    _regular_file(path, error="run_path_invalid")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != RUN_SCHEMA:
        raise GenerationReceiptError("run_schema_invalid")
    return payload


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_bound_authoring_packet(path: Path) -> tuple[dict[str, Any], str, str]:
    """Load packet JSON and recover the exact neutral task embedded by its prompt."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenerationReceiptError("input_packet_json_invalid") from exc
    if not isinstance(payload, dict) or payload.get("schema") != PACKET_SCHEMA:
        raise GenerationReceiptError("input_packet_schema_invalid")
    context_pack = payload.get("context_pack")
    if not isinstance(context_pack, dict):
        raise GenerationReceiptError("context_pack_binding_invalid")
    base_sha256 = context_pack.get("base_sha256")
    if not isinstance(base_sha256, str) or not base_sha256.startswith("sha256:"):
        raise GenerationReceiptError("context_pack_binding_invalid")
    prompt = payload.get("prompt")
    if not isinstance(prompt, dict) or not isinstance(prompt.get("utf8"), str):
        raise GenerationReceiptError("packet_prompt_invalid")
    prompt_text = prompt["utf8"]
    if prompt.get("sha256") != _sha256_bytes(prompt_text.encode("utf-8")):
        raise GenerationReceiptError("packet_prompt_hash_mismatch")
    if prompt_text.count(NEUTRAL_TASK_START) != 1:
        raise GenerationReceiptError("neutral_task_binding_invalid")
    task_start = prompt_text.index(NEUTRAL_TASK_START) + len(NEUTRAL_TASK_START)
    task_ends = [
        prompt_text.find(marker, task_start)
        for marker in NEUTRAL_TASK_END_MARKERS
        if prompt_text.find(marker, task_start) >= 0
    ]
    if not task_ends:
        raise GenerationReceiptError("neutral_task_binding_invalid")
    task = prompt_text[task_start : min(task_ends)]
    if not task.strip():
        raise GenerationReceiptError("neutral_task_binding_invalid")
    canonical_task = task.rstrip("\n") + "\n"
    return payload, _sha256_bytes(canonical_task.encode("utf-8")), base_sha256


def record_generation_receipt(
    run_path: Path,
    *,
    model_id: str,
    source_commit: str,
    input_packet: Path,
    budget_contract: Path,
    starting_artifact: Path,
    generated_artifact: Path,
) -> dict[str, str]:
    """Bind a run manifest to its local contract, artifacts, and transcript."""
    run_path = _regular_file(run_path, error="run_path_invalid")
    run = _load_run(run_path)
    if not model_id.strip() or not source_commit.strip():
        raise GenerationReceiptError("model_or_commit_missing")
    input_packet = _adjacent_artifact(
        run_path, input_packet, error="input_packet_invalid"
    )
    budget_contract = _regular_file(budget_contract, error="budget_contract_invalid")
    starting_artifact = _adjacent_artifact(
        run_path, starting_artifact, error="starting_artifact_invalid"
    )
    generated_artifact = _adjacent_artifact(
        run_path, generated_artifact, error="generated_artifact_invalid"
    )
    if run.get("input_packet_hash") != _sha256(input_packet):
        raise GenerationReceiptError("input_packet_hash_mismatch")
    if run.get("budget_contract_hash") != _sha256(budget_contract):
        raise GenerationReceiptError("budget_contract_hash_mismatch")
    packet, shared_task_sha256, context_pack_base_sha256 = (
        load_bound_authoring_packet(input_packet)
    )
    if packet.get("model_id") != model_id:
        raise GenerationReceiptError("model_id_mismatch")
    if run.get("shared_task_hash") != shared_task_sha256:
        raise GenerationReceiptError("shared_task_hash_mismatch")

    transcript_path = run_path.with_suffix(".transcript.json")
    if transcript_path.exists():
        raise GenerationReceiptError("transcript_already_exists")
    transcript = {
        "model_id": model_id,
        "input_packet_path": input_packet.name,
        "input_packet_sha256": _sha256(input_packet),
        "shared_task_sha256": shared_task_sha256,
        "shared_task_binding_source": (
            "input_packet.prompt.shared_neutral_authoring_task"
        ),
        "context_pack_base_sha256": context_pack_base_sha256,
        "budget_contract_sha256": _sha256(budget_contract),
        "source_commit": source_commit,
        "starting_artifact_path": starting_artifact.name,
        "starting_artifact_sha256": _sha256(starting_artifact),
        "generated_artifact_path": generated_artifact.name,
        "generated_artifact_sha256": _sha256(generated_artifact),
    }
    transcript_bytes = json.dumps(
        transcript, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    transcript_path.write_bytes(transcript_bytes)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        **transcript,
        "transcript_path": transcript_path.name,
        "transcript_sha256": _sha256(transcript_path),
    }
    run["generation_receipt"] = receipt
    run_path.write_text(yaml.safe_dump(run, sort_keys=False), encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generation-receipt")
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--input-packet", type=Path, required=True)
    parser.add_argument("--budget-contract", type=Path, required=True)
    parser.add_argument("--starting-artifact", type=Path, required=True)
    parser.add_argument("--generated-artifact", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = record_generation_receipt(
            args.run,
            model_id=args.model_id,
            source_commit=args.source_commit,
            input_packet=args.input_packet,
            budget_contract=args.budget_contract,
            starting_artifact=args.starting_artifact,
            generated_artifact=args.generated_artifact,
        )
    except GenerationReceiptError as exc:
        parser.error(str(exc))
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
