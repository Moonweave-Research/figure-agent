from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "fig1_reference_semantic.svg"
EXPECTED_HASH = "76c7976517daf457f7f996945c69d8fd75314113b3125076c41527b04b2ec946"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")

    actual_hash = hashlib.sha256(SVG.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_HASH:
        return _fail(f"fig1 baseline hash mismatch: expected {EXPECTED_HASH}, got {actual_hash}")

    print(f"fig1 baseline hash passed: {actual_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
