"""Compile immutable, byte-bound authoring execution packets."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import authoring_context_pack

SCHEMA = "figure-agent.authoring-execution-packet.v1"
MANDATORY_SOURCE_REQUIREMENTS = (
    r"\documentclass[tikz,border=4pt]{standalone}",
    r"\usepackage{tikz}",
    r"\usepackage{polymer-paper-preamble}",
)
ATTEMPT_ROOT = Path("review/failure-first")
ATTEMPT_NAME = re.compile(r"execution-binding-v[1-9][0-9]*")


class AuthoringExecutionPacketError(ValueError):
    """Raised when an authoring execution packet cannot be bound safely."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_packet_sha256(packet: dict[str, object]) -> str:
    """Hash canonical packet fields without recursively hashing the hash field."""
    payload = {key: value for key, value in packet.items() if key != "packet_sha256"}
    return _sha256_bytes(_canonical_json_bytes(payload))


def _safe_relative_path(value: str, *, label: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        raise AuthoringExecutionPacketError(f"{label} must be repo-relative")
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise AuthoringExecutionPacketError(f"{label} contains an unsafe path component")
    return path


def _safe_execution_cwd(value: str) -> str:
    if value == ".":
        return value
    return _safe_relative_path(value, label="execution cwd").as_posix()


def _resolve_regular_file(workspace_root: Path, value: str, *, label: str) -> Path:
    relative = _safe_relative_path(value, label=label)
    current = workspace_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringExecutionPacketError(f"{label} must not traverse a symlink")
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise AuthoringExecutionPacketError(f"{label} must be a regular file") from exc
    if not resolved.is_relative_to(workspace_root.resolve()) or not resolved.is_file():
        raise AuthoringExecutionPacketError(f"{label} must be a regular file")
    return resolved


def _validate_output_path(workspace_root: Path, name: str, value: str) -> Path:
    relative = _safe_relative_path(value, label="output path")
    required_root = Path("examples") / name / ATTEMPT_ROOT
    if (
        relative.parent.parent != required_root
        or not ATTEMPT_NAME.fullmatch(relative.parent.name)
    ):
        raise AuthoringExecutionPacketError(
            "output path must remain inside a versioned execution-binding-v directory"
        )
    if relative.suffix != ".tex":
        raise AuthoringExecutionPacketError("output path must end in .tex")
    output = workspace_root / relative
    current = workspace_root
    for part in relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringExecutionPacketError("output path must not traverse a symlink")
    if output.exists() or output.is_symlink():
        raise AuthoringExecutionPacketError("output path already exists")
    return relative


def resolve_attempt_artifact_path(
    workspace_root: Path,
    name: str,
    value: str,
    *,
    suffix: str,
) -> Path:
    """Resolve a new packet-side artifact inside the fixture attempt directory."""
    relative = _safe_relative_path(value, label="attempt artifact")
    required_root = Path("examples") / name / ATTEMPT_ROOT
    if (
        relative.parent.parent != required_root
        or not ATTEMPT_NAME.fullmatch(relative.parent.name)
        or relative.suffix != suffix
    ):
        raise AuthoringExecutionPacketError(
            f"attempt artifact must be a {suffix} file inside execution-binding-vN"
        )
    path = workspace_root.resolve() / relative
    current = workspace_root.resolve()
    for part in relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringExecutionPacketError(
                "attempt artifact must not traverse a symlink"
            )
    return path


def _validate_prompt_requirements(prompt: str) -> None:
    for requirement in MANDATORY_SOURCE_REQUIREMENTS:
        count = prompt.count(requirement)
        if count == 0:
            raise AuthoringExecutionPacketError(
                f"missing mandatory source requirement: {requirement}"
            )
        if count > 1:
            raise AuthoringExecutionPacketError(
                f"duplicate mandatory source requirement: {requirement}"
            )


def _contract_lines(context_pack: dict[str, Any]) -> list[str]:
    contracts = context_pack.get("semantic_contracts", {})
    lines: list[str] = []
    for claim in contracts.get("semantic_claims", []):
        lines.append(f"- Semantic claim [{claim['panel_id']}:{claim['id']}]: {claim['claim']}")
    for invariant in contracts.get("locked_invariants", []):
        lines.append(
            f"- Locked invariant [{invariant['panel_id']}:{invariant['id']}]: "
            f"{invariant['invariant']}"
        )
    if not lines:
        lines.append("- No fixture semantic contracts are enabled.")
    return lines


def _fixture_briefing_lines(context_pack: dict[str, Any]) -> list[str]:
    lines = ["- Required panels:"]
    for panel in context_pack.get("fixture", {}).get("panels", []):
        lines.append(f"  - [{panel['id']}] {panel['caption']}")
    briefing = context_pack.get("paper_context", {}).get("briefing", "")
    if briefing:
        lines.extend(["- Binding fixture briefing (verbatim):", "", briefing])
    else:
        lines.append("- No fixture briefing was provided.")
    return lines


def render_authoring_prompt(
    *,
    name: str,
    output_path: str,
    context_pack: dict[str, Any],
    model_id: str,
    execution_cwd: str = ".",
) -> str:
    """Render the sole authoring prompt authority in a deterministic order."""
    lines = [
        f"# Bound authoring execution: {name}",
        "",
        "## Output and attempt boundary",
        (
            "- Resolve the output path from the repository root."
            if execution_cwd == "."
            else "- Before resolving the output path, change directory from the "
            f"repository root to [{execution_cwd}]."
        ),
        f"- Write exactly one new source to [{output_path}].",
        "- Start from the declared blank artifact; perform one attempt only.",
        "- Do not inspect or repair historical generated sources.",
        "",
        "## Mandatory standalone TikZ source requirements",
        *[f"- {requirement}" for requirement in MANDATORY_SOURCE_REQUIREMENTS],
        "",
        "## Semantic contracts and forbidden implications",
        *_fixture_briefing_lines(context_pack),
        "",
        *_contract_lines(context_pack),
        "- Do not imply physics or quantitative relations absent from the declared contracts.",
        "",
        "## Declared layout directives",
    ]
    layout = context_pack.get("layout_constraints")
    if layout:
        lines.extend(f"- {item}" for item in layout.get("authoring_directives", []))
    else:
        lines.append("- No optional layout contract selected.")
    lines.extend(["", "## Optional shape-profile directives"])
    shape_profile = context_pack.get("shape_profile")
    if shape_profile:
        lines.extend(
            f"- {item}" for item in shape_profile.get("authoring_directives", [])
        )
    else:
        lines.append("- No optional shape profile selected.")
    lines.extend(
        [
            "",
            "## Provenance and publication boundary",
            f"- Declared model: {model_id}",
            "- feedback_rounds: 0",
            "- manual_repairs: 0",
            "- filesystem_read_isolation: unavailable",
            "- publication_acceptance: not_claimed",
        ]
    )
    prompt = "\n".join(lines) + "\n"
    _validate_prompt_requirements(prompt)
    return prompt


def compile_authoring_execution_packet(
    name: str,
    *,
    plugin_root: Path,
    workspace_root: Path,
    model_id: str,
    budget_contract: str,
    blank_start: str,
    output_path: str,
    execution_cwd: str = ".",
    layout_contract: str | None = None,
    shape_profile: str | None = None,
) -> tuple[dict[str, object], str]:
    """Compile one deterministic packet without executing an authoring model."""
    if not model_id.strip():
        raise AuthoringExecutionPacketError("model_id must be non-empty")
    workspace_root = workspace_root.resolve()
    budget_path = _resolve_regular_file(
        workspace_root, budget_contract, label="budget contract"
    )
    blank_path = _resolve_regular_file(workspace_root, blank_start, label="blank start")
    relative_output = _validate_output_path(workspace_root, name, output_path)
    bound_execution_cwd = _safe_execution_cwd(execution_cwd)
    context_pack = authoring_context_pack.build_context_pack(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
        layout_contract=layout_contract,
        shape_profile=shape_profile,
    )
    context_hash = _sha256_bytes(_canonical_json_bytes(context_pack))
    base_context_pack = {
        key: value for key, value in context_pack.items() if key != "shape_profile"
    }
    prompt = render_authoring_prompt(
        name=name,
        output_path=relative_output.as_posix(),
        context_pack=context_pack,
        model_id=model_id.strip(),
        execution_cwd=bound_execution_cwd,
    )
    packet: dict[str, object] = {
        "schema": SCHEMA,
        "fixture": name,
        "context_pack": {
            "schema": context_pack["schema"],
            "sha256": context_hash,
            "base_sha256": _sha256_bytes(_canonical_json_bytes(base_context_pack)),
        },
        "model_id": model_id.strip(),
        "budget_contract": {
            "path": Path(budget_contract).as_posix(),
            "sha256": _sha256_bytes(budget_path.read_bytes()),
        },
        "blank_start": {
            "path": Path(blank_start).as_posix(),
            "sha256": _sha256_bytes(blank_path.read_bytes()),
        },
        "output_path": relative_output.as_posix(),
        "execution_cwd": bound_execution_cwd,
        "layout_contract": (
            {
                "path": context_pack["sources"]["layout_lanes"],
                "sha256": _sha256_bytes(
                    (workspace_root / context_pack["sources"]["layout_lanes"]).read_bytes()
                ),
            }
            if layout_contract
            else None
        ),
        "shape_profile": (
            {
                "path": context_pack["shape_profile"]["path"],
                "sha256": context_pack["shape_profile"]["sha256"],
                "authoring_directives": context_pack["shape_profile"][
                    "authoring_directives"
                ],
            }
            if shape_profile
            else None
        ),
        "mandatory_source_requirements": list(MANDATORY_SOURCE_REQUIREMENTS),
        "forbidden_import_classes": [
            "fig1_fixture_artifacts",
            "historical_generated_sources",
        ],
        "feedback_rounds": 0,
        "manual_repairs": 0,
        "filesystem_read_isolation": "unavailable",
        "publication_acceptance": "not_claimed",
        "prompt": {
            "utf8": prompt,
            "sha256": _sha256_text(prompt),
        },
    }
    packet["packet_sha256"] = canonical_packet_sha256(packet)
    return packet, prompt


def write_authoring_execution_packet(
    packet_path: Path,
    prompt_path: Path,
    *,
    packet: dict[str, object],
    prompt: str,
) -> None:
    """Persist an adjacent packet/prompt pair once and verify the bytes."""
    if packet_path.parent.resolve(strict=False) != prompt_path.parent.resolve(
        strict=False
    ):
        raise AuthoringExecutionPacketError("packet and prompt must be adjacent")
    if (
        packet_path.exists()
        or packet_path.is_symlink()
        or prompt_path.exists()
        or prompt_path.is_symlink()
    ):
        raise AuthoringExecutionPacketError("packet or prompt already exists")
    if packet.get("packet_sha256") != canonical_packet_sha256(packet):
        raise AuthoringExecutionPacketError("packet hash drift")
    prompt_record = packet.get("prompt")
    if not isinstance(prompt_record, dict) or prompt_record.get("sha256") != _sha256_text(
        prompt
    ):
        raise AuthoringExecutionPacketError("prompt hash drift")
    if prompt_record.get("utf8") != prompt:
        raise AuthoringExecutionPacketError("prompt byte drift")
    _validate_prompt_requirements(prompt)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_bytes = json.dumps(
        packet, indent=2, sort_keys=True, ensure_ascii=False
    ).encode("utf-8") + b"\n"
    packet_path.write_bytes(packet_bytes)
    prompt_path.write_bytes(prompt.encode("utf-8"))
    persisted = json.loads(packet_path.read_text(encoding="utf-8"))
    if persisted != packet or prompt_path.read_bytes() != prompt.encode("utf-8"):
        raise AuthoringExecutionPacketError("persisted packet or prompt drift")
