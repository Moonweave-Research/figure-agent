"""Tests for sub-region iteration log starter and append helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from subregion_active_set import (  # noqa: E402
    active_subregion_ids,
    iteration_patch_ids,
    parse_active_target_rows,
)
from subregion_iteration_log import (  # noqa: E402
    SubregionIterationLogError,
    append_iteration_row,
    main,
    subregion_iteration_log_template,
    write_subregion_iteration_log,
)


def _example_dir_at(root: Path, name: str = "demo_fig") -> Path:
    example_dir = root / name
    example_dir.mkdir(parents=True)
    (example_dir / f"{name}.tex").write_text("% demo\n", encoding="utf-8")
    return example_dir


def _example_dir(tmp_path: Path) -> Path:
    return _example_dir_at(tmp_path / "examples")


def test_template_is_parseable_by_existing_active_set_parser(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)

    text = subregion_iteration_log_template(example_dir)

    assert "# Sub-Region Iteration Log - demo_fig" in text
    assert "## Active Target Set" in text
    assert "## Iteration Log" in text
    rows = parse_active_target_rows(text)
    assert active_subregion_ids(rows) == []
    assert iteration_patch_ids(text) == []


def test_template_rejects_missing_example_directory(tmp_path: Path) -> None:
    missing_dir = tmp_path / "examples" / "missing_fig"

    try:
        subregion_iteration_log_template(missing_dir)
    except SubregionIterationLogError as exc:
        assert "missing example directory" in str(exc)
    else:
        raise AssertionError("expected SubregionIterationLogError")

    assert not missing_dir.exists()


def test_write_template_refuses_overwrite_without_force(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    log_path.write_text("existing\n", encoding="utf-8")

    try:
        write_subregion_iteration_log(log_path, subregion_iteration_log_template(example_dir))
    except FileExistsError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")

    assert log_path.read_text(encoding="utf-8") == "existing\n"


def test_write_template_allows_explicit_force_overwrite(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    log_path.write_text("existing\n", encoding="utf-8")

    write_subregion_iteration_log(
        log_path,
        subregion_iteration_log_template(example_dir),
        force=True,
    )

    assert "## Active Target Set" in log_path.read_text(encoding="utf-8")


def test_append_iteration_row_rejects_missing_log(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"

    try:
        append_iteration_row(
            log_path,
            iteration="iter-001",
            subregion_id="D-1",
            problem="missing log",
            patch_summary="none",
            result="none",
            follow_up="create log first",
        )
    except SubregionIterationLogError as exc:
        assert "missing subregion_iteration_log.md" in str(exc)
    else:
        raise AssertionError("expected SubregionIterationLogError")


def test_append_iteration_row_preserves_parseable_iteration_ids(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    write_subregion_iteration_log(log_path, subregion_iteration_log_template(example_dir))

    append_iteration_row(
        log_path,
        iteration="iter-001",
        subregion_id="D-1..D-2, Row2-BR2",
        problem="label hierarchy was too flat",
        patch_summary="raised the active label and tightened the arrow",
        result="improved",
        follow_up="recheck print crop",
    )

    text = log_path.read_text(encoding="utf-8")
    assert "iter-001" in text
    assert iteration_patch_ids(text) == ["D-1", "D-2", "Row2-BR2"]


def test_append_iteration_row_lands_in_iteration_log_with_trailing_section(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    write_subregion_iteration_log(log_path, subregion_iteration_log_template(example_dir))
    # A human accretes a trailing section after the Iteration Log.
    log_path.write_text(
        log_path.read_text(encoding="utf-8") + "\n## Notes\n\n- print at 88mm\n",
        encoding="utf-8",
    )

    append_iteration_row(
        log_path,
        iteration="iter-001",
        subregion_id="D-2",
        problem="label hierarchy was too flat",
        patch_summary="raised the active label",
        result="fixed",
        follow_up="none",
    )

    text = log_path.read_text(encoding="utf-8")
    assert iteration_patch_ids(text) == ["D-2"]
    assert text.index("| iter-001 |") < text.index("## Notes")


def test_append_iteration_row_handles_iteration_log_as_final_line_without_newline(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    # ## Iteration Log is the last line with no trailing newline. The body_start
    # search returns -1 here; the row must still land after the heading (EOF path),
    # never spliced before an earlier section.
    log_path.write_text("## Active Target Set\n\n## Iteration Log", encoding="utf-8")

    append_iteration_row(
        log_path,
        iteration="iter-001",
        subregion_id="D-2",
        problem="p",
        patch_summary="s",
        result="fixed",
        follow_up="none",
    )

    text = log_path.read_text(encoding="utf-8")
    assert text.index("## Iteration Log") < text.index("| iter-001 |")


def test_append_iteration_row_escapes_pipe_without_breaking_table(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    log_path = example_dir / "subregion_iteration_log.md"
    write_subregion_iteration_log(log_path, subregion_iteration_log_template(example_dir))

    append_iteration_row(
        log_path,
        iteration="iter-003",
        subregion_id="E-1",
        problem="label | leader ambiguity",
        patch_summary="moved label | kept leader",
        result="fixed",
        follow_up="none",
    )

    text = log_path.read_text(encoding="utf-8")
    assert "label &#124; leader ambiguity" in text
    assert iteration_patch_ids(text) == ["E-1"]


def test_cli_write_template_and_append_are_reloadable(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    script = Path(__file__).resolve().parents[1] / "scripts" / "subregion_iteration_log.py"

    write_result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--template",
            str(example_dir),
            "--write-template",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert write_result.returncode == 0, write_result.stderr
    log_path = example_dir / "subregion_iteration_log.md"
    assert log_path.is_file()

    append_result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--append",
            str(example_dir),
            "--iteration",
            "iter-002",
            "--subregion-id",
            "G-1",
            "--problem",
            "gap too small",
            "--patch-summary",
            "moved leader one point",
            "--result",
            "fixed",
            "--follow-up",
            "none",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert append_result.returncode == 0, append_result.stderr
    text = log_path.read_text(encoding="utf-8")
    assert active_subregion_ids(parse_active_target_rows(text)) == []
    assert iteration_patch_ids(text) == ["G-1"]


def test_cli_template_rejects_parent_relative_fixture_before_writing(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = _example_dir_at(tmp_path, "outside")
    log_path = outside_dir / "subregion_iteration_log.md"
    monkeypatch.chdir(tmp_path)

    exit_code = main(["--template", "examples/../outside", "--write-template"])

    assert exit_code == 2
    assert "invalid fixture path" in capsys.readouterr().err
    assert not log_path.exists()


def test_cli_append_rejects_existing_relative_dir_outside_examples(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    (tmp_path / "examples").mkdir()
    outside_dir = _example_dir_at(tmp_path, "outside")
    log_path = outside_dir / "subregion_iteration_log.md"
    write_subregion_iteration_log(log_path, subregion_iteration_log_template(outside_dir))
    before = log_path.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--append",
            "outside",
            "--iteration",
            "iter-999",
            "--subregion-id",
            "X-1",
            "--problem",
            "outside append",
            "--patch-summary",
            "should not write",
            "--result",
            "blocked",
        ]
    )

    assert exit_code == 2
    assert "invalid fixture path" in capsys.readouterr().err
    assert log_path.read_text(encoding="utf-8") == before
