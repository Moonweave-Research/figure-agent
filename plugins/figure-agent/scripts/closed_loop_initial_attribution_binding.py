"""Attempt-local human attribution binding for an approved initial critique.

This is deliberately a boundary adapter.  It validates one named human's
mapping of one approved initial-review finding to one editable selector, then
publishes a v2 ``repair_bound`` leaf.  It does not compile packets, invoke a
model, mutate source, or reuse the global legacy critique bridge.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_current_state
import critique_contract
import repair_transaction
import yaml

SCHEMA = "figure-agent.initial-attribution-binding.v2"
ACTION = "closed_loop_initial_attribution_binding"
BINDING_DIRECTORY = "initial-attribution"
BINDING_FILE = "binding.json"
BINDING_SNAPSHOT_FILE = "binding.snapshot.json"
PUBLICATION_ACCEPTANCE = "not_claimed"

_BINDING_FIELDS = {
    "schema",
    "fixture",
    "attempt_id",
    "current_state",
    "attribution_handoff",
    "adjudication",
    "initial_visual_review_response",
    "critique",
    "human_attributor",
    "authored_source",
    "selector_registry",
    "semantic_contract",
    "selector_id",
    "repair_family",
    "publication_acceptance",
    "binding_sha256",
}


class ClosedLoopInitialAttributionBindingError(ValueError):
    """Raised when a v2 attribution cannot safely bind the current attempt."""


@dataclass(frozen=True)
class _FileSnapshot:
    path: Path
    content: bytes
    fingerprint: tuple[int, int, int, int, int]
    label: str


@dataclass(frozen=True)
class _Snapshot:
    path: Path
    payload: dict[str, Any]
    content: bytes
    fingerprint: tuple[int, int, int, int, int]
    dependencies: tuple[_FileSnapshot, ...] = ()

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.content)


def _sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def canonical_binding_sha256(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "binding_sha256"}
    return _sha256_bytes(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def _regular_file(path: Path, *, root: Path, label: str) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_outside_workspace"
        ) from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_symlink")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_missing"
        ) from exc
    if not stat.S_ISREG(mode):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_not_regular")
    return path


def _load_json(path: Path, *, root: Path, label: str) -> tuple[dict[str, Any], bytes]:
    _regular_file(path, root=root, label=label)
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        payload = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_invalid"
        ) from exc
    if _fingerprint(before) != _fingerprint(after):
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_changed_during_snapshot"
        )
    if not isinstance(payload, dict):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_invalid")
    return payload, content


def _fingerprint(stat_result: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )


def _snapshot(path: Path, *, root: Path) -> _Snapshot:
    _regular_file(path, root=root, label="binding")
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        payload = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_invalid"
        ) from exc
    fingerprint = _fingerprint(after)
    if _fingerprint(before) != fingerprint:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_changed_during_snapshot"
        )
    if not isinstance(payload, dict):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_binding_invalid")
    return _Snapshot(path=path, payload=payload, content=content, fingerprint=fingerprint)


def _file_snapshot(path: Path, *, root: Path, label: str, expected_sha256: str) -> _FileSnapshot:
    _regular_file(path, root=root, label=label)
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_invalid"
        ) from exc
    fingerprint = _fingerprint(after)
    if _fingerprint(before) != fingerprint or _sha256_bytes(content) != expected_sha256:
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_drift")
    return _FileSnapshot(path=path, content=content, fingerprint=fingerprint, label=label)


def _assert_file_snapshot_current(snapshot: _FileSnapshot, *, root: Path, label: str) -> None:
    _regular_file(snapshot.path, root=root, label=label)
    try:
        before = snapshot.path.stat()
        content = snapshot.path.read_bytes()
        after = snapshot.path.stat()
    except OSError as exc:
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_{label}_drift"
        ) from exc
    if (
        _fingerprint(before) != _fingerprint(after)
        or _fingerprint(after) != snapshot.fingerprint
        or content != snapshot.content
    ):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_drift")


def _assert_snapshot_current(snapshot: _Snapshot, *, root: Path) -> None:
    _regular_file(snapshot.path, root=root, label="binding")
    try:
        before = snapshot.path.stat()
        content = snapshot.path.read_bytes()
        after = snapshot.path.stat()
    except OSError as exc:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_binding_drift") from exc
    if (
        _fingerprint(before) != _fingerprint(after)
        or _fingerprint(after) != snapshot.fingerprint
        or content != snapshot.content
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_binding_drift")
    for dependency in snapshot.dependencies:
        _assert_file_snapshot_current(
            dependency,
            root=root,
            label=dependency.label,
        )


def _load_state(root: Path, fixture: str, value: Path) -> tuple[dict[str, Any], Path]:
    requested = Path(os.path.abspath(value if value.is_absolute() else root / value))
    payload, _ = _load_json(requested, root=root, label="closed_loop_state")
    try:
        state = closed_loop_attempt_state.validate_state(payload, workspace_root=root)
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopInitialAttributionBindingError(f"closed_loop_state_invalid:{exc}") from exc
    if state["fixture"] != fixture or requested != closed_loop_attempt_state.state_path(
        state, workspace_root=root
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_state_path_mismatch")
    return state, requested


def _assert_current(root: Path, fixture: str, state: dict[str, Any], path: Path) -> None:
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") != "current"
        or current.get("path") != path.relative_to(root).as_posix()
        or current.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_current_state_mismatch")


def _records(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {str(record["role"]): record for record in state["evidence"]}


def _reference(
    value: Any, expected: dict[str, str], *, label: str, finding_id: bool = False
) -> None:
    fields = {"path", "sha256", "finding_id"} if finding_id else {"path", "sha256"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_invalid")
    if value.get("path") != expected["path"] or value.get("sha256") != expected["sha256"]:
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_mismatch")
    if finding_id and (
        not isinstance(value.get("finding_id"), str) or not value["finding_id"].strip()
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_finding_invalid")


def _human(value: Any) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "identity"}
        or value.get("kind") != "human"
        or not isinstance(value.get("identity"), str)
        or not value["identity"].strip()
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_human_attributor_invalid"
        )
    return {"kind": "human", "identity": value["identity"].strip()}


def _root_authored_source(
    root: Path, fixture: str, state_path: Path, attempt_id: str
) -> dict[str, str]:
    root_path = state_path.parent / "state-000-authored_rendered.json"
    root_state, published = _load_state(root, fixture, root_path)
    if (
        published != root_path
        or root_state["attempt_id"] != attempt_id
        or root_state["state"] != "authored_rendered"
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_root_state_invalid")
    records = _records(root_state)
    source = records.get("authored_source")
    if not isinstance(source, dict):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_root_source_missing")
    return source


def _critique_ids(path: Path, *, fixture: str) -> set[str]:
    try:
        frontmatter = critique_contract.load_critique_frontmatter(path)
        if frontmatter.get("fixture") != fixture:
            raise critique_contract.CritiqueContractError("fixture mismatch")
        identifiers = [
            critique_contract.critique_finding_id(finding, "initial critique finding")
            for finding in critique_contract.critique_findings(frontmatter)
        ]
    except (critique_contract.CritiqueContractError, ValueError) as exc:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_critique_invalid"
        ) from exc
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_critique_invalid")
    return set(identifiers)


def _safe_record_path(root: Path, value: dict[str, str], *, label: str) -> Path:
    relative = Path(value["path"])
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_path_unsafe")
    return _regular_file(root / relative, root=root, label=label)


def _binding_record(value: Any, *, root: Path, label: str) -> tuple[dict[str, str], Path]:
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_invalid")
    record = {"path": str(value["path"]), "sha256": str(value["sha256"])}
    path = _safe_record_path(root, record, label=label)
    if record["sha256"] != _sha256(path):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_hash_stale")
    return record, path


def _string_list(value: Any, *, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_invalid")
    if len(value) != len(set(value)):
        raise ClosedLoopInitialAttributionBindingError(f"initial_attribution_{label}_ambiguous")
    return [item.strip() for item in value]


def _validate_selector(
    *,
    root: Path,
    registry_path: Path,
    registry_record: dict[str, str],
    semantic_record: dict[str, str],
    source_record: dict[str, str],
    selector_id: str,
    repair_family: str,
) -> None:
    registry, _ = _load_json(registry_path, root=root, label="selector_registry")
    required = {"schema", "source_path", "source_sha256", "semantic_contract", "selectors"}
    if (
        set(registry) != required
        or registry.get("schema") != "figure-agent.source-selector-registry.v1"
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_selector_registry_invalid"
        )
    if (
        registry.get("source_path") != source_record["path"]
        or registry.get("source_sha256") != source_record["sha256"]
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_selector_registry_source_mismatch"
        )
    if registry.get("semantic_contract") != semantic_record:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_selector_registry_semantic_mismatch"
        )
    selectors = registry.get("selectors")
    if not isinstance(selectors, list):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_selector_invalid")
    matches = [
        item
        for item in selectors
        if isinstance(item, dict) and item.get("selector_id") == selector_id
    ]
    if len(matches) != 1:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_selector_invalid")
    selector = matches[0]
    if selector.get("repair_role") != "movable":
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_selector_not_movable")
    if not repair_family or repair_family not in authoring_repair_packet.ALLOWED_REPAIR_FAMILIES:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_repair_family_invalid")
    if selector.get("repair_family") != repair_family:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_repair_family_mismatch")
    anchors = (selector.get("anchor_start"), selector.get("anchor_end"))
    if (
        any(not isinstance(anchor, str) or not anchor.strip() for anchor in anchors)
        or anchors[0] == anchors[1]
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_selector_anchor_invalid"
        )
    source = root / source_record["path"]
    _regular_file(source, root=root, label="authored_source")
    source_text = source.read_text(encoding="utf-8")
    start_index = source_text.find(anchors[0])
    end_index = source_text.find(anchors[1])
    if (
        source_text.count(anchors[0]) != 1
        or source_text.count(anchors[1]) != 1
        or start_index < 0
        or end_index < 0
        or start_index + len(anchors[0]) > end_index
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_selector_anchor_invalid"
        )
    _string_list(selector.get("protected_invariants"), label="selector_invariants")
    object_refs = _string_list(selector.get("semantic_object_refs"), label="semantic_object_refs")
    relation_refs = _string_list(
        selector.get("semantic_relation_refs"), label="semantic_relation_refs"
    )
    semantic_path = root / semantic_record["path"]
    _regular_file(semantic_path, root=root, label="semantic_contract")
    try:
        semantic = yaml.safe_load(semantic_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_semantic_contract_invalid"
        ) from exc
    if (
        not isinstance(semantic, dict)
        or semantic.get("publication_acceptance") != PUBLICATION_ACCEPTANCE
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_semantic_contract_invalid"
        )
    objects = semantic.get("required_objects")
    relations = semantic.get("protected_relations")
    if (
        not isinstance(objects, list)
        or not isinstance(relations, list)
        or not set(object_refs).issubset(set(objects))
        or not set(relation_refs).issubset(set(relations))
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_semantic_references_invalid"
        )


def _validate_binding(
    root: Path, fixture: str, state: dict[str, Any], state_path: Path, binding_path: Path
) -> _Snapshot:
    expected_path = state_path.parent / BINDING_DIRECTORY / BINDING_FILE
    if (
        binding_path != expected_path
        or binding_path.parent.is_symlink()
        or not binding_path.parent.is_dir()
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_path_outside_attempt"
        )
    snapshot = _snapshot(binding_path, root=root)
    payload = snapshot.payload
    if (
        set(payload) != _BINDING_FIELDS
        or payload.get("schema") != SCHEMA
        or payload.get("binding_sha256") != canonical_binding_sha256(payload)
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_binding_schema_invalid")
    if (
        payload.get("fixture") != fixture
        or payload.get("attempt_id") != state["attempt_id"]
        or payload.get("publication_acceptance") != PUBLICATION_ACCEPTANCE
    ):
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_identity_invalid"
        )
    _reference(
        payload.get("current_state"),
        {"path": state_path.relative_to(root).as_posix(), "sha256": state["state_sha256"]},
        label="current_state",
    )
    evidence = _records(state)
    for field, role in (
        ("attribution_handoff", "attribution_handoff"),
        ("adjudication", "adjudication"),
        ("initial_visual_review_response", "initial_visual_review_response"),
    ):
        expected = evidence.get(role)
        if expected is None:
            raise ClosedLoopInitialAttributionBindingError(
                "initial_attribution_state_evidence_missing"
            )
        _reference(payload.get(field), expected, label=field)
    critique = evidence.get("critique")
    if critique is None:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_state_evidence_missing")
    _reference(payload.get("critique"), critique, label="critique", finding_id=True)
    handoff_path = root / evidence["attribution_handoff"]["path"]
    handoff, _ = _load_json(handoff_path, root=root, label="attribution_handoff")
    if (
        handoff.get("schema") != "figure-agent.initial-attribution-handoff.v1"
        or handoff.get("fixture") != fixture
        or handoff.get("attempt_id") != state["attempt_id"]
        or handoff.get("source_mutation") != "forbidden"
        or handoff.get("publication_acceptance") != PUBLICATION_ACCEPTANCE
    ):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_handoff_invalid")
    human = _human(payload.get("human_attributor"))
    if handoff.get("human_attributor") != human:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_human_attributor_mismatch"
        )
    finding_id = payload["critique"]["finding_id"]
    selected = handoff.get("selected_finding_ids")
    if not isinstance(selected, list) or selected.count(finding_id) != 1:
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_finding_not_selected")
    critique_path = root / critique["path"]
    if finding_id not in _critique_ids(critique_path, fixture=fixture):
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_finding_invalid")
    root_source = _root_authored_source(root, fixture, state_path, state["attempt_id"])
    _reference(payload.get("authored_source"), root_source, label="authored_source")
    source_record, source_path = _binding_record(
        payload.get("authored_source"), root=root, label="authored_source"
    )
    registry_record, registry_path = _binding_record(
        payload.get("selector_registry"), root=root, label="selector_registry"
    )
    semantic_record, semantic_path = _binding_record(
        payload.get("semantic_contract"), root=root, label="semantic_contract"
    )
    selector_id = payload.get("selector_id")
    if not isinstance(selector_id, str) or not selector_id.strip():
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_selector_invalid")
    repair_family = payload.get("repair_family")
    if not isinstance(repair_family, str) or not repair_family.strip():
        raise ClosedLoopInitialAttributionBindingError("initial_attribution_repair_family_invalid")
    _validate_selector(
        root=root,
        registry_path=registry_path,
        registry_record=registry_record,
        semantic_record=semantic_record,
        source_record=source_record,
        selector_id=selector_id,
        repair_family=repair_family,
    )
    return _Snapshot(
        path=snapshot.path,
        payload=snapshot.payload,
        content=snapshot.content,
        fingerprint=snapshot.fingerprint,
        dependencies=(
            _file_snapshot(
                source_path,
                root=root,
                label="authored_source",
                expected_sha256=source_record["sha256"],
            ),
            _file_snapshot(
                registry_path,
                root=root,
                label="selector_registry",
                expected_sha256=registry_record["sha256"],
            ),
            _file_snapshot(
                semantic_path,
                root=root,
                label="semantic_contract",
                expected_sha256=semantic_record["sha256"],
            ),
        ),
    )


def _snapshot_path(binding_path: Path) -> Path:
    return binding_path.with_name(BINDING_SNAPSHOT_FILE)


def _assert_snapshot_destination(path: Path, snapshot: _Snapshot, *, root: Path) -> None:
    if path.is_symlink():
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_snapshot_symlink"
        )
    if not path.exists():
        return
    _regular_file(path, root=root, label="binding_snapshot")
    try:
        existing = path.read_bytes()
    except OSError as exc:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_snapshot_invalid"
        ) from exc
    if existing != snapshot.content:
        raise ClosedLoopInitialAttributionBindingError(
            "initial_attribution_binding_snapshot_conflict"
        )


def _publish_snapshot(path: Path, snapshot: _Snapshot, *, root: Path) -> None:
    _assert_snapshot_destination(path, snapshot, root=root)
    if path.exists():
        return
    try:
        repair_transaction.atomic_create_text(path, snapshot.content.decode("utf-8"))
    except (FileExistsError, UnicodeDecodeError) as exc:
        if isinstance(exc, UnicodeDecodeError):
            raise ClosedLoopInitialAttributionBindingError(
                "initial_attribution_binding_snapshot_invalid"
            ) from exc
        _assert_snapshot_destination(path, snapshot, root=root)


def _published_matches(
    state: dict[str, Any],
    *,
    previous: dict[str, Any],
    previous_path: Path,
    snapshot_path: Path,
    snapshot: _Snapshot,
    root: Path,
    human: str,
) -> bool:
    if (
        state["state"] != "repair_bound"
        or state["actor"] != human
        or state["actor_role"] != "human_attributor"
    ):
        return False
    if (
        state.get("previous_state_path") != previous_path.relative_to(root).as_posix()
        or state.get("previous_state_sha256") != previous["state_sha256"]
    ):
        return False
    expected = {
        "role": "adjudicated_repair_binding",
        "path": snapshot_path.relative_to(root).as_posix(),
        "sha256": snapshot.sha256,
    }
    return state.get("evidence") == [expected]


def run_initial_attribution_binding(
    fixture: str,
    *,
    state_path: Path,
    binding_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Publish only a hash-bound v2 ``repair_bound`` leaf for one human mapping."""
    root = Path(os.path.abspath(workspace_root))
    requested = Path(
        os.path.abspath(binding_path if binding_path.is_absolute() else root / binding_path)
    )
    current, current_path = _load_state(root, fixture, state_path)
    if expected_state_sha256 is not None and current["state_sha256"] != expected_state_sha256:
        raise ClosedLoopInitialAttributionBindingError("closed_loop_projected_state_hash_mismatch")
    _assert_current(root, fixture, current, current_path)
    if current["state"] == "repair_bound":
        previous_value = current.get("previous_state_path")
        if not isinstance(previous_value, str):
            raise ClosedLoopInitialAttributionBindingError(
                "initial_attribution_parent_state_missing"
            )
        previous, previous_path = _load_state(root, fixture, Path(previous_value))
        if previous["state"] != "adjudicated_unbound":
            raise ClosedLoopInitialAttributionBindingError(
                "initial_attribution_parent_state_invalid"
            )
        snapshot = _validate_binding(root, fixture, previous, previous_path, requested)
        snapshot_path = _snapshot_path(requested)
        _assert_snapshot_destination(snapshot_path, snapshot, root=root)
        _regular_file(snapshot_path, root=root, label="binding_snapshot")
        if snapshot_path.read_bytes() != snapshot.content or not _published_matches(
            current,
            previous=previous,
            previous_path=previous_path,
            snapshot_path=snapshot_path,
            snapshot=snapshot,
            root=root,
            human=snapshot.payload["human_attributor"]["identity"].strip(),
        ):
            raise ClosedLoopInitialAttributionBindingError(
                "initial_attribution_published_state_stale"
            )
        return {
            "action": ACTION,
            "created": False,
            "input_state": previous,
            "input_state_path": previous_path,
            "next_state": current["state"],
            "next_state_path": current_path,
            "binding_path": requested,
            "binding_snapshot_path": snapshot_path,
            "published_state": current,
            "stop_boundary": current["required_actor"],
            "stop_reason": current["required_actor"],
        }
    if current["state"] != "adjudicated_unbound":
        raise ClosedLoopInitialAttributionBindingError("closed_loop_state_not_adjudicated_unbound")
    snapshot = _validate_binding(root, fixture, current, current_path, requested)
    snapshot_path = _snapshot_path(requested)
    _assert_snapshot_destination(snapshot_path, snapshot, root=root)
    next_path = current_path.parent / f"state-{current['sequence'] + 1:03d}-repair_bound.json"
    if not execute:
        return {
            "action": ACTION,
            "created": False,
            "input_state": current,
            "input_state_path": current_path,
            "next_state": "repair_bound",
            "next_state_path": next_path,
            "binding_path": requested,
            "binding_snapshot_path": snapshot_path,
            "published_state": None,
            "stop_boundary": "workflow_agent",
            "stop_reason": "plan_only",
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(current_path.parent):
            fresh, fresh_path = _load_state(root, fixture, current_path)
            _assert_current(root, fixture, fresh, fresh_path)
            if fresh != current or fresh_path != current_path:
                raise ClosedLoopInitialAttributionBindingError(
                    "initial_attribution_state_drift_detected"
                )
            fresh_snapshot = _validate_binding(root, fixture, fresh, fresh_path, requested)
            if (
                fresh_snapshot.content != snapshot.content
                or fresh_snapshot.fingerprint != snapshot.fingerprint
            ):
                raise ClosedLoopInitialAttributionBindingError(
                    "initial_attribution_inputs_drift_detected"
                )
            _assert_snapshot_current(fresh_snapshot, root=root)
            _publish_snapshot(snapshot_path, fresh_snapshot, root=root)
            next_state = closed_loop_attempt_state.transition_state(
                fresh,
                next_state="repair_bound",
                actor=fresh_snapshot.payload["human_attributor"]["identity"].strip(),
                actor_role="human_attributor",
                evidence={"adjudicated_repair_binding": snapshot_path},
                workspace_root=root,
                previous_state_path=fresh_path,
            )
            try:
                published = closed_loop_attempt_state.publish_state(next_state, workspace_root=root)
            except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
                if str(exc) != "state_already_published":
                    raise
                existing, existing_path = _load_state(root, fixture, next_path)
                if not _published_matches(
                    existing,
                    previous=fresh,
                    previous_path=fresh_path,
                    snapshot_path=snapshot_path,
                    snapshot=fresh_snapshot,
                    root=root,
                    human=fresh_snapshot.payload["human_attributor"]["identity"].strip(),
                ):
                    raise ClosedLoopInitialAttributionBindingError(
                        "initial_attribution_state_conflict"
                    ) from exc
                next_state, published = existing, existing_path
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, ClosedLoopInitialAttributionBindingError):
            raise
        raise ClosedLoopInitialAttributionBindingError(
            f"initial_attribution_publication_failed:{exc}"
        ) from exc
    return {
        "action": ACTION,
        "created": True,
        "input_state": current,
        "input_state_path": current_path,
        "next_state": next_state["state"],
        "next_state_path": published,
        "binding_path": requested,
        "binding_snapshot_path": snapshot_path,
        "published_state": next_state,
        "stop_boundary": next_state["required_actor"],
        "stop_reason": next_state["required_actor"],
    }
