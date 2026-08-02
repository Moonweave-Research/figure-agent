"""Validate a fixture's physical print-size contract against its PDF and TeX.

The PDF is authored at its natural size and scaled when placed in a manuscript.
This check therefore validates the declared natural page geometry, the
height-limited target placement, and the smallest explicitly declared TeX font
at that placement scale. It intentionally does not infer journal policy from
pixels or treat a screen render as print-size evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

PT_TO_MM = 25.4 / 72.0
MM_TOLERANCE = 0.25
FONT_TOLERANCE = 0.01
JOURNAL_MIN_PRINT_FONT_PT = 5.0
NATURE_FAMILY_BASES = {
    "height_limited_nature_family_main_figure",
    "width_limited_nature_family_main_figure",
}


class PrintSizeContractError(ValueError):
    """Raised when the print-size contract is malformed or violated."""


def find_contract_file(tex_path: Path) -> Path | None:
    """Find a source-specific or nearest fixture print-size contract.

    A sibling ``<source-stem>.authority.yaml`` is reserved for a prospective
    review source whose natural page geometry differs from the canonical
    fixture.  It scopes only the print-size measurement to that source; it
    cannot alter fixture acceptance, semantic contracts, or promotion state.
    """

    source_specific = tex_path.with_suffix(".authority.yaml")
    if source_specific.is_file():
        return source_specific

    for directory in (tex_path.parent, *tex_path.parents):
        for name in ("spec.yaml", "authority.yaml"):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def _number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PrintSizeContractError(f"{name} must be numeric") from exc
    if result <= 0:
        raise PrintSizeContractError(f"{name} must be positive")
    return result


def _contract_values(contract: dict[str, Any]) -> tuple[float, float, float, float, float]:
    natural = contract.get("natural_size_mm")
    if not isinstance(natural, list) or len(natural) != 2:
        raise PrintSizeContractError("natural_size_mm must contain [width, height]")
    natural_width = _number(natural[0], "natural_size_mm[0]")
    natural_height = _number(natural[1], "natural_size_mm[1]")
    target_width = _number(contract.get("target_width_mm"), "target_width_mm")
    max_height = _number(contract.get("max_height_mm"), "max_height_mm")
    min_print_font = _number(contract.get("min_print_font_pt"), "min_print_font_pt")
    return natural_width, natural_height, target_width, max_height, min_print_font


def _journal_policy_floor(contract: dict[str, Any]) -> float | None:
    """Return the built-in floor for an explicitly named journal profile."""

    if contract.get("basis") in NATURE_FAMILY_BASES:
        return JOURNAL_MIN_PRINT_FONT_PT
    return None


def _page_size_pt(pdf_path: Path) -> tuple[float, float]:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PrintSizeContractError(f"pdfinfo failed: {result.stderr.strip()}")
    match = re.search(r"^Page size:\s*([0-9.]+) x ([0-9.]+) pts", result.stdout, re.MULTILINE)
    if match is None:
        raise PrintSizeContractError("pdfinfo did not report a point-size page")
    return float(match.group(1)), float(match.group(2))


def _font_sizes_pt(tex_text: str) -> list[float]:
    return [
        float(value)
        for value in re.findall(
            r"\\fontsize\s*\{\s*([0-9]+(?:\.[0-9]+)?)\s*\}", tex_text
        )
    ]


def evaluate_contract(
    *,
    page_size_pt: tuple[float, float],
    source_font_sizes_pt: list[float],
    contract: dict[str, Any],
    policy_min_print_font_pt: float | None = None,
) -> dict[str, Any]:
    """Return deterministic print-size metrics and violations."""

    natural_width, natural_height, target_width, max_height, min_print_font = (
        _contract_values(contract)
    )
    effective_min_print_font = max(
        min_print_font,
        policy_min_print_font_pt or min_print_font,
    )
    page_width = page_size_pt[0] * PT_TO_MM
    page_height = page_size_pt[1] * PT_TO_MM
    violations: list[str] = []
    if (
        policy_min_print_font_pt is not None
        and min_print_font + FONT_TOLERANCE < policy_min_print_font_pt
    ):
        violations.append(
            f"declared min_print_font_pt {min_print_font:.2f} pt is below the built-in "
            f"journal floor {policy_min_print_font_pt:.2f} pt"
        )
    if abs(page_width - natural_width) > MM_TOLERANCE:
        violations.append(
            f"PDF width {page_width:.2f} mm differs from declared natural width "
            f"{natural_width:.2f} mm"
        )
    if abs(page_height - natural_height) > MM_TOLERANCE:
        violations.append(
            f"PDF height {page_height:.2f} mm differs from declared natural height "
            f"{natural_height:.2f} mm"
        )

    scale_width = target_width / natural_width
    scale_height = max_height / natural_height
    placement_scale = min(scale_width, scale_height)
    placement_width = natural_width * placement_scale
    placement_height = natural_height * placement_scale
    height_at_target_width = natural_height * scale_width
    width_at_max_height = natural_width * scale_height
    if height_at_target_width > max_height + MM_TOLERANCE:
        violations.append(
            f"target width {target_width:.2f} mm would produce {height_at_target_width:.2f} mm "
            f"height, above max_height {max_height:.2f} mm"
        )
    if not source_font_sizes_pt:
        violations.append("no explicit \\fontsize declarations found in TeX")
        source_min_font = None
        print_min_font = None
    else:
        source_min_font = min(source_font_sizes_pt)
        print_min_font = source_min_font * placement_scale
        if print_min_font + FONT_TOLERANCE < effective_min_print_font:
            floor_label = (
                "effective min_print_font_pt"
                if policy_min_print_font_pt is not None
                else "min_print_font_pt"
            )
            violations.append(
                f"smallest explicit font {source_min_font:.2f} pt becomes {print_min_font:.2f} pt "
                f"at print scale, below {floor_label} "
                f"{effective_min_print_font:.2f} pt"
            )

    return {
        "natural_size_mm": [natural_width, natural_height],
        "pdf_size_mm": [page_width, page_height],
        "target_width_mm": target_width,
        "max_height_mm": max_height,
        "width_at_max_height_mm": width_at_max_height,
        "height_at_target_width_mm": height_at_target_width,
        "placement_size_mm": [placement_width, placement_height],
        "placement_scale": placement_scale,
        "source_min_font_pt": source_min_font,
        "print_min_font_pt": print_min_font,
        "min_print_font_pt": min_print_font,
        "policy_min_print_font_pt": policy_min_print_font_pt,
        "effective_min_print_font_pt": effective_min_print_font,
        "violations": violations,
        "status": "passed" if not violations else "failed",
    }


def validate(
    *,
    pdf_path: Path,
    tex_path: Path,
    authority_path: Path | None,
    require_contract: bool,
) -> dict[str, Any]:
    if authority_path is None:
        if require_contract:
            raise PrintSizeContractError(
                "authority.yaml or spec.yaml with final_size_contract is required"
            )
        return {"status": "skipped", "reason": "authority.yaml/spec.yaml not found"}

    payload = yaml.safe_load(authority_path.read_text(encoding="utf-8")) or {}
    contract = payload.get("final_size_contract")
    if not isinstance(contract, dict):
        if require_contract:
            raise PrintSizeContractError("fixture contract lacks final_size_contract")
        return {"status": "skipped", "reason": "final_size_contract not declared"}
    if not pdf_path.is_file():
        raise PrintSizeContractError(f"PDF not found: {pdf_path}")
    result = evaluate_contract(
        page_size_pt=_page_size_pt(pdf_path),
        source_font_sizes_pt=_font_sizes_pt(tex_path.read_text(encoding="utf-8")),
        contract=contract,
        policy_min_print_font_pt=_journal_policy_floor(contract),
    )
    result["authority"] = str(authority_path)
    result["pdf"] = str(pdf_path)
    result["tex"] = str(tex_path)
    if result["violations"]:
        raise PrintSizeContractError("; ".join(result["violations"]))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--tex", required=True, type=Path)
    parser.add_argument("--authority", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--require-contract", action="store_true")
    args = parser.parse_args(argv)
    authority = args.authority or find_contract_file(args.tex.resolve())
    try:
        result = validate(
            pdf_path=args.pdf,
            tex_path=args.tex,
            authority_path=authority,
            require_contract=args.require_contract,
        )
    except PrintSizeContractError as exc:
        print(f"FAIL print_size_contract: {exc}", file=sys.stderr)
        return 1
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if result["status"] == "skipped":
        print(f"SKIP print_size_contract: {result['reason']}")
    else:
        print(
            "OK print_size_contract: "
            f"natural={result['natural_size_mm'][0]:.2f}x{result['natural_size_mm'][1]:.2f} mm, "
            f"placement={result['placement_size_mm'][0]:.2f}x"
            f"{result['placement_size_mm'][1]:.2f} mm, "
            f"min_print_font={result['print_min_font_pt']:.2f} pt"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
