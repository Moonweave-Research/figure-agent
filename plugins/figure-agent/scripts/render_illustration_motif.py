from __future__ import annotations

import argparse
import hashlib
import platform
from pathlib import Path
from typing import Any

import yaml
from illustration_backend import IllustrationBackendError
from illustration_backend_svg import render_svg
from illustration_backend_tikz import render_tikz
from illustration_scene import compile_illustration_scene


def render_pair(
    grammar: Path,
    instance: Path,
    tikz_profile: Path,
    svg_profile: Path,
    output_dir: Path,
) -> dict[str, Any]:
    scene = compile_illustration_scene(grammar, instance)
    tikz_first = render_tikz(scene, tikz_profile)
    svg_first = render_svg(scene, svg_profile)
    if tikz_first != render_tikz(scene, tikz_profile) or svg_first != render_svg(
        scene, svg_profile
    ):
        raise IllustrationBackendError("render_nondeterministic")

    output_dir.mkdir(parents=True, exist_ok=True)
    tikz_path = output_dir / "sulfur_trap_domain.tikz.tex"
    svg_path = output_dir / "sulfur_trap_domain.svg"
    scene_path = output_dir / "sulfur_trap_domain.scene.yaml"
    tikz_path.write_text(tikz_first, encoding="utf-8")
    svg_path.write_text(svg_first, encoding="utf-8")
    scene_path.write_text(
        yaml.safe_dump(scene, sort_keys=True),
        encoding="utf-8",
    )
    source_paths = [
        Path(__file__),
        Path(__file__).with_name("illustration_backend.py"),
        Path(__file__).with_name("illustration_backend_tikz.py"),
        Path(__file__).with_name("illustration_backend_svg.py"),
        Path(__file__).with_name("illustration_scene.py"),
        Path(__file__).with_name("illustration_grammar.py"),
    ]
    manifest = {
        "schema": "figure-agent.illustration-render.v1",
        "motif_family": scene["motif_family"],
        "inputs": {
            "grammar": {"name": grammar.name, "sha256": _sha256(grammar)},
            "instance": {"name": instance.name, "sha256": _sha256(instance)},
            "tikz_profile": {"name": tikz_profile.name, "sha256": _sha256(tikz_profile)},
            "svg_profile": {"name": svg_profile.name, "sha256": _sha256(svg_profile)},
        },
        "sources": {path.name: _sha256(path) for path in source_paths},
        "toolchain": {"python": platform.python_version()},
        "artifacts": {
            "scene": {"path": scene_path.name, "sha256": _sha256(scene_path)},
            "tikz": {"path": tikz_path.name, "sha256": _sha256(tikz_path)},
            "svg": {"path": svg_path.name, "sha256": _sha256(svg_path)},
        },
        "publication_acceptance": "not_claimed",
    }
    manifest_path = output_dir / "render_manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=True), encoding="utf-8")
    return manifest


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render one illustration motif through both backends"
    )
    parser.add_argument("--grammar", type=Path, required=True)
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--tikz-profile", type=Path, required=True)
    parser.add_argument("--svg-profile", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    render_pair(
        args.grammar,
        args.instance,
        args.tikz_profile,
        args.svg_profile,
        args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
