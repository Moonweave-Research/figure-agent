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
    args = parser.parse_args(argv)
    try:
        payload = build_context_pack(
            args.name,
            plugin_root=plugin_root,
            workspace_root=workspace_root,
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
