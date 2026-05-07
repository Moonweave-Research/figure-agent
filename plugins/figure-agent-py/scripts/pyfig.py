#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = REPO_ROOT / "experiments" / "python_svg_semantic_fig1"
SRC = EXPERIMENT / "src"
RENDER_DEPS = (
    "drawsvg",
    "matplotlib",
    "numpy",
    "rdkit",
    "shapely",
    "svgelements",
    "svgpathtools",
)
ARTIFACTS = (
    EXPERIMENT / "fig1_reference_semantic.svg",
    EXPERIMENT / "fig1_reference_semantic.png",
    EXPERIMENT / "reference_vs_fig1_reference_semantic.png",
    EXPERIMENT / "fig1_visual_judgment_report.md",
)


def _uv_python(script: Path) -> list[str]:
    command = ["uv", "run"]
    for dep in RENDER_DEPS:
        command.extend(("--with", dep))
    command.extend(("python", str(script)))
    return command


def _run(command: list[str]) -> int:
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return result.returncode


def render_fig1(_: argparse.Namespace) -> int:
    return _run(_uv_python(SRC / "render_fig1_l1.py"))


def verify_fig1(_: argparse.Namespace) -> int:
    return _run(_uv_python(SRC / "run_fig1_gates.py"))


def status_fig1(_: argparse.Namespace) -> int:
    print(f"figure-agent-py experiment: {EXPERIMENT}")
    missing = False
    for artifact in ARTIFACTS:
        if artifact.exists():
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()[:16]
            rel = artifact.relative_to(REPO_ROOT)
            print(f"present {rel} sha256:{digest}")
        else:
            missing = True
            print(f"missing {artifact.relative_to(REPO_ROOT)}")

    print("running Fig1 gates...")
    gate_status = verify_fig1(argparse.Namespace())
    if gate_status == 0 and not missing:
        print("figure-agent-py status: ready")
        return 0
    if gate_status == 0:
        print("figure-agent-py status: gates pass but artifacts are missing")
        return 1
    print("figure-agent-py status: gates failed")
    return gate_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="figure-agent-py command wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render-fig1", help="render Fig1 SVG/PNG artifacts")
    render.set_defaults(func=render_fig1)

    verify = sub.add_parser("verify-fig1", help="run Fig1 verifier gates")
    verify.set_defaults(func=verify_fig1)

    status = sub.add_parser("status-fig1", help="report artifacts and gates")
    status.set_defaults(func=status_fig1)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
