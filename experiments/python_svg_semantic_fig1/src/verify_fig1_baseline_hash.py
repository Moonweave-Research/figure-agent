from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "fig1_reference_semantic.svg"
EXPECTED_HASH = "6d0a37bab6f9e79489101a84ea517a03a077e0cdb3a5d248e80e73815278f39b"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    if not SVG.exists():
        return _fail(f"missing rendered SVG: {SVG}")

    actual_hash = hashlib.sha256(SVG.read_bytes()).hexdigest()
    if actual_hash != EXPECTED_HASH:
        return _fail(
            f"fig1 baseline hash mismatch: expected {EXPECTED_HASH}, got {actual_hash}"
        )

    print(f"fig1 baseline hash passed: {actual_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
