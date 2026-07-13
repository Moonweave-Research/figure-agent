"""Compile one fail-closed, hash-bound authoring repair execution packet."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "figure-agent.repair-execution-packet.v3"
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


def _safe_relative(value: str, *, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(
        part in {"", ".", ".."} for part in path.parts
    ):
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
    if (
        relative.parent.parent != root
        or not attempt_pattern.fullmatch(relative.parent.name)
    ):
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
            not isinstance(selector.get(field), str) or not selector[field]
            for field in required
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
            "- Put only the replacement content between the anchors in the "
            "replacement_utf8 field.",
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
        raise RepairExecutionPacketError(
            "source path must name a declared comparable arm"
        )
    if (
        REPAIR_ATTEMPT.fullmatch(source_relative.parent.name)
        and source_relative.name not in REPAIR_SOURCE_NAMES
    ):
        raise RepairExecutionPacketError(
            "source path must name a materialized repair output"
        )
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
    contract_path = _regular_file(
        workspace_root, target_contract, label="target contract"
    )
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
        raise RepairExecutionPacketError(
            "target contract must be adjacent to the declared output"
        )

    targets = contract.get("targets")
    if not isinstance(targets, list) or not targets:
        raise RepairExecutionPacketError("target contract must declare targets")
    exact_targets: list[dict[str, Any]] = []
    review_only: list[dict[str, str]] = []
    reports: dict[str, dict[str, Any]] = {}
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
            report_path = _regular_file(
                workspace_root, report_key, label="finding report"
            )
            reports[report_key] = _load_json(report_path, label="finding report")
        report = reports[report_key]
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
    for report_key, report in sorted(reports.items()):
        for finding in _report_findings(report):
            finding_id = finding.get("id")
            if (
                isinstance(finding_id, str)
                and (report_key, finding_id) not in referenced_findings
            ):
                review_only.append(
                    {"finding_id": finding_id, "attribution": "unbound"}
                )
    if len(exact_targets) != 1:
        raise RepairExecutionPacketError("exact attribution required for one repair target")

    editable = exact_targets[0]
    source_lines = source_text.splitlines()
    editable_start, editable_end = _anchor_indexes(source_text, editable["selector"])
    editable_source = "\n".join(source_lines[editable_start + 1 : editable_end]) + "\n"
    bound_execution_cwd = _safe_execution_cwd(execution_cwd)
    repository_output_path = (
        Path(bound_execution_cwd) / output_relative
    ).as_posix()
    report_records = [
        {
            "path": path,
            "schema": report["schema"],
            "sha256": _sha256_bytes((workspace_root / path).read_bytes()),
        }
        for path, report in sorted(reports.items())
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
) -> dict[str, object]:
    """Validate an LLM response and materialize its additive source once."""
    if packet.get("schema") != SCHEMA:
        raise RepairExecutionPacketError("packet schema invalid")
    if packet.get("packet_sha256") != canonical_packet_sha256(packet):
        raise RepairExecutionPacketError("packet hash drift")
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

    workspace_root = workspace_root.resolve()
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
    invariants = editable.get("protected_invariants") if isinstance(editable, dict) else None
    if not isinstance(selector, dict) or not isinstance(invariants, list):
        raise RepairExecutionPacketError("packet editable target invalid")
    if selector.get("source_hash") != source_record.get("sha256"):
        raise RepairExecutionPacketError("selector source hash drift")
    original_start, original_end = _anchor_indexes(original, selector)
    replacement_lines = replacement.splitlines()
    if any(
        line in {selector["anchor_start"], selector["anchor_end"]}
        for line in replacement_lines
    ):
        raise RepairExecutionPacketError("replacement must not contain anchor lines")

    original_lines = original.splitlines()
    editable_lines = original_lines[original_start + 1 : original_end]
    leading_padding = next(
        (index for index, line in enumerate(editable_lines) if line.strip()),
        len(editable_lines),
    )
    trailing_padding = next(
        (
            index
            for index, line in enumerate(reversed(editable_lines))
            if line.strip()
        ),
        len(editable_lines),
    )
    replacement_leading = next(
        (index for index, line in enumerate(replacement_lines) if line.strip()),
        len(replacement_lines),
    )
    replacement_trailing = next(
        (
            index
            for index, line in enumerate(reversed(replacement_lines))
            if line.strip()
        ),
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
    output = workspace_root / output_relative
    if output.exists() or output.is_symlink():
        raise RepairExecutionPacketError("output path already exists")
    current = workspace_root
    for part in output_relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise RepairExecutionPacketError("output path must not traverse a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(candidate, encoding="utf-8")
    return {
        "schema": "figure-agent.repair-materialization-receipt.v1",
        "decision": "materialized_verification_pending",
        "packet_sha256": packet["packet_sha256"],
        "source_sha256": source_record["sha256"],
        "output_path": output_relative.as_posix(),
        "output_sha256": _sha256_bytes(output.read_bytes()),
        "changed_source_blocks": 1,
        "changed_lines": changed_lines,
        "preserved_boundary_blank_lines": added_leading + added_trailing,
        "change_summary": summary.strip(),
        "external_compile": "pending",
        "human_review": "pending",
        "publication_acceptance": "not_claimed",
    }


def write_repair_execution_packet(
    packet_path: Path,
    prompt_path: Path,
    *,
    packet: dict[str, object],
    prompt: str,
) -> None:
    """Persist a packet/prompt pair once after validating their hashes."""
    if packet_path.parent.resolve(strict=False) != prompt_path.parent.resolve(
        strict=False
    ):
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
