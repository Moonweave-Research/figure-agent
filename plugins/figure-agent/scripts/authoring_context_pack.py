"""Compile a deterministic, read-only authoring context pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import aesthetic_intent
import authoring_rules
import composition_profile as composition_profile_compiler
import narrative_context
import runtime_paths
import shape_profile as shape_profile_compiler
import yaml
from checks import check_label_path_proximity
from inputs import parse_spec
from semantic_contracts import SemanticContractError, collect_semantic_contracts

SCHEMA = "figure-agent.authoring-context-pack.v1"
VISUAL_ASSETS_SCHEMA = "figure-agent.authoring-visual-assets.v1"
REUSABLE_VISUAL_ASSET_STATUSES = {
    "shipped",
    "reviewed_reusable",
}
LAYOUT_LANES_SCHEMA = "figure-agent.layout-lanes.v1"
SAFE_CATALOG_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class AuthoringContextPackError(ValueError):
    """Raised when an authoring context pack cannot be compiled."""


def _read_optional_text(path: Path, *, limit: int = 12000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def _relative(base: Path, path: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _style_lock_tokens(style_path: Path) -> dict[str, Any]:
    text = _read_optional_text(style_path, limit=20000)
    tokens: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("\\definecolor") or stripped.startswith("\\tikzset"):
            tokens.append(stripped)
    return {
        "path": style_path.name,
        "token_count": len(tokens),
        "tokens": tokens[:80],
    }


def _paper_context(example_dir: Path) -> dict[str, str]:
    files = {
        "briefing": example_dir / "briefing.md",
        "design": example_dir / "design.md",
        "authoring_contract": example_dir / "authoring_contract.md",
        "authoring_plan": example_dir / "authoring_plan.md",
        "theory_guard": example_dir / "theory_guard.md",
        "reference_pack": example_dir / "reference" / "reference_pack.md",
    }
    return {
        key: _read_optional_text(path)
        for key, path in files.items()
        if path.is_file() and _read_optional_text(path)
    }


def _aesthetic_intent(example_dir: Path, workspace_root: Path) -> dict[str, Any] | None:
    try:
        intent = aesthetic_intent.load_optional_aesthetic_intent(example_dir)
    except aesthetic_intent.AestheticIntentError as exc:
        raise AuthoringContextPackError(f"aesthetic intent is invalid: {exc}") from exc
    if intent is None:
        return None

    def render_items(items: list[str]) -> str:
        return "; ".join(item.rstrip(".") for item in items) + "."

    path = example_dir / "aesthetic_intent.yaml"
    directives = [
        f"Preserve {principle['id']}: {principle['instruction']}"
        for principle in intent["design_principles"]
    ]
    for lever in intent.get("aesthetic_levers", []):
        lever_id = lever["id"]
        directives.extend(
            [
                f"For {lever_id}: {lever['intent']}",
                f"Avoid {lever_id} anti-patterns: {render_items(lever['anti_patterns'])}",
                f"Allowed for {lever_id}: {render_items(lever['allowed_adjustments'])}",
                f"Forbidden for {lever_id}: {render_items(lever['forbidden_adjustments'])}",
                f"Use {lever['default_route']} for {lever_id} by default.",
            ]
        )
    return {
        "path": _relative(workspace_root, path),
        "sha256": _sha256_file(path),
        "schema": intent["schema"],
        "authoring_directives": directives,
    }


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_file(plugin_root: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str):
        raise AuthoringContextPackError(f"{label} path is invalid")
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise AuthoringContextPackError(f"{label} path is invalid")
    path = plugin_root / relative
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AuthoringContextPackError(f"{label} path is missing") from exc
    if (
        not resolved.is_relative_to(plugin_root.resolve())
        or path.is_symlink()
        or not path.is_file()
    ):
        raise AuthoringContextPackError(f"{label} path is invalid")
    return path


def _authoring_visual_assets(plugin_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    catalog_path = plugin_root / "styles" / "snippets" / "INDEX.yaml"
    config = spec.get("authoring_context_pack") or {}
    if not isinstance(config, dict):
        raise AuthoringContextPackError("authoring_context_pack must be an object")
    raw_ids = config.get("visual_asset_ids", [])
    if (
        not isinstance(raw_ids, list)
        or any(not isinstance(asset_id, str) or not asset_id for asset_id in raw_ids)
        or len(set(raw_ids)) != len(raw_ids)
    ):
        raise AuthoringContextPackError("visual_asset_ids must be a unique string list")

    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    entries = catalog.get("snippets")
    if not isinstance(entries, dict):
        raise AuthoringContextPackError("curated visual asset catalog is invalid")

    selected: list[dict[str, Any]] = []
    for asset_id in raw_ids:
        entry = entries.get(asset_id)
        if not isinstance(entry, dict):
            raise AuthoringContextPackError(
                f"visual asset id is not present in the curated catalog: {asset_id}"
            )
        status = entry.get("status")
        if status not in REUSABLE_VISUAL_ASSET_STATUSES:
            raise AuthoringContextPackError(
                f"visual asset is not reusable: {asset_id}"
            )
        source_path = _catalog_file(
            plugin_root, entry.get("file"), label=f"visual asset {asset_id}"
        )
        role = entry.get("role") if isinstance(entry.get("role"), dict) else {}
        api = entry.get("api") if isinstance(entry.get("api"), dict) else {}
        directives = [
            f"Reuse curated visual asset [{asset_id}] from [{entry['file']}]. "
            "Do not redraw its owned geometry."
        ]
        source_relative = Path(entry["file"])
        if source_relative.parts[:1] == ("styles",):
            tex_input_path = Path(*source_relative.parts[1:]).as_posix()
            directives.append(
                f"Import [{asset_id}] with "
                rf"[\input{{{tex_input_path}}}] so compile.sh can resolve it."
            )
        signature = api.get("signature")
        tunable = api.get("tunable")
        if isinstance(signature, str):
            tunable_text = (
                ", ".join(str(item) for item in tunable)
                if isinstance(tunable, list)
                else "documented parameters"
            )
            directives.append(
                f"Invoke [{asset_id}] through [{signature}] and adapt only "
                f"[{tunable_text}]."
            )
        depicts = role.get("depicts")
        if isinstance(depicts, str):
            directives.append(f"Preserve its declared role: {depicts}.")

        item: dict[str, Any] = {
            "id": asset_id,
            "status": status,
            "path": entry["file"],
            "sha256": _sha256_file(source_path),
            "role": role,
            "api": api,
            "known_pitfalls": list(entry.get("known_pitfalls") or []),
            "anti_patterns": list(entry.get("anti_patterns") or []),
            "smoke_fixture": entry.get("smoke_fixture", ""),
            "authoring_directives": directives,
            "read_paths": [entry["file"]],
        }
        for output_key, entry_key in (
            ("contract", "contract"),
            ("transfer_receipt", "transfer_receipt"),
        ):
            if entry_key not in entry:
                continue
            binding_path = _catalog_file(
                plugin_root,
                entry[entry_key],
                label=f"visual asset {asset_id} {entry_key}",
            )
            item[output_key] = {
                "path": entry[entry_key],
                "sha256": _sha256_file(binding_path),
            }
            item["read_paths"].append(entry[entry_key])
        transfer = item.get("transfer_receipt")
        if isinstance(transfer, dict):
            receipt_payload = yaml.safe_load(
                (plugin_root / transfer["path"]).read_text(encoding="utf-8")
            ) or {}
            shared_bindings = receipt_payload.get("shared_bindings")
            expected_bindings = {
                item["path"]: item["sha256"],
                **(
                    {item["contract"]["path"]: item["contract"]["sha256"]}
                    if isinstance(item.get("contract"), dict)
                    else {}
                ),
            }
            if not isinstance(shared_bindings, dict) or any(
                shared_bindings.get(path) != digest
                for path, digest in expected_bindings.items()
            ):
                raise AuthoringContextPackError(
                    f"visual asset transfer receipt is stale: {asset_id}"
                )
        selected.append(item)

    return {
        "schema": VISUAL_ASSETS_SCHEMA,
        "catalog_path": "styles/snippets/INDEX.yaml",
        "catalog_sha256": _sha256_file(catalog_path),
        "selected": selected,
    }


def _layout_constraints(
    example_dir: Path,
    selector: str | None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if selector is None:
        return None, None
    relative = Path(selector)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise AuthoringContextPackError(
            "layout contract must be a fixture-relative safe path"
        )
    contract_path = example_dir / relative
    try:
        resolved_contract = contract_path.resolve(strict=True)
    except OSError as exc:
        raise AuthoringContextPackError("layout contract not found or symlinked") from exc
    if not resolved_contract.is_relative_to(example_dir.resolve()):
        raise AuthoringContextPackError("layout contract must remain inside the fixture")
    if contract_path.is_symlink() or not contract_path.is_file():
        raise AuthoringContextPackError("layout contract not found or symlinked")
    payload = yaml.safe_load(resolved_contract.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict) or payload.get("schema") != LAYOUT_LANES_SCHEMA:
        raise AuthoringContextPackError(f"layout contract must use {LAYOUT_LANES_SCHEMA}")
    raw_groups = payload.get("label_groups")
    raw_rules = payload.get("rules")
    if not isinstance(raw_groups, list) or not isinstance(raw_rules, list):
        raise AuthoringContextPackError("layout contract requires label_groups and rules")
    raw_regions = payload.get("regions", [])
    if not isinstance(raw_regions, list):
        raise AuthoringContextPackError("layout regions must be a list")
    regions: set[str] = set()
    for region in raw_regions:
        if not isinstance(region, dict):
            raise AuthoringContextPackError("layout region must be an object")
        region_id = region.get("id")
        bbox = region.get("normalized_bbox")
        if (
            not isinstance(region_id, str)
            or region_id in regions
            or not isinstance(bbox, list)
            or len(bbox) != 4
            or not all(isinstance(value, int | float) for value in bbox)
            or not (
                0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1
            )
        ):
            raise AuthoringContextPackError("layout region is invalid")
        regions.add(region_id)
    groups: dict[str, list[str]] = {}
    for group in raw_groups:
        if not isinstance(group, dict):
            raise AuthoringContextPackError("layout label group must be an object")
        group_id = group.get("id")
        terms = group.get("required_terms")
        phrase = group.get("required_phrase")
        has_terms = (
            isinstance(terms, list)
            and bool(terms)
            and all(isinstance(term, str) and term.strip() for term in terms)
        )
        has_phrase = isinstance(phrase, str) and bool(phrase.strip())
        group_region = group.get("region")
        if (
            not isinstance(group_id, str)
            or group_id in groups
            or has_terms == has_phrase
            or (
                group_region is not None
                and (not isinstance(group_region, str) or group_region not in regions)
            )
        ):
            raise AuthoringContextPackError("layout label group is invalid")
        groups[group_id] = terms if has_terms else [phrase]
    directives: list[str] = []
    raw_text_budgets = payload.get("text_budgets", [])
    if not isinstance(raw_text_budgets, list):
        raise AuthoringContextPackError("layout text_budgets must be a list")
    budget_ids: set[str] = set()
    for budget in raw_text_budgets:
        if not isinstance(budget, dict):
            raise AuthoringContextPackError("layout text budget must be an object")
        budget_id = budget.get("id")
        region = budget.get("region")
        maximum = budget.get("maximum_words")
        if (
            not isinstance(budget_id, str)
            or budget_id in budget_ids
            or not isinstance(region, str)
            or region not in regions
            or not isinstance(maximum, int)
            or isinstance(maximum, bool)
            or maximum < 0
        ):
            raise AuthoringContextPackError("layout text budget is invalid")
        budget_ids.add(budget_id)
        directives.append(
            f"Keep region [{region}] at or below {maximum} rendered words."
        )
    result_ids: set[str] = set()

    def reserve_result_ids(*candidate_ids: str) -> None:
        if any(candidate in result_ids for candidate in candidate_ids):
            raise AuthoringContextPackError("duplicate layout result id")
        result_ids.update(candidate_ids)

    for rule in raw_rules:
        if not isinstance(rule, dict):
            raise AuthoringContextPackError("layout rule is invalid")
        rule_id = rule.get("id")
        if not isinstance(rule_id, str):
            raise AuthoringContextPackError("layout rule is invalid")
        kind = rule.get("kind")
        if kind in {"contained_in_region", "minimum_clearance_from_region"}:
            group = rule.get("group")
            region = rule.get("region")
            minimum_key = (
                "minimum_normalized_inset"
                if kind == "contained_in_region"
                else "minimum_normalized_clearance"
            )
            minimum = rule.get(minimum_key)
            if (
                not isinstance(group, str)
                or group not in groups
                or not isinstance(region, str)
                or region not in regions
                or not isinstance(minimum, int | float)
                or float(minimum) < 0
            ):
                raise AuthoringContextPackError("layout region rule is invalid")
            reserve_result_ids(rule_id)
            terms = ", ".join(groups[group])
            if kind == "contained_in_region":
                directives.append(
                    f"Keep text group [{terms}] inside region [{region}] with at least "
                    f"{float(minimum):g} normalized page inset."
                )
            else:
                directives.append(
                    f"Keep text group [{terms}] at least {float(minimum):g} "
                    f"page-diagonal units clear of region [{region}]."
                )
            continue
        if kind == "minimum_clearance_from_groups":
            group = rule.get("group")
            other_groups = rule.get("other_groups")
            minimum = rule.get("minimum_normalized_clearance")
            if (
                not isinstance(group, str)
                or group not in groups
                or not isinstance(other_groups, list)
                or not other_groups
                or not all(isinstance(item, str) for item in other_groups)
                or len(set(other_groups)) != len(other_groups)
                or group in other_groups
                or any(item not in groups for item in other_groups)
                or not isinstance(minimum, int | float)
                or isinstance(minimum, bool)
                or float(minimum) < 0
            ):
                raise AuthoringContextPackError(
                    "layout group-clearance rule is invalid"
                )
            reserve_result_ids(
                *(f"{rule_id}:{other_group}" for other_group in other_groups)
            )
            group_terms = ", ".join(groups[group])
            neighbor_terms = "; ".join(
                f"[{', '.join(groups[item])}]" for item in other_groups
            )
            directives.append(
                f"Keep text group [{group_terms}] at least {float(minimum):g} "
                "page-diagonal units clear of each declared neighboring text "
                f"group: {neighbor_terms}."
            )
            continue
        if kind != "minimum_clearance":
            raise AuthoringContextPackError("layout rule is invalid")
        first = rule.get("first")
        second = rule.get("second")
        minimum = rule.get("minimum_normalized_clearance")
        if (
            not isinstance(first, str)
            or not isinstance(second, str)
            or first not in groups
            or second not in groups
            or not isinstance(minimum, int | float)
            or float(minimum) < 0
        ):
            raise AuthoringContextPackError("layout clearance rule is invalid")
        reserve_result_ids(rule_id)
        first_terms = ", ".join(groups[first])
        second_terms = ", ".join(groups[second])
        directives.append(
            f"Keep text group [{first_terms}] at least {float(minimum):g} "
            f"page-diagonal units clear of text group [{second_terms}]."
        )
    return contract_path, {
        "schema": LAYOUT_LANES_SCHEMA,
        "label_groups": raw_groups,
        "regions": raw_regions,
        "text_budgets": raw_text_budgets,
        "rules": raw_rules,
        "authoring_directives": directives,
    }


def _shape_profile(
    example_dir: Path,
    selector: str | None,
) -> dict[str, Any] | None:
    if selector is None:
        return None
    if not selector or any(part in {"", ".", ".."} for part in selector.split("/")):
        raise AuthoringContextPackError(
            "shape profile must be a fixture-relative safe path"
        )
    relative = Path(selector)
    if relative.is_absolute() or relative.suffix not in {".yaml", ".yml"}:
        raise AuthoringContextPackError(
            "shape profile must be a fixture-relative YAML path"
        )
    profile_path = example_dir / relative
    fixture_root = example_dir.resolve()
    current = example_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringContextPackError("shape profile not found or symlinked")
    try:
        resolved_profile = profile_path.resolve(strict=True)
    except OSError as exc:
        raise AuthoringContextPackError("shape profile not found or symlinked") from exc
    if not resolved_profile.is_relative_to(fixture_root):
        raise AuthoringContextPackError("shape profile must remain inside the fixture")
    if not profile_path.is_file():
        raise AuthoringContextPackError("shape profile not found or symlinked")
    raw_bytes = resolved_profile.read_bytes()
    raw_payload = yaml.safe_load(raw_bytes)
    try:
        compiled = shape_profile_compiler.compile_shape_profile(raw_payload)
    except shape_profile_compiler.ShapeProfileError as exc:
        raise AuthoringContextPackError(str(exc)) from exc
    return {
        "path": relative.as_posix(),
        "sha256": f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}",
        **compiled,
    }


def _composition_profile(
    example_dir: Path,
    selector: str | None,
) -> dict[str, Any] | None:
    if selector is None:
        return None
    relative = Path(selector)
    if (
        not selector
        or relative.is_absolute()
        or relative.suffix not in {".yaml", ".yml"}
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise AuthoringContextPackError(
            "composition profile must be a fixture-relative YAML path"
        )
    current = example_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringContextPackError("composition profile not found or symlinked")
    try:
        resolved = current.resolve(strict=True)
    except OSError as exc:
        raise AuthoringContextPackError(
            "composition profile not found or symlinked"
        ) from exc
    if not resolved.is_relative_to(example_dir.resolve()) or not resolved.is_file():
        raise AuthoringContextPackError(
            "composition profile must remain inside the fixture"
        )
    raw_bytes = resolved.read_bytes()
    try:
        compiled = composition_profile_compiler.compile_composition_profile(
            yaml.safe_load(raw_bytes)
        )
    except composition_profile_compiler.CompositionProfileError as exc:
        raise AuthoringContextPackError(str(exc)) from exc
    return {
        "path": relative.as_posix(),
        "sha256": f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}",
        **compiled,
    }


def _authoring_context_config(spec: dict[str, Any]) -> dict[str, Any]:
    config = spec.get("authoring_context_pack")
    return config if isinstance(config, dict) else {}


def _safe_catalog_selector(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthoringContextPackError(f"{label} must be a non-empty string")
    selector = value.strip()
    if not SAFE_CATALOG_ID.fullmatch(selector):
        raise AuthoringContextPackError(
            f"{label} must be a safe id or bundled catalog filename"
        )
    return selector


def _catalog_path_for_selector(paths: runtime_paths.RuntimePaths, selector: str) -> Path:
    filename = (
        selector
        if selector.startswith("authoring-rules-") and selector.endswith(".md")
        else f"authoring-rules-{selector}.md"
    )
    return paths.plugin_root / "docs" / filename


def _selected_rule_catalog_path(
    spec: dict[str, Any],
    paths: runtime_paths.RuntimePaths,
) -> Path | None:
    config = _authoring_context_config(spec)
    if "rule_catalog" in config:
        selector = _safe_catalog_selector(
            config.get("rule_catalog"),
            label="authoring_context_pack.rule_catalog",
        )
    else:
        raw_paper_id = (
            config.get("paper_id")
            or spec.get("paper_id")
            or config.get("series_id")
            or spec.get("series_id")
        )
        if raw_paper_id is None:
            return None
        selector = _safe_catalog_selector(raw_paper_id, label="paper_id")
    catalog_path = _catalog_path_for_selector(paths, selector)
    if not catalog_path.is_file():
        raise AuthoringContextPackError(
            f"authoring_context_pack rule catalog not found: {catalog_path.name}"
        )
    return catalog_path


def build_context_pack(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    layout_contract: str | None = None,
    shape_profile: str | None = None,
    composition_profile: str | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        raise AuthoringContextPackError(f"examples/{name} not found")
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        raise AuthoringContextPackError(f"missing {spec_path}")
    spec = parse_spec(spec_path.read_text(encoding="utf-8"))
    try:
        semantic_contracts = collect_semantic_contracts(spec)
    except SemanticContractError as exc:
        raise AuthoringContextPackError(str(exc)) from exc

    catalog_path = _selected_rule_catalog_path(spec, paths)
    fixture_catalog = (
        authoring_rules.load_rule_catalog(catalog_path) if catalog_path is not None else None
    )
    # Optional project-scope catalog: cross-figure conventions (e.g. cantilever
    # orientation) inherited by every figure, not locked to the fig1 pilot.
    project_catalog_path = paths.plugin_root / "docs" / "authoring-rules-project.md"
    project_catalog = (
        authoring_rules.load_rule_catalog(project_catalog_path)
        if project_catalog_path.is_file()
        else None
    )
    philosophy_path = paths.plugin_root / "docs" / "figure-design-philosophy.md"
    style_path = paths.styles_dir / "polymer-paper-preamble.sty"
    layout_path, layout_constraints = _layout_constraints(example_dir, layout_contract)
    label_path_checks = check_label_path_proximity.load_label_path_proximity_checks(
        spec_path
    )
    path_constraints = (
        check_label_path_proximity.authoring_context(label_path_checks)
        if label_path_checks
        else None
    )
    visual_assets = _authoring_visual_assets(paths.plugin_root, spec)
    selected_shape_profile = _shape_profile(example_dir, shape_profile)
    selected_composition_profile = _composition_profile(
        example_dir, composition_profile
    )
    selected_aesthetic_intent = _aesthetic_intent(example_dir, paths.workspace_root)
    payload = {
        "schema": SCHEMA,
        "name": name,
        "read_only": True,
        "sources": {
            "spec": _relative(paths.workspace_root, spec_path),
            "briefing": _relative(paths.workspace_root, example_dir / "briefing.md"),
            "design_philosophy": _relative(paths.plugin_root, philosophy_path),
            "style_lock": _relative(paths.plugin_root, style_path),
            "rule_catalog": (
                _relative(paths.plugin_root, catalog_path)
                if fixture_catalog and catalog_path is not None
                else ""
            ),
            "project_rule_catalog": (
                _relative(paths.plugin_root, project_catalog_path) if project_catalog else ""
            ),
            "layout_lanes": (
                _relative(paths.workspace_root, layout_path) if layout_path is not None else ""
            ),
            "visual_asset_catalog": visual_assets["catalog_path"],
            "aesthetic_intent": (
                selected_aesthetic_intent["path"] if selected_aesthetic_intent else ""
            ),
        },
        "fixture": {
            "title": spec.get("title", ""),
            "style_profile": spec.get("style_profile", ""),
            "panels": [
                {
                    "id": panel.get("id", f"panel_{index + 1}"),
                    "caption": panel.get("caption", ""),
                    "reference_image": panel.get("reference_image", ""),
                }
                for index, panel in enumerate(spec.get("panels", []))
                if isinstance(panel, dict)
            ],
        },
        "design_philosophy": _read_optional_text(philosophy_path),
        "style_lock": _style_lock_tokens(style_path),
        "rule_catalog": fixture_catalog,
        "project_rule_catalog": project_catalog,
        "semantic_contracts": semantic_contracts,
        "visual_assets": visual_assets,
        "narrative_context": narrative_context.build_narrative_context(
            example_dir,
            workspace_root=paths.workspace_root,
            spec=spec,
        ),
        "paper_context": _paper_context(example_dir),
        "layout_constraints": layout_constraints,
        "scope_boundary": {
            "generation_executor": False,
            "prompt_loop": False,
            "model_calls": False,
            "automatic_physics_detector": False,
            "durable_paper_specific_knowledge_compilation": True,
        },
    }
    if selected_shape_profile is not None:
        payload["shape_profile"] = selected_shape_profile
    if selected_composition_profile is not None:
        payload["composition_profile"] = selected_composition_profile
    if selected_aesthetic_intent is not None:
        payload["aesthetic_intent"] = selected_aesthetic_intent
    if path_constraints is not None:
        payload["path_constraints"] = path_constraints
    return payload


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"# Authoring context pack - {payload['name']}",
        "",
        f"Schema: `{payload['schema']}`",
        "Mode: read-only compiler; no generation executor, prompt loop, or model call.",
        "",
        "## Semantic Contracts",
    ]
    contracts = payload["semantic_contracts"]
    if not contracts["enabled"]:
        lines.append("- Not enabled for this fixture.")
    else:
        for claim in contracts["semantic_claims"]:
            lines.append(f"- Claim {claim['panel_id']} {claim['id']}: {claim['claim']}")
        for invariant in contracts["locked_invariants"]:
            lines.append(
                f"- Locked invariant {invariant['panel_id']} {invariant['id']}: "
                f"{invariant['invariant']}"
            )
    project = payload.get("project_rule_catalog")
    if project:
        lines.extend(["", "## Project Rule Catalog (cross-figure conventions)"])
        for rule in project["rules"]:
            lines.append(f"- {rule['id']} ({rule['category']}): {rule['rule']}")
    fixture_catalog = payload.get("rule_catalog")
    if fixture_catalog:
        lines.extend(["", "## Fig1 Rule Catalog"])
        for rule in fixture_catalog["rules"]:
            lines.append(f"- {rule['id']} ({rule['category']}): {rule['rule']}")
    layout_constraints = payload.get("layout_constraints")
    if layout_constraints:
        lines.extend(["", "## Declared Layout Constraints"])
        for directive in layout_constraints["authoring_directives"]:
            lines.append(f"- {directive}")
    path_constraints = payload.get("path_constraints")
    if path_constraints:
        lines.extend(["", "## Declared Label-Path Constraints"])
        for directive in path_constraints["authoring_directives"]:
            lines.append(f"- {directive}")
    selected_shape_profile = payload.get("shape_profile")
    if selected_shape_profile:
        lines.extend(["", "## Shape Profile"])
        for directive in selected_shape_profile["authoring_directives"]:
            lines.append(f"- {directive}")
    selected_composition_profile = payload.get("composition_profile")
    if selected_composition_profile:
        lines.extend(["", "## Composition Profile"])
        for directive in selected_composition_profile["authoring_directives"]:
            lines.append(f"- {directive}")
    selected_aesthetic_intent = payload.get("aesthetic_intent")
    if selected_aesthetic_intent:
        lines.extend(["", "## Aesthetic Intent"])
        for directive in selected_aesthetic_intent["authoring_directives"]:
            lines.append(f"- {directive}")
    visual_assets = payload.get("visual_assets", {})
    selected_assets = visual_assets.get("selected", [])
    lines.extend(["", "## Curated Visual Assets"])
    if selected_assets:
        for asset in selected_assets:
            lines.append(
                f"- {asset['id']} ({asset['status']}): {asset['path']}"
            )
            for directive in asset.get("authoring_directives", []):
                lines.append(f"  - {directive}")
    else:
        lines.append("- No curated visual assets selected.")
    return "\n".join(lines) + "\n"


def main(
    argv: list[str] | None = None,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--layout-contract")
    parser.add_argument("--shape-profile")
    parser.add_argument("--composition-profile")
    args = parser.parse_args(argv)
    try:
        payload = build_context_pack(
            args.name,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            layout_contract=args.layout_contract,
            shape_profile=args.shape_profile,
            composition_profile=args.composition_profile,
        )
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print(f"fig-agent context-pack: {exc}", flush=True)
        return 1
    if args.json or args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
