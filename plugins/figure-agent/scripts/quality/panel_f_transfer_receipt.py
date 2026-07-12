#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "styles/snippets/panel-f-floating-cantilever.transfer.yaml"
SNIPPET = ROOT / "styles/snippets/panel-f-floating-cantilever.tex"
CONTRACT = ROOT / "styles/snippets/panel-f-floating-cantilever.contract.yaml"
FIXTURES = (
    ROOT
    / "examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex",
    ROOT
    / "examples/fig1_overview_v5f_art_direction_001_vault"
    / "fig1_overview_v5f_art_direction_001_vault.tex",
)
CROP_GEOMETRY = "1000x1100+3150+1650"
REPRODUCE = "uv run python scripts/quality/panel_f_transfer_receipt.py refresh"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _pixel_sha256(path: Path) -> str:
    pixels = subprocess.run(
        ["magick", str(path), "rgba:-"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return "sha256:" + hashlib.sha256(pixels).hexdigest()


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _render_path(fixture: Path) -> Path:
    return fixture.parent / "build" / f"{fixture.stem}.png"


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _comparison() -> dict[str, object]:
    renders = tuple(_render_path(fixture) for fixture in FIXTURES)
    for render in renders:
        if not render.is_file() or not render.read_bytes():
            raise RuntimeError(f"render artifact missing or empty: {_relative(render)}")

    with tempfile.TemporaryDirectory(prefix="panel-f-transfer-") as temp_dir:
        temp = Path(temp_dir)
        crops = (temp / "pilot.png", temp / "v5f.png")
        diff = temp / "diff.png"
        for render, crop in zip(renders, crops, strict=True):
            _run(
                [
                    "magick",
                    str(render),
                    "-crop",
                    CROP_GEOMETRY,
                    "+repage",
                    "-strip",
                    str(crop),
                ]
            )
        compared = subprocess.run(
            ["compare", "-metric", "AE", str(crops[0]), str(crops[1]), str(diff)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        metric = compared.stderr.strip()
        match = re.fullmatch(r"(\d+) \(([0-9.]+)\)", metric)
        if match is None or compared.returncode not in {0, 1}:
            raise RuntimeError(f"unexpected compare result: {metric}")
        _run(["magick", str(diff), "-strip", str(diff)])
        pixels, fraction = match.groups()
        return {
            "status": "passed_with_fixture_local_differences",
            "scope": "same_family_reuse_only",
            "geometry": CROP_GEOMETRY,
            "absolute_error_pixels": int(pixels),
            "absolute_error_fraction": float(fraction),
            "render_bindings": {_relative(path): _sha256(path) for path in renders},
            "crop_bindings": {
                "pilot": _pixel_sha256(crops[0]),
                "v5f": _pixel_sha256(crops[1]),
            },
            "diff_sha256": _pixel_sha256(diff),
            "reproduce": REPRODUCE,
        }


def _payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "motif": "panel-f-floating-cantilever",
        "shared_bindings": {
            _relative(path): _sha256(path) for path in (SNIPPET, CONTRACT)
        },
        "source_bindings": {_relative(path): _sha256(path) for path in FIXTURES},
        "compile_results": {_relative(path): "passed" for path in FIXTURES},
        "crop_comparison": _comparison(),
        "strict_review_evidence": "generated_not_passed",
        "publication_acceptance": "not_claimed",
    }


def refresh() -> None:
    for fixture in FIXTURES:
        _run(["bash", "scripts/compile.sh", _relative(fixture)])
    RECEIPT.write_text(yaml.safe_dump(_payload(), sort_keys=False), encoding="utf-8")


def verify() -> None:
    recorded = yaml.safe_load(RECEIPT.read_text(encoding="utf-8"))
    current = _payload()
    if recorded != current:
        raise RuntimeError("panel F transfer receipt is stale or fabricated")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"refresh", "verify"}:
        print("usage: panel_f_transfer_receipt.py {refresh|verify}", file=sys.stderr)
        return 2
    try:
        refresh() if sys.argv[1] == "refresh" else verify()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
