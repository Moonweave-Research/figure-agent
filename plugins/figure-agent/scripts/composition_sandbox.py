from __future__ import annotations

import re
from pathlib import Path

import fixture_identity
import runtime_paths

SHELL_ESCAPE_TOKENS = frozenset({"--shell-escape", "-shell-escape", "-enable-write18"})
FORBIDDEN_INPUT_RE = re.compile(r"\\input\s*\{\s*(?:/|\.\.)")
WRITE_ESCAPE_RE = re.compile(r"\\(?:immediate\s*)?\\write18")


def _workspace_root(workspace_root: Path | None) -> Path:
    return runtime_paths.resolve_runtime_paths(workspace_root=workspace_root).workspace_root


def _blocked(code: str, message: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "diagnostics": [{"code": code, "stage": "pre_tex", "message": message}],
    }


def _passed() -> dict[str, object]:
    return {"status": "passed", "diagnostics": []}


def _fixture_root(name: str, workspace_root: Path | None) -> Path:
    fixture_identity.validate_fixture_name(name)
    return _workspace_root(workspace_root) / "examples" / name


def _candidate_source(
    fixture: Path,
    candidate_source_path: Path,
) -> tuple[Path | None, dict[str, object] | None]:
    if candidate_source_path.is_absolute():
        try:
            candidate_source_path.resolve(strict=False).relative_to(fixture.resolve(strict=False))
        except ValueError:
            return None, _blocked("absolute_path_forbidden", "absolute source path escapes fixture")
        target = candidate_source_path
    else:
        if ".." in candidate_source_path.parts:
            return None, _blocked("path_escape_forbidden", "candidate source path escapes fixture")
        target = fixture / candidate_source_path

    if target.is_symlink():
        return None, _blocked("sandbox_symlink_forbidden", "candidate source is a symlink")
    try:
        target.resolve(strict=False).relative_to(fixture.resolve(strict=False))
    except ValueError:
        return None, _blocked("path_escape_forbidden", "candidate source path escapes fixture")
    return target, None


def preflight_candidate_source_path(
    name: str,
    *,
    candidate_source_path: Path,
    workspace_root: Path | None = None,
) -> tuple[Path | None, dict[str, object] | None]:
    fixture = _fixture_root(name, workspace_root)
    return _candidate_source(fixture, candidate_source_path)


def validate_tex_sandbox_policy(
    name: str,
    *,
    candidate_source_path: Path,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    source, blocked = preflight_candidate_source_path(
        name,
        candidate_source_path=candidate_source_path,
        workspace_root=workspace_root,
    )
    if blocked is not None:
        return blocked
    assert source is not None
    tex_source = source.read_text(encoding="utf-8")
    if FORBIDDEN_INPUT_RE.search(tex_source):
        return _blocked("forbidden_input_directive", "fixture-external input is forbidden")
    if WRITE_ESCAPE_RE.search(tex_source):
        return _blocked("write_escape_forbidden", "TeX write escape is forbidden")
    return _passed()


def validate_tex_compile_command(
    name: str,
    *,
    compile_command: list[str],
    workspace_root: Path | None = None,
) -> dict[str, object]:
    _fixture_root(name, workspace_root)
    if any(token in SHELL_ESCAPE_TOKENS for token in compile_command):
        return _blocked("shell_escape_forbidden", "TeX shell escape is forbidden")
    return _passed()
