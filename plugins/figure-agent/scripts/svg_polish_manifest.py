"""Parse and validate SVG polish final-artifact manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from inputs import parse_spec
from quality_manifest import file_sha256, input_manifest_hash
from reference_contract import (
    declared_figure_reference_path,
    participating_panel_reference_paths,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
STYLE_LOCK_PATH = REPO_ROOT / "styles" / "polymer-paper-preamble.sty"
SCHEMA = "figure-agent.svg-polish-manifest.v1"
ALLOWED_EDITORS = frozenset({"human", "external_tool", "agent_assisted"})
ALLOWED_EDIT_CLASSES = frozenset(
    {
        "label_micro_position",
        "leader_line_micro_position",
        "stroke_polish",
        "icon_detail",
        "spacing_balance",
        "color_opacity_polish",
        "typography_cleanup",
        "export_cleanup",
    }
)
_HASH_FIELDS = (
    ("base", "source_set_hash"),
    ("base", "source_tex_hash"),
    ("base", "briefing_hash"),
    ("base", "spec_hash"),
    ("base", "generated_svg_hash"),
    ("base", "export_pdf_hash"),
    ("base", "critique_hash"),
    ("polished", "polished_svg_hash"),
    ("polished", "audit_hash"),
)


class SvgPolishManifestError(ValueError):
    """Expected user-facing error for malformed SVG polish manifest files."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SvgPolishManifestError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SvgPolishManifestError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_bool(data: dict[str, Any], key: str, *, label: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise SvgPolishManifestError(f"{label}.{key} must be a boolean")
    return value


