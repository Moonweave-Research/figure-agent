"""Scaffold SVG polish audit and manifest files for one fixture."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import fixture_identity
from quality_manifest import file_sha256
from svg_polish_manifest import (
    ALLOWED_EDIT_CLASSES,
    ALLOWED_EDITORS,
    STYLE_LOCK_PATH,
    SVG_POLISH_MANIFEST_RELATIVE_PATH,
    final_artifact_source_set_hash,
    write_svg_polish_manifest,
)

AUDIT_RELATIVE_PATH = "polish/svg_polish_audit.md"
SEMANTIC_BACKPORT_CHECKS = (
    ("components", "pass"),
    ("labels/material identity", "pass"),
    ("mechanism directions", "pass"),
    ("panel/storyline meaning", "pass"),
    ("scale/proximity meaning", "pass"),
    ("unresolved critique findings", "visible"),
)


class SvgPolishHandoffError(ValueError):
    """Controlled error for SVG polish handoff scaffold failures."""


def _fixture_name(example_dir: Path) -> str:
    name = example_dir.name
    if not name:
        raise SvgPolishHandoffError("example_dir must name one fixture")
    return name


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise SvgPolishHandoffError(f"missing {label}: {path}")


def _require_non_empty_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SvgPolishHandoffError(f"{label} must be a non-empty string")
    return value.strip()


def _validate_editor(editor: str) -> None:
    if editor not in ALLOWED_EDITORS:
        allowed = ", ".join(sorted(ALLOWED_EDITORS))
        raise SvgPolishHandoffError(f"editor must be one of: {allowed}")


def _validate_edit_classes(edit_classes: Sequence[str]) -> list[str]:
    if not edit_classes:
        raise SvgPolishHandoffError("at least one --edit-class is required")
    result: list[str] = []
    for edit_class in edit_classes:
        if edit_class not in ALLOWED_EDIT_CLASSES:
            allowed = ", ".join(sorted(ALLOWED_EDIT_CLASSES))
            raise SvgPolishHandoffError(f"unknown edit class {edit_class!r}; allowed: {allowed}")
        if edit_class not in result:
            result.append(edit_class)
    return result


def _validate_toolchain(toolchain: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    if not toolchain:
        raise SvgPolishHandoffError("at least one --toolchain entry is required")
    result: list[dict[str, str]] = []
    for index, item in enumerate(toolchain):
        name = item.get("name", "").strip()
        version = item.get("version", "").strip()
        if not name or not version:
            raise SvgPolishHandoffError(
                f"toolchain[{index}] must include non-empty name and version"
            )
        result.append({"name": name, "version": version})
    return result


def _validate_inputs(example_dir: Path, name: str, polished_path: Path) -> None:
    if not example_dir.is_dir():
        raise SvgPolishHandoffError(f"fixture directory does not exist: {example_dir}")
    required = (
        (example_dir / f"{name}.tex", "source TeX"),
        (example_dir / "briefing.md", "briefing.md"),
        (example_dir / "spec.yaml", "spec.yaml"),
        (example_dir / "exports" / f"{name}.svg", "generated SVG export"),
        (example_dir / "exports" / f"{name}.pdf", "generated PDF export"),
        (example_dir / "critique.md", "critique.md"),
        (polished_path, "polished SVG"),
    )
    for path, label in required:
        _require_file(path, label)


def _validate_metadata(reviewer: str, reviewed_at: str, notes: str) -> tuple[str, str, str]:
    return (
        _require_non_empty_text(reviewer, "reviewer"),
        _require_non_empty_text(reviewed_at, "reviewed_at"),
        _require_non_empty_text(notes, "notes"),
    )


def _guard_output_paths(audit_path: Path, manifest_path: Path, *, force: bool) -> None:
    if force:
        return
    existing = [path for path in (audit_path, manifest_path) if path.exists()]
    if existing:
        joined = ", ".join(str(path) for path in existing)
        raise SvgPolishHandoffError(f"refusing to overwrite existing output(s): {joined}")


def build_audit_markdown(
    example_dir: Path,
    *,
    reviewer: str,
    editor: str,
    toolchain: Sequence[dict[str, str]],
    edit_classes: Sequence[str],
    reviewed_at: str,
    notes: str,
    semantic_change_declared: bool,
    backport_required: bool,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path | None = None,
) -> str:
    """Return deterministic `svg_polish_audit.md` content for the fixture."""
    name = _fixture_name(example_dir)
    base_dir = base_dir or Path(__file__).resolve().parents[1]
    generated_svg = example_dir / "exports" / f"{name}.svg"
    export_pdf = example_dir / "exports" / f"{name}.pdf"
    polished_svg = example_dir / "polish" / f"{name}.polished.svg"
    _validate_inputs(example_dir, name, polished_svg)
    _validate_editor(editor)
    reviewer, reviewed_at, notes = _validate_metadata(reviewer, reviewed_at, notes)
    edit_classes = _validate_edit_classes(edit_classes)
    toolchain = _validate_toolchain(toolchain)
    source_set_hash = final_artifact_source_set_hash(
        example_dir,
        name,
        style_lock_path=style_lock_path,
        base_dir=base_dir,
    )
    lines = [
        f"# SVG Polish Audit: {name}",
        "",
        "## Base Artifact",
        "",
        f"- generated_svg: exports/{name}.svg",
        f"- generated_svg_hash: {file_sha256(generated_svg)}",
        f"- export_pdf_hash: {file_sha256(export_pdf)}",
        f"- source_set_hash: {source_set_hash}",
        "",
        "## Polished Artifact",
        "",
        f"- polished_svg: polish/{name}.polished.svg",
        f"- polished_svg_hash: {file_sha256(polished_svg)}",
        f"- manifest: {SVG_POLISH_MANIFEST_RELATIVE_PATH}",
        "",
        "## Edit Classes",
        "",
    ]
    for edit_class in edit_classes:
        lines.append(f"- {edit_class}: visual-only polish")
    lines.extend(
        [
            "",
            "## Semantic Preservation",
            "",
            f"- semantic_change_declared: {str(semantic_change_declared).lower()}",
            f"- backport_required: {str(backport_required).lower()}",
            f"- reviewer_decision: {notes}",
            "",
            "## Must-Backport Review",
            "",
        ]
    )
    for label, verdict in SEMANTIC_BACKPORT_CHECKS:
        lines.append(f"- {label}: {verdict} + reviewed")
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- reviewer: {reviewer}",
            f"- reviewed_at: {reviewed_at}",
            f"- editor: {editor}",
            "- toolchain:",
        ]
    )
    for item in toolchain:
        lines.append(f"  - {item['name']} {item['version']}")
    lines.extend(
        [
            "",
            "## Closeout",
            "",
            "- compile/export refreshed if needed: operator-confirmed",
            "- critique refreshed if needed: operator-confirmed",
            "- manifest recreated or validated: yes",
            "- /fig_status final artifact state: pending",
            "",
        ]
    )
    return "\n".join(lines)


def build_manifest_payload(
    example_dir: Path,
    *,
    reviewer: str,
    editor: str,
    toolchain: Sequence[dict[str, str]],
    edit_classes: Sequence[str],
    reviewed_at: str,
    notes: str,
    semantic_change_declared: bool,
    backport_required: bool,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Build a manifest payload for the current polish/audit files."""
    name = _fixture_name(example_dir)
    base_dir = base_dir or Path(__file__).resolve().parents[1]
    _validate_editor(editor)
    reviewer, reviewed_at, notes = _validate_metadata(reviewer, reviewed_at, notes)
    edit_classes = _validate_edit_classes(edit_classes)
    toolchain = _validate_toolchain(toolchain)
    _validate_inputs(example_dir, name, example_dir / "polish" / f"{name}.polished.svg")
    _require_file(example_dir / AUDIT_RELATIVE_PATH, "svg_polish_audit.md")
    return {
        "schema": "figure-agent.svg-polish-manifest.v1",
        "fixture": name,
        "base": {
            "source_set_hash": final_artifact_source_set_hash(
                example_dir,
                name,
                style_lock_path=style_lock_path,
                base_dir=base_dir,
            ),
            "source_tex_hash": file_sha256(example_dir / f"{name}.tex"),
            "briefing_hash": file_sha256(example_dir / "briefing.md"),
            "spec_hash": file_sha256(example_dir / "spec.yaml"),
            "generated_svg_hash": file_sha256(example_dir / "exports" / f"{name}.svg"),
            "export_pdf_hash": file_sha256(example_dir / "exports" / f"{name}.pdf"),
            "critique_hash": file_sha256(example_dir / "critique.md"),
        },
        "polished": {
            "path": f"polish/{name}.polished.svg",
            "polished_svg_hash": file_sha256(example_dir / "polish" / f"{name}.polished.svg"),
            "audit_hash": file_sha256(example_dir / AUDIT_RELATIVE_PATH),
            "editor": editor,
            "toolchain": list(toolchain),
            "edit_classes": list(edit_classes),
            "semantic_change_declared": semantic_change_declared,
            "backport_required": backport_required,
        },
        "provenance": {
            "reviewer": reviewer,
            "reviewed_at": reviewed_at,
            "notes": notes,
        },
    }


