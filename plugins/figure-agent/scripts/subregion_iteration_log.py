"""Create and append text-form sub-region iteration logs.

This helper keeps the sub-region workflow deliberately lightweight: the source
of truth remains `examples/<name>/subregion_iteration_log.md`, and existing
parsers continue to read the Markdown tables from that file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fixture_identity

SUBREGION_ITERATION_LOG_FILENAME = "subregion_iteration_log.md"


class SubregionIterationLogError(Exception):
    """Controlled error for sub-region iteration log operations."""


def _fixture_name(example_dir: Path) -> str:
    if not example_dir.is_dir():
        raise SubregionIterationLogError(f"missing example directory: {example_dir}")
    name = example_dir.name
    if not name:
        raise SubregionIterationLogError("example directory must have a name")
    return name


def _markdown_cell(value: str) -> str:
    text = value.strip()
    if not text:
        return "none"
    return text.replace("|", "&#124;").replace("\n", " ")


def subregion_iteration_log_template(example_dir: Path) -> str:
    fixture = _fixture_name(example_dir)
    return "\n".join(
        [
            f"# Sub-Region Iteration Log - {fixture}",
            "",
            "## Active Target Set",
            "",
            "| State | Sub-region ID | Evidence | Notes |",
            "|---|---|---|---|",
            "| named but stable | none | initial template | add active targets before patching |",
            "",
            "## Iteration Log",
            "",
            "| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |",
            "|---|---|---|---|---|---|",
            "",
        ]
    )


def write_subregion_iteration_log(path: Path, text: str, *, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"subregion_iteration_log already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iteration_row(
    *,
    iteration: str,
    subregion_id: str,
    problem: str,
    patch_summary: str,
    result: str,
    follow_up: str,
) -> str:
    return (
        "| "
        + " | ".join(
            [
                _markdown_cell(iteration),
                _markdown_cell(subregion_id),
                _markdown_cell(problem),
                _markdown_cell(patch_summary),
                _markdown_cell(result),
                _markdown_cell(follow_up),
            ]
        )
        + " |"
    )


def append_iteration_row(
    log_path: Path,
    *,
    iteration: str,
    subregion_id: str,
    problem: str,
    patch_summary: str,
    result: str,
    follow_up: str,
) -> None:
    if not log_path.is_file():
        raise SubregionIterationLogError(f"missing subregion_iteration_log.md: {log_path}")
    text = log_path.read_text(encoding="utf-8")
    if "## Iteration Log" not in text:
        raise SubregionIterationLogError("subregion_iteration_log.md missing ## Iteration Log")
    row = _iteration_row(
        iteration=iteration,
        subregion_id=subregion_id,
        problem=problem,
        patch_summary=patch_summary,
        result=result,
        follow_up=follow_up,
    )
    prefix = text.rstrip()
    log_path.write_text(f"{prefix}\n{row}\n", encoding="utf-8")


def _log_path(example_dir: Path) -> Path:
    return example_dir / SUBREGION_ITERATION_LOG_FILENAME


def _resolve_example_dir_for_cli(value: Path) -> Path:
    if value.is_absolute():
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise SubregionIterationLogError(
                "invalid fixture path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise SubregionIterationLogError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return value
    raise SubregionIterationLogError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, "
        "or an absolute path"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise SubregionIterationLogError(f"invalid fixture path: {original}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--template", type=Path, help="example directory to scaffold")
    mode.add_argument("--append", type=Path, help="example directory whose log receives a row")
    parser.add_argument("--write-template", action="store_true", help="write the template file")
    parser.add_argument("--force", action="store_true", help="overwrite an existing template file")
    parser.add_argument("--iteration")
    parser.add_argument("--subregion-id")
    parser.add_argument("--problem")
    parser.add_argument("--patch-summary")
    parser.add_argument("--result")
    parser.add_argument("--follow-up", default="none")
    args = parser.parse_args(argv)

    try:
        if args.template is not None:
            example_dir = _resolve_example_dir_for_cli(args.template)
            text = subregion_iteration_log_template(example_dir)
            if args.write_template:
                path = _log_path(example_dir)
                write_subregion_iteration_log(path, text, force=args.force)
                print(path)
            else:
                print(text, end="")
            return 0

        required = {
            "--iteration": args.iteration,
            "--subregion-id": args.subregion_id,
            "--problem": args.problem,
            "--patch-summary": args.patch_summary,
            "--result": args.result,
        }
        missing = [
            name
            for name, value in required.items()
            if not isinstance(value, str) or not value.strip()
        ]
        if missing:
            parser.error("--append requires " + ", ".join(missing))
        example_dir = _resolve_example_dir_for_cli(args.append)
        append_iteration_row(
            _log_path(example_dir),
            iteration=args.iteration,
            subregion_id=args.subregion_id,
            problem=args.problem,
            patch_summary=args.patch_summary,
            result=args.result,
            follow_up=args.follow_up,
        )
        print(_log_path(example_dir))
        return 0
    except (FileExistsError, SubregionIterationLogError) as exc:
        print(f"subregion_iteration_log.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
