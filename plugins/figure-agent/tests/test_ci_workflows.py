from __future__ import annotations

from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_pr_workflow_is_fast_and_skips_render_marked_tests() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert 'uv run pytest -q -m "not render and not quarantine"' in workflow
    assert "uv run pytest -q -m quarantine" in workflow
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
    assert "PYTHONPATH:" in workflow
    assert "plugins/figure-agent/scripts/checks" in workflow
    assert "scripts/checks/check_visual_clash_budget.py examples" in workflow
    assert "uv run pytest -q" in workflow


def test_full_render_workflow_has_timeout_guardrails() -> None:
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "full-render.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["full-render"]
    steps = {step.get("name"): step for step in job["steps"]}

    # Compiling all 31 fixtures takes about 7 minutes on the runner and the
    # full suite about 20; a job budget below that cancelled the run before
    # the render tests reported (run 33600403826). Pin the floor, not the
    # literal, so raising the budget does not fail this guard.
    assert job["timeout-minutes"] >= 45
    assert steps["Install system dependencies"]["timeout-minutes"] >= 10
    assert steps["Compile fixtures and check visual clash budgets"]["timeout-minutes"] >= 15


def test_workflows_use_node24_ready_action_versions() -> None:
    fast_workflow = (REPO_ROOT / ".github" / "workflows" / "test.yml").read_text(
        encoding="utf-8"
    )
    full_render_workflow = (REPO_ROOT / ".github" / "workflows" / "full-render.yml").read_text(
        encoding="utf-8"
    )

    for workflow in (fast_workflow, full_render_workflow):
        assert "actions/checkout@v4" not in workflow
        assert "astral-sh/setup-uv@v4" not in workflow
        assert "actions/checkout@v5" in workflow
        assert "astral-sh/setup-uv@v8.1.0" in workflow
    assert "cache-suffix: fast-tests" in fast_workflow
    assert "cache-suffix: full-render" in full_render_workflow


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
        "test_slice3_cohort_dogfood.py",
    ]

    for filename in render_modules:
        source = (PLUGIN_ROOT / "tests" / filename).read_text(encoding="utf-8")
        assert (
            "pytestmark = pytest.mark.render" in source or "@pytest.mark.render" in source
        ), filename
