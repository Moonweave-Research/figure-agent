"""Compile immutable, byte-bound authoring execution packets."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import authoring_context_pack

SCHEMA = "figure-agent.authoring-execution-packet.v1"
MANDATORY_SOURCE_REQUIREMENTS = (
    r"\documentclass[tikz,border=4pt]{standalone}",
    r"\usepackage{tikz}",
    r"\usepackage{polymer-paper-preamble}",
)
STYLE_LOCK_AUTHORING_REQUIREMENTS = (
    "Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, "
    "cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, "
    "white, and gray.",
    "Keep every explicit line width at or above 0.25pt.",
    r"Do not use local \tiny or \scriptsize font overrides.",
)
ALLOWED_REPOSITORY_READ_PATHS = (
    "AGENTS.md",
    "styles/polymer-paper-preamble.sty",
)
ATTEMPT_ROOT = Path("review/failure-first")
ATTEMPT_NAME = re.compile(r"execution-binding-v[1-9][0-9]*")
COMPARISON_NAME = re.compile(r"comparable-v[1-9][0-9]*")
COMPARISON_OUTPUT_NAMES = frozenset(
    {
        "raw_generated.tex",
        "verified_generated.tex",
        "repaired_generated.tex",
        "free_composition_generated.tex",
        "assisted_composition_generated.tex",
    }
)
COMPARISON_ARTIFACT_NAMES = frozenset(
    f"{arm}_{kind}{suffix}"
    for arm in (
        "raw",
        "verified",
        "repaired",
        "free_composition",
        "assisted_composition",
    )
    for kind, suffix in (("packet", ".json"), ("prompt", ".md"))
)
ORRO_LANE_ID = re.compile(r"[a-z0-9][a-z0-9-]*")


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


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _validate_bound_packet(packet: dict[str, object]) -> None:
    if packet.get("schema") != SCHEMA:
        raise AuthoringExecutionPacketError("packet schema invalid")
    if packet.get("packet_sha256") != canonical_packet_sha256(packet):
        raise AuthoringExecutionPacketError("packet hash drift")
    prompt = packet.get("prompt")
    if not isinstance(prompt, dict):
        raise AuthoringExecutionPacketError("packet prompt invalid")
    prompt_text = prompt.get("utf8")
    if not isinstance(prompt_text, str) or prompt.get("sha256") != _sha256_text(
        prompt_text
    ):
        raise AuthoringExecutionPacketError("prompt hash drift")
    _validate_prompt_requirements(prompt_text)


def compile_orro_execution_plans(
    packet: dict[str, object],
    *,
    goal: str,
    lane_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Compile ORRO plans from one already byte-bound authoring packet."""
    _validate_bound_packet(packet)
    if not goal.strip():
        raise AuthoringExecutionPacketError("ORRO goal must be non-empty")
    if not ORRO_LANE_ID.fullmatch(lane_id):
        raise AuthoringExecutionPacketError("ORRO lane id is invalid")
    execution_cwd = Path(_safe_execution_cwd(str(packet.get("execution_cwd", "."))))
    output_path = _safe_relative_path(str(packet["output_path"]), label="output path")
    write_scope = [(execution_cwd / output_path).as_posix()]
    model_id = str(packet["model_id"])
    prompt = packet["prompt"]
    assert isinstance(prompt, dict)
    prompt_text = str(prompt["utf8"])
    workflow: dict[str, object] = {
        "boundary": {
            "depone_verifies": True,
            "orro_exposes_workflow": True,
            "orro_is_third_engine": False,
            "witnessd_executes": True,
        },
        "engine_calls": [
            {
                "command": "orro scout",
                "engine": "witnessd",
                "executes": False,
                "phase": "scout",
                "verifies": False,
            },
            {
                "command": "orro flowplan",
                "engine": "ORRO",
                "executes": False,
                "phase": "flowplan",
                "verifies": False,
            },
            {
                "command": "orro proofrun",
                "engine": "witnessd",
                "executes": True,
                "phase": "proofrun",
                "verifies": False,
            },
            {
                "command": "orro proofcheck",
                "engine": "Depone",
                "executes": False,
                "phase": "proofcheck",
                "verifies": True,
            },
            {
                "command": "orro handoff",
                "engine": "ORRO",
                "executes": False,
                "phase": "handoff",
                "verifies": False,
            },
        ],
        "flow": ["scout", "flowplan", "proofrun", "proofcheck", "handoff"],
        "forbidden_assurance_sources": [
            "skill text",
            "session transcript",
            "model confidence",
            "MCP output alone",
            "engine-lock",
            "doctor readiness",
            "handoff prose",
        ],
        "goal": goal.strip(),
        "kind": "orro-workflow-plan",
        "profile": "code-change",
        "required_gates": [
            "proofrun emits evidence",
            "proofcheck writes proofcheck-verdict.json",
            "handoff requires passing bound proofcheck verdict",
        ],
        "roles": [
            {
                "engine": "ORRO/witnessd",
                "may_execute": False,
                "may_verify": False,
                "phase": "scout",
                "purpose": "collect repository context before planning",
                "raises_assurance": False,
                "role_id": "scout",
            },
            {
                "engine": "ORRO/witnessd",
                "may_execute": False,
                "may_verify": False,
                "phase": "flowplan",
                "purpose": "compile an execution plan without running workers",
                "raises_assurance": False,
                "role_id": "planner",
            },
            {
                "engine": "witnessd",
                "may_execute": True,
                "may_verify": False,
                "phase": "proofrun",
                "purpose": "execute the planned work and emit evidence",
                "raises_assurance": False,
                "role_id": "runner",
            },
            {
                "engine": "Depone",
                "may_execute": False,
                "may_verify": True,
                "phase": "proofcheck",
                "purpose": "verify persisted evidence bytes",
                "raises_assurance": False,
                "role_id": "verifier",
            },
            {
                "engine": "ORRO/witnessd",
                "may_execute": False,
                "may_verify": False,
                "phase": "handoff",
                "purpose": "package review references after proofcheck",
                "raises_assurance": False,
                "role_id": "handoff",
            },
        ],
        "schema_version": "0.1",
    }
    capability = {
        "adapters": ["codex"],
        "capability": "execute",
        "model": model_id,
        "role_id": "runner",
        "schema_version": "0.2",
        "tools": {"allow": [], "mcp": []},
        "write_scope": write_scope,
    }
    lane = {
        "adapter": "codex",
        "budget": {"max_depth": 1, "max_tokens": 0, "max_usd": 0.0},
        "engine": "witnessd",
        "granted_adapters": ["codex"],
        "granted_tools": {"allow": [], "mcp": []},
        "granted_write_scope": write_scope,
        "lane_id": lane_id,
        "may_execute": True,
        "may_verify": False,
        "model": model_id,
        "model_source": "rolepack",
        "phase": "proofrun",
        "prompt": prompt_text,
        "raises_assurance": False,
        "region": write_scope,
        "role_capability": capability,
        "role_id": "runner",
        "role_purpose": "execute the planned work and emit evidence",
        "tier": "frontier",
    }
    role_lanes: dict[str, object] = {
        "boundary": {
            "approves_merge": False,
            "depone_verifies": True,
            "orro_exposes_workflow": True,
            "raises_assurance": False,
            "role_lane_plan_is_proof": False,
            "witnessd_executes": True,
        },
        "execution_allowed": True,
        "goal": goal.strip(),
        "kind": "orro-role-lane-plan",
        "lanes": [lane],
        "schema_version": "0.1",
        "workflow_plan_hash": _canonical_sha256(workflow),
        "workflow_profile": "code-change",
    }
    return workflow, role_lanes


