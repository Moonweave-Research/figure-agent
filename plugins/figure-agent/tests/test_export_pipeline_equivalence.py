"""Layer B: cross-pipeline equivalence smoke for fixtures opting in.

A fixture opts in by adding `export_pipeline_equivalence: { ae_max: <float> }`
to its spec.yaml. This test asserts that the AE (absolute error pixel count
under fuzz_pct% color tolerance) divided by total pixel count does not exceed
ae_max. Fixtures without the section are skipped — equivalence is forward-
looking insurance, not the operational fix.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fixtures_with_equivalence_contract() -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for spec_path in (REPO_ROOT / "examples").glob("*/spec.yaml"):
        try:
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if isinstance(spec, dict) and isinstance(spec.get("export_pipeline_equivalence"), dict):
            out.append((spec_path.parent, spec))
    return out


@pytest.mark.skipif(
    shutil.which("magick") is None
    or shutil.which("lualatex") is None
    or shutil.which("dvisvgm") is None
    or shutil.which("rsvg-convert") is None,
    reason="requires magick, lualatex, dvisvgm, rsvg-convert",
)
@pytest.mark.parametrize(
    "fixture_dir,spec",
    _fixtures_with_equivalence_contract(),
    ids=lambda x: x.name if isinstance(x, Path) else "spec",
)
def test_layer_b_equivalence_smoke(fixture_dir: Path, spec: dict) -> None:
    """build/PNG and exports/PNG must agree within the declared AE threshold."""
    name = spec["name"]
    contract = spec["export_pipeline_equivalence"]
    ae_max = float(contract["ae_max"])
    fuzz_pct = int(contract.get("fuzz_pct", 5))

    # Prime build/ and exports/ via the canonical pipeline.
    subprocess.run(
        ["bash", "scripts/compile.sh", str(fixture_dir / f"{name}.tex")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "run", "python", "scripts/run_export.py", name, "--skip-critique"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )

    build_png = fixture_dir / "build" / f"{name}.png"
    exports_png = fixture_dir / "exports" / f"{name}.png"
    assert build_png.is_file(), build_png
    assert exports_png.is_file(), exports_png

    # magick compare exits 1 on any difference even within tolerance; capture metric instead.
    result = subprocess.run(
        [
            "magick",
            "compare",
            "-metric",
            "AE",
            "-fuzz",
            f"{fuzz_pct}%",
            str(build_png),
            str(exports_png),
            "null:",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # magick compare exits 0 (no diff) or 1 (diff present) on success; any other
    # exit code (2, 64, ...) means the tool itself failed (bad args, format
    # mismatch, etc.). Surface the raw stderr in that case so the failure is
    # diagnosable instead of decaying into a cryptic ValueError on int(raw).
    if result.returncode not in (0, 1):
        raise AssertionError(
            f"magick compare failed unexpectedly (exit {result.returncode}) "
            f"for {name}:\n{result.stderr}"
        )
    # AE is reported on stderr as an integer (or "<int> (<float>)" with -compose).
    raw = result.stderr.strip().split()[0] if result.stderr.strip() else ""
    try:
        ae = int(raw)
    except ValueError as exc:
        raise AssertionError(
            f"magick compare produced non-integer AE output for {name}: stderr={result.stderr!r}"
        ) from exc

    # Compare to total pixels.
    dim_result = subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(build_png)],
        capture_output=True,
        text=True,
        check=True,
    )
    width, height = (int(s) for s in dim_result.stdout.split())
    total = width * height
    fraction = ae / total

    assert fraction <= ae_max, (
        f"Layer B equivalence violated for {name}: "
        f"AE={ae} ({fraction:.4f}) exceeds ae_max={ae_max:.4f}. "
        f"build/PNG and exports/PNG diverge beyond declared tolerance."
    )
