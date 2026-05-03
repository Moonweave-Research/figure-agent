"""Tests for scripts/export_freshness.compute_export_state — sub-state logic.

Layer A end-to-end invariant test (`test_freshness_invariant_after_run_export`)
is part of this file; it complements the four sub-state branch tests by
asserting build/PDF == exports/PDF after run_export.py succeeds.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from export_freshness import (  # noqa: E402
    EXPORT_FRESH,
    EXPORT_MISSING,
    EXPORT_STALE,
    EXPORT_TRACKED_GOLDEN,
    compute_export_state,
)


def _scaffold_minimal_fixture(root: Path, name: str, body: str = "hello") -> Path:
    """Create a fixture dir with a minimal compiled PDF in build/."""
    fixture = root / "examples" / name
    (fixture / "build").mkdir(parents=True, exist_ok=True)
    (fixture / "exports").mkdir(parents=True, exist_ok=True)
    (fixture / f"{name}.tex").write_text(
        r"\documentclass[border=2pt]{standalone}"
        "\n"
        rf"\begin{{document}}{body}\end{{document}}"
        "\n",
        encoding="utf-8",
    )
    if shutil.which("lualatex") is None:
        pytest.skip("requires lualatex")
    subprocess.run(
        [
            "lualatex",
            "-output-directory",
            str(fixture / "build"),
            "-interaction=nonstopmode",
            str(fixture / (name + ".tex")),
        ],
        check=True,
        capture_output=True,
    )
    return fixture


def test_state_missing_when_no_exports_pdf(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_missing")
    assert compute_export_state(fixture, "fix_missing") == EXPORT_MISSING


def test_state_fresh_when_exports_pdf_matches_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_fresh")
    shutil.copy(fixture / "build" / "fix_fresh.pdf", fixture / "exports" / "fix_fresh.pdf")
    assert compute_export_state(fixture, "fix_fresh") == EXPORT_FRESH


def test_state_stale_when_exports_pdf_differs_from_build(tmp_path: Path) -> None:
    fixture = _scaffold_minimal_fixture(tmp_path, "fix_stale_a", body="hello")
    other = _scaffold_minimal_fixture(tmp_path, "fix_stale_b", body="goodbye world")
    shutil.copy(other / "build" / "fix_stale_b.pdf", fixture / "exports" / "fix_stale_a.pdf")
    assert compute_export_state(fixture, "fix_stale_a") == EXPORT_STALE


def test_state_tracked_golden_for_self_contained_git_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """compute_export_state must return TRACKED_GOLDEN for any git-tracked
    exports/<name>.pdf, regardless of build state. Uses a self-contained
    git repo so coverage does not depend on the real golden fixture being
    present on disk.
    """
    repo = tmp_path / "fake_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    fixture = repo / "examples" / "fake_fixture"
    (fixture / "exports").mkdir(parents=True)
    pdf = fixture / "exports" / "fake_fixture.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy\n")

    subprocess.run(
        ["git", "add", str(pdf.relative_to(repo))],
        cwd=repo,
        check=True,
    )

    # Redirect REPO_ROOT so is_tracked() checks our temp repo
    import export_freshness

    monkeypatch.setattr(export_freshness, "REPO_ROOT", repo)

    state = compute_export_state(fixture, "fake_fixture")
    assert state == EXPORT_TRACKED_GOLDEN


def test_freshness_invariant_after_run_export() -> None:
    """After run_export.py succeeds on a non-golden fixture, build/PDF and
    exports/PDF must hash-equal. Lock this as the Layer A always-on contract.
    """
    if (
        shutil.which("lualatex") is None
        or shutil.which("dvisvgm") is None
        or shutil.which("rsvg-convert") is None
        or shutil.which("pdftocairo") is None
    ):
        pytest.skip("requires lualatex, dvisvgm, rsvg-convert, pdftocairo")

    # Use a real fixture so all toolchain pieces are exercised.
    fixture_name = "_macro_smoke"
    fixture = REPO_ROOT / "examples" / fixture_name

    # Prime build/.
    subprocess.run(
        ["bash", "scripts/compile.sh", str(fixture / f"{fixture_name}.tex")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )

    # Force regeneration by removing the freshness key (the PDF). The bash scripts
    # beneath the orchestrator are what we want to exercise; an early-exit no-op
    # would make this test pass trivially after any prior run.
    exports_pdf_pre = fixture / "exports" / f"{fixture_name}.pdf"
    exports_pdf_pre.unlink(missing_ok=True)

    # Prime exports/ via the orchestrator.
    result = subprocess.run(
        ["uv", "run", "python", "scripts/run_export.py", fixture_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    # Layer A invariant.
    from export_freshness import compute_pdf_content_hash  # noqa: PLC0415

    build_pdf = fixture / "build" / f"{fixture_name}.pdf"
    exports_pdf = fixture / "exports" / f"{fixture_name}.pdf"
    assert compute_pdf_content_hash(build_pdf) == compute_pdf_content_hash(exports_pdf), (
        "Layer A invariant violated: exports/PDF content hash differs from build/PDF "
        "after run_export.py reported success."
    )


def test_run_export_skips_tracked_golden_without_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_export.py must not require build/PDF when exports/PDF is
    TRACKED_GOLDEN — the golden artifact is the source of truth and a
    fresh-clone user should never be forced to compile just to see it.
    """
    repo = tmp_path / "fake_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    fixture_name = "golden_in_tmp"
    fixture = repo / "examples" / fixture_name
    (fixture / "exports").mkdir(parents=True)
    pdf = fixture / "exports" / f"{fixture_name}.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy\n")
    subprocess.run(["git", "add", str(pdf.relative_to(repo))], cwd=repo, check=True)

    # Note: build/ does NOT exist. This is the fresh-checkout scenario.

    import export_freshness
    import run_export

    monkeypatch.setattr(run_export, "REPO_ROOT", repo)
    # compute_export_state uses export_freshness.REPO_ROOT when calling is_tracked;
    # patch it so the fake git repo is used for the tracked-golden check.
    monkeypatch.setattr(export_freshness, "REPO_ROOT", repo)
    monkeypatch.setattr("sys.argv", ["run_export.py", fixture_name])

    rc = run_export.main()

    assert rc == 0, (
        "TRACKED_GOLDEN without --force-golden must succeed (golden protection is the success path)"
    )
