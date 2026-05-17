from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quality_manifest import input_manifest_hash  # noqa: E402


def test_input_manifest_hash_changes_when_file_content_changes(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("first\n", encoding="utf-8")

    before = input_manifest_hash((source,), base_dir=tmp_path)
    source.write_text("second\n", encoding="utf-8")
    after = input_manifest_hash((source,), base_dir=tmp_path)

    assert before.startswith("sha256:")
    assert after.startswith("sha256:")
    assert before != after


def test_input_manifest_hash_is_stable_for_path_order(tmp_path: Path) -> None:
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("a\n", encoding="utf-8")
    second.write_text("b\n", encoding="utf-8")

    assert input_manifest_hash((first, second), base_dir=tmp_path) == input_manifest_hash(
        (second, first), base_dir=tmp_path
    )
