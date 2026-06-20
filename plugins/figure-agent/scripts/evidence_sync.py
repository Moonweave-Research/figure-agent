"""Preview or write generated evidence index metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import evidence_index
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.evidence-sync.v1"


class EvidenceSyncError(ValueError):
    """Raised when evidence sync cannot safely write generated metadata."""


def _fixture_relative(example_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(example_dir.resolve()).as_posix()
    except ValueError as exc:
        raise EvidenceSyncError("path_escape") from exc


def _ensure_safe_write_target(example_dir: Path, output: Path) -> None:
    build_dir = example_dir / "build"
    for label, path in (
        ("build", build_dir),
        ("evidence", output.parent),
        ("evidence_index.json", output),
    ):
        if path.is_symlink():
            raise EvidenceSyncError(f"sandbox_symlink_forbidden: {label}")


def sync_evidence(
    name: str,
    *,
    candidate_id: str | None = None,
    candidate_set_path: Path | None = None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    index = evidence_index.build_evidence_index(
        name,
        candidate_id=candidate_id,
        candidate_set_path=candidate_set_path,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    writes: list[str] = []
    blocking_reasons = sorted(
        set(index.get("diagnostics", [])) & {"candidate_id_mismatch", "hash_mismatch"}
    )
    if write and not blocking_reasons:
        output = example_dir / "build" / "evidence" / "evidence_index.json"
        _ensure_safe_write_target(example_dir, output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        writes.append(_fixture_relative(example_dir, output))
    return {
        "schema": SCHEMA,
        "figure_name": name,
        "mode": "write" if write else "preview",
        "writes": writes,
        "blocking_reasons": blocking_reasons,
        "evidence_index": index,
    }
