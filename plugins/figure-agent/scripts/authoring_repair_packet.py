"""Compile one fail-closed, hash-bound authoring repair execution packet."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_initial_review
import critique_contract
import critique_repair_bridge
import human_decision_record
import repair_transaction
import yaml

SCHEMA = "figure-agent.repair-execution-packet.v4"
LEGACY_SCHEMA = "figure-agent.repair-execution-packet.v3"
ATTEMPT_LOCAL_BINDING_SCHEMA = "figure-agent.attempt-local-repair-binding.v2"
ATTEMPT_LOCAL_PACKET_SCHEMA = "figure-agent.attempt-local-repair-packet.v1"
AUTHORITY_CONTRACT_SCHEMA = "figure-agent.repair-authority-contract.v1"
LEGACY_AUTHORITY_MODE = "legacy_explicit_inputs"
BOUND_AUTHORITY_MODE = "adjudicated_binding"
CANONICAL_BINDING_NAME = "critique_repair_binding.json"
MATERIALIZATION_PREVIEW_SCHEMA = "figure-agent.repair-materialization-preview.v1"
CONTRACT_SCHEMA = "figure-agent.repair-target-contract.v1"
SOURCE_ATTEMPT = re.compile(
    r"(?:execution-binding|comparable|execution-repair)-v[1-9][0-9]*"
)
COMPARISON_ATTEMPT = re.compile(r"comparable-v[1-9][0-9]*")
COMPARISON_SOURCE_NAMES = {
    "raw_generated.tex",
    "verified_generated.tex",
    "repaired_generated.tex",
}
REPAIR_SOURCE_NAMES = {"repaired_generated.tex"}
REPAIR_ATTEMPT = re.compile(r"execution-repair-v[1-9][0-9]*")
REPORT_COLLECTIONS = {
    "figure-agent.text-collisions.v1": "collisions",
    "figure-agent.label-hyphenation.v1": "issues",
    "figure-agent.undeclared-geometry.v1": "candidates",
    "figure-agent.visual-clash.v1": "candidates",
    "figure-agent.human-correction-findings.v1": "findings",
}
ALLOWED_REPAIR_FAMILIES = {
    "clipping_repair",
    "contour_contact",
    "label_reflow",
    "local_reposition",
    "panel_rebalance",
    "relation_restore",
    "salience_adjustment",
    "style_normalization",
}
RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["replacement_utf8", "change_summary"],
    "properties": {
        "replacement_utf8": {"type": "string", "minLength": 1},
        "change_summary": {"type": "string", "minLength": 1},
    },
}


class RepairExecutionPacketError(ValueError):
    """Raised when a repair execution packet cannot be bound safely."""


def is_supported_packet_schema(value: object) -> bool:
    """Return whether a serialized repair packet schema remains readable."""
    return value in {SCHEMA, LEGACY_SCHEMA, ATTEMPT_LOCAL_PACKET_SCHEMA}


def is_attempt_local_packet_schema(value: object) -> bool:
    """Return whether a packet uses the R4.13 attempt-local authority graph."""
    return value == ATTEMPT_LOCAL_PACKET_SCHEMA


def attempt_local_packet_path(packet: dict[str, object]) -> str:
    """Return the one canonical packet path accepted by a v2 authorization."""
    binding = packet.get("attempt_local_repair_binding")
    if not isinstance(binding, dict):
        raise RepairExecutionPacketError("attempt-local packet binding invalid")
    binding_relative = _safe_relative(
        str(binding.get("path") or ""), label="attempt-local packet binding"
    )
    if binding_relative.name != "attempt-local-repair-binding.json":
        raise RepairExecutionPacketError("attempt-local packet binding invalid")
    return (binding_relative.parent / "attempt-local-repair-packet.json").as_posix()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_packet_sha256(packet: dict[str, object]) -> str:
    payload = {key: value for key, value in packet.items() if key != "packet_sha256"}
    return _sha256_bytes(_canonical_json_bytes(payload))


def canonical_attempt_local_binding_sha256(binding: dict[str, object]) -> str:
    """Return the immutable digest for an R4.13 attempt-local authority binding."""
    payload = {key: value for key, value in binding.items() if key != "binding_sha256"}
    return _sha256_bytes(_canonical_json_bytes(payload))


def _attempt_local_record(
    value: object,
    *,
    workspace_root: Path,
    label: str,
) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise RepairExecutionPacketError(f"attempt-local {label} record invalid")
    path_value, sha256 = value.get("path"), value.get("sha256")
    if not isinstance(path_value, str) or not isinstance(sha256, str):
        raise RepairExecutionPacketError(f"attempt-local {label} record invalid")
    path = _regular_file(workspace_root, path_value, label=f"attempt-local {label}")
    if _sha256_bytes(path.read_bytes()) != sha256:
        raise RepairExecutionPacketError(f"attempt-local {label} hash drift")
    return {"path": path_value, "sha256": sha256}


def _attempt_local_state(
    state: dict[str, object],
    *,
    workspace_root: Path,
    expected_name: str,
) -> tuple[dict[str, object], Path]:
    value = state.get("previous_state_path")
    if not isinstance(value, str):
        raise RepairExecutionPacketError("attempt-local lineage missing")
    path = _regular_file(workspace_root, value, label="attempt-local previous state")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        validated = closed_loop_attempt_state.validate_state(
            payload,
            workspace_root=workspace_root,
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
    ) as exc:
        raise RepairExecutionPacketError("attempt-local lineage invalid") from exc
    if (
        validated["state"] != expected_name
        or validated["fixture"] != state["fixture"]
        or validated["attempt_id"] != state["attempt_id"]
        or path != closed_loop_attempt_state.state_path(validated, workspace_root=workspace_root)
    ):
        raise RepairExecutionPacketError("attempt-local lineage invalid")
    return validated, path


def _attempt_local_evidence(state: dict[str, object], role: str) -> dict[str, str]:
    matches = [record for record in state["evidence"] if record["role"] == role]
    if len(matches) != 1:
        raise RepairExecutionPacketError("attempt-local lineage evidence missing")
    return {"path": str(matches[0]["path"]), "sha256": str(matches[0]["sha256"])}


def _attempt_local_json_record(
    record: dict[str, str],
    *,
    workspace_root: Path,
    label: str,
) -> dict[str, Any]:
    path = _regular_file(workspace_root, record["path"], label=f"attempt-local {label}")
    try:
        content = path.read_bytes()
        payload = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError(f"attempt-local {label} invalid") from exc
    if _sha256_bytes(content) != record["sha256"]:
        raise RepairExecutionPacketError(f"attempt-local {label} hash drift")
    if not isinstance(payload, dict):
        raise RepairExecutionPacketError(f"attempt-local {label} invalid")
    return payload


def _validate_attempt_local_snapshot_cross_checks(
    binding: dict[str, object],
    *,
    workspace_root: Path,
    handoff_record: dict[str, str],
    critique_record: dict[str, str],
    snapshot_record: dict[str, str],
) -> None:
    """Cross-check the immutable R4.12 snapshot, not just its hash record."""
    snapshot = _attempt_local_json_record(
        snapshot_record,
        workspace_root=workspace_root,
        label="initial attribution binding",
    )
    if (
        snapshot.get("schema") != "figure-agent.initial-attribution-binding.v2"
        or snapshot.get("fixture") != binding["fixture"]
        or snapshot.get("attempt_id") != binding["attempt_id"]
        or snapshot.get("publication_acceptance") != "not_claimed"
        or snapshot.get("binding_sha256")
        != _sha256_bytes(
            _canonical_json_bytes(
                {key: value for key, value in snapshot.items() if key != "binding_sha256"}
            )
        )
    ):
        raise RepairExecutionPacketError("attempt-local attribution snapshot invalid")
    handoff = _attempt_local_json_record(
        handoff_record,
        workspace_root=workspace_root,
        label="attribution handoff",
    )
    if (
        handoff.get("schema") != "figure-agent.initial-attribution-handoff.v1"
        or handoff.get("fixture") != binding["fixture"]
        or handoff.get("attempt_id") != binding["attempt_id"]
        or handoff.get("source_mutation") != "forbidden"
        or handoff.get("publication_acceptance") != "not_claimed"
        or snapshot.get("attribution_handoff") != handoff_record
        or snapshot.get("human_attributor") != handoff.get("human_attributor")
        or snapshot.get("human_attributor") != binding.get("human_attributor")
    ):
        raise RepairExecutionPacketError("attempt-local attribution handoff mismatch")
    selected = handoff.get("selected_finding_ids")
    finding_id = binding.get("selected_finding_id")
    snapshot_critique = snapshot.get("critique")
    if (
        not isinstance(selected, list)
        or selected.count(finding_id) != 1
        or not isinstance(snapshot_critique, dict)
        or snapshot_critique.get("finding_id") != finding_id
        or snapshot_critique.get("path") != critique_record["path"]
        or snapshot_critique.get("sha256") != critique_record["sha256"]
    ):
        raise RepairExecutionPacketError("attempt-local selected finding mismatch")
    critique_path = _regular_file(
        workspace_root,
        critique_record["path"],
        label="attempt-local critique",
    )
    try:
        frontmatter = critique_contract.load_critique_frontmatter(critique_path)
        findings = critique_contract.critique_findings(frontmatter)
        identifiers = {
            critique_contract.critique_finding_id(item, "attempt-local critique finding")
            for item in findings
        }
    except (critique_contract.CritiqueContractError, ValueError) as exc:
        raise RepairExecutionPacketError("attempt-local critique invalid") from exc
    if frontmatter.get("fixture") != binding["fixture"] or finding_id not in identifiers:
        raise RepairExecutionPacketError("attempt-local selected finding mismatch")
    registry_record = snapshot.get("selector_registry")
    semantic_record = snapshot.get("semantic_contract")
    if (
        not isinstance(registry_record, dict)
        or not isinstance(semantic_record, dict)
        or binding.get("semantic_contract") != semantic_record
    ):
        raise RepairExecutionPacketError("attempt-local attribution snapshot invalid")
    registry_reference = {
        "path": str(registry_record.get("path") or ""),
        "sha256": str(registry_record.get("sha256") or ""),
    }
    registry = _attempt_local_json_record(
        registry_reference,
        workspace_root=workspace_root,
        label="selector registry",
    )
    semantic_path = _regular_file(
        workspace_root,
        str(semantic_record.get("path") or ""),
        label="attempt-local semantic contract",
    )
    try:
        semantic = yaml.safe_load(semantic_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RepairExecutionPacketError("attempt-local semantic contract invalid") from exc
    selector_id = snapshot.get("selector_id")
    selectors = registry.get("selectors")
    matches = [
        item
        for item in selectors or []
        if isinstance(item, dict) and item.get("selector_id") == selector_id
    ]
    if (
        len(matches) != 1
        or snapshot.get("repair_family") != binding.get("repair_family")
        or binding.get("selector") != matches[0]
        or binding.get("selector") is None
        or not isinstance(semantic, dict)
    ):
        raise RepairExecutionPacketError("attempt-local selector snapshot mismatch")
    selector = matches[0]
    if (
        selector.get("repair_family") != binding.get("repair_family")
        or not set(selector.get("semantic_object_refs", [])).issubset(
            set(semantic.get("required_objects", []))
        )
        or not set(selector.get("semantic_relation_refs", [])).issubset(
            set(semantic.get("protected_relations", []))
        )
        or semantic.get("publication_acceptance") != "not_claimed"
    ):
        raise RepairExecutionPacketError("attempt-local semantic snapshot mismatch")


def _current_attempt_descends_from(
    *, root: Path, fixture: str, attempt_id: str, ancestor_path: Path
) -> bool:
    """Return whether the canonical current state remains in this exact attempt."""
    projection = closed_loop_current_state.resolve_current_attempt(root, fixture)
    current_value = projection.get("path")
    if (
        projection.get("resolution") != "current"
        or projection.get("attempt_id") != attempt_id
        or not isinstance(current_value, str)
    ):
        return False
    current_path = _regular_file(root, current_value, label="attempt-local current state")
    for _ in range(16):
        if current_path == ancestor_path:
            return True
        try:
            current = json.loads(current_path.read_text(encoding="utf-8"))
            validated = closed_loop_attempt_state.validate_state(current, workspace_root=root)
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            closed_loop_attempt_state.ClosedLoopAttemptStateError,
        ):
            return False
        previous = validated.get("previous_state_path")
        if not isinstance(previous, str):
            return False
        try:
            current_path = _regular_file(root, previous, label="attempt-local previous state")
        except RepairExecutionPacketError:
            return False
    return False


def validate_attempt_local_repair_binding_v2(
    binding: dict[str, object],
    *,
    workspace_root: Path,
    require_current_repair_bound: bool = True,
) -> dict[str, object]:
    """Validate the self-contained R4.13 binding without legacy bridge reads."""
    required = {
        "schema",
        "fixture",
        "attempt_id",
        "current_state",
        "authored_source",
        "render",
        "initial_review_request",
        "initial_visual_review_response",
        "critique",
        "adjudication",
        "attribution_handoff",
        "initial_attribution_binding",
        "crop_manifest",
        "crops",
        "selected_finding_id",
        "human_attributor",
        "selector",
        "repair_family",
        "semantic_contract",
        "publication_acceptance",
        "binding_sha256",
    }
    if (
        set(binding) != required
        or binding.get("schema") != ATTEMPT_LOCAL_BINDING_SCHEMA
        or binding.get("publication_acceptance") != "not_claimed"
        or binding.get("binding_sha256") != canonical_attempt_local_binding_sha256(binding)
        or not isinstance(binding.get("fixture"), str)
        or not str(binding["fixture"]).strip()
        or not isinstance(binding.get("attempt_id"), str)
        or not str(binding["attempt_id"]).strip()
        or not isinstance(binding.get("selected_finding_id"), str)
        or not str(binding["selected_finding_id"]).strip()
    ):
        raise RepairExecutionPacketError("attempt-local binding schema invalid")
    root = workspace_root.resolve()
    normalized: dict[str, object] = dict(binding)
    current_state = binding.get("current_state")
    if not isinstance(current_state, dict) or set(current_state) != {"path", "sha256"}:
        raise RepairExecutionPacketError("attempt-local current state record invalid")
    current_state_path = _regular_file(
        root,
        str(current_state.get("path") or ""),
        label="attempt-local current state",
    )
    try:
        current_state_payload = json.loads(current_state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError("attempt-local current state invalid") from exc
    if current_state.get("sha256") != current_state_payload.get("state_sha256"):
        raise RepairExecutionPacketError("attempt-local current state hash drift")
    try:
        validated_current = closed_loop_attempt_state.validate_state(
            current_state_payload,
            workspace_root=root,
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise RepairExecutionPacketError("attempt-local current state invalid") from exc
    if (
        validated_current["state"] != "repair_bound"
        or validated_current["fixture"] != binding["fixture"]
        or validated_current["attempt_id"] != binding["attempt_id"]
        or current_state_path
        != closed_loop_attempt_state.state_path(validated_current, workspace_root=root)
    ):
        raise RepairExecutionPacketError("attempt-local current state is not repair_bound")
    projection = closed_loop_current_state.resolve_current_attempt(
        root,
        str(binding["fixture"]),
    )
    if require_current_repair_bound:
        current_valid = (
            projection.get("resolution") == "current"
            and projection.get("state") == "repair_bound"
            and projection.get("path") == str(current_state["path"])
            and projection.get("state_sha256") == str(current_state["sha256"])
            and projection.get("attempt_id") == binding["attempt_id"]
        )
    else:
        current_valid = _current_attempt_descends_from(
            root=root,
            fixture=str(binding["fixture"]),
            attempt_id=str(binding["attempt_id"]),
            ancestor_path=current_state_path,
        )
    if not current_valid:
        raise RepairExecutionPacketError("attempt-local current state is not canonical")
    adjudicated, adjudicated_path = _attempt_local_state(
        validated_current,
        workspace_root=root,
        expected_name="adjudicated_unbound",
    )
    critique_state, critique_path = _attempt_local_state(
        adjudicated,
        workspace_root=root,
        expected_name="critique_unadjudicated",
    )
    review_state, review_path = _attempt_local_state(
        critique_state,
        workspace_root=root,
        expected_name="initial_review_requested",
    )
    authored_state, _authored_path = _attempt_local_state(
        review_state,
        workspace_root=root,
        expected_name="authored_rendered",
    )
    try:
        closed_loop_attempt_state.validate_chain(
            [
                authored_state,
                review_state,
                critique_state,
                adjudicated,
                validated_current,
            ],
            workspace_root=root,
        )
        request_path, manifest_path, _request = (
            closed_loop_initial_review.validate_outbound_request_pack(
                state=review_state,
                state_path=review_path,
                workspace_root=root,
            )
        )
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        closed_loop_initial_review.ClosedLoopInitialReviewError,
    ) as exc:
        raise RepairExecutionPacketError("attempt-local initial request invalid") from exc
    expected_records = {
        "authored_source": _attempt_local_evidence(authored_state, "authored_source"),
        "render": _attempt_local_evidence(authored_state, "render"),
        "initial_review_request": _attempt_local_evidence(
            review_state, "initial_visual_review_request"
        ),
        "initial_visual_review_response": _attempt_local_evidence(
            critique_state, "initial_visual_review_response"
        ),
        "critique": _attempt_local_evidence(critique_state, "critique"),
        "adjudication": _attempt_local_evidence(adjudicated, "adjudication"),
        "attribution_handoff": _attempt_local_evidence(
            adjudicated, "attribution_handoff"
        ),
        "initial_attribution_binding": _attempt_local_evidence(
            validated_current, "adjudicated_repair_binding"
        ),
    }
    expected_records["crop_manifest"] = {
        "path": manifest_path.relative_to(root).as_posix(),
        "sha256": _sha256_bytes(manifest_path.read_bytes()),
    }
    for name, expected in expected_records.items():
        if binding.get(name) != expected:
            raise RepairExecutionPacketError("attempt-local lineage evidence mismatch")
    _validate_attempt_local_snapshot_cross_checks(
        binding,
        workspace_root=root,
        handoff_record=expected_records["attribution_handoff"],
        critique_record=expected_records["critique"],
        snapshot_record=expected_records["initial_attribution_binding"],
    )
    normalized["current_state"] = {
        "path": str(current_state["path"]),
        "sha256": str(current_state["sha256"]),
    }
    for key in (
        "authored_source",
        "render",
        "initial_review_request",
        "initial_visual_review_response",
        "critique",
        "adjudication",
        "attribution_handoff",
        "initial_attribution_binding",
        "crop_manifest",
        "semantic_contract",
    ):
        normalized[key] = _attempt_local_record(binding[key], workspace_root=root, label=key)
    crops = binding.get("crops")
    expected_crop_ids = {
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
        "print_178mm",
        "print_thumbnail",
    }
    if not isinstance(crops, list) or len(crops) != len(expected_crop_ids):
        raise RepairExecutionPacketError("attempt-local crops invalid")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError("attempt-local crops invalid") from exc
    manifest_crops = manifest.get("crops") if isinstance(manifest, dict) else None
    manifest_by_id = {
        item.get("id"): item
        for item in manifest_crops or []
        if isinstance(item, dict)
    }
    if set(manifest_by_id) != expected_crop_ids:
        raise RepairExecutionPacketError("attempt-local crops invalid")
    normalized_crops: list[dict[str, str]] = []
    for crop in crops:
        if not isinstance(crop, dict) or set(crop) != {"id", "path", "sha256"}:
            raise RepairExecutionPacketError("attempt-local crops invalid")
        crop_id = crop.get("id")
        if not isinstance(crop_id, str) or crop_id not in expected_crop_ids:
            raise RepairExecutionPacketError("attempt-local crops invalid")
        record = _attempt_local_record(
            {"path": crop.get("path"), "sha256": crop.get("sha256")},
            workspace_root=root,
            label=f"crop {crop_id}",
        )
        normalized_crops.append({"id": crop_id, **record})
    if {crop["id"] for crop in normalized_crops} != expected_crop_ids:
        raise RepairExecutionPacketError("attempt-local crops invalid")
    expected_crops = []
    for crop_id in (
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
        "print_178mm",
        "print_thumbnail",
    ):
        crop = manifest_by_id[crop_id]
        expected_crops.append(
            {
                "id": crop_id,
                "path": f"examples/{binding['fixture']}/{crop.get('path')}",
                "sha256": crop.get("sha256"),
            }
        )
    if crops != expected_crops:
        raise RepairExecutionPacketError("attempt-local crops do not match initial request")
    normalized["crops"] = sorted(normalized_crops, key=lambda crop: crop["id"])
    human = binding.get("human_attributor")
    if (
        not isinstance(human, dict)
        or set(human) != {"kind", "identity"}
        or human.get("kind") != "human"
        or not isinstance(human.get("identity"), str)
        or not human["identity"].strip()
    ):
        raise RepairExecutionPacketError("attempt-local human attributor invalid")
    selector = binding.get("selector")
    selector_keys = {
        "selector_id",
        "anchor_start",
        "anchor_end",
        "repair_role",
        "repair_family",
        "protected_invariants",
        "semantic_object_refs",
        "semantic_relation_refs",
    }
    if not isinstance(selector, dict) or set(selector) != selector_keys:
        raise RepairExecutionPacketError("attempt-local selector invalid")
    if (
        selector.get("repair_role") != "movable"
        or selector.get("repair_family") != binding.get("repair_family")
        or binding.get("repair_family") not in ALLOWED_REPAIR_FAMILIES
    ):
        raise RepairExecutionPacketError("attempt-local repair family invalid")
    for key in (
        "selector_id",
        "anchor_start",
        "anchor_end",
    ):
        if not isinstance(selector.get(key), str) or not str(selector[key]).strip():
            raise RepairExecutionPacketError("attempt-local selector invalid")
    if selector["anchor_start"] == selector["anchor_end"]:
        raise RepairExecutionPacketError("attempt-local selector invalid")
    for key in ("protected_invariants", "semantic_object_refs", "semantic_relation_refs"):
        value = selector.get(key)
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)
            or len(value) != len(set(value))
        ):
            raise RepairExecutionPacketError("attempt-local selector invalid")
    source = root / normalized["authored_source"]["path"]  # type: ignore[index]
    source_text = source.read_text(encoding="utf-8")
    if (
        source_text.count(str(selector["anchor_start"])) != 1
        or source_text.count(str(selector["anchor_end"])) != 1
        or source_text.find(str(selector["anchor_start"]))
        >= source_text.find(str(selector["anchor_end"]))
    ):
        raise RepairExecutionPacketError("attempt-local selector anchor drift")
    return normalized


def compile_attempt_local_repair_packet_v2(
    binding: dict[str, object],
    *,
    binding_path: str,
    sandbox_path: str,
    model_id: str,
    workspace_root: Path,
    require_current_repair_bound: bool = True,
) -> tuple[dict[str, object], str]:
    """Compile an R4.13 packet only; it neither invokes nor materializes a model."""
    if not isinstance(model_id, str) or not model_id.strip():
        raise RepairExecutionPacketError("attempt-local model id invalid")
    root = workspace_root.resolve()
    normalized = validate_attempt_local_repair_binding_v2(
        binding,
        workspace_root=root,
        require_current_repair_bound=require_current_repair_bound,
    )
    binding_relative = _safe_relative(binding_path, label="attempt-local binding")
    sandbox_relative = _safe_relative(sandbox_path, label="attempt-local sandbox")
    current_state = normalized["current_state"]
    assert isinstance(current_state, dict)
    attempt_root = Path(str(current_state["path"])).parent
    expected_binding = attempt_root / "repair-packet" / "attempt-local-repair-binding.json"
    expected_sandbox = attempt_root / "repair-packet" / "repaired.tex"
    if binding_relative != expected_binding:
        raise RepairExecutionPacketError("attempt-local binding path must be canonical")
    if sandbox_relative != expected_sandbox:
        raise RepairExecutionPacketError("attempt-local sandbox path must be canonical")
    source = normalized["authored_source"]
    assert isinstance(source, dict)
    source_path = _regular_file(root, str(source["path"]), label="attempt-local source")
    source_text = source_path.read_text(encoding="utf-8")
    selector = normalized["selector"]
    assert isinstance(selector, dict)
    start = source_text.find(str(selector["anchor_start"]))
    end = source_text.find(str(selector["anchor_end"]))
    editable = source_text[start + len(str(selector["anchor_start"])) : end]
    prompt = (
        "\n".join(
            [
                f"# Attempt-local bounded repair: {normalized['fixture']}",
                "",
                "Return one JSON object with replacement_utf8 and change_summary only.",
                "Do not use filesystem, shell, compile, render, host, or review tools.",
                "Do not modify any source; this is a packet-only planning boundary.",
                f"Repair family: {normalized['repair_family']}",
                f"Selected initial finding: {normalized['selected_finding_id']}",
                f"Editable selector: {selector['selector_id']}",
                f"Anchor start: {selector['anchor_start']}",
                f"Anchor end: {selector['anchor_end']}",
                "Protected invariants:",
                *[f"- {item}" for item in selector["protected_invariants"]],
                "Semantic object references:",
                *[f"- {item}" for item in selector["semantic_object_refs"]],
                "Semantic relation references:",
                *[f"- {item}" for item in selector["semantic_relation_refs"]],
                "",
                "```tex",
                editable.strip("\n"),
                "```",
                "",
                "publication_acceptance: not_claimed",
            ]
        )
        + "\n"
    )
    packet: dict[str, object] = {
        "schema": ATTEMPT_LOCAL_PACKET_SCHEMA,
        "fixture": normalized["fixture"],
        "attempt_id": normalized["attempt_id"],
        "model_id": model_id.strip(),
        "attempt_local_repair_binding": {
            "path": binding_relative.as_posix(),
            "sha256": normalized["binding_sha256"],
        },
        "source": source,
        "repaired_source_sandbox": {
            "path": sandbox_relative.as_posix(),
            "sha256": source["sha256"],
        },
        # The R4.13a sandbox is immutable source evidence.  The materialized
        # candidate must be a distinct additive neighbour, not an overwrite of
        # that snapshot or of the authored source.
        "output_path": (sandbox_relative.parent / "materialized-repair.tex").as_posix(),
        "render": normalized["render"],
        "crops": normalized["crops"],
        "selected_finding_id": normalized["selected_finding_id"],
        "editable_target": {
            "selector": selector,
            "repair_family": normalized["repair_family"],
            "semantic_contract": normalized["semantic_contract"],
        },
        "change_budget": {"max_attempts": 1, "max_source_blocks": 1, "max_changed_lines": 6},
        "author_may_compile": False,
        "author_may_write_files": False,
        "response_schema": RESPONSE_SCHEMA,
        "publication_acceptance": "not_claimed",
        "prompt": {"utf8": prompt, "sha256": _sha256_bytes(prompt.encode("utf-8"))},
    }
    packet["packet_sha256"] = canonical_packet_sha256(packet)
    return packet, prompt


def validate_attempt_local_repair_packet_v2(
    packet: dict[str, object],
    *,
    workspace_root: Path,
) -> dict[str, object]:
    """Validate a v2 packet against its own attempt-local authority only."""
    required = {
        "schema",
        "fixture",
        "attempt_id",
        "model_id",
        "attempt_local_repair_binding",
        "source",
        "repaired_source_sandbox",
        "output_path",
        "render",
        "crops",
        "selected_finding_id",
        "editable_target",
        "change_budget",
        "author_may_compile",
        "author_may_write_files",
        "response_schema",
        "publication_acceptance",
        "prompt",
        "packet_sha256",
    }
    if (
        set(packet) != required
        or packet.get("schema") != ATTEMPT_LOCAL_PACKET_SCHEMA
        or packet.get("packet_sha256") != canonical_packet_sha256(packet)
        or packet.get("publication_acceptance") != "not_claimed"
        or packet.get("author_may_compile") is not False
        or packet.get("author_may_write_files") is not False
        or packet.get("response_schema") != RESPONSE_SCHEMA
        or not isinstance(packet.get("fixture"), str)
        or not str(packet["fixture"]).strip()
        or not isinstance(packet.get("attempt_id"), str)
        or not str(packet["attempt_id"]).strip()
        or not isinstance(packet.get("model_id"), str)
        or not str(packet["model_id"]).strip()
    ):
        raise RepairExecutionPacketError("attempt-local packet schema invalid")
    root = workspace_root.resolve()
    binding_record = packet.get("attempt_local_repair_binding")
    if not isinstance(binding_record, dict) or set(binding_record) != {"path", "sha256"}:
        raise RepairExecutionPacketError("attempt-local packet binding invalid")
    binding_path = _regular_file(
        root,
        str(binding_record.get("path") or ""),
        label="attempt-local packet binding",
    )
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError("attempt-local packet binding invalid") from exc
    if not isinstance(binding, dict):
        raise RepairExecutionPacketError("attempt-local packet binding invalid")
    normalized = validate_attempt_local_repair_binding_v2(
        binding,
        workspace_root=root,
        require_current_repair_bound=False,
    )
    current = normalized["current_state"]
    assert isinstance(current, dict)
    attempt_root = Path(str(current["path"])).parent
    expected_binding = attempt_root / "repair-packet" / "attempt-local-repair-binding.json"
    expected_output = attempt_root / "repair-packet" / "materialized-repair.tex"
    if (
        binding_record.get("path") != expected_binding.as_posix()
        or binding_record.get("sha256") != normalized["binding_sha256"]
        or Path(str(packet.get("output_path") or "")) != expected_output
    ):
        raise RepairExecutionPacketError("attempt-local packet path invalid")
    sandbox = packet.get("repaired_source_sandbox")
    if (
        not isinstance(sandbox, dict)
        or sandbox != {
            "path": (attempt_root / "repair-packet" / "repaired.tex").as_posix(),
            "sha256": normalized["authored_source"]["sha256"],
        }
        or packet.get("source") != normalized["authored_source"]
        or packet.get("render") != normalized["render"]
        or packet.get("crops") != normalized["crops"]
        or packet.get("selected_finding_id") != normalized["selected_finding_id"]
        or packet.get("editable_target")
        != {
            "selector": normalized["selector"],
            "repair_family": normalized["repair_family"],
            "semantic_contract": normalized["semantic_contract"],
        }
        or packet.get("change_budget")
        != {"max_attempts": 1, "max_source_blocks": 1, "max_changed_lines": 6}
    ):
        raise RepairExecutionPacketError("attempt-local packet authority mismatch")
    expected, _prompt = compile_attempt_local_repair_packet_v2(
        normalized,
        binding_path=expected_binding.as_posix(),
        sandbox_path=(attempt_root / "repair-packet" / "repaired.tex").as_posix(),
        model_id=str(packet["model_id"]),
        workspace_root=root,
        require_current_repair_bound=False,
    )
    if packet != expected:
        raise RepairExecutionPacketError("attempt-local packet is not canonical")
    return dict(packet)


def canonical_materialization_preview_sha256(record: dict[str, object]) -> str:
    """Rebuild the exact preview authorized before additive materialization."""
    preview = {
        "schema": MATERIALIZATION_PREVIEW_SCHEMA,
        "fixture": record.get("fixture"),
        "packet_sha256": record.get("packet_sha256"),
        "source_sha256": record.get("source_sha256"),
        "output_path": record.get("output_path"),
        "output_sha256": record.get("output_sha256"),
        "changed_source_blocks": record.get("changed_source_blocks"),
        "changed_lines": record.get("changed_lines"),
        "preserved_boundary_blank_lines": record.get("preserved_boundary_blank_lines"),
        "change_summary": record.get("change_summary"),
        "publication_acceptance": record.get("publication_acceptance"),
    }
    return _sha256_bytes(_canonical_json_bytes(preview))


def validate_materialization_preview(
    preview: dict[str, object],
    *,
    packet: dict[str, object],
) -> None:
    """Validate one dry-run preview against its exact current repair packet."""
    expected_fields = {
        "schema",
        "fixture",
        "packet_sha256",
        "source_sha256",
        "output_path",
        "output_sha256",
        "changed_source_blocks",
        "changed_lines",
        "preserved_boundary_blank_lines",
        "change_summary",
        "publication_acceptance",
        "preview_sha256",
    }
    source = packet.get("source")
    budget = packet.get("change_budget")
    changed_lines = preview.get("changed_lines")
    preserved_blank_lines = preview.get("preserved_boundary_blank_lines")
    output_sha256 = preview.get("output_sha256")
    if (
        set(preview) != expected_fields
        or preview.get("schema") != MATERIALIZATION_PREVIEW_SCHEMA
        or preview.get("fixture") != packet.get("fixture")
        or preview.get("packet_sha256") != packet.get("packet_sha256")
        or not isinstance(source, dict)
        or preview.get("source_sha256") != source.get("sha256")
        or preview.get("output_path") != packet.get("output_path")
        or preview.get("changed_source_blocks") != 1
        or not isinstance(output_sha256, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", output_sha256)
        or type(changed_lines) is not int
        or changed_lines < 1
        or not isinstance(budget, dict)
        or type(budget.get("max_changed_lines")) is not int
        or changed_lines > int(budget["max_changed_lines"])
        or type(preserved_blank_lines) is not int
        or preserved_blank_lines < 0
        or not isinstance(preview.get("change_summary"), str)
        or not str(preview["change_summary"]).strip()
        or preview.get("publication_acceptance") != "not_claimed"
        or preview.get("preview_sha256") != canonical_materialization_preview_sha256(preview)
    ):
        raise RepairExecutionPacketError("materialization preview invalid")


def _safe_relative(value: str, *, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RepairExecutionPacketError(f"{label} must be repository-relative and safe")
    return path


def _safe_execution_cwd(value: str) -> str:
    if value == ".":
        return value
    return _safe_relative(value, label="execution cwd").as_posix()


def _regular_file(workspace_root: Path, value: str, *, label: str) -> Path:
    relative = _safe_relative(value, label=label)
    current = workspace_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RepairExecutionPacketError(f"{label} must not traverse a symlink")
    if not current.is_file():
        raise RepairExecutionPacketError(f"{label} must be a regular file")
    return current


def _fixture_attempt_path(
    relative: Path,
    *,
    fixture: str,
    attempt_pattern: re.Pattern[str],
    label: str,
) -> None:
    root = Path("examples") / fixture / "review" / "failure-first"
    if relative.parent.parent != root or not attempt_pattern.fullmatch(relative.parent.name):
        attempt_name = (
            "execution-binding-vN, comparable-vN, or execution-repair-vN"
            if attempt_pattern is SOURCE_ATTEMPT
            else "execution-repair-vN"
        )
        raise RepairExecutionPacketError(f"{label} must be inside {attempt_name}")


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise RepairExecutionPacketError(f"{label} must be a JSON object")
    return payload


def _load_json_bytes(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairExecutionPacketError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise RepairExecutionPacketError(f"{label} must be a JSON object")
    return payload


def _authority_contract(mode: str) -> dict[str, object]:
    return {
        "schema": AUTHORITY_CONTRACT_SCHEMA,
        "mode": mode,
        "required_record": ("adjudicated_repair_binding" if mode == BOUND_AUTHORITY_MODE else None),
    }


def _packet_authority_mode(packet: dict[str, object], workspace_root: Path) -> tuple[str, Path]:
    schema = packet.get("schema")
    contract = packet.get("authority_contract")
    if schema == LEGACY_SCHEMA:
        if contract is not None:
            raise RepairExecutionPacketError("legacy packet must not carry a v4 authority contract")
        mode = (
            BOUND_AUTHORITY_MODE
            if packet.get("adjudicated_repair_binding") is not None
            else LEGACY_AUTHORITY_MODE
        )
    else:
        if not isinstance(contract, dict) or set(contract) != {
            "schema",
            "mode",
            "required_record",
        }:
            raise RepairExecutionPacketError("packet authority contract is invalid")
        mode = contract.get("mode")
        if contract != _authority_contract(str(mode or "")) or mode not in {
            LEGACY_AUTHORITY_MODE,
            BOUND_AUTHORITY_MODE,
        }:
            raise RepairExecutionPacketError("packet authority contract is invalid")

    target_record = packet.get("target_contract")
    if not isinstance(target_record, dict):
        raise RepairExecutionPacketError("packet target contract invalid")
    target_relative = _safe_relative(str(target_record.get("path") or ""), label="target contract")
    canonical_binding = target_relative.parent / CANONICAL_BINDING_NAME
    canonical_path = workspace_root / canonical_binding
    canonical_binding_present = canonical_path.exists() or canonical_path.is_symlink()
    if canonical_binding_present and mode != BOUND_AUTHORITY_MODE:
        raise RepairExecutionPacketError("attempt requires adjudicated binding authority")
    return str(mode), canonical_binding


def validate_bound_packet_authority(
    packet: dict[str, object],
    workspace_root: Path,
    *,
    allow_legacy_packet: bool = False,
) -> None:
    """Revalidate the live adjudicated authority graph for a bound packet."""
    workspace_root = workspace_root.resolve()
    if is_attempt_local_packet_schema(packet.get("schema")):
        validate_attempt_local_repair_packet_v2(packet, workspace_root=workspace_root)
        return
    authority_mode, canonical_binding = _packet_authority_mode(packet, workspace_root)
    if (
        packet.get("schema") == LEGACY_SCHEMA or authority_mode == LEGACY_AUTHORITY_MODE
    ) and not allow_legacy_packet:
        raise RepairExecutionPacketError(
            "legacy repair packet requires explicit compatibility opt-in"
        )
    binding_record = packet.get("adjudicated_repair_binding")
    if authority_mode == LEGACY_AUTHORITY_MODE:
        if binding_record is not None:
            raise RepairExecutionPacketError(
                "legacy packet must not carry adjudicated binding authority"
            )
        return
    if binding_record is None:
        raise RepairExecutionPacketError("adjudicated binding authority record is required")
    if not isinstance(binding_record, dict) or set(binding_record) != {
        "path",
        "sha256",
    }:
        raise RepairExecutionPacketError("adjudicated repair binding record is invalid")
    fixture = packet.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise RepairExecutionPacketError("packet fixture invalid")
    binding_relative = _safe_relative(
        str(binding_record.get("path") or ""), label="adjudicated binding"
    )
    if binding_relative != canonical_binding:
        raise RepairExecutionPacketError(
            "adjudicated binding must be canonical and target-adjacent"
        )
    binding_path = _regular_file(
        workspace_root,
        binding_relative.as_posix(),
        label="adjudicated binding",
    )
    try:
        binding, _binding_paths, binding_sha256 = (
            critique_repair_bridge.validate_adjudicated_repair_binding_snapshot(
                binding_relative,
                fixture=fixture,
                workspace_root=workspace_root,
            )
        )
    except critique_repair_bridge.CritiqueRepairBridgeError as exc:
        raise RepairExecutionPacketError(str(exc)) from exc
    if (
        binding_record.get("sha256") != binding_sha256
        or _sha256_bytes(binding_path.read_bytes()) != binding_sha256
    ):
        raise RepairExecutionPacketError("adjudicated binding hash drift")

    editable = packet.get("editable_target")
    finding_reports = packet.get("finding_reports")
    machine_finding = binding["machine_finding"]
    if (
        packet.get("source") != binding["source"]
        or packet.get("target_contract") != binding["target_contract"]
        or not isinstance(editable, dict)
        or editable.get("finding_id") != machine_finding["finding_id"]
        or editable.get("report_path") != machine_finding["report_path"]
        or not isinstance(finding_reports, list)
    ):
        raise RepairExecutionPacketError("bound packet authority substitution detected")
    matching_reports = [
        report
        for report in finding_reports
        if isinstance(report, dict) and report.get("path") == machine_finding["report_path"]
    ]
    if (
        len(matching_reports) != 1
        or matching_reports[0].get("sha256") != machine_finding["report_sha256"]
    ):
        raise RepairExecutionPacketError("bound packet finding report substitution detected")


def _report_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    collection = REPORT_COLLECTIONS.get(str(report.get("schema")))
    if collection is None:
        raise RepairExecutionPacketError("finding report schema is unsupported")
    findings = report.get(collection)
    if not isinstance(findings, list):
        raise RepairExecutionPacketError("finding report collection is invalid")
    return [finding for finding in findings if isinstance(finding, dict)]


def _exact_selector(target: dict[str, Any], source_text: str, source_hash: str) -> dict[str, str]:
    selector = target.get("selector")
    required = ("selector_id", "anchor_start", "anchor_end")
    if (
        not isinstance(selector, dict)
        or selector.get("kind") != "semantic_anchor"
        or any(
            not isinstance(selector.get(field), str) or not selector[field] for field in required
        )
    ):
        raise RepairExecutionPacketError("exact semantic selector required")
    start = str(selector["anchor_start"])
    end = str(selector["anchor_end"])
    lines = source_text.splitlines()
    starts = [index for index, line in enumerate(lines) if line == start]
    ends = [index for index, line in enumerate(lines) if line == end]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise RepairExecutionPacketError("exact semantic selector required")
    return {
        "kind": "semantic_anchor",
        "selector_id": str(selector["selector_id"]),
        "anchor_start": start,
        "anchor_end": end,
        "source_hash": source_hash,
    }


def _render_prompt(
    *,
    fixture: str,
    model_id: str,
    repository_output_path: str,
    source_path: str,
    editable_source: str,
    target: dict[str, Any],
) -> str:
    selector = target["selector"]
    finding = json.dumps(target["finding"], sort_keys=True, ensure_ascii=False)
    invariants = target["protected_invariants"]
    return "\n".join(
        [
            f"# Bound repair execution: {fixture}",
            "",
            "## Single-attempt boundary",
            "- Return one JSON object matching the bound response schema.",
            "- Do not use filesystem or shell tools.",
            "- Put only the replacement content between the anchors in the replacement_utf8 field.",
            "- Put a concise factual description in the change_summary field.",
            "- The controller will materialize a validated candidate at "
            f"[{repository_output_path}].",
            f"- Reproduce the complete bound source from [{source_path}] below.",
            "- Perform one repair attempt only.",
            "- Do not compile, render, or run a gate.",
            "- Do not inspect any historical source or review artifact.",
            "- Do not overwrite the bound source or any existing artifact.",
            "- Change at most six source lines in one source block.",
            "",
            "## Exact editable boundary",
            f"- Repair family: {target['repair_family']}",
            f"- Machine finding: {finding}",
            "- Change content only between the exact anchor lines "
            f"[{selector['anchor_start']}] and [{selector['anchor_end']}].",
            "- Keep both anchor lines byte-identical.",
            "- Do not act on ambiguous or unbound findings.",
            "",
            "## Protected scientific invariants",
            *[f"- Preserve the exact token [{token}]." for token in invariants],
            "",
            "## Bound editable source bytes",
            "```tex",
            editable_source.rstrip("\n"),
            "```",
            "",
            "## Provenance boundary",
            f"- Declared model: {model_id}",
            "- feedback_rounds: 1",
            "- manual_repairs: 0",
            "- publication_acceptance: not_claimed",
            "",
        ]
    )


def compile_repair_execution_packet(
    fixture: str,
    *,
    workspace_root: Path,
    model_id: str,
    source_path: str,
    target_contract: str,
    output_path: str,
    execution_cwd: str = ".",
) -> tuple[dict[str, object], str]:
    """Compile one packet without executing an authoring model or a renderer."""
    if not model_id.strip():
        raise RepairExecutionPacketError("model_id must be non-empty")
    workspace_root = workspace_root.resolve()
    source_relative = _safe_relative(source_path, label="source path")
    _fixture_attempt_path(
        source_relative,
        fixture=fixture,
        attempt_pattern=SOURCE_ATTEMPT,
        label="source path",
    )
    if (
        COMPARISON_ATTEMPT.fullmatch(source_relative.parent.name)
        and source_relative.name not in COMPARISON_SOURCE_NAMES
    ):
        raise RepairExecutionPacketError("source path must name a declared comparable arm")
    if (
        REPAIR_ATTEMPT.fullmatch(source_relative.parent.name)
        and source_relative.name not in REPAIR_SOURCE_NAMES
    ):
        raise RepairExecutionPacketError("source path must name a materialized repair output")
    source = _regular_file(workspace_root, source_path, label="source path")
    source_bytes = source.read_bytes()
    source_hash = _sha256_bytes(source_bytes)
    source_text = source_bytes.decode("utf-8")

    contract_relative = _safe_relative(target_contract, label="target contract")
    _fixture_attempt_path(
        contract_relative,
        fixture=fixture,
        attempt_pattern=REPAIR_ATTEMPT,
        label="target contract",
    )
    contract_path = _regular_file(workspace_root, target_contract, label="target contract")
    contract = _load_json(contract_path, label="target contract")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise RepairExecutionPacketError("target contract schema is invalid")
    if contract.get("source_path") != source_relative.as_posix():
        raise RepairExecutionPacketError("target contract source path drift")
    if contract.get("source_sha256") != source_hash:
        raise RepairExecutionPacketError("source hash drift")

    output_relative = _safe_relative(output_path, label="output path")
    _fixture_attempt_path(
        output_relative,
        fixture=fixture,
        attempt_pattern=REPAIR_ATTEMPT,
        label="output path",
    )
    if output_relative.suffix != ".tex":
        raise RepairExecutionPacketError("output path must be a .tex file")
    output = workspace_root / output_relative
    if output.exists() or output.is_symlink():
        raise RepairExecutionPacketError("output path already exists")
    if source_relative.parent == output_relative.parent:
        raise RepairExecutionPacketError("repair output must use a later additive attempt")
    if contract_relative.parent != output_relative.parent:
        raise RepairExecutionPacketError("target contract must be adjacent to the declared output")

    targets = contract.get("targets")
    if not isinstance(targets, list) or not targets:
        raise RepairExecutionPacketError("target contract must declare targets")
    exact_targets: list[dict[str, Any]] = []
    review_only: list[dict[str, str]] = []
    reports: dict[str, tuple[dict[str, Any], str]] = {}
    referenced_findings: set[tuple[str, str]] = set()
    for raw_target in targets:
        if not isinstance(raw_target, dict):
            raise RepairExecutionPacketError("repair target must be an object")
        finding_ref = raw_target.get("finding")
        if not isinstance(finding_ref, dict):
            raise RepairExecutionPacketError("repair target finding reference is invalid")
        report_relative = _safe_relative(
            str(finding_ref.get("report_path") or ""), label="finding report"
        )
        _fixture_attempt_path(
            report_relative,
            fixture=fixture,
            attempt_pattern=REPAIR_ATTEMPT,
            label="finding report",
        )
        report_key = report_relative.as_posix()
        if report_key not in reports:
            report_path = _regular_file(workspace_root, report_key, label="finding report")
            report_bytes = report_path.read_bytes()
            reports[report_key] = (
                _load_json_bytes(report_bytes, label="finding report"),
                _sha256_bytes(report_bytes),
            )
        report, _report_sha256 = reports[report_key]
        if (
            report.get("schema") == "figure-agent.human-correction-findings.v1"
            and report.get("bound_source_sha256") != source_hash
        ):
            raise RepairExecutionPacketError("human finding source hash drift")
        finding_id = str(finding_ref.get("id") or "")
        matches = [
            finding for finding in _report_findings(report) if finding.get("id") == finding_id
        ]
        if len(matches) != 1:
            raise RepairExecutionPacketError("finding id must resolve exactly once")
        referenced_findings.add((report_key, finding_id))
        state = (raw_target.get("attribution") or {}).get("state")
        if state != "exact":
            review_only.append({"finding_id": finding_id, "attribution": str(state)})
            continue
        repair_family = raw_target.get("repair_family")
        if repair_family not in ALLOWED_REPAIR_FAMILIES:
            raise RepairExecutionPacketError("repair family is unsupported")
        invariants = raw_target.get("protected_invariants")
        if (
            not isinstance(invariants, list)
            or not invariants
            or any(not isinstance(token, str) or not token for token in invariants)
            or any(source_text.count(token) == 0 for token in invariants)
        ):
            raise RepairExecutionPacketError("protected invariants are invalid")
        exact_targets.append(
            {
                "finding_id": finding_id,
                "finding": matches[0],
                "report_path": report_key,
                "repair_family": repair_family,
                "selector": _exact_selector(raw_target, source_text, source_hash),
                "protected_invariants": list(invariants),
            }
        )
    for report_key, (report, _report_sha256) in sorted(reports.items()):
        for finding in _report_findings(report):
            finding_id = finding.get("id")
            if isinstance(finding_id, str) and (report_key, finding_id) not in referenced_findings:
                review_only.append({"finding_id": finding_id, "attribution": "unbound"})
    if len(exact_targets) != 1:
        raise RepairExecutionPacketError("exact attribution required for one repair target")

    editable = exact_targets[0]
    source_lines = source_text.splitlines()
    editable_start, editable_end = _anchor_indexes(source_text, editable["selector"])
    editable_source = "\n".join(source_lines[editable_start + 1 : editable_end]) + "\n"
    bound_execution_cwd = _safe_execution_cwd(execution_cwd)
    repository_output_path = (Path(bound_execution_cwd) / output_relative).as_posix()
    report_records = [
        {
            "path": path,
            "schema": report["schema"],
            "sha256": report_sha256,
        }
        for path, (report, report_sha256) in sorted(reports.items())
    ]
    prompt = _render_prompt(
        fixture=fixture,
        model_id=model_id.strip(),
        repository_output_path=repository_output_path,
        source_path=source_relative.as_posix(),
        editable_source=editable_source,
        target=editable,
    )
    packet: dict[str, object] = {
        "schema": SCHEMA,
        "authority_contract": _authority_contract(LEGACY_AUTHORITY_MODE),
        "fixture": fixture,
        "model_id": model_id.strip(),
        "source": {"path": source_relative.as_posix(), "sha256": source_hash},
        "target_contract": {
            "path": contract_relative.as_posix(),
            "sha256": _sha256_bytes(contract_path.read_bytes()),
        },
        "finding_reports": report_records,
        "editable_target": editable,
        "review_only_findings": sorted(
            review_only, key=lambda item: (item["finding_id"], item["attribution"])
        ),
        "output_path": output_relative.as_posix(),
        "repository_output_path": repository_output_path,
        "execution_cwd": bound_execution_cwd,
        "change_budget": {
            "max_attempts": 1,
            "max_source_blocks": 1,
            "max_changed_lines": 6,
        },
        "author_may_compile": False,
        "author_may_write_files": False,
        "verification": "external_sequential_compile_required",
        "publication_acceptance": "not_claimed",
        "response_schema": RESPONSE_SCHEMA,
        "prompt": {"utf8": prompt, "sha256": _sha256_bytes(prompt.encode("utf-8"))},
    }
    packet["packet_sha256"] = canonical_packet_sha256(packet)
    return packet, prompt


def compile_adjudicated_repair_execution_packet(
    fixture: str,
    *,
    workspace_root: Path,
    model_id: str,
    binding_path: str,
    output_path: str,
    execution_cwd: str = ".",
) -> tuple[dict[str, object], str]:
    """Compile a repair packet whose source and target come from one binding."""
    workspace_root = workspace_root.resolve()
    binding_relative = _safe_relative(binding_path, label="adjudicated binding")
    try:
        binding, _binding_paths, binding_sha256 = (
            critique_repair_bridge.validate_adjudicated_repair_binding_snapshot(
                binding_relative,
                fixture=fixture,
                workspace_root=workspace_root,
            )
        )
    except critique_repair_bridge.CritiqueRepairBridgeError as exc:
        raise RepairExecutionPacketError(str(exc)) from exc
    if "semantic_attribution" not in binding:
        raise RepairExecutionPacketError(
            "current v4 repair packets require semantic attribution authority"
        )
    source_record = binding["source"]
    target_record = binding["target_contract"]
    target_relative = _safe_relative(target_record["path"], label="binding target contract")
    output_relative = _safe_relative(output_path, label="output path")
    _fixture_attempt_path(
        output_relative,
        fixture=fixture,
        attempt_pattern=REPAIR_ATTEMPT,
        label="output path",
    )
    if not (binding_relative.parent == target_relative.parent == output_relative.parent):
        raise RepairExecutionPacketError("binding, target contract, and output must be adjacent")

    packet, prompt = compile_repair_execution_packet(
        fixture,
        workspace_root=workspace_root,
        model_id=model_id,
        source_path=source_record["path"],
        target_contract=target_record["path"],
        output_path=output_relative.as_posix(),
        execution_cwd=execution_cwd,
    )
    if (
        packet.get("source") != source_record
        or packet.get("target_contract") != target_record
        or not isinstance(packet.get("editable_target"), dict)
        or packet["editable_target"].get("finding_id") != binding["machine_finding"]["finding_id"]
        or packet["editable_target"].get("report_path") != binding["machine_finding"]["report_path"]
    ):
        raise RepairExecutionPacketError("compiled packet authority substitution detected")
    try:
        revalidated, _binding_paths, revalidated_binding_sha256 = (
            critique_repair_bridge.validate_adjudicated_repair_binding_snapshot(
                binding_relative,
                fixture=fixture,
                workspace_root=workspace_root,
            )
        )
    except critique_repair_bridge.CritiqueRepairBridgeError as exc:
        raise RepairExecutionPacketError(str(exc)) from exc
    if revalidated != binding or revalidated_binding_sha256 != binding_sha256:
        raise RepairExecutionPacketError("adjudicated binding hash drift")

    packet["adjudicated_repair_binding"] = {
        "path": binding_relative.as_posix(),
        "sha256": binding_sha256,
    }
    packet["authority_contract"] = _authority_contract(BOUND_AUTHORITY_MODE)
    packet["packet_sha256"] = canonical_packet_sha256(packet)
    return packet, prompt


def _anchor_indexes(text: str, selector: dict[str, Any]) -> tuple[int, int]:
    lines = text.splitlines()
    start_marker = str(selector["anchor_start"])
    end_marker = str(selector["anchor_end"])
    starts = [index for index, line in enumerate(lines) if line == start_marker]
    ends = [index for index, line in enumerate(lines) if line == end_marker]
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        raise RepairExecutionPacketError("candidate exact anchor drift")
    return starts[0], ends[0]


def materialize_repair_candidate(
    packet: dict[str, object],
    response: dict[str, object],
    *,
    workspace_root: Path,
    authorization: dict[str, object] | None = None,
    apply: bool = True,
    receipt_path: Path | None = None,
    allow_legacy_packet: bool = False,
    response_provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    """Validate an LLM response and materialize its additive source once."""
    if is_attempt_local_packet_schema(packet.get("schema")):
        return materialize_attempt_local_repair_candidate_v2(
            packet,
            response,
            workspace_root=workspace_root,
            authorization=authorization,
            apply=apply,
            receipt_path=receipt_path,
            response_provenance=response_provenance,
        )
    if not is_supported_packet_schema(packet.get("schema")):
        raise RepairExecutionPacketError("packet schema invalid")
    if packet.get("packet_sha256") != canonical_packet_sha256(packet):
        raise RepairExecutionPacketError("packet hash drift")
    workspace_root = workspace_root.resolve()
    validate_bound_packet_authority(
        packet,
        workspace_root,
        allow_legacy_packet=allow_legacy_packet,
    )
    if set(response) != {"replacement_utf8", "change_summary"}:
        raise RepairExecutionPacketError("candidate response schema invalid")
    replacement = response.get("replacement_utf8")
    summary = response.get("change_summary")
    if (
        not isinstance(replacement, str)
        or not replacement
        or not isinstance(summary, str)
        or not summary.strip()
    ):
        raise RepairExecutionPacketError("candidate response schema invalid")
    if re.search(r"\\[nr](?:[ \t]|$)", replacement):
        raise RepairExecutionPacketError("replacement contains literal escaped newline")

    source_record = packet.get("source")
    if not isinstance(source_record, dict):
        raise RepairExecutionPacketError("packet source invalid")
    source_path = _regular_file(
        workspace_root, str(source_record.get("path") or ""), label="source path"
    )
    source_bytes = source_path.read_bytes()
    if source_record.get("sha256") != _sha256_bytes(source_bytes):
        raise RepairExecutionPacketError("source hash drift")
    original = source_bytes.decode("utf-8")

    editable = packet.get("editable_target")
    selector = editable.get("selector") if isinstance(editable, dict) else None
    invariants = (
        selector.get("protected_invariants")
        if is_attempt_local_packet_schema(packet.get("schema")) and isinstance(selector, dict)
        else editable.get("protected_invariants") if isinstance(editable, dict) else None
    )
    if not isinstance(selector, dict) or not isinstance(invariants, list):
        raise RepairExecutionPacketError("packet editable target invalid")
    if (
        not is_attempt_local_packet_schema(packet.get("schema"))
        and selector.get("source_hash") != source_record.get("sha256")
    ):
        raise RepairExecutionPacketError("selector source hash drift")
    original_start, original_end = _anchor_indexes(original, selector)
    replacement_lines = replacement.splitlines()
    if any(
        line in {selector["anchor_start"], selector["anchor_end"]} for line in replacement_lines
    ):
        raise RepairExecutionPacketError("replacement must not contain anchor lines")

    original_lines = original.splitlines()
    editable_lines = original_lines[original_start + 1 : original_end]
    leading_padding = next(
        (index for index, line in enumerate(editable_lines) if line.strip()),
        len(editable_lines),
    )
    trailing_padding = next(
        (index for index, line in enumerate(reversed(editable_lines)) if line.strip()),
        len(editable_lines),
    )
    replacement_leading = next(
        (index for index, line in enumerate(replacement_lines) if line.strip()),
        len(replacement_lines),
    )
    replacement_trailing = next(
        (index for index, line in enumerate(reversed(replacement_lines)) if line.strip()),
        len(replacement_lines),
    )
    added_leading = max(0, leading_padding - replacement_leading)
    added_trailing = max(0, trailing_padding - replacement_trailing)
    replacement_lines = [
        *([""] * added_leading),
        *replacement_lines,
        *([""] * added_trailing),
    ]
    candidate_lines = [
        *original_lines[: original_start + 1],
        *replacement_lines,
        *original_lines[original_end:],
    ]
    candidate = "\n".join(candidate_lines) + ("\n" if original.endswith("\n") else "")
    candidate_start, candidate_end = _anchor_indexes(candidate, selector)
    changes = [
        opcode
        for opcode in difflib.SequenceMatcher(
            a=original_lines, b=candidate_lines, autojunk=False
        ).get_opcodes()
        if opcode[0] != "equal"
    ]
    if len(changes) != 1:
        raise RepairExecutionPacketError("candidate must change one source block")
    _tag, old_start, old_end, new_start, new_end = changes[0]
    old_inside = (
        original_start < old_start <= original_end
        if old_start == old_end
        else original_start < old_start and old_end <= original_end
    )
    new_inside = (
        candidate_start < new_start <= candidate_end
        if new_start == new_end
        else candidate_start < new_start and new_end <= candidate_end
    )
    if not old_inside or not new_inside:
        raise RepairExecutionPacketError("candidate changed outside exact anchor")

    budget = packet.get("change_budget")
    max_changed_lines = budget.get("max_changed_lines") if isinstance(budget, dict) else None
    changed_lines = (old_end - old_start) + (new_end - new_start)
    if not isinstance(max_changed_lines, int) or changed_lines > max_changed_lines:
        raise RepairExecutionPacketError("candidate change budget exceeded")
    for token in invariants:
        if (
            not isinstance(token, str)
            or not token
            or original.count(token) != candidate.count(token)
        ):
            raise RepairExecutionPacketError("protected invariant changed")

    output_relative = _safe_relative(str(packet.get("output_path") or ""), label="output path")
    output_sha256 = _sha256_bytes(candidate.encode("utf-8"))
    preview = {
        "schema": MATERIALIZATION_PREVIEW_SCHEMA,
        "fixture": packet.get("fixture"),
        "packet_sha256": packet["packet_sha256"],
        "source_sha256": source_record["sha256"],
        "output_path": output_relative.as_posix(),
        "output_sha256": output_sha256,
        "changed_source_blocks": 1,
        "changed_lines": changed_lines,
        "preserved_boundary_blank_lines": added_leading + added_trailing,
        "change_summary": summary.strip(),
        "publication_acceptance": "not_claimed",
    }
    preview["preview_sha256"] = canonical_materialization_preview_sha256(preview)
    if not apply:
        return preview
    if not isinstance(authorization, dict):
        raise RepairExecutionPacketError("materialization authorization missing")
    try:
        normalized_authorization = (
            human_decision_record.validate_additive_materialization_authorization(
                authorization,
                fixture=str(packet.get("fixture") or ""),
                packet_schema=str(packet.get("schema") or ""),
                packet_sha256=str(packet.get("packet_sha256") or ""),
                output_path=output_relative.as_posix(),
                output_sha256=output_sha256,
                preview_sha256=str(preview["preview_sha256"]),
            )
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise RepairExecutionPacketError(f"materialization authorization invalid: {exc}") from exc
    output = workspace_root / output_relative
    bound_response: dict[str, object] | None = None
    if response_provenance is not None:
        if set(response_provenance) != {"path", "sha256", "payload"}:
            raise RepairExecutionPacketError("repair response provenance invalid")
        response_path = _regular_file(
            workspace_root,
            str(response_provenance.get("path") or ""),
            label="repair response path",
        )
        try:
            response_bytes = response_path.read_bytes()
            response_payload = json.loads(response_bytes)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairExecutionPacketError("repair response provenance invalid") from exc
        if (
            response_path.parent != output.parent
            or response_provenance.get("sha256") != _sha256_bytes(response_bytes)
            or response_provenance.get("payload") != response
            or response_payload != response
        ):
            raise RepairExecutionPacketError("repair response provenance invalid")
        bound_response = dict(response_provenance)
    if receipt_path is None:
        raise RepairExecutionPacketError("materialization receipt path missing")
    resolved_receipt = (
        receipt_path if receipt_path.is_absolute() else workspace_root / receipt_path
    ).resolve(strict=False)
    try:
        resolved_receipt.relative_to(workspace_root)
    except ValueError as exc:
        raise RepairExecutionPacketError(
            "materialization receipt path must remain inside workspace"
        ) from exc
    if resolved_receipt.parent != output.parent:
        raise RepairExecutionPacketError("materialization receipt must be adjacent to output")
    if output.exists() or output.is_symlink():
        raise RepairExecutionPacketError("output path already exists")
    if resolved_receipt.exists() or resolved_receipt.is_symlink():
        raise RepairExecutionPacketError("materialization receipt already exists")
    current = workspace_root
    for part in output_relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise RepairExecutionPacketError("output path must not traverse a symlink")
    receipt = {
        "schema": "figure-agent.repair-materialization-receipt.v2",
        "decision": "materialized_verification_pending",
        **{key: value for key, value in preview.items() if key != "schema"},
        "authorization": {
            "reviewer": normalized_authorization["reviewer"],
            "record_sha256": _sha256_bytes(_canonical_json_bytes(authorization)),
            "authorized_packet_sha256": normalized_authorization["authorized_packet_sha256"],
            "authorized_output_path": normalized_authorization["authorized_output_path"],
            "authorized_output_sha256": normalized_authorization["authorized_output_sha256"],
            "authorized_preview_sha256": normalized_authorization["authorized_preview_sha256"],
        },
        **({"repair_response": bound_response} if bound_response is not None else {}),
        "rollback": {
            "strategy": "delete_materialized_output_if_hash_matches",
            "pre_transaction_state": "absent",
            "output_path": output_relative.as_posix(),
            "output_sha256": output_sha256,
        },
        "post_render_verification": "pending",
        "external_compile": "pending",
        "human_review": "pending",
        "publication_acceptance": "not_claimed",
        "recovery_required": False,
    }
    try:
        with repair_transaction.recoverable_exclusive_lock(
            output.parent / ".materialization.lock",
            owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
        ):
            validate_bound_packet_authority(
                packet,
                workspace_root,
                allow_legacy_packet=allow_legacy_packet,
            )
            if output.exists() or output.is_symlink():
                raise RepairExecutionPacketError("output path already exists")
            if resolved_receipt.exists() or resolved_receipt.is_symlink():
                raise RepairExecutionPacketError("materialization receipt already exists")
            if _sha256_bytes(source_path.read_bytes()) != source_record["sha256"]:
                raise RepairExecutionPacketError("source hash drift")
            prepared_receipt = {
                **receipt,
                "decision": "materialization_prepared",
                "recovery_required": True,
            }
            repair_transaction.atomic_write_json(resolved_receipt, prepared_receipt)
            repair_transaction.atomic_write_text(output, candidate)
            repair_transaction.atomic_write_json(resolved_receipt, receipt)
    except repair_transaction.RepairTransactionError as exc:
        raise RepairExecutionPacketError("materialization transaction already active") from exc
    return receipt


def materialize_attempt_local_repair_candidate_v2(
    packet: dict[str, object],
    response: dict[str, object],
    *,
    workspace_root: Path,
    authorization: dict[str, object] | None = None,
    apply: bool = True,
    receipt_path: Path | None = None,
    response_provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    """Materialize only the v2 sandbox using its character-level selector."""
    workspace_root = workspace_root.resolve()
    validate_attempt_local_repair_packet_v2(packet, workspace_root=workspace_root)
    if set(response) != {"replacement_utf8", "change_summary"}:
        raise RepairExecutionPacketError("candidate response schema invalid")
    replacement = response.get("replacement_utf8")
    summary = response.get("change_summary")
    if (
        not isinstance(replacement, str)
        or not replacement
        or not isinstance(summary, str)
        or not summary.strip()
        or re.search(r"\\[nr](?:[ \t]|$)", replacement)
    ):
        raise RepairExecutionPacketError("candidate response schema invalid")
    source_record = packet["source"]
    assert isinstance(source_record, dict)
    source_path = _regular_file(
        workspace_root, str(source_record["path"]), label="attempt-local source"
    )
    source_bytes = source_path.read_bytes()
    if source_record.get("sha256") != _sha256_bytes(source_bytes):
        raise RepairExecutionPacketError("source hash drift")
    original = source_bytes.decode("utf-8")
    editable = packet["editable_target"]
    assert isinstance(editable, dict)
    selector = editable["selector"]
    assert isinstance(selector, dict)
    start_marker = str(selector["anchor_start"])
    end_marker = str(selector["anchor_end"])
    start = original.find(start_marker)
    end = original.find(end_marker, start + len(start_marker))
    if (
        start < 0
        or end < 0
        or original.count(start_marker) != 1
        or original.count(end_marker) != 1
        or start + len(start_marker) > end
    ):
        raise RepairExecutionPacketError("attempt-local selector anchor drift")
    if start_marker in replacement or end_marker in replacement:
        raise RepairExecutionPacketError("replacement must not contain anchor lines")
    candidate = original[: start + len(start_marker)] + replacement + original[end:]
    if candidate == original:
        raise RepairExecutionPacketError("candidate must change one source block")
    invariants = selector.get("protected_invariants")
    if not isinstance(invariants, list) or any(
        not isinstance(token, str) or not token or original.count(token) != candidate.count(token)
        for token in invariants
    ):
        raise RepairExecutionPacketError("protected invariant changed")
    changed_lines = max(1, len(replacement.splitlines()))
    budget = packet.get("change_budget")
    if (
        not isinstance(budget, dict)
        or type(budget.get("max_changed_lines")) is not int
        or changed_lines > budget["max_changed_lines"]
    ):
        raise RepairExecutionPacketError("candidate change budget exceeded")
    output_relative = _safe_relative(str(packet["output_path"]), label="output path")
    preview: dict[str, object] = {
        "schema": MATERIALIZATION_PREVIEW_SCHEMA,
        "fixture": packet["fixture"],
        "packet_sha256": packet["packet_sha256"],
        "source_sha256": source_record["sha256"],
        "output_path": output_relative.as_posix(),
        "output_sha256": _sha256_bytes(candidate.encode("utf-8")),
        "changed_source_blocks": 1,
        "changed_lines": changed_lines,
        "preserved_boundary_blank_lines": 0,
        "change_summary": summary.strip(),
        "publication_acceptance": "not_claimed",
    }
    preview["preview_sha256"] = canonical_materialization_preview_sha256(preview)
    if not apply:
        return preview
    if not isinstance(authorization, dict):
        raise RepairExecutionPacketError("materialization authorization missing")
    try:
        normalized_authorization = (
            human_decision_record.validate_additive_materialization_authorization(
                authorization,
                fixture=str(packet["fixture"]),
                packet_schema=str(packet["schema"]),
                packet_sha256=str(packet["packet_sha256"]),
                output_path=output_relative.as_posix(),
                output_sha256=str(preview["output_sha256"]),
                preview_sha256=str(preview["preview_sha256"]),
                expected_packet_path=attempt_local_packet_path(packet),
            )
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise RepairExecutionPacketError(f"materialization authorization invalid: {exc}") from exc
    output = workspace_root / output_relative
    current = workspace_root
    for part in output_relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise RepairExecutionPacketError("attempt-local materialization path invalid")
    if receipt_path is None:
        raise RepairExecutionPacketError("materialization receipt path missing")
    resolved_receipt = receipt_path if receipt_path.is_absolute() else workspace_root / receipt_path
    if (
        not resolved_receipt.is_relative_to(workspace_root)
        or resolved_receipt.parent != output.parent
        or output.exists()
        or output.is_symlink()
        or resolved_receipt.exists()
        or resolved_receipt.is_symlink()
    ):
        raise RepairExecutionPacketError("attempt-local materialization path invalid")
    if response_provenance is not None:
        if set(response_provenance) != {"path", "sha256", "payload"}:
            raise RepairExecutionPacketError("repair response provenance invalid")
        response_path = _regular_file(
            workspace_root, str(response_provenance.get("path") or ""), label="repair response path"
        )
        response_bytes = response_path.read_bytes()
        try:
            response_payload = json.loads(response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairExecutionPacketError("repair response provenance invalid") from exc
        if (
            response_path.parent != output.parent
            or response_provenance.get("sha256") != _sha256_bytes(response_bytes)
            or response_provenance.get("payload") != response
            or response_payload != response
        ):
            raise RepairExecutionPacketError("repair response provenance invalid")
    receipt: dict[str, object] = {
        "schema": "figure-agent.repair-materialization-receipt.v2",
        "decision": "materialized_verification_pending",
        **{key: value for key, value in preview.items() if key != "schema"},
        "authorization": {
            "reviewer": normalized_authorization["reviewer"],
            "record_sha256": _sha256_bytes(_canonical_json_bytes(authorization)),
            "authorized_packet_sha256": normalized_authorization["authorized_packet_sha256"],
            "authorized_output_path": normalized_authorization["authorized_output_path"],
            "authorized_output_sha256": normalized_authorization["authorized_output_sha256"],
            "authorized_preview_sha256": normalized_authorization["authorized_preview_sha256"],
        },
        "rollback": {
            "strategy": "delete_materialized_output_if_hash_matches",
            "pre_transaction_state": "absent",
            "output_path": output_relative.as_posix(),
            "output_sha256": preview["output_sha256"],
        },
        "post_render_verification": "pending",
        "external_compile": "pending",
        "human_review": "pending",
        "publication_acceptance": "not_claimed",
        "recovery_required": False,
    }
    if response_provenance is not None:
        receipt["repair_response"] = dict(response_provenance)
    try:
        with repair_transaction.recoverable_exclusive_lock(
            output.parent / ".materialization.lock",
            owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
        ):
            validate_attempt_local_repair_packet_v2(packet, workspace_root=workspace_root)
            if _sha256_bytes(source_path.read_bytes()) != source_record["sha256"]:
                raise RepairExecutionPacketError("source hash drift")
            prepared = {
                **receipt,
                "decision": "materialization_prepared",
                "recovery_required": True,
            }
            repair_transaction.atomic_write_json(resolved_receipt, prepared)
            repair_transaction.atomic_write_text(output, candidate)
            repair_transaction.atomic_write_json(resolved_receipt, receipt)
    except repair_transaction.RepairTransactionError as exc:
        raise RepairExecutionPacketError("materialization transaction already active") from exc
    return receipt


def write_repair_execution_packet(
    packet_path: Path,
    prompt_path: Path,
    *,
    packet: dict[str, object],
    prompt: str,
) -> None:
    """Persist a packet/prompt pair once after validating their hashes."""
    if packet_path.parent.resolve(strict=False) != prompt_path.parent.resolve(strict=False):
        raise RepairExecutionPacketError("packet and prompt must be adjacent")
    if any(path.exists() or path.is_symlink() for path in (packet_path, prompt_path)):
        raise RepairExecutionPacketError("packet or prompt already exists")
    if packet.get("packet_sha256") != canonical_packet_sha256(packet):
        raise RepairExecutionPacketError("packet hash drift")
    prompt_record = packet.get("prompt")
    if (
        not isinstance(prompt_record, dict)
        or prompt_record.get("utf8") != prompt
        or prompt_record.get("sha256") != _sha256_bytes(prompt.encode("utf-8"))
    ):
        raise RepairExecutionPacketError("prompt hash drift")
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(
        json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    prompt_path.write_text(prompt, encoding="utf-8")
