from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig1_updated_agent_redraw_v1"

sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))

import phrase_binding  # noqa: E402
from check_visual_clash import extract_pdf_words_and_page  # noqa: E402

# Declarations that bound nothing until the matcher stopped depending on the
# rendered top-edge order: two of them are two-line nodes, one is a subscript
# run whose second word sorts first.
FORMERLY_DEAD = (
    ("text_boundary_checks", "panel-e-apparatus-labels", "panel_e_grounded_substrate"),
    ("text_boundary_checks", "panel-e-apparatus-labels", "panel_e_manual_sample_transfer"),
    ("label_path_proximity_checks", "panel-e-vs-meter-lead", "vs-meter"),
)


@pytest.fixture(scope="module")
def compiled_fig1() -> Path:
    completed = subprocess.run(
        [
            "bash",
            str(PLUGIN_ROOT / "scripts" / "compile.sh"),
            str(FIXTURE / "fig1_updated_agent_redraw_v1.tex"),
        ],
        cwd=PLUGIN_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return FIXTURE / "build"


@pytest.mark.render
def test_fig1_binds_every_declared_phrase(compiled_fig1: Path) -> None:
    for report_name, checked in (
        ("text_boundary_clash.json", 17),
        ("label_path_proximity.json", 4),
    ):
        payload = json.loads((compiled_fig1 / report_name).read_text(encoding="utf-8"))
        assert payload["phrase_binding"] == {
            "checked": checked,
            "state": "passed",
            "failures": [],
        }, report_name


@pytest.mark.render
def test_fig1_formerly_dead_declarations_now_bind(compiled_fig1: Path) -> None:
    words, _ = extract_pdf_words_and_page(compiled_fig1 / "fig1_updated_agent_redraw_v1.pdf")
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))

    for field, check_id, phrase_id in FORMERLY_DEAD:
        check = next(item for item in spec[field] if item["id"] == check_id)
        phrase = next(item for item in check["text_phrases"] if item["id"] == phrase_id)
        matches = phrase_binding.group_phrase_words(
            words,
            phrase,
            max_gap=6.0,
            max_center_delta=6.0,
        )
        assert len(matches) == 1, f"{check_id}/{phrase_id} bound {len(matches)} spans"


@pytest.mark.render
def test_fig1_no_longer_declares_the_off_page_panel_d_decay_path() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))

    assert "panel-d-transient-decay" not in {
        item["id"] for item in spec["label_path_proximity_checks"]
    }