def write_orro_execution_plans(
    workflow_path: Path,
    role_lane_path: Path,
    *,
    workflow: dict[str, object],
    role_lanes: dict[str, object],
) -> None:
    """Persist a compiled ORRO plan pair once without weakening its binding."""
    if workflow_path.exists() or workflow_path.is_symlink():
        raise AuthoringExecutionPacketError("workflow plan already exists")
    if role_lane_path.exists() or role_lane_path.is_symlink():
        raise AuthoringExecutionPacketError("role-lane plan already exists")
    if role_lanes.get("workflow_plan_hash") != _canonical_sha256(workflow):
        raise AuthoringExecutionPacketError("workflow plan hash drift")
    workflow_path.parent.mkdir(parents=True, exist_ok=True)
    role_lane_path.parent.mkdir(parents=True, exist_ok=True)
    workflow_path.write_text(
        json.dumps(workflow, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    role_lane_path.write_text(
        json.dumps(role_lanes, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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
    if relative.parent.parent != required_root:
        raise AuthoringExecutionPacketError(
            "output path must remain inside a versioned execution-binding-v or "
            "comparable-v directory"
        )
    directory_name = relative.parent.name
    is_execution_attempt = bool(ATTEMPT_NAME.fullmatch(directory_name))
    is_comparison = bool(COMPARISON_NAME.fullmatch(directory_name))
    if not is_execution_attempt and not is_comparison:
        raise AuthoringExecutionPacketError(
            "output path must remain inside a versioned execution-binding-v or "
            "comparable-v directory"
        )
    if is_comparison and relative.name not in COMPARISON_OUTPUT_NAMES:
        raise AuthoringExecutionPacketError(
            "output path must name a declared comparable arm"
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
    if relative.parent.parent != required_root or relative.suffix != suffix:
        raise AuthoringExecutionPacketError(
            f"attempt artifact must be a {suffix} file inside execution-binding-vN "
            "or comparable-vN"
        )
    directory_name = relative.parent.name
    is_execution_attempt = bool(ATTEMPT_NAME.fullmatch(directory_name))
    is_comparison = bool(COMPARISON_NAME.fullmatch(directory_name))
    if not is_execution_attempt and not is_comparison:
        raise AuthoringExecutionPacketError(
            f"attempt artifact must be a {suffix} file inside execution-binding-vN "
            "or comparable-vN"
        )
    if is_comparison and relative.name not in COMPARISON_ARTIFACT_NAMES:
        raise AuthoringExecutionPacketError(
            "attempt artifact must name a declared comparable artifact"
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


def _authoring_rule_lines(context_pack: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for catalog_key, label in (
        ("project_rule_catalog", "Project rule"),
        ("rule_catalog", "Paper rule"),
    ):
        catalog = context_pack.get(catalog_key) or {}
        for rule in catalog.get("rules", []):
            rule_id = rule.get("id")
            rule_text = rule.get("rule")
            if isinstance(rule_id, str) and isinstance(rule_text, str):
                lines.append(f"- {label} [{rule_id}]: {rule_text}")
    if not lines:
        lines.append("- No project or paper authoring rules are enabled.")
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


def _required_panel_markers(context_pack: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    for panel in context_pack.get("fixture", {}).get("panels", []):
        panel_id = panel.get("id") if isinstance(panel, dict) else None
        if isinstance(panel_id, str) and panel_id.strip():
            markers.append(f"% Panel {panel_id.strip()}")
    return markers


def _visual_asset_lines(context_pack: dict[str, Any]) -> list[str]:
    selected = context_pack.get("visual_assets", {}).get("selected", [])
    if not selected:
        return ["- No curated visual assets selected."]
    lines: list[str] = []
    for asset in selected:
        lines.append(f"- Curated asset [{asset['id']}]: [{asset['path']}]")
        lines.extend(f"  - {item}" for item in asset.get("authoring_directives", []))
        for pitfall in asset.get("known_pitfalls", []):
            lines.append(f"  - Known pitfall: {pitfall}")
        for anti_pattern in asset.get("anti_patterns", []):
            lines.append(f"  - Do not transfer: {anti_pattern}")
    return lines


def render_authoring_prompt(
    *,
    name: str,
    repository_output_path: str,
    allowed_repository_read_paths: tuple[str, ...],
    context_pack: dict[str, Any],
    model_id: str,
) -> str:
    """Render the sole authoring prompt authority in a deterministic order."""
    lines = [
        f"# Bound authoring execution: {name}",
        "",
        "## Output and attempt boundary",
        "- Resolve every repository path from the repository root.",
        "- Do not change directory before resolving paths.",
        f"- Write exactly one new source to [{repository_output_path}].",
        "- Do not create an intermediate subdirectory beneath "
        f"[{Path(repository_output_path).parent.as_posix()}].",
        "- Start from the declared blank artifact; perform one attempt only.",
        "- Do not inspect or repair historical generated sources.",
        "- Read repository file content only from "
        + " and ".join(f"[{path}]" for path in allowed_repository_read_paths)
        + "; all other required authoring context is already bound below.",
        "",
        "## Mandatory standalone TikZ source requirements",
        *[f"- {requirement}" for requirement in MANDATORY_SOURCE_REQUIREMENTS],
        "",
        "## Required source attribution markers",
        *(
            [
                f"- Add exactly one canonical marker [{marker}] immediately before "
                "that panel's editable body. Keep markers in narrative order."
                for marker in _required_panel_markers(context_pack)
            ]
            or ["- No panel markers are required for this fixture."]
        ),
        "- These comments do not prescribe coordinates or layout; they bind rendered "
        "findings back to editable source regions.",
        "",
        "## Style Lock authoring requirements",
        *[f"- {requirement}" for requirement in STYLE_LOCK_AUTHORING_REQUIREMENTS],
        "",
        "## Semantic contracts and forbidden implications",
        *_fixture_briefing_lines(context_pack),
        "",
        *_contract_lines(context_pack),
        "- Do not imply physics or quantitative relations absent from the declared contracts.",
        "",
        "## Project and paper authoring rules",
        *_authoring_rule_lines(context_pack),
        "",
        "## Curated visual assets",
        *_visual_asset_lines(context_pack),
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
    lines.extend(["", "## Optional composition-profile directives"])
    composition_profile = context_pack.get("composition_profile")
    if composition_profile:
        lines.extend(
            f"- {item}"
            for item in composition_profile.get("authoring_directives", [])
        )
    else:
        lines.append("- No optional composition profile selected.")
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
    composition_profile: str | None = None,
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
    repository_output_path = (
        Path(bound_execution_cwd) / relative_output
    ).as_posix()
    context_pack = authoring_context_pack.build_context_pack(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
        layout_contract=layout_contract,
        shape_profile=shape_profile,
        composition_profile=composition_profile,
    )
    allowed_repository_read_paths = list(
        (Path(bound_execution_cwd) / path).as_posix()
        for path in ALLOWED_REPOSITORY_READ_PATHS
    )
    runtime_visual_assets = deepcopy(context_pack["visual_assets"])
    runtime_visual_assets["root"] = {
        "kind": "plugin_root",
        "path": str(plugin_root.resolve()),
    }
    for asset in runtime_visual_assets.get("selected", []):
        asset["resolved_read_paths"] = [
            str((plugin_root.resolve() / path).resolve())
            for path in asset.get("read_paths", [])
        ]
        allowed_repository_read_paths.extend(asset["resolved_read_paths"])
    allowed_repository_read_paths = tuple(dict.fromkeys(allowed_repository_read_paths))
    context_hash = _sha256_bytes(_canonical_json_bytes(context_pack))
    base_context_pack = {
        key: value
        for key, value in context_pack.items()
        if key not in {"shape_profile", "composition_profile"}
    }
    prompt = render_authoring_prompt(
        name=name,
        repository_output_path=repository_output_path,
        allowed_repository_read_paths=allowed_repository_read_paths,
        context_pack=context_pack,
        model_id=model_id.strip(),
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
        "repository_output_path": repository_output_path,
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
        "composition_profile": (
            {
                "path": context_pack["composition_profile"]["path"],
                "sha256": context_pack["composition_profile"]["sha256"],
                "policy": context_pack["composition_profile"]["policy"],
                "authoring_directives": context_pack["composition_profile"][
                    "authoring_directives"
                ],
            }
            if composition_profile
            else None
        ),
        "visual_assets": runtime_visual_assets,
        "mandatory_source_requirements": list(MANDATORY_SOURCE_REQUIREMENTS),
        "required_panel_markers": _required_panel_markers(context_pack),
        "style_lock_authoring_requirements": list(STYLE_LOCK_AUTHORING_REQUIREMENTS),
        "allowed_repository_read_paths": list(allowed_repository_read_paths),
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


def validate_visual_asset_bindings(packet: dict[str, object]) -> None:
    """Revalidate byte-bound plugin assets immediately before/after execution."""
    visual_assets = packet.get("visual_assets")
    if not isinstance(visual_assets, dict):
        raise AuthoringExecutionPacketError("visual_assets binding invalid")
    root_record = visual_assets.get("root")
    if not isinstance(root_record, dict) or root_record.get("kind") != "plugin_root":
        raise AuthoringExecutionPacketError("visual_assets root binding invalid")
    root_value = root_record.get("path")
    if not isinstance(root_value, str) or not Path(root_value).is_absolute():
        raise AuthoringExecutionPacketError("visual_assets root binding invalid")
    root = Path(root_value).resolve(strict=True)

    records: list[tuple[str, str]] = []
    catalog_path = visual_assets.get("catalog_path")
    catalog_sha256 = visual_assets.get("catalog_sha256")
    if isinstance(catalog_path, str) and isinstance(catalog_sha256, str):
        records.append((catalog_path, catalog_sha256))
    selected = visual_assets.get("selected")
    if not isinstance(selected, list):
        raise AuthoringExecutionPacketError("visual_assets selection invalid")
    allowed_paths = packet.get("allowed_repository_read_paths")
    if not isinstance(allowed_paths, list):
        raise AuthoringExecutionPacketError("allowed repository read paths invalid")
    for asset in selected:
        if not isinstance(asset, dict):
            raise AuthoringExecutionPacketError("visual_assets selection invalid")
        records.append((str(asset.get("path", "")), str(asset.get("sha256", ""))))
        for key in ("contract", "transfer_receipt"):
            binding = asset.get(key)
            if isinstance(binding, dict):
                records.append(
                    (str(binding.get("path", "")), str(binding.get("sha256", "")))
                )
        expected_resolved = [str((root / path).resolve()) for path in asset.get("read_paths", [])]
        if asset.get("resolved_read_paths") != expected_resolved:
            raise AuthoringExecutionPacketError("visual asset resolved path drift")
        if any(path not in allowed_paths for path in expected_resolved):
            raise AuthoringExecutionPacketError("visual asset missing from read allowlist")

    for relative_value, expected_hash in records:
        relative = Path(relative_value)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise AuthoringExecutionPacketError("visual asset path invalid")
        candidate = root / relative
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root) or candidate.is_symlink() or not candidate.is_file():
            raise AuthoringExecutionPacketError("visual asset path invalid")
        if _sha256_bytes(candidate.read_bytes()) != expected_hash:
            raise AuthoringExecutionPacketError(f"visual asset byte drift: {relative_value}")


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
