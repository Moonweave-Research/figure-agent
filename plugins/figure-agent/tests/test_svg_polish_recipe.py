from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

pytestmark = pytest.mark.quarantine

from svg_polish_recipe import (  # noqa: E402
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    SvgPolishRecipeError,
    load_svg_polish_recipe,
    main,
    svg_polish_recipe_input_hash,
    svg_polish_recipe_is_stale,
    svg_polish_recipe_template,
    validate_svg_polish_recipe,
    write_svg_polish_recipe,
)


def _make_fixture_at(root: Path, name: str = "demo_fig") -> Path:
    fig_dir = root / name
    (fig_dir / "exports").mkdir(parents=True)
    (fig_dir / "polish").mkdir()
    (fig_dir / "exports" / f"{name}.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="label-a">A</text></svg>\n',
        encoding="utf-8",
    )
    (fig_dir / "critique.md").write_text(
        "---\nschema: figure-agent.critique.v1.11\n---\n",
        encoding="utf-8",
    )
    (fig_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v2\n"
        "fixture: demo_fig\n"
        "aesthetic_levers:\n"
        "  - id: typography_authority\n",
        encoding="utf-8",
    )
    return fig_dir


def _make_fixture(tmp_path: Path, name: str = "demo_fig") -> Path:
    return _make_fixture_at(tmp_path / "examples", name)


def _valid_recipe(fig_dir: Path) -> dict:
    name = fig_dir.name
    return {
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
                "action": {"type": "translate", "dx": 0.0, "dy": -1.5, "unit": "px"},
                "rationale": "Move label optically without changing meaning.",
                "linked_aesthetic_lever": "typography_authority",
                "semantic_guard": {
                    "allowed": True,
                    "reason": "same label and target; sub-2px optical adjustment",
                },
                "future_note": "preserve me",
            }
        ],
        "future_top_level": {"preserve": True},
    }


