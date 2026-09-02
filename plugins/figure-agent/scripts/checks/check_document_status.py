#!/usr/bin/env python3
"""Validate Figure Agent document governance."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from document_status import (  # noqa: E402
    GOVERNED_DOCUMENT_SUFFIXES,
    PLUGIN_ROOT,
    classify_document,
    load_policy,
)

# Shipped from the plugin root by scripts/package_cowork_plugin.py. Scanning
# only docs/ left them unclassified, so behavioral instruction reached an
# installed bundle outside the policy that is supposed to fail closed.
PACKAGED_ROOT_FILES = (
    ".mcp.json",
    "AGENTS.md",
    "CHANGELOG.md",
    "README.md",
    "pyproject.toml",
    "uv.lock",
)


def check(plugin_root: Path = PLUGIN_ROOT) -> dict[str, object]:
    policy = load_policy(plugin_root / "docs" / "document-status.yaml")
    documents = [
        path
        for path in (plugin_root / "docs").rglob("*")
        if path.is_file() and path.suffix.lower() in GOVERNED_DOCUMENT_SUFFIXES
    ]
    documents.extend(
        path for name in PACKAGED_ROOT_FILES if (path := plugin_root / name).is_file()
    )
    statuses = [
        classify_document(path.relative_to(plugin_root), policy=policy)
        for path in documents
    ]
    authority = [status.path for status in statuses if status.classification == "authority"]
    unclassified = [status.path for status in statuses if status.classification == "unclassified"]
    executable_non_active = [
        status.path for status in statuses if status.agent_executable and not status.active
    ]
    invalid_shippable = [
        status.path
        for status in statuses
        if status.ship and status.classification not in {"authority", "reference"}
    ]
    findings = {
        "authority_count": len(authority),
        "authority": authority,
        "unclassified": sorted(unclassified),
        "executable_non_active": sorted(executable_non_active),
        "invalid_shippable": sorted(invalid_shippable),
    }
    findings["passed"] = (
        authority == [policy.get("authority")]
        and not unclassified
        and not executable_non_active
        and not invalid_shippable
    )
    return findings


def main() -> int:
    result = check()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
