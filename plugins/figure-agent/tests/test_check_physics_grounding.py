from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_physics_grounding as cpg  # noqa: E402

BRIEFING_WITH = "# Briefing\n\n## §6. Physics invariants\n- bend opposite\n\n## §7. Author intent\n"
BRIEFING_NO_SECTION_MARK = "# Briefing\n\n## 6. Physics invariants\n- foo\n"
BRIEFING_WITHOUT = "# Briefing\n\n## §1. Topic\nsome prose\n"


def test_has_physics_invariants_detects_the_section():
    assert cpg.has_physics_invariants(BRIEFING_WITH) is True


def test_has_physics_invariants_detects_without_section_mark():
    assert cpg.has_physics_invariants(BRIEFING_NO_SECTION_MARK) is True


def test_has_physics_invariants_false_when_absent():
    assert cpg.has_physics_invariants(BRIEFING_WITHOUT) is False
    assert cpg.has_physics_invariants("") is False


def test_has_tex_assertions_true_for_nonempty_list():
    assert cpg.has_tex_assertions({"tex_assertions": [{"id": "a"}]}) is True


def test_has_tex_assertions_false_for_empty_or_absent():
    assert cpg.has_tex_assertions({"tex_assertions": []}) is False
    assert cpg.has_tex_assertions({}) is False


def test_grounded_via_semantic_assertions_too():
    # A label-relational invariant (shallow above deep) is enforced by
    # semantic_assertions, not tex_assertions — that figure is still grounded.
    spec = {"semantic_assertions": [{"id": "shallow-above-deep"}]}
    assert cpg.classify_grounding(BRIEFING_WITH, spec) == "grounded"


def test_classify_grounded():
    assert cpg.classify_grounding(BRIEFING_WITH, {"tex_assertions": [{"id": "a"}]}) == "grounded"


def test_classify_declared_unenforced():
    assert cpg.classify_grounding(BRIEFING_WITH, {}) == "declared_unenforced"


def test_classify_undeclared():
    assert (
        cpg.classify_grounding(BRIEFING_WITHOUT, {"tex_assertions": [{"id": "a"}]}) == "undeclared"
    )


def _figure(tmp_path, briefing, spec_yaml):
    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "briefing.md").write_text(briefing, encoding="utf-8")
    (fixture / "spec.yaml").write_text(spec_yaml, encoding="utf-8")
    return fixture


def test_grounding_status_declared_unenforced(tmp_path):
    fixture = _figure(tmp_path, BRIEFING_WITH, "name: demo\n")
    assert cpg.grounding_status(fixture) == {"figure": "demo", "status": "declared_unenforced"}


def test_grounding_status_grounded(tmp_path):
    fixture = _figure(
        tmp_path,
        BRIEFING_WITH,
        "name: demo\ntex_assertions:\n  - id: a\n    anchor_style: forceArr\n"
        "    axis: x\n    direction: decreasing\n",
    )
    assert cpg.grounding_status(fixture)["status"] == "grounded"


def test_grounding_status_briefing_missing_is_non_benign(tmp_path):
    # A missing briefing must surface as a distinct gap, not collapse into the
    # benign "undeclared" bucket (fail-closed, Task 0.6e).
    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    assert cpg.grounding_status(fixture)["status"] == "briefing_missing"


def test_main_strict_fails_on_missing_briefing(tmp_path, monkeypatch):
    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_physics_grounding.py", str(fixture), "--strict"])
    assert cpg.main() == 1


def test_main_reports_but_does_not_fail_missing_briefing_without_strict(tmp_path, monkeypatch):
    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_physics_grounding.py", str(fixture)])
    assert cpg.main() == 0


def test_grounding_payload_shape():
    payload = cpg.grounding_payload("demo", "declared_unenforced")
    assert payload["schema"] == "figure-agent.physics-grounding.v1"
    assert payload["status"] == "declared_unenforced"
