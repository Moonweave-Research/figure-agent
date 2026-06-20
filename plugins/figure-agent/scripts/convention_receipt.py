"""Surface the injected use_as_constraint authoring rules as a build receipt.

Spec §4 Phase 1a (injection receipt): at compile time list which catalog rules
were injected into the figure's authoring context, each with its source quote, so
the author sees "cantilever = vertical (clip on top); source: ..." on every figure.

This is report-only and the demonstrated-valuable injection half: it only SURFACES
the already-injected rules. It does NOT verify anything against the render (that is
Phase 1b, out of scope here).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import authoring_context_pack
import runtime_paths
import yaml

SCHEMA = "figure-agent.convention-receipt.v1"
TRANSFER_POLICY = "use_as_constraint"


class ConventionReceiptError(ValueError):
    """Raised when a convention receipt cannot be compiled."""


def _injected_rules(
    catalog: dict[str, Any] | None, scope: str, source_path: str
) -> list[dict[str, Any]]:
    if not catalog:
        return []
    injected: list[dict[str, Any]] = []
    for rule in catalog["rules"]:
        if rule.get("transfer_policy") != TRANSFER_POLICY:
            continue
        source = rule["source"]
        injected.append(
            {
                "id": rule["id"],
                "scope": scope,
                "category": rule["category"],
                "rule": rule["rule"],
                "transfer_policy": TRANSFER_POLICY,
                "source": {
                    "kind": source["kind"],
                    "locator": source["locator"],
                    "quote": source["quote"],
                },
                "catalog": source_path,
            }
        )
    return injected


def build_convention_receipt(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    """Compile the deterministic injection receipt for one fixture."""
    pack = authoring_context_pack.build_context_pack(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    project_source = pack["sources"].get("project_rule_catalog", "")
    fixture_source = pack["sources"].get("rule_catalog", "")
    conventions = _injected_rules(
        pack.get("project_rule_catalog"),
        scope="project",
        source_path=project_source,
    )
    conventions.extend(
        _injected_rules(
            pack.get("rule_catalog"),
            scope="fixture",
            source_path=fixture_source,
        )
    )
    return {
        "schema": SCHEMA,
        "name": name,
        "read_only": True,
        "context_pack_schema": pack["schema"],
        "transfer_policy": TRANSFER_POLICY,
        "sources": {
            "project_rule_catalog": project_source,
            "rule_catalog": fixture_source,
        },
        "counts": {
            "project": sum(1 for rule in conventions if rule["scope"] == "project"),
            "fixture": sum(1 for rule in conventions if rule["scope"] == "fixture"),
            "total": len(conventions),
        },
        "conventions": conventions,
        "scope_boundary": {
            "render_verification": False,
            "model_calls": False,
            "auto_mutation": False,
            "injection_surface_only": True,
        },
    }


def render_text(payload: dict[str, Any]) -> str:
    lines = [
        f"# Convention propagation receipt - {payload['name']}",
        "",
        f"Schema: `{payload['schema']}`",
        "Mode: report-only injection surface; no render verification or model call.",
        "",
        (
            f"Injected `{payload['transfer_policy']}` conventions: "
            f"{payload['counts']['total']} "
            f"(project: {payload['counts']['project']}, fixture: {payload['counts']['fixture']})"
        ),
        "",
        "## Injected conventions",
    ]
    if not payload["conventions"]:
        lines.append("- None injected for this fixture.")
    else:
        for rule in payload["conventions"]:
            lines.append(f"- {rule['id']} [{rule['scope']}] ({rule['category']}): {rule['rule']}")
            source = rule["source"]
            lines.append(f"  - source: {source['locator']}")
            lines.append(f'  - quote: "{source["quote"]}"')
    return "\n".join(lines) + "\n"


def write_receipt(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    """Build the receipt and write build/convention_receipt.{json,md}."""
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        raise ConventionReceiptError(f"examples/{name} not found")
    payload = build_convention_receipt(
        name,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    build_dir = example_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "convention_receipt.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (build_dir / "convention_receipt.md").write_text(render_text(payload), encoding="utf-8")
    return payload


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
    parser.add_argument(
        "--write",
        action="store_true",
        help="write build/convention_receipt.{json,md} for the fixture",
    )
    args = parser.parse_args(argv)
    try:
        if args.write:
            payload = write_receipt(
                args.name,
                plugin_root=plugin_root,
                workspace_root=workspace_root,
            )
        else:
            payload = build_convention_receipt(
                args.name,
                plugin_root=plugin_root,
                workspace_root=workspace_root,
            )
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print(f"fig-agent convention-receipt: {exc}", flush=True)
        return 1
    if args.json or args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
