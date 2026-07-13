"""Audit declared repository content reads in an authoring transcript."""

from __future__ import annotations

import hashlib
import json
import shlex
from pathlib import Path
from typing import Any

SCHEMA = "figure-agent.authoring-execution-input-audit.v1"
_CONTENT_READ_COMMANDS = {"cat", "grep", "head", "rg", "sed", "tail"}


class AuthoringExecutionInputAuditError(ValueError):
    """Raised when transcript evidence cannot be audited safely."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _safe_relative_path(value: str, *, label: str) -> str:
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AuthoringExecutionInputAuditError(
            f"{label} must be a safe repository-relative path"
        )
    return path.as_posix()


def _shell_tokens(command: str) -> list[str]:
    try:
        outer = shlex.split(command)
        if "-lc" in outer:
            index = outer.index("-lc")
            return shlex.split(outer[index + 1])
        return outer
    except (ValueError, IndexError) as exc:
        raise AuthoringExecutionInputAuditError(
            "unable to parse transcript command"
        ) from exc


def _looks_like_repository_path(token: str) -> bool:
    if token.startswith(("/", "~", "-")):
        return False
    path = Path(token)
    if any(part in {"", ".", ".."} for part in path.parts):
        return False
    return (
        token == "AGENTS.md"
        or "/" in token
        or path.suffix in {".md", ".sty", ".tex", ".yaml", ".yml", ".json"}
    )


def _content_read_paths(command: str) -> list[str]:
    tokens = _shell_tokens(command)
    if not tokens:
        return []
    executable = Path(tokens[0]).name
    if executable not in _CONTENT_READ_COMMANDS:
        return []
    if executable == "rg" and "--files" in tokens:
        return []

    candidates = [token for token in tokens[1:] if _looks_like_repository_path(token)]
    if executable in {"rg", "grep"} and candidates:
        # The first positional argument can be a path-like search pattern. A real
        # path follows it in the bounded authoring commands this audit supports.
        positional = [token for token in tokens[1:] if not token.startswith("-")]
        if candidates and positional and candidates[0] == positional[0]:
            candidates = candidates[1:]
    return candidates


def audit_authoring_transcript(
    transcript_path: Path,
    *,
    allowed_repository_reads: list[str],
) -> dict[str, Any]:
    """Return a deterministic audit of shell-visible repository content reads."""
    transcript_bytes = transcript_path.read_bytes()
    allowed = sorted(
        {
            _safe_relative_path(path, label="allowed repository read")
            for path in allowed_repository_reads
        }
    )
    observed: set[str] = set()
    audited_commands = 0
    for line_number, raw_line in enumerate(
        transcript_bytes.decode("utf-8").splitlines(), start=1
    ):
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise AuthoringExecutionInputAuditError(
                f"invalid transcript JSON at line {line_number}"
            ) from exc
        if not isinstance(event, dict) or event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        command = item.get("command")
        if not isinstance(command, str):
            raise AuthoringExecutionInputAuditError(
                f"command missing at transcript line {line_number}"
            )
        audited_commands += 1
        observed.update(_content_read_paths(command))

    observed_paths = sorted(observed)
    undeclared = sorted(set(observed_paths) - set(allowed))
    return {
        "schema": SCHEMA,
        "decision": "blocked" if undeclared else "pass",
        "transcript_sha256": _sha256_bytes(transcript_bytes),
        "allowed_repository_reads": allowed,
        "observed_repository_reads": observed_paths,
        "undeclared_repository_reads": undeclared,
        "audited_command_count": audited_commands,
        "audit_boundary": "shell_visible_cat_grep_head_rg_sed_tail_reads_only",
        "filesystem_read_isolation": "unavailable",
        "publication_acceptance": "not_claimed",
    }


def write_authoring_input_audit(path: Path, payload: dict[str, Any]) -> None:
    """Persist a one-write audit artifact."""
    if path.exists() or path.is_symlink():
        raise AuthoringExecutionInputAuditError("input audit already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
