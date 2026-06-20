"""Build a deterministic read-only defect ledger for figure quality work."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import audit_evidence_graph
import fixture_identity
import quality_patch_policy
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.quality-defect-ledger.v1"


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _fixture_file_node(graph: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return None
    for node in nodes:
        if isinstance(node, dict) and node.get("id") == node_id:
            return node
    return None


def _source_hashes(example_dir: Path, name: str) -> dict[str, str]:
    source = example_dir / f"{name}.tex"
    if not source.exists() or not source.is_file():
        return {}
    return {f"examples/{name}/{name}.tex": file_sha256(source)}


def _source_path_escape(graph: dict[str, Any]) -> bool:
    node = _fixture_file_node(graph, f"source:{graph.get('name')}.tex")
    return bool(node and node.get("blocked") and node.get("reason") == "path_escape")


def _first_blocker_defect(graph: dict[str, Any], name: str) -> dict[str, Any]:
    blocker = graph.get("first_blocker")
    if not isinstance(blocker, dict):
        blocker = {"code": "source_not_authored", "message": "source is not authored"}
    return {
        "id": "QD001",
        "source": "status",
        "evidence": [{"node_id": f"blocker:{blocker.get('code', 'unknown')}"}],
        "severity": "blocker",
        "owner": "human",
        "defect_class": str(blocker.get("code") or "source_not_authored"),
        "patchability": {
            "state": "human_required",
            "reasons": [],
            "blocked_codes": [str(blocker.get("code") or "source_not_authored")],
            "may_edit": False,
            "policy_version": quality_patch_policy.SCHEMA,
        },
        "affected_files": [f"examples/{name}/{name}.tex"],
        "freshness": {
            "status_input_hash": "sha256:" + "0" * 64,
            "critique_input_hash": "sha256:" + "0" * 64,
            "audit_evidence_graph_hash": _canonical_hash(graph),
            "source_hashes": {},
        },
        "policy": {
            "version": quality_patch_policy.SCHEMA,
            "blocked_codes": [str(blocker.get("code") or "source_not_authored")],
        },
    }


def _text_boundary_defect(example_dir: Path, name: str, graph_hash: str) -> dict[str, Any] | None:
    report = example_dir / "build" / "text_boundary_clash.json"
    if not report.is_file():
        return None
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return None
    candidate = candidates[0] if isinstance(candidates[0], dict) else {}
    defect = {
        "id": "QD001",
        "source": "deterministic_audit",
        "evidence": [
            {
                "uri": f"figure://{name}/audit/text-boundary",
                "node_id": "checker:text_boundary",
            }
        ],
        "severity": "action",
        "owner": "tool",
        "defect_class": "text_overlap",
        "affected_files": [f"examples/{name}/{name}.tex"],
        "freshness": {
            "status_input_hash": "sha256:" + "0" * 64,
            "critique_input_hash": "sha256:" + "0" * 64,
            "audit_evidence_graph_hash": graph_hash,
            "source_hashes": _source_hashes(example_dir, name),
        },
        "selector_hint": {"kind": "node_name", "value": candidate.get("text") or "label"},
        "suggested_change": {
            "operation_type": "tikz_coordinate_adjust",
            "summary": "Move the overlapping label by a bounded amount",
            "patch": "",
        },
    }
    patchability = quality_patch_policy.classify_patchability(defect)
    defect["patchability"] = patchability
    defect["policy"] = {
        "version": quality_patch_policy.SCHEMA,
        "blocked_codes": patchability["blocked_codes"],
    }
    return defect


def build_quality_defect_ledger(
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
    graph = audit_evidence_graph.build_audit_evidence_graph(
        name,
        plugin_root=paths.plugin_root,
        workspace_root=paths.workspace_root,
    )
    graph_hash = _canonical_hash(graph)
    example_dir = paths.examples_dir / name

    if _source_path_escape(graph):
        defect = _first_blocker_defect(graph, name)
        defect["patchability"] = {
            "state": "unsupported",
            "reasons": [],
            "blocked_codes": ["path_escape"],
            "may_edit": False,
            "policy_version": quality_patch_policy.SCHEMA,
        }
        defect["policy"] = {
            "version": quality_patch_policy.SCHEMA,
            "blocked_codes": ["path_escape"],
        }
        defects = [defect]
    else:
        text_defect = _text_boundary_defect(example_dir, name, graph_hash)
        defects = [text_defect] if text_defect is not None else [_first_blocker_defect(graph, name)]

    payload = {
        "schema": SCHEMA,
        "fixture": name,
        "workspace_root": str(paths.workspace_root),
        "defects": defects,
    }
    payload["ledger_hash"] = _canonical_hash(payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default=None)
    args = parser.parse_args(argv)
    payload = build_quality_defect_ledger(args.name)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
