"""Build a lean, self-contained local marketplace for Codex development."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import package_cowork_plugin

PLUGIN_NAME = "figure-agent"
MARKETPLACE_NAME = "figure-agent-local"


class CodexMarketplaceBuildError(ValueError):
    """Raised when a local marketplace export would be unsafe or ambiguous."""


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        member_path = Path(member.filename)
        target = destination / member_path
        if member_path.is_absolute() or not target.resolve().is_relative_to(root):
            raise CodexMarketplaceBuildError("archive_path_escape")
        if member.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)


def _marketplace_payload() -> dict[str, object]:
    return {
        "name": MARKETPLACE_NAME,
        "interface": {"displayName": "Figure Agent local development"},
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }


def build_marketplace(output: Path) -> dict[str, object]:
    """Export the release package as a marketplace without repository baggage."""
    output = output.expanduser()
    if output.exists():
        raise CodexMarketplaceBuildError("output_already_exists")
    with tempfile.TemporaryDirectory(prefix="figure-agent-codex-marketplace-") as temp:
        release_dir = Path(temp)
        zip_path = package_cowork_plugin.build_zip(release_dir)
        plugin_destination = output / "plugins" / PLUGIN_NAME
        plugin_destination.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as archive:
            _safe_extract(archive, plugin_destination)
    marketplace_path = output / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True)
    marketplace_path.write_text(
        json.dumps(_marketplace_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": "figure-agent.codex-marketplace-export.v1",
        "marketplace_path": marketplace_path.as_posix(),
        "plugin_root": plugin_destination.as_posix(),
        "source": "release_zip",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = build_marketplace(args.output)
    except CodexMarketplaceBuildError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["marketplace_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
