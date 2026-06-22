"""Build a deterministic read-only defect ledger for figure quality work."""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import audit_evidence_graph
import audit_evidence_summary
import critique_finding_gate
import fixture_identity
import quality_patch_policy
import runtime_paths
from critique_contract import CritiqueContractError, critique_finding_id, critique_findings
from quality_manifest import file_sha256, yaml_frontmatter

SCHEMA = "figure-agent.quality-defect-ledger.v1"


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + sha256(encoded).hexdigest()


def _source_fingerprint(defect: dict[str, Any]) -> str:
    affected_files = defect.get("affected_files")
    evidence = defect.get("evidence")
    selector_hint = defect.get("selector_hint")
    return _canonical_hash(
        {
            "affected_files": affected_files if isinstance(affected_files, list) else [],
            "defect_class": str(defect.get("defect_class") or ""),
            "evidence": evidence if isinstance(evidence, list) else [],
            "selector_hint": selector_hint if isinstance(selector_hint, dict) else {},
            "source": str(defect.get("source") or ""),
        }
    )


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


def _normalize_detector_defect(defect: dict[str, Any]) -> dict[str, Any]:
    patchability = quality_patch_policy.classify_patchability(defect)
    defect["patchability"] = patchability
    defect["policy"] = {
        "version": quality_patch_policy.SCHEMA,
        "blocked_codes": patchability["blocked_codes"],
    }
    return defect


def _undeclared_geometry_defects(
    example_dir: Path,
    name: str,
    graph_hash: str,
) -> list[dict[str, Any]]:
    report = example_dir / "build" / "undeclared_geometry.json"
    if not report.is_file():
        return []
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return []
    source_hashes = _source_hashes(example_dir, name)
    defects: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        # add_micro_defect candidates are real label-near-text near-misses; the
        # add_spec_check subset (undeclared column/horizontal rules, rect bounds)
        # is spec-hygiene noise that carries no concrete overlap to patch.
        if candidate.get("recommended_action") != "add_micro_defect":
            continue
        source_line = candidate.get("source_line")
        if not isinstance(source_line, int) or isinstance(source_line, bool):
            continue
        candidate_id = candidate.get("id")
        defect = {
            "source": "deterministic_audit",
            "evidence": [
                {
                    "uri": f"figure://{name}/audit/undeclared-geometry",
                    "node_id": candidate_id,
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
                "source_hashes": source_hashes,
            },
            "selector_hint": {"kind": "line_range", "value": f"{source_line}:{source_line}"},
            "suggested_change": {
                "operation_type": "tikz_coordinate_adjust",
                "summary": "Clear the label endpoint from the nearby text by a bounded amount",
                "patch": "",
            },
        }
        defects.append(defect)
    return defects


def _kept_visual_clash_finding_ids(frontmatter: dict[str, Any]) -> dict[str, str]:
    """Map each kept (not false-positive) visual_clash candidate to its linked finding id.

    Mirrors the audit_evidence_summary kept-vs-dismissed predicate: a micro_defect is a
    detector false positive iff status==accept_simplification AND reason==false_positive.
    """
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return {}
    kept: dict[str, str] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        ref = item.get("visual_clash_ref")
        if not isinstance(ref, str) or not ref.strip():
            continue
        if (
            item.get("status") == "accept_simplification"
            and item.get("accept_simplification_reason") == "false_positive"
        ):
            continue
        linked_finding_id = item.get("linked_finding_id")
        if isinstance(linked_finding_id, str) and linked_finding_id.strip():
            kept[ref.strip()] = linked_finding_id.strip()
    return kept


def _visual_clash_defects(example_dir: Path, name: str, graph_hash: str) -> list[dict[str, Any]]:
    report = example_dir / "build" / "visual_clash.json"
    critique_path = example_dir / "critique.md"
    if not report.is_file() or not critique_path.is_file():
        return []
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        return []
    try:
        frontmatter = yaml_frontmatter(critique_path)
        kept_finding_ids = _kept_visual_clash_finding_ids(frontmatter)
        findings = critique_findings(frontmatter)
    except CritiqueContractError:
        return []
    eligible_findings = critique_finding_gate.kept_bounded_findings(example_dir)
    finding_by_id: dict[str, dict[str, Any]] = {}
    for index, finding in enumerate(findings):
        try:
            finding_by_id[critique_finding_id(finding, f"critique finding {index}")] = finding
        except CritiqueContractError:
            continue
    source_hashes = _source_hashes(example_dir, name)
    defects: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str):
            continue
        linked_finding_id = kept_finding_ids.get(candidate_id.strip())
        if linked_finding_id is None:
            continue
        finding = finding_by_id.get(linked_finding_id)
        eligible = eligible_findings.get(linked_finding_id)
        if finding is None or eligible is None:
            continue
        tex_lines = eligible["tex_lines"]
        start, end = tex_lines
        defect = {
            "source": "critique_adjudication",
            "evidence": [
                {
                    "uri": f"figure://{name}/audit/visual-clash",
                    "node_id": candidate_id.strip(),
                    "critique_finding_id": linked_finding_id,
                }
            ],
            "severity": "action",
            "owner": "tool",
            "defect_class": eligible["defect_class"],
            "affected_files": [f"examples/{name}/{name}.tex"],
            "freshness": {
                "status_input_hash": "sha256:" + "0" * 64,
                "critique_input_hash": "sha256:" + "0" * 64,
                "audit_evidence_graph_hash": graph_hash,
                "source_hashes": source_hashes,
            },
            "selector_hint": {"kind": "line_range", "value": f"{start}:{end}"},
            "suggested_change": {
                "operation_type": "tikz_coordinate_adjust",
                "summary": "Move the clashing label off the underlying fill by a bounded amount",
                "patch": "",
            },
        }
        defects.append(defect)
    return defects


