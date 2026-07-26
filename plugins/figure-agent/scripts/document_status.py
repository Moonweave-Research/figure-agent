"""Fail-closed document classification for Figure Agent."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PLUGIN_ROOT / "docs" / "document-status.yaml"
GOVERNED_DOCUMENT_SUFFIXES = frozenset({".json", ".jsonl", ".md", ".yaml", ".yml"})


class DocumentStatusError(ValueError):
    """Raised when the document policy is missing or internally inconsistent."""


@dataclass(frozen=True)
class DocumentStatus:
    path: str
    classification: str
    active: bool
    ship: bool
    agent_executable: bool


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DocumentStatusError("document status policy must be a mapping")
    if payload.get("schema") != "figure-agent.document-status-policy.v1":
        raise DocumentStatusError("unsupported document status policy schema")
    classes = payload.get("classes")
    rules = payload.get("rules")
    if not isinstance(classes, dict) or not isinstance(rules, list):
        raise DocumentStatusError("document status policy requires classes and rules")
    return payload


def _normalized(relative_path: str | Path) -> str:
    path = PurePosixPath(str(relative_path).replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise DocumentStatusError(f"document path escapes plugin root: {relative_path}")
    return path.as_posix()


def _rule_matches(rule: dict[str, Any], relative_path: str) -> bool:
    exact = rule.get("path")
    paths = rule.get("paths", [])
    globs = rule.get("globs", [])
    if exact == relative_path:
        return True
    if isinstance(paths, list) and relative_path in paths:
        return True
    return isinstance(globs, list) and any(
        isinstance(pattern, str) and fnmatchcase(relative_path, pattern)
        for pattern in globs
    )


def classify_document(
    relative_path: str | Path,
    *,
    policy: dict[str, Any] | None = None,
) -> DocumentStatus:
    """Classify a plugin-relative document; unmatched paths fail closed."""

    relative = _normalized(relative_path)
    loaded = policy or load_policy()
    classes = loaded["classes"]
    for rule in loaded["rules"]:
        if not isinstance(rule, dict) or not _rule_matches(rule, relative):
            continue
        name = rule.get("class")
        semantics = classes.get(name)
        if not isinstance(name, str) or not isinstance(semantics, dict):
            raise DocumentStatusError(f"invalid class for {relative}")
        required = ("active", "ship", "agent_executable")
        if any(not isinstance(semantics.get(field), bool) for field in required):
            raise DocumentStatusError(f"invalid semantics for class {name}")
        return DocumentStatus(relative, name, **{field: semantics[field] for field in required})
    return DocumentStatus(relative, "unclassified", False, False, False)


def shippable_document_paths(plugin_root: Path = PLUGIN_ROOT) -> list[Path]:
    """Return only explicitly approved active documents."""

    policy = load_policy(plugin_root / "docs" / "document-status.yaml")
    docs_root = plugin_root / "docs"
    candidates = (
        path
        for path in docs_root.rglob("*")
        if path.is_file() and path.suffix.lower() in GOVERNED_DOCUMENT_SUFFIXES
    )
    approved = []
    for path in candidates:
        relative = path.relative_to(plugin_root).as_posix()
        if classify_document(relative, policy=policy).ship:
            approved.append(path)
    return sorted(approved, key=lambda path: path.relative_to(plugin_root).as_posix())
