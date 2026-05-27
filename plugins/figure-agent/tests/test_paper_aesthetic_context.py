from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import paper_aesthetic_context  # noqa: E402


def _example_dir(tmp_path: Path, fixture: str = "fig1_demo") -> Path:
    example_dir = tmp_path / "examples" / fixture
    example_dir.mkdir(parents=True)
    return example_dir


def _write_pack(
    example_dir: Path,
    *,
    paper_id: str = "inverse-vulcanization-charge-trapping",
    fixture: str = "fig1_demo",
    extra: str = "",
) -> Path:
    pack_dir = example_dir.parent / "_paper_aesthetic_contexts"
    pack_dir.mkdir(parents=True, exist_ok=True)
    path = pack_dir / f"{paper_id}.yaml"
    path.write_text(
        f"""
schema: figure-agent.paper-aesthetic-context.v1
paper_id: {paper_id}
target_journal: Nature Communications
visual_maturity: editorial
density: balanced
shared_visual_language:
  - id: restrained_palette
    dimension: palette
    instruction: keep palette muted and consistent across figures
    priority: required
    positive_signals:
      - repeated restrained accent colors across main figures
    anti_patterns:
      - poster-like saturation in one figure
  - id: typography_authority
    dimension: typography
    instruction: preserve compact journal-style label hierarchy
    priority: required
    positive_signals:
      - consistent small label scale across panels
    anti_patterns:
      - oversized explanatory slide labels
figure_roles:
  - fixture: {fixture}
    role: overview_mechanism
    must_align_with:
      - restrained_palette
      - typography_authority
    allowed_variations:
      - may use one stronger hero panel than downstream data figures
must_avoid:
  - id: series_drift
    pattern: one figure looks like a different design system from the rest
    severity: MAJOR
{extra}
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_load_paper_aesthetic_context_accepts_valid_pack(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)

    pack = paper_aesthetic_context.load_paper_aesthetic_context(path)
    role = paper_aesthetic_context.matching_figure_role(pack, "fig1_demo")

    assert pack["schema"] == "figure-agent.paper-aesthetic-context.v1"
    assert pack["paper_id"] == "inverse-vulcanization-charge-trapping"
    assert pack["target_journal"] == "Nature Communications"
    assert role["role"] == "overview_mechanism"
    assert role["must_align_with"] == ["restrained_palette", "typography_authority"]


def test_load_paper_aesthetic_context_rejects_unsafe_paper_id(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "paper_id: inverse-vulcanization-charge-trapping",
            "paper_id: ../escape",
        ),
        encoding="utf-8",
    )

    with pytest.raises(paper_aesthetic_context.PaperAestheticContextError, match="safe id"):
        paper_aesthetic_context.load_paper_aesthetic_context(path)


def test_load_paper_aesthetic_context_rejects_hidden_file_style_id(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "paper_id: inverse-vulcanization-charge-trapping",
            "paper_id: .hidden-paper",
        ),
        encoding="utf-8",
    )

    with pytest.raises(paper_aesthetic_context.PaperAestheticContextError, match="safe id"):
        paper_aesthetic_context.load_paper_aesthetic_context(path)


def test_load_paper_aesthetic_context_rejects_filename_mismatch(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir, paper_id="paper-a")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "paper_id: paper-a",
            "paper_id: paper-b",
        ),
        encoding="utf-8",
    )

    with pytest.raises(paper_aesthetic_context.PaperAestheticContextError, match="filename"):
        paper_aesthetic_context.load_paper_aesthetic_context(path)


def test_load_paper_aesthetic_context_rejects_unknown_alignment_id(tmp_path: Path) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "- typography_authority",
            "- unknown_language",
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        paper_aesthetic_context.PaperAestheticContextError,
        match="unknown must_align_with",
    ):
        paper_aesthetic_context.load_paper_aesthetic_context(path)


def test_load_optional_paper_aesthetic_context_returns_none_without_opt_in(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    _write_pack(example_dir)

    assert (
        paper_aesthetic_context.load_optional_paper_aesthetic_context(
            example_dir,
            {"name": "fig1_demo"},
        )
        is None
    )


def test_load_optional_paper_aesthetic_context_rejects_missing_opted_pack(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)

    with pytest.raises(paper_aesthetic_context.PaperAestheticContextError, match="missing"):
        paper_aesthetic_context.load_optional_paper_aesthetic_context(
            example_dir,
            {
                "name": "fig1_demo",
                "paper_aesthetic_context": "inverse-vulcanization-charge-trapping",
            },
        )


def test_load_optional_paper_aesthetic_context_rejects_fixture_mismatch(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    _write_pack(example_dir, fixture="other_fixture")

    with pytest.raises(paper_aesthetic_context.PaperAestheticContextError, match="figure_roles"):
        paper_aesthetic_context.load_optional_paper_aesthetic_context(
            example_dir,
            {
                "name": "fig1_demo",
                "paper_aesthetic_context": "inverse-vulcanization-charge-trapping",
            },
        )


def test_paper_context_anchors_include_series_fields_and_role_constraints(
    tmp_path: Path,
) -> None:
    example_dir = _example_dir(tmp_path)
    path = _write_pack(example_dir)
    pack = paper_aesthetic_context.load_paper_aesthetic_context(path)

    anchors = paper_aesthetic_context.paper_context_anchors(pack, "fig1_demo")

    assert anchors == {
        "inverse-vulcanization-charge-trapping",
        "Nature Communications",
        "editorial",
        "balanced",
        "overview_mechanism",
        "restrained_palette",
        "typography_authority",
        "series_drift",
    }
