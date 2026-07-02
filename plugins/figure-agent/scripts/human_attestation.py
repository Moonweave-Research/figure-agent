"""Human attestation for publication release gates.

Threat model: this prevents release PASS by accident or by well-formed text
alone. A deliberate local actor who reads `~/.figure-agent/attest.key` and forges
an HMAC is out of scope, matching the repository's executor-allowlist boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.human-attestation.v1"


def _key_path() -> Path:
    return Path.home() / ".figure-agent" / "attest.key"


def _load_or_create_key() -> bytes:
    path = _key_path()
    if not path.exists():
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(secrets.token_bytes(32))
    path.chmod(0o600)
    return path.read_bytes()


def tex_sha256(example_dir: Path) -> str:
    fixture = example_dir.name
    fixture_identity.validate_fixture_name(fixture)
    tex_path = example_dir / f"{fixture}.tex"
    digest = hashlib.sha256()
    with tex_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _signature(fixture: str, tex_hash: str, key: bytes) -> str:
    message = f"{fixture}|{tex_hash}".encode()
    return "sha256:" + hmac.new(key, message, hashlib.sha256).hexdigest()


def write_attestation(example_dir: Path) -> dict[str, Any]:
    fixture = example_dir.name
    fixture_identity.validate_fixture_name(fixture)
    tex_hash = tex_sha256(example_dir)
    payload = {
        "schema": SCHEMA,
        "fixture": fixture,
        "tex_sha256": tex_hash,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "signature": _signature(fixture, tex_hash, _load_or_create_key()),
    }
    output = example_dir / "human_attestation.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify_attestation(example_dir: Path) -> tuple[bool, str]:
    path = example_dir / "human_attestation.json"
    if not path.is_file():
        return False, "missing_human_attestation"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "attestation_unreadable"
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return False, "schema_mismatch"

    fixture = example_dir.name
    if payload.get("fixture") != fixture:
        return False, "fixture_mismatch"
    try:
        current_hash = tex_sha256(example_dir)
    except (OSError, ValueError):
        return False, "tex_unreadable"
    if payload.get("tex_sha256") != current_hash:
        return False, "stale_tex_sha256"

    signature = payload.get("signature")
    if not isinstance(signature, str):
        return False, "bad_hmac"
    expected = _signature(fixture, current_hash, _load_or_create_key())
    if not hmac.compare_digest(signature, expected):
        return False, "bad_hmac"
    return True, "ok"


def _create(args: argparse.Namespace) -> int:
    if not sys.stdin.isatty():
        print("human attestation requires an interactive terminal", file=sys.stderr)
        return 1
    fixture = args.fixture
    fixture_identity.validate_fixture_name(fixture)
    example_dir = runtime_paths.resolve_runtime_paths().examples_dir / fixture
    print(f"Type {fixture} to attest the current source hash:", file=sys.stderr)
    typed = input("> ").strip()
    if typed != fixture:
        print("human attestation cancelled: fixture name mismatch", file=sys.stderr)
        return 1
    payload = write_attestation(example_dir)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="human_attestation.py")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("fixture")
    args = parser.parse_args(argv)
    if args.command == "create":
        return _create(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
