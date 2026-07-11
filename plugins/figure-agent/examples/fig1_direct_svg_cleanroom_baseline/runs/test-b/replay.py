"""Render or verify the immutable Test B direct-SVG cycle artifacts."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[4]
RUN_ROOT = Path(__file__).resolve().parent
CONTRACT_ROOT = RUN_ROOT.parents[1] / "contract"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from direct_svg_candidate import render_candidate  # noqa: E402


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _safe_plugin_path(raw: str) -> Path:
    relative = Path(raw)
    candidate = (PLUGIN_ROOT / relative).resolve()
    if relative.is_absolute() or not candidate.is_relative_to(PLUGIN_ROOT):
        raise ValueError("path must be plugin-root-relative")
    return candidate


def _render(svg: str, png: str, width: int, height: int) -> None:
    result = render_candidate(
        _safe_plugin_path(svg),
        _safe_plugin_path(png),
        width=width,
        height=height,
        fontconfig_file=CONTRACT_ROOT / "fontconfig.xml",
    )
    print(yaml.safe_dump(result, sort_keys=False).strip())


def _verify() -> None:
    verified = 0
    with tempfile.TemporaryDirectory(prefix="figure-agent-test-b-replay-") as tmp:
        temp_root = Path(tmp)
        for panel in ("c", "f"):
            ledger_path = RUN_ROOT / f"panel-{panel}" / "ledger.yaml"
            ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
            for receipt in ledger["iterations"]:
                svg = RUN_ROOT / receipt["svg_path"]
                expected = RUN_ROOT / receipt["png_path"]
                replay = temp_root / panel / f"cycle-{receipt['cycle']:02d}.png"
                render_candidate(
                    svg,
                    replay,
                    width=receipt["render_width"],
                    height=receipt["render_height"],
                    fontconfig_file=CONTRACT_ROOT / "fontconfig.xml",
                )
                if _sha256(replay) != _sha256(expected):
                    raise RuntimeError(f"replay mismatch: {receipt['png_path']}")
                verified += 1
    print(f"replay verified: {verified}/6 deterministic renders")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("svg", nargs="?")
    parser.add_argument("png", nargs="?")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=640)
    args = parser.parse_args()
    if args.verify:
        _verify()
        return
    if not args.render or not args.svg or not args.png:
        parser.error("use --verify or --render SVG PNG")
    _render(args.svg, args.png, args.width, args.height)


if __name__ == "__main__":
    main()
