"""Resolve an explicitly declared, content-bound custom preamble."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from inputs import parse_spec

COLOR_DEFINITION = re.compile(
    r"\\definecolor\{([A-Za-z][A-Za-z0-9]*)\}\{(RGB|rgb|HTML)\}\{[^{}]+\}"
)


def resolve_style(example_dir: Path, default: Path) -> tuple[Path, tuple[str, ...]]:
    spec_path = example_dir / "spec.yaml"
    spec = parse_spec(spec_path.read_text()) if spec_path.is_file() else {}
    contract = spec.get("style_lock")
    if contract is None:
        return default, ()
    if not isinstance(contract, dict) or set(contract) - {
        "preamble",
        "sha256",
        "source_color_definitions",
    }:
        raise ValueError("style_lock must declare preamble, sha256 and source_color_definitions")
    name = contract.get("preamble")
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("style_lock.preamble must be a fixture-relative .sty path")
    path = (example_dir / name).resolve()
    if (
        not path.is_relative_to(example_dir.resolve())
        or path.suffix != ".sty"
        or not path.is_file()
    ):
        raise ValueError("style_lock.preamble must be an existing .sty inside the fixture")
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    if contract.get("sha256") != digest:
        raise ValueError("style_lock.preamble hash mismatch")
    definitions = contract.get("source_color_definitions", [])
    if not isinstance(definitions, list) or any(
        not isinstance(value, str) or COLOR_DEFINITION.fullmatch(value) is None
        for value in definitions
    ):
        raise ValueError(
            "style_lock.source_color_definitions must contain exact color declarations"
        )
    names = [COLOR_DEFINITION.fullmatch(value).group(1) for value in definitions]
    if len(names) != len(set(names)):
        raise ValueError("style_lock.source_color_definitions has duplicate color names")
    return path, tuple(definitions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("example", type=Path)
    parser.add_argument("default", type=Path)
    args = parser.parse_args()
    print(resolve_style(args.example, args.default)[0])