def write_handoff_files(
    example_dir: Path,
    *,
    reviewer: str,
    editor: str,
    toolchain: Sequence[dict[str, str]],
    edit_classes: Sequence[str],
    reviewed_at: str,
    notes: str,
    semantic_change_declared: bool,
    backport_required: bool,
    force: bool = False,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write audit then manifest for one polished SVG handoff."""
    name = _fixture_name(example_dir)
    audit_path = example_dir / AUDIT_RELATIVE_PATH
    manifest_path = example_dir / SVG_POLISH_MANIFEST_RELATIVE_PATH
    polished_path = example_dir / "polish" / f"{name}.polished.svg"
    _validate_inputs(example_dir, name, polished_path)
    _validate_editor(editor)
    reviewer, reviewed_at, notes = _validate_metadata(reviewer, reviewed_at, notes)
    edit_classes = _validate_edit_classes(edit_classes)
    toolchain = _validate_toolchain(toolchain)
    _guard_output_paths(audit_path, manifest_path, force=force)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit = build_audit_markdown(
        example_dir,
        reviewer=reviewer,
        editor=editor,
        toolchain=toolchain,
        edit_classes=edit_classes,
        reviewed_at=reviewed_at,
        notes=notes,
        semantic_change_declared=semantic_change_declared,
        backport_required=backport_required,
        style_lock_path=style_lock_path,
        base_dir=base_dir,
    )
    audit_path.write_text(audit, encoding="utf-8")
    manifest = build_manifest_payload(
        example_dir,
        reviewer=reviewer,
        editor=editor,
        toolchain=toolchain,
        edit_classes=edit_classes,
        reviewed_at=reviewed_at,
        notes=notes,
        semantic_change_declared=semantic_change_declared,
        backport_required=backport_required,
        style_lock_path=style_lock_path,
        base_dir=base_dir,
    )
    write_svg_polish_manifest(manifest_path, manifest)
    return audit_path, manifest_path


def _parse_toolchain(value: str) -> dict[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("toolchain must use NAME:VERSION")
    name, version = value.split(":", 1)
    if not name.strip() or not version.strip():
        raise argparse.ArgumentTypeError("toolchain must use NAME:VERSION")
    return {"name": name.strip(), "version": version.strip()}


def _resolve_example_dir_for_cli(value: Path) -> Path:
    if value.is_absolute():
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise SvgPolishHandoffError(
                "invalid fixture path: expected examples/<fixture-name>"
            )
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise SvgPolishHandoffError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return value
    raise SvgPolishHandoffError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, "
        "or an absolute path"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise SvgPolishHandoffError(f"invalid fixture path: {original}: {exc}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--editor", required=True)
    parser.add_argument("--toolchain", action="append", type=_parse_toolchain, required=True)
    parser.add_argument("--edit-class", action="append", dest="edit_classes", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--notes", default="visual-only polish")
    parser.add_argument("--semantic-change-declared", action="store_true")
    parser.add_argument("--backport-required", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--style-lock-path", type=Path, default=STYLE_LOCK_PATH)
    parser.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parents[1])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        example_dir = _resolve_example_dir_for_cli(args.example_dir)
        if args.write:
            audit_path, manifest_path = write_handoff_files(
                example_dir,
                reviewer=args.reviewer,
                editor=args.editor,
                toolchain=args.toolchain,
                edit_classes=args.edit_classes,
                reviewed_at=args.reviewed_at,
                notes=args.notes,
                semantic_change_declared=args.semantic_change_declared,
                backport_required=args.backport_required,
                force=args.force,
                style_lock_path=args.style_lock_path,
                base_dir=args.base_dir,
            )
            print(f"wrote {audit_path.relative_to(example_dir)}")
            print(f"wrote {manifest_path.relative_to(example_dir)}")
            return 0
        name = _fixture_name(example_dir)
        _validate_inputs(
            example_dir,
            name,
            example_dir / "polish" / f"{name}.polished.svg",
        )
        _validate_editor(args.editor)
        _validate_metadata(args.reviewer, args.reviewed_at, args.notes)
        _validate_edit_classes(args.edit_classes)
        _validate_toolchain(args.toolchain)
        print("dry-run: would write polish/svg_polish_audit.md")
        print("dry-run: would write polish/svg_polish_manifest.yaml")
        return 0
    except SvgPolishHandoffError as exc:
        print(f"svg_polish_handoff.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
