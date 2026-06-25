from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

pytestmark = pytest.mark.quarantine

import svg_polish_delta  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402
from svg_polish_delta import (  # noqa: E402
    SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH,
    SvgPolishDeltaError,
    build_svg_polish_delta_pack,
    load_svg_polish_delta_manifest,
    svg_polish_delta_is_stale,
)
from svg_polish_recipe import (  # noqa: E402
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    svg_polish_recipe_input_hash,
    write_svg_polish_recipe,
)


def _make_fixture(tmp_path: Path, name: str = "demo_fig") -> Path:
    fig_dir = tmp_path / "examples" / name
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "polish").mkdir()
    (fig_dir / "exports" / f"{name}.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="label-a">A</text></svg>\n',
        encoding="utf-8",
    )
    (fig_dir / "polish" / f"{name}.polished.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="label-a">A</text></svg>\n',
        encoding="utf-8",
    )
    (fig_dir / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.11\n---\n",
        encoding="utf-8",
    )
    (fig_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v2\nfixture: demo_fig\n",
        encoding="utf-8",
    )
    return fig_dir


def _write_recipe(fig_dir: Path) -> Path:
    name = fig_dir.name
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(
        recipe_path,
        {
            "schema": "figure-agent.svg-polish-recipe.v1",
            "fixture": name,
            "source_svg": f"exports/{name}.svg",
            "target_svg": f"polish/{name}.polished.svg",
            "recipe_input_hash": svg_polish_recipe_input_hash(
                fig_dir,
                name,
                source_svg=f"exports/{name}.svg",
                base_dir=fig_dir.parent.parent,
            ),
            "operations": [
                {
                    "id": "R001",
                    "class": "label_micro_position",
                    "selector": {"kind": "element_id", "value": "label-a"},
                    "action": {"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
                    "rationale": "visual-only polish",
                    "semantic_guard": {
                        "allowed": True,
                        "reason": "same label and target",
                    },
                }
            ],
        },
    )
    return recipe_path


def _fake_renderer(source_svg: Path, output_png: Path) -> None:
    color = (255, 0, 0, 255) if "exports" in source_svg.parts else (0, 0, 255, 255)
    Image.new("RGBA", (4, 4), color).save(output_png)


def test_delta_pack_generates_before_after_diff_and_manifest(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)

    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )

    assert manifest_path == fig_dir / SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH
    assert (fig_dir / "polish" / "aesthetic_delta" / "before.png").is_file()
    assert (fig_dir / "polish" / "aesthetic_delta" / "after.png").is_file()
    assert (fig_dir / "polish" / "aesthetic_delta" / "diff.png").is_file()
    manifest = load_svg_polish_delta_manifest(manifest_path, example_dir=fig_dir)
    assert manifest["operation_ids"] == ["R001"]
    assert manifest["artifacts"]["before_png"] == "polish/aesthetic_delta/before.png"


def test_delta_manifest_contains_current_hashes(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)

    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["source_svg_hash"] == file_sha256(fig_dir / "exports" / "demo_fig.svg")
    assert manifest["polished_svg_hash"] == file_sha256(
        fig_dir / "polish" / "demo_fig.polished.svg"
    )
    assert manifest["recipe_hash"] == file_sha256(recipe_path)
    assert svg_polish_delta_is_stale(manifest_path, example_dir=fig_dir) is False


def test_delta_manifest_contains_artifact_hashes_and_renderer_metadata(
    tmp_path: Path,
) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)

    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["artifact_hashes"] == {
        "before_png_hash": file_sha256(fig_dir / "polish" / "aesthetic_delta" / "before.png"),
        "after_png_hash": file_sha256(fig_dir / "polish" / "aesthetic_delta" / "after.png"),
        "diff_png_hash": file_sha256(fig_dir / "polish" / "aesthetic_delta" / "diff.png"),
    }
    assert manifest["renderer"]["executable"]
    assert manifest["renderer"]["version"]
    assert manifest["renderer"]["script_hash"].startswith("sha256:")


@pytest.mark.parametrize(
    "relative_path",
    (
        "polish/aesthetic_delta/before.png",
        "polish/aesthetic_delta/after.png",
        "polish/aesthetic_delta/diff.png",
    ),
)
def test_changed_delta_artifact_marks_delta_stale(
    tmp_path: Path,
    relative_path: str,
) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)
    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )

    Image.new("RGBA", (4, 4), (13, 17, 19, 255)).save(fig_dir / relative_path)

    assert svg_polish_delta_is_stale(manifest_path, example_dir=fig_dir) is True


def test_malformed_delta_artifact_hash_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)
    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact_hashes"]["before_png_hash"] = "sha256:not-a-real-hash"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SvgPolishDeltaError, match="before_png_hash"):
        load_svg_polish_delta_manifest(manifest_path, example_dir=fig_dir)


def test_stale_recipe_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)
    (fig_dir / "exports" / "demo_fig.svg").write_text("<svg>changed</svg>\n", encoding="utf-8")

    with pytest.raises(SvgPolishDeltaError, match="recipe is stale"):
        build_svg_polish_delta_pack(
            fig_dir,
            recipe_path=recipe_path,
            renderer=_fake_renderer,
            base_dir=fig_dir.parent.parent,
        )


def test_missing_polished_svg_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)
    (fig_dir / "polish" / "demo_fig.polished.svg").unlink()

    with pytest.raises(SvgPolishDeltaError, match="missing polished SVG"):
        build_svg_polish_delta_pack(
            fig_dir,
            recipe_path=recipe_path,
            renderer=_fake_renderer,
            base_dir=fig_dir.parent.parent,
        )


def test_changed_polished_svg_marks_delta_stale(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(fig_dir)
    manifest_path = build_svg_polish_delta_pack(
        fig_dir,
        recipe_path=recipe_path,
        renderer=_fake_renderer,
        base_dir=fig_dir.parent.parent,
    )

    (fig_dir / "polish" / "demo_fig.polished.svg").write_text(
        "<svg>changed polished</svg>\n",
        encoding="utf-8",
    )

    assert svg_polish_delta_is_stale(manifest_path, example_dir=fig_dir) is True


def test_missing_delta_manifest_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)

    with pytest.raises(SvgPolishDeltaError, match="missing SVG polish delta manifest"):
        load_svg_polish_delta_manifest(
            fig_dir / SVG_POLISH_DELTA_MANIFEST_RELATIVE_PATH,
            example_dir=fig_dir,
        )


def test_default_renderer_tolerates_nonutf8_stderr(monkeypatch, tmp_path: Path) -> None:
    # rsvg-convert/inkscape can emit non-UTF8 locale bytes on stderr; the real
    # subprocess.run(..., text=True) decode must not crash before the renderer
    # raises its own SvgPolishDeltaError on the non-zero exit.
    fake_root = tmp_path / "fake_repo"
    (fake_root / "scripts").mkdir(parents=True)
    stub = fake_root / "scripts" / "svg_to_png.sh"
    stub.write_text("printf '\\xff fontconfig warn\\n' >&2\nexit 1\n", encoding="utf-8")
    monkeypatch.setattr(svg_polish_delta, "REPO_ROOT", fake_root)

    source_svg = tmp_path / "in.svg"
    source_svg.write_text("<svg/>\n", encoding="utf-8")

    with pytest.raises(SvgPolishDeltaError, match="SVG render failed"):
        svg_polish_delta._default_renderer(source_svg, tmp_path / "out.png")
