"""Compile a deterministic, read-only authoring context pack."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import authoring_rules
import narrative_context
import runtime_paths
import yaml
from inputs import parse_spec
from semantic_contracts import SemanticContractError, collect_semantic_contracts

SCHEMA = "figure-agent.authoring-context-pack.v1"
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
    for rule in raw_rules:
        if not isinstance(rule, dict):
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
    return {
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
    args = parser.parse_args(argv)
    try:
        payload = build_context_pack(
            args.name,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
            layout_contract=args.layout_contract,
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