def _critique_finding_defects(
    example_dir: Path,
    name: str,
    graph_hash: str,
    skip_finding_ids: set[str],
) -> list[dict[str, Any]]:
    source_hashes = _source_hashes(example_dir, name)
    defects: list[dict[str, Any]] = []
    for finding_id, eligible in critique_finding_gate.kept_bounded_findings(example_dir).items():
        if finding_id in skip_finding_ids:
            continue
        start, end = eligible["tex_lines"]
        decision = eligible["decision"]
        defect = {
            "source": "critique_adjudication",
            "evidence": [
                {
                    "uri": f"figure://{name}/critique/finding/{finding_id}",
                    "node_id": finding_id,
                    "adjudication_decision": "keep",
                }
            ],
            "severity": "action",
            "owner": "tool",
            "defect_class": eligible["defect_class"],
            "affected_files": [f"examples/{name}/{name}.tex"],
            "freshness": {
                "status_input_hash": "sha256:" + "0" * 64,
                "critique_input_hash": "sha256:" + "0" * 64,
                "audit_evidence_graph_hash": graph_hash,
                "source_hashes": source_hashes,
            },
            "selector_hint": {"kind": "line_range", "value": f"{start}:{end}"},
            "suggested_change": {
                "operation_type": "tikz_coordinate_adjust",
                "summary": str(decision.get("reason") or "Bounded critique finding candidate"),
                "patch": "",
            },
        }
        defects.append(defect)
    return defects


def _detector_defects(example_dir: Path, name: str, graph_hash: str) -> list[dict[str, Any]]:
    # summarize_audit_evidence is the existing detector-adjudication gate: it reads
    # build/*.json and (when critique.md exists) the micro_defect accounting. It yields
    # linked_defect_count 0 whenever audit evidence is incomplete -- no critique, missing
    # detector reports or crop manifest (e.g. git clean), or an out-of-scope critique
    # schema -- which suppresses the visual_clash path and prevents fabricating a defect
    # from stale evidence. (The undeclared_geometry path below is self-adjudicating via
    # recommended_action and does not depend on this gate.)
    summary = audit_evidence_summary.summarize_audit_evidence(example_dir)
    defects = _undeclared_geometry_defects(example_dir, name, graph_hash)
    visual_clash_defects: list[dict[str, Any]] = []
    if summary.get("detector_feedback", {}).get("visual_clash", {}).get("linked_defect_count"):
        visual_clash_defects = _visual_clash_defects(example_dir, name, graph_hash)
    visual_clash_finding_ids = {
        str(evidence.get("critique_finding_id"))
        for defect in visual_clash_defects
        for evidence in defect.get("evidence", [])
        if isinstance(evidence, dict) and isinstance(evidence.get("critique_finding_id"), str)
    }
    defects += _critique_finding_defects(
        example_dir,
        name,
        graph_hash,
        visual_clash_finding_ids,
    )
    defects += visual_clash_defects
    for index, defect in enumerate(defects, start=1):
        defect["id"] = f"QD{index:03d}"
        _normalize_detector_defect(defect)
    return defects


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
        detector_defects = _detector_defects(example_dir, name, graph_hash)
        if detector_defects:
            defects = detector_defects
        else:
            text_defect = _text_boundary_defect(example_dir, name, graph_hash)
            defects = (
                [text_defect] if text_defect is not None else [_first_blocker_defect(graph, name)]
            )

    for defect in defects:
        if isinstance(defect, dict):
            defect["source_fingerprint"] = _source_fingerprint(defect)

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
