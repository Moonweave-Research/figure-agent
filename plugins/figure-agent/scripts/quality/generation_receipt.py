"""Write an auditable generation receipt for one failure-ablation run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
RECEIPT_SCHEMA = "figure-agent.generation-receipt.v1"


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
    input_packet = _regular_file(input_packet, error="input_packet_invalid")
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

    transcript_path = run_path.with_suffix(".transcript.json")
    if transcript_path.exists():
        raise GenerationReceiptError("transcript_already_exists")
    transcript = {
        "model_id": model_id,
        "input_packet_sha256": _sha256(input_packet),
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
