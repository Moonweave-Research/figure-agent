"""Minimum artifact gates for accepted golden figure fixtures.

Per-fixture contract lives in `spec.yaml` under the `golden_contract` key:

    golden_contract:
      required_labels:
        - "Experiment"               # single requirement: all words must appear
        - ["g e t", "g et"]          # alternatives: at least one must appear
      source_inventory:
        separator_lines: { pattern: '\\\\draw\\[sep\\]', min: 2 }
        band_boxes:      { pattern: '\\\\BandBox\\b', min: 2 }

`required_labels` strings are matched against PDF text after normalization
(lowercase, alphanumeric tokens, symbols replaced). Accepted mode is enabled
by `--require-accepted` or automatically when `spec.yaml` declares the
`accepted` key. Use `--no-require-accepted` for artifact-shape-only inspection.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from PIL import Image

# Reuse the shared TeX comment stripper so source_inventory counts ignore
# commented-out macro calls. Running this module via the pytest harness puts
# the scripts/ directory on sys.path; running it as a CLI does the same.
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
for script_dir in reversed(
    (
        SCRIPTS_DIR,
        SCRIPTS_DIR / "checks",
        SCRIPTS_DIR / "candidates",
        SCRIPTS_DIR / "quality",
        SCRIPTS_DIR / "loop",
        SCRIPTS_DIR / "driver",
    )
):
    sys.path.insert(0, str(script_dir))

import fixture_identity  # noqa: E402
import human_attestation  # noqa: E402
from inputs import parse_spec  # noqa: E402
from lint_tex import strip_tex_comment  # noqa: E402
from publication_gate import publication_compliance_failure_records  # noqa: E402
from quality_manifest import input_manifest_hash, yaml_frontmatter  # noqa: E402
from reference_pack import reference_pack_failures  # noqa: E402

VISIBLE_SVG_TAGS = frozenset(
    {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "text", "use"}
)
IGNORED_SVG_SUBTREES = frozenset({"defs", "desc", "metadata", "style", "title"})
MIN_TIFF_DPI = 590.0


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_pdf_text(text: str) -> str:
    replacements = {
        "α": " alpha ",
        "τ": " tau ",
        "∝": " propto ",
        "−": "-",
        "–": "-",
        "—": "-",
        "_": " ",
        "-": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def _label_present(haystack_with_padding: str, label: str) -> bool:
    """True if every normalized token of label appears as a word in haystack."""
    normalized = normalize_pdf_text(label)
    if not normalized:
        return True
    return all(f" {token} " in haystack_with_padding for token in normalized.split())


def _canonical_label_name(entry: str | list) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, list) and entry:
        return str(entry[0])
    return repr(entry)


def missing_pdf_labels(text: str, required: list | None) -> list[str]:
    """Return canonical names of required labels that are not present.

    `required` is a list whose entries are either:
      - a string: that string's normalized tokens must all appear in `text`
      - a list of strings: at least one alternative must all-appear in `text`
    `None` or empty list returns []."""
    if not required:
        return []
    normalized = normalize_pdf_text(text)
    haystack = f" {normalized} "
    missing: list[str] = []
    for entry in required:
        if isinstance(entry, str):
            if not _label_present(haystack, entry):
                missing.append(entry)
        elif isinstance(entry, list):
            if not entry or not all(isinstance(alt, str) for alt in entry):
                raise ValueError(
                    f"required_labels list entry must be non-empty list of str: {entry!r}"
                )
            if not any(_label_present(haystack, alt) for alt in entry):
                missing.append(_canonical_label_name(entry))
        else:
            raise ValueError(f"invalid required_labels entry: {entry!r}")
    return missing


def extract_pdf_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {pdf_path}: {result.stderr}")
    return result.stdout


def count_svg_visible_elements(svg_path: Path) -> int:
    root = ET.parse(svg_path).getroot()

    def visit(element: ET.Element, ignored: bool = False) -> int:
        local = _local_name(element.tag)
        ignored = ignored or local in IGNORED_SVG_SUBTREES
        count = 0
        if not ignored and local in VISIBLE_SVG_TAGS:
            count += 1
        for child in element:
            count += visit(child, ignored)
        return count

    return visit(root)


def png_has_white_opaque_corners(png_path: Path, tolerance: int = 8) -> bool:
    with Image.open(png_path) as image:
        rgba = image.convert("RGBA")
        width, height = rgba.size
        if width < 2 or height < 2:
            return False
        corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
        for point in corners:
            red, green, blue, alpha = rgba.getpixel(point)
            if alpha != 255:
                return False
            if any(channel < 255 - tolerance for channel in (red, green, blue)):
                return False
    return True


def fixture_is_accepted(spec_path: Path) -> bool:
    if not spec_path.exists():
        return False
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("accepted") is True


def spec_declares_accepted_key(spec_path: Path) -> bool:
    """Return True iff spec.yaml declares the `accepted` key (any value).

    Used to auto-escalate `check_example` into accepted mode for any fixture
    whose spec class is golden, so a missing --require-accepted CLI flag
    cannot silently bypass the contract.
    """
    if not spec_path.exists():
        return False
    return "accepted" in _load_spec_mapping(spec_path)


def _load_spec_mapping(spec_path: Path) -> dict:
    if not spec_path.exists():
        return {}
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid spec.yaml: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _validate_spec_semantics(spec_path: Path) -> None:
    if not spec_path.exists():
        return
    try:
        parse_spec(spec_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        if str(exc).startswith("invalid spec.yaml:"):
            raise
        raise ValueError(f"invalid spec.yaml: {exc}") from exc


def _resolve_fixture_relative_path(example_dir: Path, relative: str) -> Path | None:
    if Path(relative).is_absolute():
        return None
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def required_export_artifact_failures(exports: Path, name: str) -> list[str]:
    """Verify the four required export artifacts exist. TIFF accepts .tif or .tiff."""
    failures: list[str] = []
    pdf = exports / f"{name}.pdf"
    svg = exports / f"{name}.svg"
    tif = exports / f"{name}.tif"
    tiff = exports / f"{name}.tiff"
    png = exports / f"{name}.png"
    if not pdf.exists():
        failures.append(f"missing artifact: {pdf}")
    if not svg.exists():
        failures.append(f"missing artifact: {svg}")
    if not (tif.exists() or tiff.exists()):
        failures.append(f"missing artifact: {tif} (or {tiff.name})")
    else:
        tiff_failure = tiff_artifact_failure(tif if tif.exists() else tiff)
        if tiff_failure:
            failures.append(tiff_failure)
    if not png.exists():
        failures.append(f"missing artifact: {png}")
    return failures


def tiff_artifact_path(exports: Path, name: str) -> Path:
    tif = exports / f"{name}.tif"
    if tif.exists():
        return tif
    return exports / f"{name}.tiff"


def _float_or_none(value: object) -> float | None:
    try:
        return float(value)  # PIL IFDRational implements float().
    except (TypeError, ValueError):
        return None


def _tiff_dpi(image: Image.Image) -> tuple[float, float] | None:
    dpi = image.info.get("dpi")
    if isinstance(dpi, tuple) and len(dpi) >= 2:
        x_dpi = _float_or_none(dpi[0])
        y_dpi = _float_or_none(dpi[1])
        if x_dpi is not None and y_dpi is not None:
            return x_dpi, y_dpi

    x_resolution = image.tag_v2.get(282)
    y_resolution = image.tag_v2.get(283)
    resolution_unit = image.tag_v2.get(296, 2)
    x_value = _float_or_none(x_resolution)
    y_value = _float_or_none(y_resolution)
    if x_value is None or y_value is None:
        return None
    if resolution_unit == 3:  # pixels per centimeter
        return x_value * 2.54, y_value * 2.54
    return x_value, y_value


def tiff_artifact_failure(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            if image.format != "TIFF":
                return f"invalid TIFF artifact: {path} is {image.format or 'unknown format'}"
            dpi = _tiff_dpi(image)
            if dpi is None:
                return f"invalid TIFF artifact: {path} missing DPI metadata"
            x_dpi, y_dpi = dpi
            if x_dpi < MIN_TIFF_DPI or y_dpi < MIN_TIFF_DPI:
                return f"TIFF resolution below 600 dpi: {path} reports {x_dpi:.1f}x{y_dpi:.1f} dpi"
            image.verify()
    except Exception as exc:
        return f"invalid TIFF artifact: {path}: {exc}"
    return None


def load_golden_contract(spec_path: Path) -> dict | None:
    """Return spec.yaml's golden_contract block, or None when absent.

    Validates basic shape; raises ValueError on malformed input."""
    if not spec_path.exists():
        return None
    try:
        data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid spec.yaml: {exc}") from exc
    if not isinstance(data, dict):
        return None
    contract = data.get("golden_contract")
    if contract is None:
        return None
    if not isinstance(contract, dict):
        raise ValueError("golden_contract must be a mapping")

    required_labels = contract.get("required_labels")
    if required_labels is not None and not isinstance(required_labels, list):
        raise ValueError("golden_contract.required_labels must be a list")

    inventory = contract.get("source_inventory")
    if inventory is not None:
        if not isinstance(inventory, dict):
            raise ValueError("golden_contract.source_inventory must be a mapping")
        for name, entry in inventory.items():
            if not isinstance(entry, dict):
                raise ValueError(f"golden_contract.source_inventory[{name!r}] must be a mapping")
            if not isinstance(entry.get("pattern"), str):
                raise ValueError(
                    f"golden_contract.source_inventory[{name!r}].pattern must be a string"
                )
            if not isinstance(entry.get("min"), int):
                raise ValueError(
                    f"golden_contract.source_inventory[{name!r}].min must be an integer"
                )
    return contract


def _strip_tex_comments_from_source(tex: str) -> str:
    """Strip TeX comments line-by-line so commented macro calls are not
    mistakenly counted by the source-inventory regex. Reuses lint_tex's
    backslash-escape-aware comment stripper for parity."""
    return "\n".join(strip_tex_comment(line) for line in tex.splitlines())


def source_inventory_counts(tex: str, patterns: dict | None) -> dict[str, int]:
    """Count regex hits for each named pattern in the contract.

    Comments are stripped before matching so a `% \\BandBox{...}` line cannot
    silently satisfy an inventory floor.
    """
    if not patterns:
        return {}
    cleaned = _strip_tex_comments_from_source(tex)
    counts: dict[str, int] = {}
    for name, entry in patterns.items():
        pattern = entry.get("pattern") if isinstance(entry, dict) else None
        if not pattern:
            continue
        counts[name] = len(re.findall(pattern, cleaned))
    return counts


def source_inventory_failures(tex_path: Path, patterns: dict | None) -> list[str]:
    if not patterns:
        return []
    counts = source_inventory_counts(tex_path.read_text(encoding="utf-8"), patterns)
    failures: list[str] = []
    for name, entry in patterns.items():
        if not isinstance(entry, dict):
            continue
        minimum = entry.get("min", 0)
        value = counts.get(name, 0)
        if value < minimum:
            failures.append(f"source inventory too low: {name} {value} < {minimum}")
    return failures


AUDIT_INPUT_HASH_KEY = "audit_input_hash"


def audit_source_paths(example_dir: Path) -> tuple[Path, ...]:
    """The source set whose content the QUALITY_AUDIT.md freshness reflects.

    Single definition shared by the freshness gate and the stamper so the stored
    hash and the recomputed hash always cover the same files."""
    name = example_dir.name
    exports = example_dir / "exports"
    return (
        example_dir / "spec.yaml",
        example_dir / "briefing.md",
        example_dir / f"{name}.tex",
        exports / f"{name}.pdf",
        exports / f"{name}.svg",
        tiff_artifact_path(exports, name),
        exports / f"{name}.png",
    )


def audit_input_hash(example_dir: Path, source_paths: tuple[Path, ...]) -> str:
    """Content hash over the audit's source set using the quality_manifest
    primitive. base_dir=example_dir keeps the manifest path strings relative to
    the fixture so the hash is invariant to where the repo is checked out."""
    return input_manifest_hash(source_paths, base_dir=example_dir)


def audit_is_fresh(example_dir: Path, source_paths: tuple[Path, ...]) -> bool:
    """Freshness of QUALITY_AUDIT.md against its source set.

    Content-based when the audit front-matter carries an `audit_input_hash`: the
    hash is recomputed over the same sources and compared, closing the gap where
    timestamp-preserving restores (git clone, cp -p, rsync --times) leave a stale
    audit mtime-fresh. Falls back to the legacy mtime check for audits that carry
    no hash (e.g. the committed golden fixture)."""
    audit = example_dir / "QUALITY_AUDIT.md"
    if not audit.exists():
        return False
    stored_hash = yaml_frontmatter(audit).get(AUDIT_INPUT_HASH_KEY)
    if isinstance(stored_hash, str) and stored_hash.strip():
        if not all(path.exists() for path in source_paths):
            return False
        return stored_hash.strip() == audit_input_hash(example_dir, source_paths)
    audit_mtime = audit.stat().st_mtime
    return all(path.exists() and path.stat().st_mtime <= audit_mtime for path in source_paths)


def stamp_audit_input_hash(example_dir: Path, source_paths: tuple[Path, ...]) -> Path:
    """Write the content hash into QUALITY_AUDIT.md front-matter so future
    freshness checks are content-based. Call after all sources exist in final
    form (post-export, post human/host finalization), not at scaffold time."""
    audit = example_dir / "QUALITY_AUDIT.md"
    digest = audit_input_hash(example_dir, source_paths)
    body = audit.read_text(encoding="utf-8") if audit.exists() else ""
    audit.write_text(_with_audit_input_hash(body, digest), encoding="utf-8")
    return audit


def _with_audit_input_hash(body: str, digest: str) -> str:
    """Return audit text with `audit_input_hash` set in a leading YAML
    front-matter block, updating the key in place if a block already exists."""
    hash_line = f"{AUDIT_INPUT_HASH_KEY}: {digest}"
    lines = body.splitlines()
    if lines and lines[0].strip() == "---":
        end_index = next(
            (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
            None,
        )
        if end_index is not None:
            front = lines[1:end_index]
            replaced = False
            for index, line in enumerate(front):
                if line.split(":", 1)[0].strip() == AUDIT_INPUT_HASH_KEY:
                    front[index] = hash_line
                    replaced = True
                    break
            if not replaced:
                front.append(hash_line)
            return "\n".join(["---", *front, "---", *lines[end_index + 1 :]]) + "\n"
    rest = f"\n{body}" if body else ""
    return f"---\n{hash_line}\n---\n{rest}"


def checker_warning_counts(audit_text: str) -> tuple[int | None, int | None]:
    collision_match = re.search(r"(\d+)\s+collision\(s\)", audit_text)
    clash_match = re.search(r"(\d+)\s+visual clash candidate\(s\)", audit_text)
    if collision_match:
        collisions = int(collision_match.group(1))
    elif "OK: no collisions found" in audit_text:
        collisions = 0
    else:
        collisions = None
    visual_clashes = int(clash_match.group(1)) if clash_match else None
    return collisions, visual_clashes


def unresolved_visual_clash_count(audit_text: str) -> int | None:
    match = re.search(r"(\d+)\s+unresolved visual clash\(es\)", audit_text)
    return int(match.group(1)) if match else None


def checker_budget_failures(
    audit_path: Path, *, max_collisions: int, max_visual_clashes: int
) -> list[str]:
    if not audit_path.exists():
        return ["missing audit: QUALITY_AUDIT.md"]
    audit_text = audit_path.read_text(encoding="utf-8")
    collisions, visual_clashes = checker_warning_counts(audit_text)
    unresolved_visual_clashes = unresolved_visual_clash_count(audit_text)
    failures = []
    if collisions is None:
        failures.append("missing collision count in QUALITY_AUDIT.md")
    elif collisions > max_collisions:
        failures.append(f"collision budget exceeded: {collisions} > {max_collisions}")
    if visual_clashes is None:
        failures.append("missing visual clash count in QUALITY_AUDIT.md")
    if unresolved_visual_clashes is None:
        failures.append("missing unresolved visual clash count in QUALITY_AUDIT.md")
    elif unresolved_visual_clashes > max_visual_clashes:
        failures.append(
            "unresolved visual clash budget exceeded: "
            f"{unresolved_visual_clashes} > {max_visual_clashes}"
        )
    return failures


def theory_guard_failures(theory_guard_path: Path) -> list[str]:
    if not theory_guard_path.exists():
        return ["missing theory guard: theory_guard.md"]

    failures: list[str] = []
    for line in theory_guard_path.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        guard_id, severity, _claim, _method, evidence = cells[:5]
        if severity != "BLOCKER" or guard_id == "ID":
            continue

        status = evidence.lower().lstrip()
        has_bad_status = status.startswith(("fail", "failed", "unresolved", "unknown", "open"))
        has_pass_status = status.startswith(("pass", "passed", "closed", "resolved", "verified"))
        if has_bad_status or not has_pass_status:
            failures.append(f"theory BLOCKER not passing: {guard_id}")
    return failures


def publication_compliance_failures(
    audit_path: Path, *, require_disclosure: bool = False
) -> list[str]:
    return [
        record.message
        for record in publication_compliance_failure_records(
            audit_path,
            require_disclosure=require_disclosure,
        )
    ]


def _requires_final_artifact_disclosure(spec_path: Path) -> bool:
    if not spec_path.exists():
        return False
    try:
        data = _load_spec_mapping(spec_path)
    except ValueError:
        return False
    final_artifact = data.get("final_artifact")
    if not isinstance(final_artifact, dict):
        return False
    kind = final_artifact.get("kind")
    if kind in {None, "", "generated_export"}:
        return False
    return True


def _spec_declares_reference_inputs(spec_path: Path) -> bool:
    if not spec_path.exists():
        return False
    try:
        data = _load_spec_mapping(spec_path)
    except ValueError:
        return False
    if isinstance(data.get("reference_image"), str) and data["reference_image"].strip():
        return True
    for panel in data.get("panels", []):
        if isinstance(panel, dict):
            reference = panel.get("reference_image")
            if isinstance(reference, str) and reference.strip():
                return True
    return False


def reference_pack_gate_failures(example_dir: Path, spec_path: Path) -> list[str]:
    pack_path = example_dir / "reference" / "reference_pack.md"
    if pack_path.exists() or _spec_declares_reference_inputs(spec_path):
        return reference_pack_failures(pack_path)
    return []


def check_example(
    example_dir: Path,
    *,
    min_svg_elements: int = 40,
    min_png_width: int = 1000,
    require_accepted: bool | None = None,
    max_collisions: int = 0,
    max_visual_clashes: int = 0,
) -> list[str]:
    name = example_dir.name
    exports = example_dir / "exports"
    spec = example_dir / "spec.yaml"
    tex = example_dir / f"{name}.tex"
    audit = example_dir / "QUALITY_AUDIT.md"
    pdf = exports / f"{name}.pdf"
    svg = exports / f"{name}.svg"
    png = exports / f"{name}.png"
    failures: list[str] = []
    try:
        _load_spec_mapping(spec)
    except ValueError as exc:
        return [str(exc)]

    # Auto-escalate to accepted mode whenever the fixture's spec.yaml declares
    # the `accepted` key (regardless of true/false). The key's presence is the
    # signal that the fixture is in the golden class; a forgotten CLI flag
    # must not be able to silently bypass the contract.
    if require_accepted is None:
        try:
            require_accepted = spec_declares_accepted_key(spec)
        except ValueError as exc:
            return [str(exc)]

    failures.extend(required_export_artifact_failures(exports, name))
    if failures:
        return failures

    # Basic artifact-shape checks (always run).
    svg_count = count_svg_visible_elements(svg)
    if svg_count < min_svg_elements:
        failures.append(f"SVG has too few visible elements: {svg_count} < {min_svg_elements}")

    with Image.open(png) as image:
        width, _height = image.size
    if width < min_png_width:
        failures.append(f"PNG width too small: {width} < {min_png_width}")
    if not png_has_white_opaque_corners(png):
        failures.append("PNG corners are not opaque white")

    # Acceptance-gate checks. Driven by spec.yaml's golden_contract block, so a
    # second golden fixture only needs to write its own contract instead of
    # editing this script.
    if require_accepted:
        try:
            _validate_spec_semantics(spec)
        except ValueError as exc:
            return [str(exc)]
        try:
            contract = load_golden_contract(spec)
        except ValueError as exc:
            if str(exc).startswith("invalid spec.yaml:"):
                failures.append(str(exc))
            else:
                failures.append(f"invalid golden_contract: {exc}")
            return failures
        if contract is None:
            failures.append(
                "golden_contract block missing in spec.yaml (required for --require-accepted)"
            )
            return failures

        if not fixture_is_accepted(spec):
            failures.append("fixture is not marked accepted: true")

        attested, attestation_reason = human_attestation.verify_attestation(example_dir)
        if not attested:
            failures.append(f"human attestation invalid: {attestation_reason}")

        required_labels = contract.get("required_labels")
        missing = missing_pdf_labels(extract_pdf_text(pdf), required_labels)
        if missing:
            failures.append(f"missing rendered PDF labels: {', '.join(missing)}")

        failures.extend(source_inventory_failures(tex, contract.get("source_inventory")))

        if not audit_is_fresh(example_dir, audit_source_paths(example_dir)):
            failures.append("QUALITY_AUDIT.md is stale or missing")
        failures.extend(theory_guard_failures(example_dir / "theory_guard.md"))
        failures.extend(
            publication_compliance_failures(
                audit,
                require_disclosure=_requires_final_artifact_disclosure(spec),
            )
        )
        failures.extend(reference_pack_gate_failures(example_dir, spec))
        failures.extend(
            checker_budget_failures(
                audit,
                max_collisions=max_collisions,
                max_visual_clashes=max_visual_clashes,
            )
        )

    return failures


def _resolve_example_dir_for_cli(value: Path) -> Path:
    if value.is_absolute():
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise ValueError("invalid fixture path: expected examples/<fixture-name>")
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise ValueError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return value
    raise ValueError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, or an absolute path"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise ValueError(f"invalid fixture path: {original}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument("--min-svg-elements", type=int, default=40)
    parser.add_argument("--min-png-width", type=int, default=1000)
    # Mutually exclusive override of the auto-escalation default. Without
    # either flag, the fixture's spec.yaml decides whether accepted-mode
    # contract checks run.
    accepted_group = parser.add_mutually_exclusive_group()
    accepted_group.add_argument(
        "--require-accepted",
        dest="require_accepted",
        action="store_true",
        default=None,
        help="force accepted-mode contract checks regardless of spec",
    )
    accepted_group.add_argument(
        "--no-require-accepted",
        dest="require_accepted",
        action="store_false",
        help="force basic mode (skip contract checks) even if spec declares accepted",
    )
    parser.add_argument("--max-collisions", type=int, default=0)
    parser.add_argument("--max-visual-clashes", type=int, default=0)
    parser.add_argument(
        "--stamp-audit-hash",
        action="store_true",
        help=(
            "stamp the content hash of the audit source set into "
            "QUALITY_AUDIT.md front-matter; run after exports and the finalized "
            "audit exist, then exit"
        ),
    )
    args = parser.parse_args()

    if args.stamp_audit_hash:
        try:
            example_dir = _resolve_example_dir_for_cli(args.example_dir)
        except ValueError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        sources = audit_source_paths(example_dir)
        missing = [str(path) for path in sources if not path.exists()]
        if missing:
            print(
                f"FAIL: cannot stamp audit hash, missing sources: {', '.join(missing)}",
                file=sys.stderr,
            )
            return 1
        if not (example_dir / "QUALITY_AUDIT.md").exists():
            print("FAIL: cannot stamp audit hash, missing QUALITY_AUDIT.md", file=sys.stderr)
            return 1
        stamp_audit_input_hash(example_dir, sources)
        print(f"OK: stamped audit_input_hash for {example_dir.name}")
        return 0

    try:
        example_dir = _resolve_example_dir_for_cli(args.example_dir)
        failures = check_example(
            example_dir,
            min_svg_elements=args.min_svg_elements,
            min_png_width=args.min_png_width,
            require_accepted=args.require_accepted,
            max_collisions=args.max_collisions,
            max_visual_clashes=args.max_visual_clashes,
        )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"OK: golden artifact gates passed for {example_dir.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
