"""Record immutable, prospective Figure Agent evidence without claiming acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

SCHEMA = "figure-agent.prospective-evidence-receipt.v1"
REQUIRED_SINGLETON_ROLES = {
    "strict_compile_report",
    "render",
    "audit_crop_manifest",
    "critique",
    "adjudication",
}
REPEATED_ROLES = {"audit_crop", "export"}
OPTIONAL_SINGLETON_ROLES = {"human_verdict"}
ALLOWED_ROLES = REQUIRED_SINGLETON_ROLES | REPEATED_ROLES | OPTIONAL_SINGLETON_ROLES


class ProspectiveEvidenceReceiptError(ValueError):
    """Raised when prospective evidence cannot be recorded safely."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(payload: dict[str, Any]) -> str:
    return _sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    )


def _relative(value: str, *, label: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ProspectiveEvidenceReceiptError(f"{label}_path_invalid")
    return path


def _reject_symlink_chain(root: Path, relative: PurePosixPath, *, label: str) -> Path:
    if root.is_symlink():
        raise ProspectiveEvidenceReceiptError("fixture_root_symlink")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ProspectiveEvidenceReceiptError(f"{label}_symlink")
    try:
        current.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ProspectiveEvidenceReceiptError(f"{label}_path_escape") from exc
    return current


def _read_regular(root: Path, relative: PurePosixPath, *, label: str) -> tuple[Path, bytes]:
    path = _reject_symlink_chain(root, relative, label=label)
    if not path.is_file():
        raise ProspectiveEvidenceReceiptError(f"{label}_missing")
    return path, path.read_bytes()


def _fingerprint(path: Path, data: bytes) -> dict[str, int | str]:
    stat = path.stat(follow_symlinks=False)
    return {
        "sha256": _sha256(data),
        "size_bytes": len(data),
        "device": stat.st_dev,
        "inode": stat.st_ino,
        "mtime_ns": stat.st_mtime_ns,
    }


def _load_declaration(data: bytes, *, suffix: str) -> dict[str, Any]:
    try:
        loaded = json.loads(data) if suffix.lower() == ".json" else yaml.safe_load(data)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ProspectiveEvidenceReceiptError("declaration_invalid") from exc
    if not isinstance(loaded, dict):
        raise ProspectiveEvidenceReceiptError("declaration_invalid")
    return loaded


def _validate_declaration(payload: dict[str, Any]) -> list[dict[str, str]]:
    fixture = payload.get("fixture")
    compile_record = payload.get("compile")
    expected_command = (
        f"FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/{fixture}/{fixture}.tex"
    )
    if (
        not isinstance(fixture, str)
        or not fixture
        or "/" in fixture
        or not isinstance(compile_record, dict)
        or compile_record.get("command") != expected_command
        or compile_record.get("strict") is not True
        or type(compile_record.get("returncode")) is not int
        or compile_record.get("returncode") != 0
        or payload.get("publication_acceptance") != "not_claimed"
    ):
        raise ProspectiveEvidenceReceiptError("strict_facts_invalid")
    correction = payload.get("correction")
    if not isinstance(correction, dict) or correction.get("state") not in {
        "measured",
        "not_captured",
    }:
        raise ProspectiveEvidenceReceiptError("correction_invalid")
    minutes = correction.get("minutes")
    if correction["state"] == "measured":
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or minutes < 0:
            raise ProspectiveEvidenceReceiptError("correction_invalid")
    elif minutes is not None:
        raise ProspectiveEvidenceReceiptError("correction_invalid")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ProspectiveEvidenceReceiptError("artifacts_invalid")
    normalized: list[dict[str, str]] = []
    roles: list[str] = []
    paths: list[str] = []
    for item in artifacts:
        if not isinstance(item, dict) or set(item) != {"role", "path"}:
            raise ProspectiveEvidenceReceiptError("artifact_record_invalid")
        role, path = item["role"], item["path"]
        if role not in ALLOWED_ROLES or not isinstance(path, str):
            raise ProspectiveEvidenceReceiptError("artifact_record_invalid")
        normalized.append({"role": role, "path": _relative(path, label="artifact").as_posix()})
        roles.append(role)
        paths.append(path)
    if len(paths) != len(set(paths)):
        raise ProspectiveEvidenceReceiptError("artifact_path_duplicate")
    if any(roles.count(role) != 1 for role in REQUIRED_SINGLETON_ROLES):
        raise ProspectiveEvidenceReceiptError("artifact_role_cardinality_invalid")
    if any(roles.count(role) < 1 for role in REPEATED_ROLES):
        raise ProspectiveEvidenceReceiptError("artifact_role_cardinality_invalid")
    if any(roles.count(role) > 1 for role in OPTIONAL_SINGLETON_ROLES):
        raise ProspectiveEvidenceReceiptError("artifact_role_cardinality_invalid")
    return normalized


def _ensure_output_parent(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ProspectiveEvidenceReceiptError("output_ancestor_symlink")
        if current.exists() and not current.is_dir():
            raise ProspectiveEvidenceReceiptError("output_ancestor_invalid")
        if not current.exists():
            current.mkdir()
    return current


def record(*, fixture_dir: Path, declaration: str, output_dir: str) -> dict[str, Any]:
    if fixture_dir.is_symlink():
        raise ProspectiveEvidenceReceiptError("fixture_root_symlink")
    root = fixture_dir.resolve(strict=True)
    declaration_relative = _relative(declaration, label="declaration")
    output_relative = _relative(output_dir, label="output")
    declaration_path, declaration_bytes = _read_regular(
        root, declaration_relative, label="declaration"
    )
    declaration_fingerprint = _fingerprint(declaration_path, declaration_bytes)
    payload = _load_declaration(declaration_bytes, suffix=declaration_path.suffix)
    artifacts = _validate_declaration(payload)
    output = _reject_symlink_chain(root, output_relative, label="output")
    if output.exists() or output.is_symlink():
        raise ProspectiveEvidenceReceiptError("output_exists")

    sources: list[tuple[dict[str, str], Path, bytes, dict[str, int | str]]] = []
    for artifact in artifacts:
        path, data = _read_regular(root, PurePosixPath(artifact["path"]), label="artifact")
        sources.append((artifact, path, data, _fingerprint(path, data)))
    strict_data = next(
        data
        for item, _path, data, _fingerprint_value in sources
        if item["role"] == "strict_compile_report"
    )
    try:
        strict_report = json.loads(strict_data)
    except json.JSONDecodeError as exc:
        raise ProspectiveEvidenceReceiptError("strict_report_invalid") from exc
    if (
        not isinstance(strict_report, dict)
        or strict_report.get("strict") is not True
        or strict_report.get("returncode") != 0
    ):
        raise ProspectiveEvidenceReceiptError("strict_report_invalid")

    parent = _ensure_output_parent(root, output_relative)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=parent))
    try:
        artifact_records: list[dict[str, Any]] = []
        snapshot_root = staging / "artifacts"
        snapshot_root.mkdir()
        for index, (artifact, source, data, fingerprint) in enumerate(sources):
            snapshot_relative = Path("artifacts") / f"{index:03d}-{artifact['role']}-{source.name}"
            snapshot = staging / snapshot_relative
            snapshot.write_bytes(data)
            artifact_records.append(
                {
                    **artifact,
                    "sha256": fingerprint["sha256"],
                    "size_bytes": fingerprint["size_bytes"],
                    "snapshot_path": snapshot_relative.as_posix(),
                }
            )
        declaration_snapshot = staging / "source-declaration" / declaration_path.name
        declaration_snapshot.parent.mkdir()
        declaration_snapshot.write_bytes(declaration_bytes)
        receipt: dict[str, Any] = {
            "schema": SCHEMA,
            "fixture": payload["fixture"],
            "compile": payload["compile"],
            "source_declaration": {
                "path": declaration_relative.as_posix(),
                "sha256": _sha256(declaration_bytes),
                "snapshot_path": declaration_snapshot.relative_to(staging).as_posix(),
            },
            "artifacts": artifact_records,
            "correction": payload["correction"],
            "publication_acceptance": "not_claimed",
        }
        receipt["receipt_sha256"] = _canonical_hash(receipt)
        (staging / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # The final barrier is deliberately after every staged write.
        _, final_declaration = _read_regular(root, declaration_relative, label="declaration")
        if final_declaration != declaration_bytes:
            raise ProspectiveEvidenceReceiptError("source_declaration_drift")
        if _fingerprint(declaration_path, final_declaration) != declaration_fingerprint:
            raise ProspectiveEvidenceReceiptError("source_declaration_drift")
        for artifact, _path, _expected, expected_fingerprint in sources:
            final_path, actual = _read_regular(
                root, PurePosixPath(artifact["path"]), label="artifact"
            )
            if _fingerprint(final_path, actual) != expected_fingerprint:
                raise ProspectiveEvidenceReceiptError("source_artifact_drift")
        if output.exists() or output.is_symlink():
            raise ProspectiveEvidenceReceiptError("output_exists")
        os.replace(staging, output)
        return receipt
    finally:
        if staging.is_dir() and not staging.is_symlink():
            shutil.rmtree(staging)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-dir", type=Path, required=True)
    parser.add_argument("--declaration", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    result = record(
        fixture_dir=args.fixture_dir,
        declaration=args.declaration,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
