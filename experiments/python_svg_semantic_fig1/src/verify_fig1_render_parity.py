from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
SRC = Path(__file__).resolve().parent
SVG = ROOT / "fig1_reference_semantic.svg"

UV_RENDER_DEPS = (
    "drawsvg",
    "matplotlib",
    "numpy",
    "shapely",
    "svgelements",
    "svgpathtools",
)


def generated_svg_text(scene: Any | None = None) -> str:
    if scene is not None:
        from render_fig1_l1 import svg_text_for_scene

        return svg_text_for_scene(scene)
    return _generated_svg_text_via_uv()


def render_parity_failures(svg_path: str | Path = SVG, *, scene: Any | None = None) -> list[str]:
    expected_path = Path(svg_path)
    if not expected_path.exists():
        return [f"missing tracked Fig1 SVG for render parity: {expected_path}"]

    expected = expected_path.read_text()
    try:
        actual = generated_svg_text(scene)
    except Exception as exc:
        return [f"render parity generation failed: {exc}"]

    if actual == expected:
        return []

    expected_hash = hashlib.sha256(expected.encode()).hexdigest()
    actual_hash = hashlib.sha256(actual.encode()).hexdigest()
    return [
        "render parity mismatch: current source does not reproduce tracked Fig1 SVG "
        f"(tracked_sha256={expected_hash}, generated_sha256={actual_hash}, "
        f"tracked_len={len(expected)}, generated_len={len(actual)}, {_first_diff_summary(expected, actual)})"
    ]


def _generated_svg_text_via_uv() -> str:
    script = f"""
from pathlib import Path
import sys
sys.path.insert(0, {str(SRC)!r})
from fig1_l1_scene import build_scene
from render_fig1_l1 import svg_text_for_scene
print(svg_text_for_scene(build_scene()), end="")
"""
    command = ["uv", "run"]
    for dep in UV_RENDER_DEPS:
        command.extend(("--with", dep))
    command.extend(("python", "-c", script))
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(detail or f"uv render subprocess exited {result.returncode}")
    return result.stdout


def _first_diff_summary(expected: str, actual: str) -> str:
    for index, (expected_char, actual_char) in enumerate(zip(expected, actual, strict=False)):
        if expected_char != actual_char:
            return f"first_diff_index={index}, tracked={expected_char!r}, generated={actual_char!r}"
    return f"common_prefix_len={min(len(expected), len(actual))}"


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    failures = render_parity_failures(SVG)
    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}", file=sys.stderr)
        print(f"fig1 render parity failed: {len(failures)} issue(s)", file=sys.stderr)
        return 1

    print("fig1 render parity passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
