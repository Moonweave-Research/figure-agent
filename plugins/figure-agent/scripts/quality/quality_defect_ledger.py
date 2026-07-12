"""Build a deterministic read-only defect ledger for figure quality work."""

from __future__ import annotations

import argparse
import json
import re
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import audit_evidence_graph
import audit_evidence_summary
import critique_finding_gate
import fixture_identity
import promotion_wiring
import quality_patch_policy
import runtime_paths
import yaml
from critique_contract import CritiqueContractError, critique_finding_id, critique_findings
from quality_manifest import file_sha256, yaml_frontmatter

SCHEMA = "figure-agent.quality-defect-ledger.v1"
CANDIDATE_SUPPORTED_DEFECT_CLASSES = frozenset(
    {"label_offset", "text_overlap", "whitespace_balance"}
)
# Mirrors candidate_tex_index.PANEL_HINT_RE; kept local because that module is off
# the live ledger path. A `% Panel X` comment line opens a panel region that holds
# until the next marker, mapping each detector source_line to its enclosing panel.
_PANEL_HINT_RE = re.compile(r"^\s*%\s*Panel\s+([A-Za-z0-9_-]+)\b")


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


def _detector_freshness(
    example_dir: Path,
    name: str,
    graph_hash: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    current_hashes = _source_hashes(example_dir, name)
    freshness: dict[str, Any] = {
        "status_input_hash": "sha256:" + "0" * 64,
        "critique_input_hash": "sha256:" + "0" * 64,
        "audit_evidence_graph_hash": graph_hash,
        "source_hashes": current_hashes,
    }
    recorded_hashes = report.get("source_hashes")
    if not isinstance(recorded_hashes, dict) or not recorded_hashes:
        freshness["state"] = "stale"
        freshness["missing_source_hashes"] = True
    elif recorded_hashes != current_hashes:
        freshness["state"] = "stale"
        freshness["recorded_source_hashes"] = recorded_hashes
    return freshness


def _declared_panels(example_dir: Path) -> set[str]:
    try:
        data = yaml.safe_load((example_dir / "spec.yaml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return set()
    spec = data if isinstance(data, dict) else {}
    panels = spec.get("panels")
    if not isinstance(panels, list):
        return set()
    declared: set[str] = set()
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        panel_id = panel.get("id")
        if isinstance(panel_id, str) and panel_id.strip():
            declared.add(panel_id.strip())
    return declared


def _explicit_target(raw: dict[str, Any]) -> dict[str, str]:
    target = raw.get("target")
    if isinstance(target, dict):
        panel = target.get("panel")
        subregion = target.get("subregion")
        if isinstance(panel, str) and panel.strip():
            return {
                "panel": panel.strip(),
                "subregion": subregion.strip()
                if isinstance(subregion, str) and subregion.strip()
                else "label-a",
            }
    panel = raw.get("panel") or raw.get("panel_id")
    if isinstance(panel, str) and panel.strip():
        return {"panel": panel.strip(), "subregion": "label-a"}
    return {"panel": "unknown", "subregion": "label-a"}


def _subregion_for_defect(defect: dict[str, Any], ordinals: dict[tuple[str, str], int]) -> str:
    target = defect.get("target")
    panel = target.get("panel", "unknown") if isinstance(target, dict) else "unknown"
    # 1. Preserve an already-explicit, non-default subregion.
    if isinstance(target, dict):
        existing = target.get("subregion")
        if isinstance(existing, str) and existing.strip() and existing.strip() != "label-a":
            return existing.strip()
    # 2. Selector hash when available (stable across runs).
    selector_hint = defect.get("selector_hint")
    if isinstance(selector_hint, dict):
        sel_hash = selector_hint.get("selector_text_hash")
        if isinstance(sel_hash, str) and sel_hash:
            return f"sel:{sel_hash.split(':')[-1][:12]}"
        value = selector_hint.get("value")
        if isinstance(value, str) and value.strip():
            return f"sel:{_canonical_hash(value.strip()).split(':')[-1][:12]}"
    # 3. Per-(panel, defect_class) ordinal fallback.
    defect_class = str(defect.get("defect_class") or "defect")
    key = (panel, defect_class)
    index = ordinals.get(key, 0)
    ordinals[key] = index + 1
    return f"{defect_class}#{index}"


def _assign_subregion_keys(defects: list[dict[str, Any]]) -> None:
    ordinals: dict[tuple[str, str], int] = {}
    for defect in defects:
        if not isinstance(defect, dict):
            continue
        target = defect.get("target")
        if not isinstance(target, dict):
            target = {"panel": "unknown", "subregion": "label-a"}
            defect["target"] = target
        target["subregion"] = _subregion_for_defect(defect, ordinals)


def _line_selector_hash(example_dir: Path, name: str, line_number: int) -> str | None:
    source = example_dir / f"{name}.tex"
    if not source.is_file():
        return None
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    if line_number < 1 or line_number > len(lines):
        return None
    return _canonical_hash(lines[line_number - 1])


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
        "freshness": _detector_freshness(example_dir, name, graph_hash, data),
        "selector_hint": {"kind": "node_name", "value": candidate.get("text") or "label"},
        "target": _explicit_target(candidate),
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


def _source_panel_map(example_dir: Path, name: str) -> list[tuple[int, str]]:
    """Return ascending (line_number, panel) markers from the fixture .tex."""
    source = example_dir / f"{name}.tex"
    if not source.is_file():
        return []
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    markers: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        match = _PANEL_HINT_RE.match(line)
        if match is not None:
            markers.append((index, match.group(1)))
    return markers


def _panel_for_source_line(markers: list[tuple[int, str]], source_line: int) -> str | None:
    panel: str | None = None
    for marker_line, marker_panel in markers:
        if marker_line <= source_line:
            panel = marker_panel
        else:
            break
    return panel


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
    freshness = _detector_freshness(example_dir, name, graph_hash, data)
    panel_markers = _source_panel_map(example_dir, name)
    defects: list[dict[str, Any]] = []
    defect_by_key: dict[tuple[object, ...], dict[str, Any]] = {}
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
        if source_line < 1:
            continue
        candidate_id = candidate.get("id")
        dedupe_key = (
            source_line,
            candidate.get("kind"),
            candidate.get("nearest_text"),
            tuple(candidate.get("bbox_pt") or ()),
        )
        existing = defect_by_key.get(dedupe_key)
        if existing is not None:
            existing["evidence"].append(
                {
                    "uri": f"figure://{name}/audit/undeclared-geometry",
                    "node_id": candidate_id,
                }
            )
            continue
        selector_hint: dict[str, Any] = {
            "kind": "line_range",
            "value": f"{source_line}:{source_line}",
        }
        selector_hash = _line_selector_hash(example_dir, name, source_line)
        if selector_hash is not None:
            selector_hint["selector_text_hash"] = selector_hash
        # Undeclared-geometry candidates carry no panel of their own. Prefer an
        # explicit candidate panel when present; otherwise map the source_line to
        # the enclosing `% Panel X` marker so the target resolves to a declared id.
        target = _explicit_target(candidate)
        if target["panel"] == "unknown":
            mapped_panel = _panel_for_source_line(panel_markers, source_line)
            if mapped_panel is not None:
                target = {"panel": mapped_panel, "subregion": "label-a"}
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
            "freshness": freshness,
            "selector_hint": selector_hint,
            "target": target,
            "suggested_change": {
                "operation_type": "tikz_coordinate_adjust",
                "summary": "Clear the label endpoint from the nearby text by a bounded amount",
                "patch": "",
            },
        }
        defect_by_key[dedupe_key] = defect
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
    freshness = _detector_freshness(example_dir, name, graph_hash, data)
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
        selector_hint: dict[str, Any] = {"kind": "line_range", "value": f"{start}:{end}"}
        if start == end:
            selector_hash = _line_selector_hash(example_dir, name, start)
            if selector_hash is not None:
                selector_hint["selector_text_hash"] = selector_hash
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
            "freshness": freshness,
            "selector_hint": selector_hint,
            "target": _explicit_target(candidate),
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
        selector_hint: dict[str, Any] = {"kind": "line_range", "value": f"{start}:{end}"}
        if start == end:
            selector_hash = _line_selector_hash(example_dir, name, start)
            if selector_hash is not None:
                selector_hint["selector_text_hash"] = selector_hash
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
            "selector_hint": selector_hint,
            "target": _explicit_target(decision),
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
    defects = promotion_wiring.auto_promoted_defects(example_dir, name)
    defects += promotion_wiring.triage_promoted_defects(example_dir, name)
    defects += _undeclared_geometry_defects(example_dir, name, graph_hash)
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


def _freshness_state(defect: dict[str, Any]) -> str:
    freshness = defect.get("freshness")
    if isinstance(freshness, dict):
        state = freshness.get("state")
        if isinstance(state, str) and state:
            return state
    return "fresh"


def _has_selector_binding(defect: dict[str, Any]) -> bool:
    freshness = defect.get("freshness")
    if not isinstance(freshness, dict):
        return False
    source_hashes = freshness.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        return False
    selector_hint = defect.get("selector_hint")
    return isinstance(selector_hint, dict) and isinstance(
        selector_hint.get("selector_text_hash"),
        str,
    )


def _target_panel(defect: dict[str, Any], declared_panels: set[str]) -> str:
    target = defect.get("target")
    if not isinstance(target, dict):
        return "unknown"
    panel = target.get("panel")
    if not isinstance(panel, str) or not panel.strip():
        return "unknown"
    panel_id = panel.strip()
    return panel_id if panel_id in declared_panels else "unknown"


def _actionability_gaps(defect: dict[str, Any], declared_panels: set[str]) -> list[str]:
    gaps: list[str] = []
    if _freshness_state(defect) == "stale":
        gaps.append("stale_detector_evidence")
    if _target_panel(defect, declared_panels) == "unknown":
        gaps.append("unknown_panel")
    if not _has_selector_binding(defect):
        gaps.append("missing_selector_hash")
    defect_class = str(defect.get("defect_class") or "")
    if defect_class not in CANDIDATE_SUPPORTED_DEFECT_CLASSES:
        gaps.append("unsupported_candidate_family")
    return gaps


def _annotate_actionability(
    defects: list[dict[str, Any]],
    declared_panels: set[str],
) -> dict[str, int]:
    metrics = {
        "safe_candidate_defect_count": 0,
        "candidate_supported_defect_count": 0,
        "unsupported_safe_defect_count": 0,
        "unknown_panel_defect_count": 0,
        "stale_detector_evidence_count": 0,
        "missing_selector_hash_count": 0,
    }
    for defect in defects:
        patchability = defect.get("patchability")
        patchability_state = (
            patchability.get("state") if isinstance(patchability, dict) else None
        )
        if patchability_state not in {"safe_candidate", "assisted_only"}:
            continue
        if patchability_state == "safe_candidate":
            metrics["safe_candidate_defect_count"] += 1
        gaps = _actionability_gaps(defect, declared_panels)
        defect["actionability"] = {
            "state": "blocked" if gaps else "candidate_supported",
            "gaps": gaps,
        }
        if "unsupported_candidate_family" in gaps:
            metrics["unsupported_safe_defect_count"] += 1
        if "unknown_panel" in gaps:
            metrics["unknown_panel_defect_count"] += 1
        if "stale_detector_evidence" in gaps:
            metrics["stale_detector_evidence_count"] += 1
        if "missing_selector_hash" in gaps:
            metrics["missing_selector_hash_count"] += 1
        if not gaps:
            metrics["candidate_supported_defect_count"] += 1
    return metrics


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
    # Slice 2: stamp a distinct, stable sub-region key AFTER the fingerprint so
    # defect identity is unchanged; only target["subregion"] gains a real value.
    _assign_subregion_keys(defects)
    actionability_metrics = _annotate_actionability(defects, _declared_panels(example_dir))

    payload = {
        "schema": SCHEMA,
        "fixture": name,
        "workspace_root": str(paths.workspace_root),
        "defects": defects,
        "actionability_metrics": actionability_metrics,
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
