from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from svg_polish_executor import (  # noqa: E402
    SvgPolishExecutorError,
    apply_svg_polish,
    main,
    plan_svg_polish,
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
        """<svg xmlns="http://www.w3.org/2000/svg">
  <g id="label-a"><text>Label A</text></g>
  <path id="line-a" stroke-width="1.0" opacity="0.5" fill-opacity="0.4" stroke-opacity="0.3" />
  <g id="class-a" class="tiny-detail"><circle /></g>
  <text id="unique-text">Unique</text>
</svg>
""",
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


def _recipe(fig_dir: Path, operations: list[dict]) -> dict:
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
        "operations": operations,
    }


def _operation(
    operation_id: str,
    *,
    selector: dict,
    action: dict,
    operation_class: str = "label_micro_position",
) -> dict:
    return {
        "id": operation_id,
        "class": operation_class,
        "selector": selector,
        "action": action,
        "rationale": "visual-only polish",
        "semantic_guard": {"allowed": True, "reason": "visual-only attribute edit"},
    }


def _write_recipe(fig_dir: Path, operations: list[dict]) -> Path:
    recipe_path = fig_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(recipe_path, _recipe(fig_dir, operations))
    return recipe_path


def test_dry_run_reports_planned_changes_and_writes_nothing(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "label-a"},
                action={"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
            )
        ],
    )

    plan = plan_svg_polish(recipe_path, example_dir=fig_dir)

    assert plan["target_svg"] == "polish/demo_fig.polished.svg"
    assert plan["write_required"] is True
    assert plan["changes"][0]["operation_id"] == "R001"
    assert plan["changes"][0]["matched_count"] == 1
    assert not (fig_dir / "polish" / "demo_fig.polished.svg").exists()


def test_write_mode_writes_only_polished_svg_and_preserves_source(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    source_path = fig_dir / "exports" / "demo_fig.svg"
    source_before = source_path.read_text(encoding="utf-8")
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "label-a"},
                action={"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
            )
        ],
    )

    output_path = apply_svg_polish(recipe_path, example_dir=fig_dir)

    assert output_path == fig_dir / "polish" / "demo_fig.polished.svg"
    assert source_path.read_text(encoding="utf-8") == source_before
    assert 'id="label-a"' in output_path.read_text(encoding="utf-8")
    assert 'transform="translate(1 -1.5)"' in output_path.read_text(encoding="utf-8")


def test_write_mode_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    (fig_dir / "polish" / "demo_fig.polished.svg").write_text("<svg />\n", encoding="utf-8")
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "label-a"},
                action={"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
            )
        ],
    )

    with pytest.raises(SvgPolishExecutorError, match="refusing to overwrite"):
        apply_svg_polish(recipe_path, example_dir=fig_dir)


@pytest.mark.parametrize(
    ("action", "expected"),
    (
        ({"type": "set_stroke_width", "value": 1.5}, 'stroke-width="1.5"'),
        ({"type": "set_opacity", "value": 0.8}, 'opacity="0.8"'),
        ({"type": "set_fill_opacity", "value": 0.7}, 'fill-opacity="0.7"'),
        ({"type": "set_stroke_opacity", "value": 0.6}, 'stroke-opacity="0.6"'),
    ),
)
def test_attribute_polish_actions_apply_bounded_numeric_changes(
    tmp_path: Path,
    action: dict,
    expected: str,
) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "line-a"},
                action=action,
                operation_class="stroke_polish",
            )
        ],
    )

    output_path = apply_svg_polish(recipe_path, example_dir=fig_dir)

    assert expected in output_path.read_text(encoding="utf-8")


def test_text_exact_selector_resolves_unique_text(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "text_exact", "value": "Unique"},
                action={"type": "translate", "dx": 0.0, "dy": 2.0, "unit": "px"},
            )
        ],
    )

    output_path = apply_svg_polish(recipe_path, example_dir=fig_dir)

    assert 'id="unique-text" transform="translate(0 2)"' in output_path.read_text(
        encoding="utf-8"
    )


def test_selector_resolving_zero_elements_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "missing"},
                action={"type": "translate", "dx": 1.0, "dy": 1.0, "unit": "px"},
            )
        ],
    )

    with pytest.raises(SvgPolishExecutorError, match="matched no SVG elements"):
        plan_svg_polish(recipe_path, example_dir=fig_dir)


def test_selector_resolving_too_many_elements_fails(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    source_path = fig_dir / "exports" / "demo_fig.svg"
    source_path.write_text(
        "<svg>"
        + "".join(f'<g id="d{i}" class="too-many" />' for i in range(6))
        + "</svg>\n",
        encoding="utf-8",
    )
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "css_class", "value": "too-many"},
                action={"type": "translate", "dx": 1.0, "dy": 1.0, "unit": "px"},
            )
        ],
    )

    with pytest.raises(SvgPolishExecutorError, match="matched too many SVG elements"):
        plan_svg_polish(recipe_path, example_dir=fig_dir)


@pytest.mark.parametrize(
    "action",
    (
        {"type": "translate", "dx": 11.0, "dy": 0.0, "unit": "px"},
        {"type": "set_opacity", "value": 1.5},
        {"type": "set_stroke_width", "value": 4.0},
    ),
)
def test_excessive_visual_change_fails(tmp_path: Path, action: dict) -> None:
    fig_dir = _make_fixture(tmp_path)
    recipe_path = _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "line-a"},
                action=action,
                operation_class="stroke_polish",
            )
        ],
    )

    with pytest.raises(SvgPolishExecutorError, match="exceeds"):
        plan_svg_polish(recipe_path, example_dir=fig_dir)


def test_cli_dry_run_prints_plan_and_writes_nothing(tmp_path: Path, capsys) -> None:
    fig_dir = _make_fixture(tmp_path)
    _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "label-a"},
                action={"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
            )
        ],
    )

    exit_code = main([str(fig_dir)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "dry-run" in output
    assert "R001" in output
    assert not (fig_dir / "polish" / "demo_fig.polished.svg").exists()


def test_cli_write_creates_polished_svg(tmp_path: Path) -> None:
    fig_dir = _make_fixture(tmp_path)
    _write_recipe(
        fig_dir,
        [
            _operation(
                "R001",
                selector={"kind": "element_id", "value": "label-a"},
                action={"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
            )
        ],
    )

    exit_code = main([str(fig_dir), "--write"])

    assert exit_code == 0
    assert (fig_dir / "polish" / "demo_fig.polished.svg").is_file()
