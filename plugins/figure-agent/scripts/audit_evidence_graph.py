"""Build a deterministic read-only audit evidence graph for one fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_identity  # noqa: E402
import runtime_paths  # noqa: E402
import status  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

SCHEMA = "figure-agent.audit-evidence-graph.v1"


def _is_relative_to_any(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved = path.resolve()
    return any(
        resolved == root.resolve() or resolved.is_relative_to(root.resolve())
        for root in roots
    )


def _relative_display(path: Path, *, workspace_root: Path, plugin_root: Path) -> str:
    for root in (workspace_root, plugin_root):
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.name


def _file_node(
    *,
    node_id: str,
    node_class: str,
    path: Path,
    workspace_root: Path,
    plugin_root: Path,
    allowed_roots: tuple[Path, ...],
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "id": node_id,
        "class": node_class,
        "path": _relative_display(path, workspace_root=workspace_root, plugin_root=plugin_root),
        "exists": path.exists(),
    }
    if not path.exists():
        return node
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        node.update(
            {
                "exists": False,
                "blocked": True,
                "reason": f"resolve_failed:{exc.__class__.__name__}",
            }
        )
        return node
    if not _is_relative_to_any(resolved, allowed_roots):
        node.update({"blocked": True, "reason": "path_escape"})
        return node
    if path.is_file():
        node["size_bytes"] = path.stat().st_size
        node["sha256"] = file_sha256(path)
    return node


def _status_node(node_id: str, node_class: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"id": node_id, "class": node_class, **payload}


def _edge(edge_class: str, source: str, target: str) -> dict[str, str]:
    return {
        "id": f"edge:{edge_class}:{source}:{target}",
        "class": edge_class,
        "from": source,
        "to": target,
    }


def _sort_and_validate(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
    node_ids = [node["id"] for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        duplicates = sorted({node_id for node_id in node_ids if node_ids.count(node_id) > 1})
        raise ValueError(f"duplicate graph node ids: {duplicates}")
    edges.sort(key=lambda item: item["id"])
    nodes.sort(key=lambda item: item["id"])


def build_audit_evidence_graph(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    status_payload = status.infer_stage(example_dir)
    first_blocker = (status_payload.get("status_explanation") or {}).get("first_blocker")
    if not isinstance(first_blocker, dict):
        first_blocker = None

    allowed_roots = (example_dir, paths.styles_dir)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    source_files = {
        "source:spec.yaml": example_dir / "spec.yaml",
        f"source:{name}.tex": example_dir / f"{name}.tex",
        "source:briefing.md": example_dir / "briefing.md",
        "source:critique.md": example_dir / "critique.md",
    }
    for node_id, path in source_files.items():
        nodes.append(
            _file_node(
                node_id=node_id,
                node_class="source",
                path=path,
                workspace_root=paths.workspace_root,
                plugin_root=paths.plugin_root,
                allowed_roots=allowed_roots,
            )
        )

    style_id = "style:polymer-paper-preamble.sty"
    nodes.append(
        _file_node(
            node_id=style_id,
            node_class="style",
            path=paths.styles_dir / "polymer-paper-preamble.sty",
            workspace_root=paths.workspace_root,
            plugin_root=paths.plugin_root,
            allowed_roots=allowed_roots,
        )
    )

    artifact_files = {
        f"build:{name}.pdf": example_dir / "build" / f"{name}.pdf",
        f"build:{name}.png": example_dir / "build" / f"{name}.png",
        f"export:{name}.pdf": example_dir / "exports" / f"{name}.pdf",
        f"export:{name}.svg": example_dir / "exports" / f"{name}.svg",
        f"export:{name}.png": example_dir / "exports" / f"{name}.png",
        f"export:{name}.tif": example_dir / "exports" / f"{name}.tif",
    }
    for node_id, path in artifact_files.items():
        nodes.append(
            _file_node(
                node_id=node_id,
                node_class="export_artifact" if node_id.startswith("export:") else "build_artifact",
                path=path,
                workspace_root=paths.workspace_root,
                plugin_root=paths.plugin_root,
                allowed_roots=allowed_roots,
            )
        )

    checker_files = {
        "checker:visual_clash": example_dir / "build" / "visual_clash.json",
        "checker:text_boundary": example_dir / "build" / "text_boundary_clash.json",
        "checker:label_path": example_dir / "build" / "label_path_proximity.json",
        "checker:undeclared_geometry": example_dir / "build" / "undeclared_geometry.json",
    }
    for node_id, path in checker_files.items():
        nodes.append(
            _file_node(
                node_id=node_id,
                node_class="checker",
                path=path,
                workspace_root=paths.workspace_root,
                plugin_root=paths.plugin_root,
                allowed_roots=allowed_roots,
            )
        )

    nodes.append(
        _status_node(
            "critique:freshness",
            "critique",
            {"state": status_payload.get("critique_state")},
        )
    )
    nodes.append(
        _status_node(
            "human_gate:acceptance",
            "human_gate",
            {
                "acceptance_state": status_payload.get("acceptance_state"),
                "publication_gate_state": status_payload.get("publication_gate_state"),
            },
        )
    )

    for source_id in (*source_files.keys(), style_id):
        edges.append(_edge("derived_from", source_id, f"build:{name}.pdf"))
    edges.append(_edge("derived_from", f"build:{name}.pdf", f"export:{name}.pdf"))
    edges.append(_edge("requires_human", "human_gate:acceptance", f"export:{name}.pdf"))
    if first_blocker:
        blocker_id = f"blocker:{first_blocker.get('code', 'unknown')}"
        nodes.append(_status_node(blocker_id, "blocker", first_blocker))
        edges.append(_edge("blocks", blocker_id, f"export:{name}.pdf"))

    _sort_and_validate(nodes, edges)
    return {
        "schema": SCHEMA,
        "name": name,
        "workspace_root": str(paths.workspace_root),
        "nodes": nodes,
        "edges": edges,
        "readiness": {
            "workflow_ready": bool(status_payload.get("workflow_ready")),
            "final_ready": bool(status_payload.get("final_ready")),
            "release_ready": bool(status_payload.get("release_ready")),
            "human_gate_required": bool(
                (status_payload.get("status_explanation") or {})
                .get("first_blocker", {})
                .get("manual", False)
            ),
        },
        "first_blocker": first_blocker,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default=None)
    args = parser.parse_args(argv)
    payload = build_audit_evidence_graph(args.name)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
