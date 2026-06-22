"""Build a read-only TeX selector index for candidate search."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-tex-index.v1"
ACTIVE_COMMANDS = ("\\draw", "\\node", "\\coordinate", "\\fill", "\\path", "\\shade")
PANEL_HINT_RE = re.compile(r"^\s*%\s*Panel\s+([A-Za-z0-9_-]+)\b")


class CandidateTexIndexError(ValueError):
    """Raised when TeX selector indexing would cross fixture boundaries."""


def _fixture_source(paths: runtime_paths.RuntimePaths, name: str) -> Path:
    fixture = paths.examples_dir / name
    if fixture.is_symlink():
        raise CandidateTexIndexError("fixture_symlink_forbidden")
    source = fixture / f"{name}.tex"
    if source.is_symlink():
        raise CandidateTexIndexError("source_symlink_forbidden")
    try:
        source.resolve().relative_to(fixture.resolve())
    except ValueError as exc:
        raise CandidateTexIndexError("source_path_escape") from exc
    return source


def _git_dirty(paths: runtime_paths.RuntimePaths, source: Path, fixture: Path) -> tuple[bool, bool]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", str(source)],
        cwd=paths.workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    affected = bool(result.stdout.strip()) if result.returncode == 0 else False
    all_dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", str(fixture)],
        cwd=paths.workspace_root,
        text=True,
        capture_output=True,
        check=False,
    )
    fixture_dirty = bool(all_dirty.stdout.strip()) if all_dirty.returncode == 0 else affected
    return fixture_dirty, affected


def _active_command(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(command) for command in ACTIVE_COMMANDS)


def _selector(
    *,
    source_rel: Path,
    panel: str,
    start_index: int,
    end_index: int,
    lines: list[str],
) -> dict[str, Any]:
    selected = "\n".join(lines[start_index : end_index + 1])
    return {
        "kind": "tex_selector.v1",
        "path": source_rel.as_posix(),
        "panel": panel,
        "line_start": start_index + 1,
        "line_end": end_index + 1,
        "source_hash": candidate_contracts.canonical_hash("\n".join(lines)),
        "selector_text_hash": candidate_contracts.canonical_hash(selected),
        "anchors": [],
        "text": selected,
    }


def _selectors(source_rel: Path, text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    selectors: list[dict[str, Any]] = []
    current_panel = "unknown"
    index = 0
    while index < len(lines):
        line = lines[index]
        hint = PANEL_HINT_RE.match(line)
        if hint:
            current_panel = hint.group(1)
            index += 1
            continue
        if not _active_command(line):
            index += 1
            continue
        start = index
        end = index
        while end < len(lines) and ";" not in lines[end]:
            end += 1
        if end >= len(lines):
            end = len(lines) - 1
        selectors.append(
            _selector(
                source_rel=source_rel,
                panel=current_panel,
                start_index=start,
                end_index=end,
                lines=lines,
            )
        )
        index = end + 1
    return selectors


def build_tex_index(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    source = _fixture_source(paths, name)
    source_rel = Path("examples") / name / source.name
    if not source.is_file():
        return {
            "schema": SCHEMA,
            "fixture": name,
            "source": source_rel.as_posix(),
            "fixture_dirty": False,
            "affected_files_dirty": False,
            "selectors": [],
            "refusals": [{"code": "source_missing"}],
        }
    fixture_dirty, affected_dirty = _git_dirty(paths, source, paths.examples_dir / name)
    text = source.read_text(encoding="utf-8")
    return {
        "schema": SCHEMA,
        "fixture": name,
        "source": source_rel.as_posix(),
        "fixture_dirty": fixture_dirty,
        "affected_files_dirty": affected_dirty,
        "selectors": _selectors(source_rel, text),
        "refusals": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_tex_index(args.name)
    except (CandidateTexIndexError, ValueError) as exc:
        print(f"candidate_tex_index: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
