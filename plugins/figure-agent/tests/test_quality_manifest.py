from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from quality_manifest import critique_manifest_paths, input_manifest_hash  # noqa: E402


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


def test_critique_manifest_includes_audit_crop_manifest_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    manifest_path = example_dir / "build" / "audit_crops" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text('{"schema":"figure-agent.audit-crop-manifest.v1"}\n')

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    manifest_path.write_text('{"schema":"figure-agent.audit-crop-manifest.v1","n":1}\n')
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert manifest_path in paths
    assert before != after


def test_critique_manifest_includes_text_boundary_report_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    report_path = example_dir / "build" / "text_boundary_clash.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        '{"schema":"figure-agent.text-boundary-clash.v1","total":0}\n',
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    report_path.write_text(
        '{"schema":"figure-agent.text-boundary-clash.v1","total":1}\n',
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert report_path in paths
    assert before != after


def test_critique_manifest_includes_critique_reference_pack_when_present(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "examples" / "demo"
    example_dir.mkdir(parents=True)
    style_lock = tmp_path / "style-lock.yml"
    style_lock.write_text("style\n", encoding="utf-8")
    for name in ("demo.tex", "briefing.md", "spec.yaml"):
        (example_dir / name).write_text(f"{name}\n", encoding="utf-8")
    pack_path = example_dir / "critique_reference_pack.yaml"
    pack_path.write_text(
        "schema: figure-agent.critique-reference-pack.v1\nfixture: demo\n",
        encoding="utf-8",
    )

    paths = critique_manifest_paths(
        example_dir,
        "demo",
        {"name": "demo"},
        style_lock_path=style_lock,
    )
    before = input_manifest_hash(paths, base_dir=tmp_path)
    pack_path.write_text(
        "schema: figure-agent.critique-reference-pack.v1\nfixture: demo\nchanged: true\n",
        encoding="utf-8",
    )
    after = input_manifest_hash(paths, base_dir=tmp_path)

    assert pack_path in paths
    assert before != after
