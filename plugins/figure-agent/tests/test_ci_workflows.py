from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pr_workflow_is_fast_and_skips_render_marked_tests() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "uv run pytest -q -m \"not render\"" in workflow
    assert "uv run ruff check ." in workflow
    assert "Install system dependencies" not in workflow
    assert "texlive-luatex" not in workflow
    assert "bash scripts/compile.sh" not in workflow


def test_full_render_workflow_owns_heavy_system_dependencies() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "full-render.yml").read_text(
        encoding="utf-8"
    )

    assert "workflow_dispatch:" in workflow
    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "labeled" in workflow
    assert "full-render" in workflow
    assert "branches:" in workflow
    assert "main" in workflow
    assert "Install system dependencies" in workflow
    assert "texlive-luatex" in workflow
    assert "texlive-fonts-extra" in workflow
    assert "bash scripts/compile.sh" in workflow
    assert "uv run pytest -q" in workflow


def test_full_render_workflow_has_timeout_guardrails() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "full-render.yml").read_text(
        encoding="utf-8"
    )

    assert "timeout-minutes: 45" in workflow
    assert "Install system dependencies\n        timeout-minutes: 30" in workflow


def test_render_pytest_marker_is_registered() -> None:
    pyproject = (PLUGIN_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "render: requires TeX/render/OCR system tools" in pyproject


def test_render_heavy_test_modules_are_marked() -> None:
    render_modules = [
        "test_band_diagram_api.py",
        "test_band_diagram_byte_classifier.py",
        "test_bell_curve_api.py",
        "test_compile_contract.py",
        "test_export_freshness.py",
        "test_export_pipeline_equivalence.py",
        "test_plot_callout_api.py",
    ]

    for filename in render_modules:
        source = (PLUGIN_ROOT / "tests" / filename).read_text(encoding="utf-8")
        assert "pytestmark = pytest.mark.render" in source, filename
