"""Build a deterministic Claude Cowork ZIP for figure-agent."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _version() -> str:
    data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
    return str(data["version"])


def _is_generated_or_cache(path: Path) -> bool:
    rel_parts = path.relative_to(PLUGIN_ROOT).parts
    generated_names = {
        ".DS_Store",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "exports",
        "previews",
        "dist",
        ".scratch",
        "node_modules",
    }
    return any(part in generated_names for part in rel_parts) or path.suffix == ".pyc"


def _included_doc_files() -> list[Path]:
    docs_root = PLUGIN_ROOT / "docs"
    if not docs_root.is_dir():
        return []
    files = [path for path in docs_root.glob("*.md") if path.is_file()]
    macros_root = docs_root / "macros"
    if macros_root.is_dir():
        files.extend(path for path in macros_root.rglob("*.md") if path.is_file())
    return files


def _included_files() -> list[Path]:
    roots = [
        PLUGIN_ROOT / ".claude-plugin",
        PLUGIN_ROOT / "mcp",
        PLUGIN_ROOT / "skills",
        PLUGIN_ROOT / "commands",
        PLUGIN_ROOT / "scripts",
        PLUGIN_ROOT / "styles",
        PLUGIN_ROOT / "bin",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*") if path.is_file())
    files.extend(_included_doc_files())
    for name in ("README.md", "CHANGELOG.md", "AGENTS.md", "pyproject.toml", "uv.lock"):
        path = PLUGIN_ROOT / name
        if path.is_file():
            files.append(path)
    mcp_config = PLUGIN_ROOT / ".mcp.json"
    if mcp_config.is_file():
        files.append(mcp_config)
    smoke_root = PLUGIN_ROOT / "examples" / "smoke_trap_demo"
    if smoke_root.is_dir():
        files.extend(
            path
            for path in smoke_root.rglob("*")
            if path.is_file() and not _is_generated_or_cache(path)
        )
    return sorted(set(files), key=lambda path: path.relative_to(PLUGIN_ROOT).as_posix())


def build_zip(output_dir: Path) -> Path:
    version = _version()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"figure-agent-cowork-{version}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _included_files():
            if _is_generated_or_cache(path):
                continue
            rel = path.relative_to(PLUGIN_ROOT).as_posix()
            info = zipfile.ZipInfo(rel)
            info.date_time = (2026, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if rel == "bin/fig-agent" else 0o644) << 16
            archive.writestr(info, path.read_bytes())
    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("dist/cowork"))
    args = parser.parse_args(argv)
    print(build_zip(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
