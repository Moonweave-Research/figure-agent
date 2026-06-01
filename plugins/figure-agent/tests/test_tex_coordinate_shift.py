from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import tex_coordinate_shift as helper  # noqa: E402


def test_shift_literal_coordinates_inside_line_range_only() -> None:
    tex = "\n".join(
        [
            r"\draw (1.00, 2.00) -- (3.0,4.0);",
            r"\draw (5.00, 6.00) -- (7.0,8.0);",
        ]
    )

    result = helper.shift_tex_coordinates(
        tex,
        dx="0.10",
        dy="-0.25",
        line_ranges=[(2, 2)],
    )

    assert result.changed_count == 2
    assert result.text.splitlines() == [
        r"\draw (1.00, 2.00) -- (3.0,4.0);",
        r"\draw (5.10, 5.75) -- (7.10, 7.75);",
    ]


def test_shift_safe_foreach_slash_tuples_preserves_payload_fields() -> None:
    tex = (
        r"\foreach \px/\py/\sz in {8.05/7.40/0.026, 9.00/7.40/0.022} {"
        "\n"
        r"  \fill (\px,\py) circle (\sz);"
    )

    result = helper.shift_tex_coordinates(tex, dx="0.10", dy="-0.05", line_ranges=[(1, 1)])

    assert result.changed_count == 2
    assert (
        result.text.splitlines()[0]
        == r"\foreach \px/\py/\sz in {8.15/7.35/0.026, 9.10/7.35/0.022} {"
    )


def test_shift_does_not_touch_unsafe_foreach_non_xy_payload() -> None:
    tex = r"\foreach \y/\n/\sn in {7.90/10/60, 7.00/18/75} {}"

    result = helper.shift_tex_coordinates(tex, dx="0.10", dy="-0.05", line_ranges=[(1, 1)])

    assert result.changed_count == 0
    assert result.text == tex


def test_shift_does_not_touch_coordinates_inside_tex_comments() -> None:
    tex = r"\draw (1.00, 2.00); % old position (3.00, 4.00)"

    result = helper.shift_tex_coordinates(tex, dx="0.10", dy="0.10", line_ranges=[(1, 1)])

    assert result.changed_count == 1
    assert result.text == r"\draw (1.10, 2.10); % old position (3.00, 4.00)"


def test_main_prints_diff_without_writing(tmp_path: Path, capsys) -> None:
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(r"\draw (1.00, 2.00) -- (3.00, 4.00);" "\n", encoding="utf-8")

    assert helper.main([str(tex_path), "--line", "1:1", "--dx", "0.10", "--dy", "0.10"]) == 0

    captured = capsys.readouterr()
    assert "-\\draw (1.00, 2.00) -- (3.00, 4.00);" in captured.out
    assert "+\\draw (1.10, 2.10) -- (3.10, 4.10);" in captured.out
    assert tex_path.read_text(encoding="utf-8") == r"\draw (1.00, 2.00) -- (3.00, 4.00);" "\n"


def test_main_write_updates_file(tmp_path: Path, capsys) -> None:
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(r"\draw (1.00, 2.00);" "\n", encoding="utf-8")

    assert (
        helper.main(
            [str(tex_path), "--line", "1:1", "--dx", "-0.25", "--dy", "0.50", "--write"]
        )
        == 0
    )

    captured = capsys.readouterr()
    assert "wrote 1 shifted coordinate" in captured.out
    assert tex_path.read_text(encoding="utf-8") == r"\draw (0.75, 2.50);" "\n"


def test_main_rejects_non_tex_file_before_write(tmp_path: Path, capsys) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text("point: (1.00, 2.00)\n", encoding="utf-8")

    assert (
        helper.main([str(path), "--line", "1:1", "--dx", "0.10", "--dy", "0.10", "--write"])
        == 2
    )

    captured = capsys.readouterr()
    assert "tex_path must be a .tex file" in captured.err
    assert path.read_text(encoding="utf-8") == "point: (1.00, 2.00)\n"


def test_main_rejects_missing_scope(tmp_path: Path, capsys) -> None:
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(r"\draw (1.00, 2.00);" "\n", encoding="utf-8")

    assert helper.main([str(tex_path), "--dx", "0.10", "--dy", "0.10"]) == 2

    captured = capsys.readouterr()
    assert "provide --line or --all" in captured.err


def test_main_rejects_zero_shift(tmp_path: Path, capsys) -> None:
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(r"\draw (1.00, 2.00);" "\n", encoding="utf-8")

    assert helper.main([str(tex_path), "--line", "1:1", "--dx", "0", "--dy", "0"]) == 2

    captured = capsys.readouterr()
    assert "dx and dy cannot both be zero" in captured.err


def test_main_rejects_no_coordinate_changes(tmp_path: Path, capsys) -> None:
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(r"\foreach \y/\n/\sn in {7.90/10/60} {}" "\n", encoding="utf-8")

    assert helper.main([str(tex_path), "--line", "1:1", "--dx", "0.10", "--dy", "0.10"]) == 2

    captured = capsys.readouterr()
    assert "no supported coordinates changed" in captured.err
