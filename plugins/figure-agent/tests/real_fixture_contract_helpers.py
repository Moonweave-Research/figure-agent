"""Shared helpers for real-fixture contract tests."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_TIME = 1_700_000_000.0
FRESH_TIME = OLD_TIME + 100


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def copy_fixture_to_repo(tmp_path: Path, fixture_name: str) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    examples_dir = repo_root / "examples"
    examples_dir.mkdir(parents=True)
    source = REPO_ROOT / "examples" / fixture_name
    if not source.is_dir():
        pytest.skip(f"real fixture not present in this plugin tree: {source}")
    fixture = examples_dir / fixture_name
    shutil.copytree(source, fixture, ignore=shutil.ignore_patterns("build", "exports"))
    return repo_root, fixture


def materialize_controlled_artifacts(
    fixture: Path,
    fixture_name: str,
    contract: dict[str, Any],
) -> None:
    artifacts = contract.get("artifacts", {})
    assert isinstance(artifacts, dict)
    if artifacts.get("build_pdf"):
        build_pdf = fixture / "build" / f"{fixture_name}.pdf"
        build_pdf.parent.mkdir(parents=True, exist_ok=True)
        build_pdf.write_bytes(b"%PDF-1.4\n% controlled test artifact\n")

    exports = artifacts.get("exports", [])
    assert isinstance(exports, list)
    for ext in exports:
        assert isinstance(ext, str)
        export_path = fixture / "exports" / f"{fixture_name}.{ext}"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_bytes(b"controlled test artifact\n")


def set_tree_mtime(root: Path, timestamp: float) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.utime(path, (timestamp, timestamp))


def normalize_fixture_mtimes(fixture: Path, fixture_name: str) -> None:
    set_tree_mtime(fixture, OLD_TIME)
    for directory_name in ("build", "exports"):
        directory = fixture / directory_name
        if directory.is_dir():
            set_tree_mtime(directory, FRESH_TIME)
    for path in (
        fixture / "critique.md",
        fixture / "critique_adjudication.yaml",
    ):
        if path.is_file():
            os.utime(path, (FRESH_TIME, FRESH_TIME))
    build_pdf = fixture / "build" / f"{fixture_name}.pdf"
    if build_pdf.is_file():
        os.utime(build_pdf, (FRESH_TIME, FRESH_TIME))


def stable_style_lock(tmp_path: Path) -> Path:
    style_lock = tmp_path / "polymer-paper-preamble.sty"
    style_lock.write_text("% stable style lock\n", encoding="utf-8")
    os.utime(style_lock, (OLD_TIME, OLD_TIME))
    return style_lock