def _require_sha256(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
        raise SvgPolishManifestError(f"{label} must be a sha256:<64 hex chars> string")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise SvgPolishManifestError(f"{label} must be lowercase sha256 hex")


def _load_spec(example_dir: Path) -> dict:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return {}
    try:
        return parse_spec(spec_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise SvgPolishManifestError(f"invalid spec.yaml: {exc}") from exc


def final_artifact_source_paths(
    example_dir: Path,
    name: str,
    spec: dict | None = None,
    *,
    style_lock_path: Path = STYLE_LOCK_PATH,
) -> tuple[Path, ...]:
    """Return files whose content affects a polished final artifact."""
    if spec is None:
        spec = _load_spec(example_dir)
    candidates = [
        example_dir / f"{name}.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
        style_lock_path,
        example_dir / "coordinate_hints.yaml",
        example_dir / "authoring_contract.md",
        example_dir / "authoring_plan.md",
        example_dir / "theory_guard.md",
        example_dir / "subregion_iteration_log.md",
        example_dir / "reference" / "reference_pack.md",
    ]
    ref_path = declared_figure_reference_path(example_dir, spec)
    if ref_path is not None:
        candidates.append(ref_path)
    candidates.extend(participating_panel_reference_paths(example_dir, spec))
    return tuple(dict.fromkeys(path for path in candidates if path.is_file()))


def final_artifact_source_set_hash(
    example_dir: Path,
    name: str,
    spec: dict | None = None,
    *,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path = REPO_ROOT,
) -> str:
    """Compute repo-relative source-set hash for final-artifact freshness."""
    return input_manifest_hash(
        final_artifact_source_paths(
            example_dir,
            name,
            spec,
            style_lock_path=style_lock_path,
        ),
        base_dir=base_dir,
    )


def _resolve_fixture_path(example_dir: Path, relative: str, label: str) -> Path:
    if Path(relative).is_absolute():
        raise SvgPolishManifestError(f"{label} must be fixture-relative")
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SvgPolishManifestError(f"{label} must stay inside the fixture") from exc
    return resolved


def _validate_polished_path(example_dir: Path, value: str) -> Path:
    resolved = _resolve_fixture_path(example_dir, value, "manifest.polished.path")
    relative = resolved.relative_to(example_dir.resolve())
    parts = relative.parts
    if not parts or parts[0] != "polish":
        raise SvgPolishManifestError("manifest.polished.path must live under polish/")
    if len(parts) < 2:
        raise SvgPolishManifestError("manifest.polished.path must point to a file")
    if "exports" in parts or "build" in parts:
        raise SvgPolishManifestError("manifest.polished.path must not point to build/exports")
    return resolved


def validate_svg_polish_manifest(
    data: dict[str, Any],
    *,
    example_dir: Path,
) -> dict[str, Any]:
    """Validate an SVG polish manifest mapping and return it unchanged."""
    data = _require_mapping(data, "manifest")
    if data.get("schema") != SCHEMA:
        raise SvgPolishManifestError(f"manifest.schema must be {SCHEMA}")
    fixture = _require_non_empty_string(data, "fixture", label="manifest")
    if fixture != example_dir.name:
        raise SvgPolishManifestError("manifest.fixture must match the fixture directory name")

    base = _require_mapping(data.get("base"), "manifest.base")
    polished = _require_mapping(data.get("polished"), "manifest.polished")
    provenance = _require_mapping(data.get("provenance"), "manifest.provenance")
    for section, key in _HASH_FIELDS:
        section_data = base if section == "base" else polished
        value = _require_non_empty_string(section_data, key, label=f"manifest.{section}")
        _require_sha256(value, f"manifest.{section}.{key}")

    _validate_polished_path(
        example_dir,
        _require_non_empty_string(polished, "path", label="manifest.polished"),
    )
    editor = _require_non_empty_string(polished, "editor", label="manifest.polished")
    if editor not in ALLOWED_EDITORS:
        allowed = ", ".join(sorted(ALLOWED_EDITORS))
        raise SvgPolishManifestError(f"manifest.polished.editor must be one of: {allowed}")

    toolchain = polished.get("toolchain")
    if not isinstance(toolchain, list) or not toolchain:
        raise SvgPolishManifestError("manifest.polished.toolchain must be a non-empty list")
    for index, item in enumerate(toolchain):
        item = _require_mapping(item, f"manifest.polished.toolchain[{index}]")
        _require_non_empty_string(item, "name", label=f"manifest.polished.toolchain[{index}]")
        _require_non_empty_string(item, "version", label=f"manifest.polished.toolchain[{index}]")

    edit_classes = polished.get("edit_classes")
    if not isinstance(edit_classes, list) or not edit_classes:
        raise SvgPolishManifestError("manifest.polished.edit_classes must be a non-empty list")
    for index, edit_class in enumerate(edit_classes):
        if not isinstance(edit_class, str) or edit_class not in ALLOWED_EDIT_CLASSES:
            allowed = ", ".join(sorted(ALLOWED_EDIT_CLASSES))
            raise SvgPolishManifestError(
                f"manifest.polished.edit_classes[{index}] must be one of: {allowed}"
            )

    _require_bool(polished, "semantic_change_declared", label="manifest.polished")
    _require_bool(polished, "backport_required", label="manifest.polished")
    _require_non_empty_string(provenance, "reviewer", label="manifest.provenance")
    _require_non_empty_string(provenance, "reviewed_at", label="manifest.provenance")
    return data


def load_svg_polish_manifest(path: Path, *, example_dir: Path) -> dict[str, Any]:
    """Load and validate an SVG polish manifest YAML file."""
    if not path.is_file():
        raise SvgPolishManifestError(f"missing SVG polish manifest: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SvgPolishManifestError(f"invalid UTF-8 in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise SvgPolishManifestError(f"invalid YAML in {path}: {exc}") from exc
    return validate_svg_polish_manifest(data, example_dir=example_dir)


def write_svg_polish_manifest(path: Path, data: dict[str, Any]) -> None:
    """Validate and write an SVG polish manifest YAML file."""
    example_dir = path.parent.parent
    validated = validate_svg_polish_manifest(data, example_dir=example_dir)
    path.write_text(
        yaml.safe_dump(validated, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _expected_hashes(
    data: dict[str, Any],
    *,
    example_dir: Path,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path = REPO_ROOT,
) -> dict[tuple[str, str], str]:
    name = data["fixture"]
    polished_path = _resolve_fixture_path(example_dir, data["polished"]["path"], "polished.path")
    try:
        return {
            ("base", "source_set_hash"): final_artifact_source_set_hash(
                example_dir,
                name,
                style_lock_path=style_lock_path,
                base_dir=base_dir,
            ),
            ("base", "source_tex_hash"): file_sha256(example_dir / f"{name}.tex"),
            ("base", "briefing_hash"): file_sha256(example_dir / "briefing.md"),
            ("base", "spec_hash"): file_sha256(example_dir / "spec.yaml"),
            ("base", "generated_svg_hash"): file_sha256(example_dir / "exports" / f"{name}.svg"),
            ("base", "export_pdf_hash"): file_sha256(example_dir / "exports" / f"{name}.pdf"),
            ("base", "critique_hash"): file_sha256(example_dir / "critique.md"),
            ("polished", "polished_svg_hash"): file_sha256(polished_path),
            ("polished", "audit_hash"): file_sha256(
                example_dir / "polish" / "svg_polish_audit.md"
            ),
        }
    except FileNotFoundError as exc:
        raise SvgPolishManifestError(f"missing SVG polish input: {exc.filename}") from exc


def svg_polish_manifest_is_stale(
    path: Path,
    *,
    example_dir: Path,
    style_lock_path: Path = STYLE_LOCK_PATH,
    base_dir: Path = REPO_ROOT,
) -> bool:
    """Return True when manifest hashes differ from current fixture content."""
    data = load_svg_polish_manifest(path, example_dir=example_dir)
    expected = _expected_hashes(
        data,
        example_dir=example_dir,
        style_lock_path=style_lock_path,
        base_dir=base_dir,
    )
    for section, key in _HASH_FIELDS:
        if data[section][key] != expected[(section, key)]:
            return True
    return False
