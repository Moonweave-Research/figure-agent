from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_families  # noqa: E402
import candidate_generator  # noqa: E402


def _energy_fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: C
    caption: Energy diagram
    bbox_pdf_cm: [0.0, 0.0, 4.0, 3.0]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text(
        "% Panel C\n"
        "\\coordinate (siteS1) at (1.0, 2.0);\n"
        "\\coordinate (siteD1) at (1.0, 1.0);\n"
        "\\node[anchor=west] at (3.0, 2.4) {mobility edge};\n"
        "\\node[anchor=west] at (3.0, 2.0) {shallow};\n"
        "\\node[anchor=west] at (3.0, 1.0) {deep};\n",
        encoding="utf-8",
    )
    return fixture


def _energy_fixture_with_reference(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = _energy_fixture(workspace, name)
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_c.png").write_bytes(b"fake")
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: C
    caption: Energy diagram
    bbox_pdf_cm: [0.0, 0.0, 4.0, 3.0]
    reference_image: reference/panel_c.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return fixture


def test_energy_trap_family_emits_review_only_panel_candidate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _energy_fixture(workspace)

    payload = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert payload["schema"] == "figure-agent.candidate-set.v1"
    assert candidate["id"] == "CAND001"
    assert candidate["target"]["panel"] == "C"
    assert candidate["family"] == "energy-trap-alignment"
    assert candidate["candidate_hash"].startswith("sha256:")
    assert candidate["apply_authority"] == "review_only"
    assert candidate["selector"]["kind"] == "tex_selector.v1"
    assert candidate["operations"][0]["original"] in (
        "\\node[anchor=west] at (3.0, 2.4) {mobility edge};",
        "\\node[anchor=west] at (3.0, 2.0) {shallow};",
        "\\node[anchor=west] at (3.0, 1.0) {deep};",
    )
    assert candidate["operations"][0]["original"] != candidate["operations"][0]["replacement"]


def test_unknown_family_refuses_with_structured_code(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _energy_fixture(workspace)

    payload = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="unknown-family",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "unsupported_candidate_family"}]


def test_known_family_on_wrong_panel_refuses(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _energy_fixture(workspace)

    payload = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="D",
        family="energy-trap-alignment",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "unsupported_panel_family"}]


def test_plot_marker_hierarchy_on_panel_c_is_panel_family_refusal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _energy_fixture(workspace)

    payload = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="plot-marker-hierarchy",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "unsupported_panel_family"}]


def test_declared_panel_required_for_family_candidates(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _energy_fixture(workspace)
    (fixture / "spec.yaml").write_text("name: candidate_demo\npanels: []\n", encoding="utf-8")

    payload = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "panel_not_declared"}]


def test_candidate_hash_excludes_absolute_reference_paths(tmp_path: Path) -> None:
    workspace_a = tmp_path / "workspace_a"
    workspace_b = tmp_path / "nested" / "workspace_b"
    _energy_fixture_with_reference(workspace_a)
    _energy_fixture_with_reference(workspace_b)

    payload_a = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace_a,
    )
    payload_b = candidate_families.build_family_candidates(
        "candidate_demo",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace_b,
    )

    assert payload_a["candidates"][0]["panel"]["reference_image"] != (
        payload_b["candidates"][0]["panel"]["reference_image"]
    )
    assert payload_a["candidates"][0]["candidate_hash"] == (
        payload_b["candidates"][0]["candidate_hash"]
    )


def test_generator_delegates_panel_family_without_breaking_default(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _energy_fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace,
    )

    assert payload["candidates"][0]["family"] == "energy-trap-alignment"


def test_real_panel_c_energy_family_produces_candidate() -> None:
    workspace = Path("plugins/figure-agent").resolve()

    payload = candidate_generator.build_candidate_set(
        "fig1_overview_v2_pair_001_vault",
        panel="C",
        family="energy-trap-alignment",
        workspace_root=workspace,
        plugin_root=workspace,
    )

    assert payload["candidates"]
    assert payload["candidates"][0]["target"]["panel"] == "C"
