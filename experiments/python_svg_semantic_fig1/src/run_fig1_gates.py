from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_ROOT.parents[1]


@dataclass(frozen=True)
class Gate:
    name: str
    script: str


GATES = (
    Gate("semantics", "verify_fig1_semantics.py"),
    Gate("docs-manifest", "check_fig1_docs_manifest.py"),
    Gate("scaffold-contract", "verify_fig1_scaffold_contract.py"),
    Gate("causal-binding", "verify_fig1_causal_binding.py"),
    Gate("causal-visibility", "verify_fig1_causal_visibility.py"),
)


def _run_gate(gate: Gate) -> subprocess.CompletedProcess[str]:
    script_path = SRC / gate.script
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    failures: list[tuple[Gate, subprocess.CompletedProcess[str]]] = []
    for gate in GATES:
        result = _run_gate(gate)
        output = (result.stdout or result.stderr).strip().splitlines()
        summary = output[-1] if output else f"exit {result.returncode}"
        if result.returncode == 0:
            print(f"[PASS] {gate.name}: {summary}")
        else:
            print(f"[FAIL] {gate.name}: {summary}", file=sys.stderr)
            failures.append((gate, result))

    if not failures:
        print(f"fig1 gates passed: {len(GATES)}/{len(GATES)}")
        return 0

    print(f"fig1 gates failed: {len(failures)}/{len(GATES)}", file=sys.stderr)
    for gate, result in failures:
        print(f"\n--- {gate.name} stdout ---", file=sys.stderr)
        print((result.stdout or "").strip(), file=sys.stderr)
        print(f"--- {gate.name} stderr ---", file=sys.stderr)
        print((result.stderr or "").strip(), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