def test_valid_recipe_loads_successfully(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    payload = _valid_recipe(fig_dir)
    write_svg_polish_recipe(recipe_path, payload)

    loaded = load_svg_polish_recipe(recipe_path, example_dir=fig_dir)

    assert loaded["fixture"] == "demo_fig"
    assert loaded["operations"][0]["id"] == "R001"
    assert loaded["operations"][0]["future_note"] == "preserve me"
    assert loaded["future_top_level"] == {"preserve": True}


def test_invalid_schema_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["schema"] = "figure-agent.svg-polish-recipe.v0"

    with pytest.raises(SvgPolishRecipeError, match="schema"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_malformed_yaml_fails_cleanly(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe_path.write_text("schema: [unterminated\n", encoding="utf-8")

    with pytest.raises(SvgPolishRecipeError, match="invalid YAML"):
        load_svg_polish_recipe(recipe_path, example_dir=fig_dir)


@pytest.mark.parametrize(
    ("field", "message"),
    (
        ("fixture", "fixture"),
        ("source_svg", "source_svg"),
        ("target_svg", "target_svg"),
        ("recipe_input_hash", "recipe_input_hash"),
        ("operations", "operations"),
    ),
)
def test_missing_required_top_level_fields_fail(
    tmp_path: Path,
    field: str,
    message: str,
) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    del payload[field]

    with pytest.raises(SvgPolishRecipeError, match=message):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_fixture_mismatch_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["fixture"] = "other_fig"

    with pytest.raises(SvgPolishRecipeError, match="fixture"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


@pytest.mark.parametrize(
    "source_svg",
    ("../demo.svg", "polish/demo.svg", "/tmp/demo.svg", "exports/../demo.svg"),
)
def test_source_svg_must_stay_under_exports(tmp_path: Path, source_svg: str) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["source_svg"] = source_svg

    with pytest.raises(SvgPolishRecipeError, match="source_svg"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_source_svg_must_be_canonical_export(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    # A real, divergent alternate export exists under exports/, so the path passes
    # the under-exports / suffix / is_file checks but is NOT the canonical export.
    (fig_dir / "exports" / "alt_source.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<text id="label-a" transform="translate(498,0)">A</text></svg>\n',
        encoding="utf-8",
    )
    payload = _valid_recipe(fig_dir)
    payload["source_svg"] = "exports/alt_source.svg"

    with pytest.raises(SvgPolishRecipeError, match="canonical"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


@pytest.mark.parametrize(
    "target_svg",
    ("../demo.svg", "exports/demo.svg", "/tmp/demo.svg", "polish/../demo.svg"),
)
def test_target_svg_must_stay_under_polish(tmp_path: Path, target_svg: str) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["target_svg"] = target_svg

    with pytest.raises(SvgPolishRecipeError, match="target_svg"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_duplicate_operation_ids_fail(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["operations"].append(dict(payload["operations"][0]))

    with pytest.raises(SvgPolishRecipeError, match="duplicate operation id"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_unknown_operation_class_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["operations"][0]["class"] = "semantic_rewrite"

    with pytest.raises(SvgPolishRecipeError, match="class"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_unknown_action_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["operations"][0]["action"]["type"] = "rewrite_path"

    with pytest.raises(SvgPolishRecipeError, match="action"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


@pytest.mark.parametrize(
    "operation_path",
    (
        ("selector",),
        ("selector", "kind"),
        ("selector", "value"),
        ("action",),
        ("action", "type"),
        ("semantic_guard",),
        ("semantic_guard", "allowed"),
        ("semantic_guard", "reason"),
        ("rationale",),
    ),
)
def test_missing_operation_required_fields_fail(
    tmp_path: Path,
    operation_path: tuple[str, ...],
) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    target = payload["operations"][0]
    for key in operation_path[:-1]:
        target = target[key]
    del target[operation_path[-1]]

    with pytest.raises(SvgPolishRecipeError):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_semantic_guard_must_allow_visual_only_polish(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    payload = _valid_recipe(fig_dir)
    payload["operations"][0]["semantic_guard"]["allowed"] = False

    with pytest.raises(SvgPolishRecipeError, match="semantic_guard.allowed"):
        validate_svg_polish_recipe(payload, example_dir=fig_dir)


def test_matching_input_hash_is_fresh(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(recipe_path, _valid_recipe(fig_dir))

    assert (
        svg_polish_recipe_is_stale(
            recipe_path,
            example_dir=fig_dir,
            base_dir=fig_dir.parent.parent,
        )
        is False
    )


def test_changed_source_svg_marks_recipe_stale(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(recipe_path, _valid_recipe(fig_dir))

    (fig_dir / "exports" / "demo_fig.svg").write_text("<svg>changed</svg>\n", encoding="utf-8")

    assert (
        svg_polish_recipe_is_stale(
            recipe_path,
            example_dir=fig_dir,
            base_dir=fig_dir.parent.parent,
        )
        is True
    )


def test_changed_aesthetic_intent_marks_recipe_stale(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(recipe_path, _valid_recipe(fig_dir))

    (fig_dir / "aesthetic_intent.yaml").write_text(
        "schema: figure-agent.aesthetic-intent.v2\nfixture: demo_fig\nchanged: true\n",
        encoding="utf-8",
    )

    assert (
        svg_polish_recipe_is_stale(
            recipe_path,
            example_dir=fig_dir,
            base_dir=fig_dir.parent.parent,
        )
        is True
    )


def test_writer_emits_reloadable_yaml_and_preserves_unknown_fields(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    payload = _valid_recipe(fig_dir)

    write_svg_polish_recipe(recipe_path, payload)

    raw = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
    assert raw["future_top_level"] == {"preserve": True}
    assert raw["operations"][0]["future_note"] == "preserve me"
    reloaded = load_svg_polish_recipe(recipe_path, example_dir=fig_dir)
    assert reloaded == raw


def test_svg_polish_recipe_template_emits_reloadable_fixture_specific_yaml(
    tmp_path: Path,
) -> None:
    fig_dir = _make_fixture(tmp_path)

    template = svg_polish_recipe_template(fig_dir, base_dir=fig_dir.parent.parent)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe_path.write_text(template, encoding="utf-8")

    loaded = load_svg_polish_recipe(recipe_path, example_dir=fig_dir)
    assert loaded["fixture"] == "demo_fig"
    assert loaded["source_svg"] == "exports/demo_fig.svg"
    assert loaded["target_svg"] == "polish/demo_fig.polished.svg"
    assert loaded["recipe_input_hash"] == svg_polish_recipe_input_hash(
        fig_dir,
        "demo_fig",
        source_svg="exports/demo_fig.svg",
        base_dir=fig_dir.parent.parent,
    )
    assert [operation["class"] for operation in loaded["operations"]] == [
        "label_micro_position",
        "stroke_polish",
        "typography_cleanup",
    ]


def test_svg_polish_recipe_template_cli_emits_fixture_template(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = _make_fixture(tmp_path)

    exit_code = main(["--template", str(fig_dir), "--base-dir", str(fig_dir.parent.parent)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "schema: figure-agent.svg-polish-recipe.v1" in captured.out
    assert "fixture: demo_fig" in captured.out
    assert "target_svg: polish/demo_fig.polished.svg" in captured.out


def test_svg_polish_recipe_template_reports_missing_export(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = _make_fixture(tmp_path)
    (fig_dir / "exports" / "demo_fig.svg").unlink()

    exit_code = main(["--template", str(fig_dir), "--base-dir", str(fig_dir.parent.parent)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "missing recipe.source_svg" in captured.err


def test_svg_polish_recipe_template_cli_can_write_canonical_recipe(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe_path.unlink(missing_ok=True)

    exit_code = main(
        [
            "--template",
            str(fig_dir),
            "--write-template",
            "--base-dir",
            str(fig_dir.parent.parent),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert f"wrote {SVG_POLISH_RECIPE_RELATIVE_PATH}" in captured.out
    assert recipe_path.is_file()
    assert load_svg_polish_recipe(recipe_path, example_dir=fig_dir)["fixture"] == "demo_fig"


def test_svg_polish_recipe_template_cli_refuses_overwrite_without_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(recipe_path, _valid_recipe(fig_dir))

    exit_code = main(
        [
            "--template",
            str(fig_dir),
            "--write-template",
            "--base-dir",
            str(fig_dir.parent.parent),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "refusing to overwrite" in captured.err


def test_template_write_rejects_parent_relative_fixture_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = _make_fixture_at(tmp_path, "outside")
    recipe_path = outside_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe_path.unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--template",
            "examples/../outside",
            "--write-template",
            "--base-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 1
    assert "invalid fixture path" in capsys.readouterr().err
    assert not recipe_path.exists()


def test_template_write_rejects_existing_relative_dir_outside_examples(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = _make_fixture_at(tmp_path, "outside")
    recipe_path = outside_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    recipe_path.unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--template",
            "outside",
            "--write-template",
            "--base-dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 1
    assert "invalid fixture path" in capsys.readouterr().err
    assert not recipe_path.exists()
