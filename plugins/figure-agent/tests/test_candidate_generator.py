from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402
import quality_defect_ledger  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _write_undeclared_candidate_defect(
    fixture: Path,
    source_line: int = 1,
    source_hashes: dict[str, str] | None = None,
) -> None:
    payload: dict[str, object] = {
        "candidates": [
            {
                "id": "UG001",
                "recommended_action": "add_micro_defect",
                "source_line": source_line,
                "panel": "A",
            }
        ]
    }
    payload["source_hashes"] = source_hashes or {
        f"examples/{fixture.name}/{fixture.name}.tex": file_sha256(fixture / f"{fixture.name}.tex")
    }
    build_dir = fixture / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "undeclared_geometry.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_undeclared_candidate_defects(
    fixture: Path,
    source_lines: list[int],
) -> None:
    payload = {
        "source_hashes": {
            f"examples/{fixture.name}/{fixture.name}.tex": file_sha256(
                fixture / f"{fixture.name}.tex"
            )
        },
        "candidates": [
            {
                "id": f"UG{index:03d}",
                "recommended_action": "add_micro_defect",
                "source_line": source_line,
                "panel": "A",
            }
            for index, source_line in enumerate(source_lines, start=1)
        ],
    }
    build_dir = fixture / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "undeclared_geometry.json").write_text(json.dumps(payload), encoding="utf-8")


def test_candidates_include_required_provenance_fields(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert payload["schema"] == "figure-agent.candidate-set.v1"
    assert payload["base"]["tex_hash"].startswith("sha256:")
    assert candidate["affected_files"] == ["examples/candidate_demo/candidate_demo.tex"]
    assert candidate["selector"]["original_hash"].startswith("sha256:")
    assert candidate["rollback"]["strategy"] == "reverse_operations"
    assert candidate["verification"]["required_commands"] == [
        "fig-agent compile candidate_demo --strict",
        "fig-agent status candidate_demo --json",
    ]
    assert candidate["apply_authority"] == "apply_eligible"
    source_defect = candidate["source_defect"]
    assert source_defect.pop("source_fingerprint").startswith("sha256:")
    assert source_defect.pop("ledger_hash").startswith("sha256:")
    assert source_defect == {
        "id": "QD001",
        "source": "deterministic_audit",
        "defect_class": "text_overlap",
        "evidence": [
            {
                "uri": "figure://candidate_demo/audit/undeclared-geometry",
                "node_id": "UG001",
            }
        ],
    }


def test_candidates_do_not_emit_blind_first_offsettable_fallback(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "no_supported_candidate"}]


def test_candidates_do_not_emit_for_missing_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples" / "candidate_demo").mkdir(parents=True)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"][0]["code"] == "source_missing"


def test_candidate_output_rejects_fixture_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
            output_path=workspace / "outside.json",
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "path_escape" in str(exc)
    else:
        raise AssertionError("expected output path escape to be rejected")


def test_candidate_output_accepts_fixture_relative_output_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
        output_path=Path("build/candidates/candidate_set.json"),
    )

    assert payload["candidates"][0]["id"] == "CAND001"


def test_candidate_generator_refuses_symlinked_source(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside.tex"
    outside.write_text("\\node (label-a) at (0,0) {External};\n", encoding="utf-8")
    (fixture / "candidate_demo.tex").unlink()
    (fixture / "candidate_demo.tex").symlink_to(outside)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "source_symlink_forbidden" in str(exc)
    else:
        raise AssertionError("expected source symlink to be rejected")


def test_candidate_generator_refuses_symlinked_fixture_dir(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    external_workspace = tmp_path / "external"
    external_fixture = _fixture(external_workspace)
    fixture_link = workspace / "examples" / "candidate_demo"
    fixture_link.parent.mkdir(parents=True)
    fixture_link.symlink_to(external_fixture)

    try:
        candidate_generator.build_candidate_set(
            "candidate_demo",
            workspace_root=workspace,
        )
    except candidate_generator.CandidateGeneratorError as exc:
        assert "fixture_symlink_forbidden" in str(exc)
    else:
        raise AssertionError("expected fixture directory symlink to be rejected")


def test_candidates_downgrade_apply_authority_from_intent_floor(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    _write_undeclared_candidate_defect(fixture)
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: missing.png
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"][0]["apply_authority"] == "review_only"


def test_candidate_targets_ledger_defect_line_not_first_offsettable(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    # First offsettable line is line 1 (the panel-letter node); the real defect is line 3.
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {a};\n"
        "\\node (title) {Origin of traps};\n"
        "\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    build_dir = fixture / "build"
    build_dir.mkdir()
    (build_dir / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    "examples/candidate_demo/candidate_demo.tex": file_sha256(
                        fixture / "candidate_demo.tex"
                    )
                },
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 3,
                        "panel": "A",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    ledger = quality_defect_ledger.build_quality_defect_ledger(
        "candidate_demo",
        workspace_root=workspace,
    )
    first_defect = ledger["defects"][0]
    assert first_defect["patchability"]["state"] == "safe_candidate"
    assert first_defect["selector_hint"]["kind"] == "line_range"
    assert first_defect["selector_hint"]["value"] == "3:3"
    assert first_defect["selector_hint"]["selector_text_hash"].startswith("sha256:")

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert candidate["id"] == "CAND001"
    assert candidate["selector"]["kind"] == "line_range_with_hash"
    assert candidate["selector"]["start_line"] == 3
    assert candidate["selector"]["end_line"] == 3


def test_candidate_generator_skips_line_weight_style_safe_defect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {
                    "id": "QD001",
                    "source": "critique_adjudication",
                    "defect_class": "line_weight_style",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "C001"}],
                    "selector_hint": {"kind": "line_range", "value": "1:1"},
                    "patchability": {"state": "safe_candidate"},
                }
            ]
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "unsupported_candidate_family", "defect_id": "QD001"}]


def test_candidate_generator_refuses_unknown_panel_safe_defect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {
                    "id": "QD001",
                    "source": "deterministic_audit",
                    "defect_class": "text_overlap",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "UG001"}],
                    "selector_hint": {
                        "kind": "line_range",
                        "value": "1:1",
                        "selector_text_hash": "sha256:" + "1" * 64,
                    },
                    "target": {"panel": "unknown", "subregion": "label-a"},
                    "patchability": {"state": "safe_candidate"},
                }
            ]
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert {item["code"] for item in payload["refusals"]} == {"unknown_panel"}


def test_candidate_generator_refuses_stale_detector_defect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {
                    "id": "QD001",
                    "source": "deterministic_audit",
                    "defect_class": "text_overlap",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "UG001"}],
                    "freshness": {"state": "stale"},
                    "selector_hint": {
                        "kind": "line_range",
                        "value": "1:1",
                        "selector_text_hash": "sha256:" + "1" * 64,
                    },
                    "target": {"panel": "A", "subregion": "label-a"},
                    "patchability": {"state": "safe_candidate"},
                }
            ]
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert {item["code"] for item in payload["refusals"]} == {"stale_detector_evidence"}


def test_candidate_generator_refuses_real_stale_detector_source_hash(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source_rel = "examples/candidate_demo/candidate_demo.tex"
    _write_undeclared_candidate_defect(
        fixture,
        source_hashes={source_rel: "sha256:" + "9" * 64},
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert {item["code"] for item in payload["refusals"]} == {"stale_detector_evidence"}


def test_candidate_generator_skips_unsupported_defect_and_reaches_supported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {a};\n"
        "\\node (title) {Origin of traps};\n"
        "\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    source_hash = file_sha256(fixture / "candidate_demo.tex")

    def fake_ledger(_name, **_kwargs):
        return {
            "defects": [
                {
                    "id": "QD001",
                    "source": "deterministic_audit",
                    "defect_class": "text_overlap",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "UG001"}],
                    "selector_hint": {
                        "kind": "line_range",
                        "value": "1:1",
                        "selector_text_hash": "sha256:" + "1" * 64,
                    },
                    "target": {"panel": "unknown", "subregion": "label-a"},
                    "patchability": {"state": "safe_candidate"},
                },
                {
                    "id": "QD002",
                    "source": "deterministic_audit",
                    "defect_class": "text_overlap",
                    "source_fingerprint": "sha256:" + "b" * 64,
                    "evidence": [{"node_id": "UG002"}],
                    "freshness": {
                        "source_hashes": {"examples/candidate_demo/candidate_demo.tex": source_hash}
                    },
                    "selector_hint": {
                        "kind": "line_range",
                        "value": "3:3",
                        "selector_text_hash": "sha256:" + "3" * 64,
                    },
                    "target": {"panel": "A", "subregion": "label-a"},
                    "patchability": {"state": "safe_candidate"},
                },
            ]
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate = payload["candidates"][0]
    assert candidate["selector"]["start_line"] == 3
    assert candidate["target"] == {"panel": "A", "subregion": "label-a"}
    assert candidate["source_defect"]["id"] == "QD002"
    assert {item["code"] for item in payload["refusals"]} == {"unknown_panel"}


def test_multi_candidate_generation_enumerates_supported_defects_with_metrics(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {A};\n"
        "\\node (title) {Origin of traps};\n"
        "\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    _write_undeclared_candidate_defects(fixture, [3, 1])

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidates = payload["candidates"]
    assert [candidate["id"] for candidate in candidates] == ["CAND001", "CAND002"]
    assert [candidate["selector"]["start_line"] for candidate in candidates] == [1, 3]
    subregions = [candidate["target"]["subregion"] for candidate in candidates]
    assert subregions[0] != subregions[1], subregions
    for candidate in candidates:
        assert candidate["target"]["panel"] == "A"
        assert candidate["target"]["subregion"] != "label-a"
        assert candidate["edit_family"] == "bounded_coordinate_offset"
        assert candidate["family"] == "bounded-coordinate-offset"
        assert candidate["variant"] == {"id": "dx+0.10cm", "dx_cm": 0.1}
        assert candidate["variant_id"] == "dx+0.10cm"
        assert candidate["operations"][0]["semantic_kind"] == "bounded_coordinate_offset"
        assert candidate["source_hash"].startswith("sha256:")
        assert candidate["selector"]["source_hash"] == candidate["source_hash"]
        assert candidate["source_defect"]["ledger_hash"].startswith("sha256:")
        assert candidate["candidate_hash"].startswith("sha256:")
    assert payload["metrics"] == {
        "safe_candidate_defect_count": 2,
        "candidate_count": 2,
        "candidate_defect_coverage": 1.0,
        "refusal_count": 0,
        "candidate_with_panel_count": 2,
        "candidate_with_family_count": 2,
        "candidate_with_source_hash_count": 2,
        "variant_count": 1,
    }


def test_candidate_offset_is_geometry_aware_for_horizontal_near_miss(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # A horizontal near-miss line must be cleared by moving it on tikz-y (whole
    # line), not by the blind first-coordinate +x nudge that leaves the gap intact.
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "\\draw[dashed] (0.45,6.15) -- (4.78,6.15);\n",
        encoding="utf-8",
    )
    source_hash = file_sha256(fixture / "candidate_demo.tex")
    build_dir = fixture / "build"
    build_dir.mkdir()
    (build_dir / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {"examples/candidate_demo/candidate_demo.tex": source_hash},
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "A",
                        "kind": "label_endpoint_near_miss",
                        "nearest_text": "shallow",
                        "bbox_pt": [12.76, 174.33, 135.50, 174.33],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (build_dir / "candidate_demo.pdf").write_bytes(b"%PDF-1.4 fake")

    def fake_extract(_pdf_path):
        words = [
            {"text": "shallow", "xmin": 21.5, "ymin": 165.5, "xmax": 45.6, "ymax": 172.1},
        ]
        return words, (512.0, 289.0)

    monkeypatch.setattr(
        candidate_generator,
        "extract_pdf_words_and_page",
        fake_extract,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    op = payload["candidates"][0]["operations"][0]
    # whole line moved on y to a smaller tikz-y (away from text), x unchanged.
    assert op["replacement"] == "\\draw[dashed] (0.45, 6.05) -- (4.78, 6.05);"


def test_candidate_ids_are_stable_for_identical_source_and_ledger_hashes(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "\\node (label-a) at (0,0) {A};\n\\draw (1.0,2.0) -- (3.0,2.0) node[right] {S};\n",
        encoding="utf-8",
    )
    _write_undeclared_candidate_defects(fixture, [2, 1])

    first = candidate_generator.build_candidate_set("candidate_demo", workspace_root=workspace)
    second = candidate_generator.build_candidate_set("candidate_demo", workspace_root=workspace)

    first_identity = [
        (candidate["id"], candidate["candidate_hash"], candidate["selector"]["start_line"])
        for candidate in first["candidates"]
    ]
    second_identity = [
        (candidate["id"], candidate["candidate_hash"], candidate["selector"]["start_line"])
        for candidate in second["candidates"]
    ]
    assert first_identity == second_identity


def test_candidate_generator_refuses_source_hash_mismatch_when_ledger_claims_supported(
    tmp_path: Path,
    monkeypatch,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    def fake_ledger(_name, **_kwargs):
        return {
            "ledger_hash": "sha256:" + "1" * 64,
            "actionability_metrics": {
                "safe_candidate_defect_count": 1,
                "candidate_supported_defect_count": 1,
                "unsupported_safe_defect_count": 0,
            },
            "defects": [
                {
                    "id": "QD001",
                    "source": "deterministic_audit",
                    "defect_class": "text_overlap",
                    "source_fingerprint": "sha256:" + "a" * 64,
                    "evidence": [{"node_id": "UG001"}],
                    "freshness": {
                        "source_hashes": {
                            "examples/candidate_demo/candidate_demo.tex": "sha256:" + "9" * 64
                        }
                    },
                    "selector_hint": {
                        "kind": "line_range",
                        "value": "1:1",
                        "selector_text_hash": "sha256:" + "1" * 64,
                    },
                    "target": {"panel": "A", "subregion": "label-a"},
                    "actionability": {"state": "candidate_supported", "gaps": []},
                    "patchability": {"state": "safe_candidate"},
                }
            ],
        }

    monkeypatch.setattr(
        candidate_generator.quality_defect_ledger,
        "build_quality_defect_ledger",
        fake_ledger,
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert payload["candidates"] == []
    assert payload["refusals"] == [{"code": "stale_detector_evidence", "defect_id": "QD001"}]
    assert payload["metrics"]["candidate_count"] == 0
    assert payload["metrics"]["refusal_count"] == 1


def _write_apply_finding(
    fixture: Path,
    finding_line: int,
    proposed_offset: dict | None = None,
    target_texts: list | None = None,
    proposed_edit: dict | None = None,
) -> None:
    name = fixture.name
    offset_block = ""
    if proposed_offset is not None:
        offset_block = (
            "    proposed_offset:\n"
            f"      axis: {proposed_offset['axis']}\n"
            f"      dx_cm: {proposed_offset['dx_cm']}\n"
        )
    edit_block = ""
    if proposed_edit is not None:
        edit_block = (
            "    proposed_edit:\n"
            f"      edit_class: {proposed_edit['edit_class']}\n"
            f"      text_width_cm: {proposed_edit['text_width_cm']}\n"
            "      reposition:\n"
            f"        axis: {proposed_edit['reposition']['axis']}\n"
            f"        dx_cm: {proposed_edit['reposition']['dx_cm']}\n"
        )
    texts_block = ""
    if target_texts is not None:
        rows = "".join(f"      - {text!r}\n" for text in target_texts)
        texts_block = "    target_texts:\n" + rows
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1.17\n"
        f"fixture: {name}\n"
        "verdict: revise\n"
        "findings:\n"
        "  - id: C001\n"
        "    severity: MINOR\n"
        "    category: label_placement\n"
        f"    tex_lines: [{finding_line}, {finding_line}]\n"
        "    status: open\n" + offset_block + edit_block + texts_block + "---\n\n# critique\n",
        encoding="utf-8",
    )
    (fixture / "critique_adjudication.yaml").write_text(
        "schema: figure-agent.critique-adjudication.v1\n"
        f"fixture: {name}\n"
        "source_critique_hash: sha256:" + "0" * 64 + "\n"
        "decisions:\n"
        "  - finding_id: C001\n"
        "    decision: apply\n"
        "    reason: lower the caption below the axis\n"
        f"    patch_target: examples/{name}/{name}.tex lines {finding_line}-{finding_line}\n"
        "    evidence: critique.md finding C001.\n",
        encoding="utf-8",
    )


def test_adjudicated_apply_finding_drives_candidate_at_finding_line(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% header line\n\\node[labelMute] at (7.60,4.12) {PI, PDMS, PET};\n",
        encoding="utf-8",
    )
    # No detector evidence: the only actionable signal is the adjudicated finding.
    _write_apply_finding(fixture, finding_line=2)

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    start_lines = {candidate["selector"]["start_line"] for candidate in payload["candidates"]}
    assert 2 in start_lines, payload


def test_adjudicated_finding_with_proposed_offset_emits_reposition(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% header line\n\\node[labelMute, anchor=north] at (7.60,4.12) {PI, PDMS, PET};\n",
        encoding="utf-8",
    )
    # The eye diagnosed the exact fix: drop the caption 0.5cm below the axis.
    _write_apply_finding(fixture, finding_line=2, proposed_offset={"axis": "y", "dx_cm": -0.5})

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    reposition = [c for c in payload["candidates"] if c.get("edit_class") == "label_reposition"]
    assert reposition, payload
    operation = reposition[0]["operations"][0]
    # Moves the y coordinate the full diagnosed distance, past the 0.10cm nudge cap.
    assert "(7.60, 3.62)" in operation["replacement"]


def test_adjudicated_finding_with_proposed_edit_emits_label_refit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% header line\n"
        "\\node[labelMute, anchor=north, text width=2.6cm, align=center] at (7.60,4.12)"
        " {PI, PDMS, PET (shallow, leaky)};\n",
        encoding="utf-8",
    )
    # The eye diagnosed a combined refit a single offset cannot author: widen the
    # caption to one line AND drop it below the axis into the 0.75cm gap.
    _write_apply_finding(
        fixture,
        finding_line=2,
        proposed_edit={
            "edit_class": "label_refit",
            "text_width_cm": 5.6,
            "reposition": {"axis": "y", "dx_cm": -0.28},
        },
    )

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    refit = [c for c in payload["candidates"] if c.get("edit_class") == "label_refit"]
    assert refit, payload
    replacement = refit[0]["operations"][0]["replacement"]
    # Both attributes rewritten, text untouched (value-preserving).
    assert "text width=5.60cm" in replacement
    assert "(7.60, 3.84)" in replacement
    assert "{PI, PDMS, PET (shallow, leaky)}" in replacement


def test_adjudicated_finding_carries_target_texts_for_verifier(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% header line\n\\node[labelMute, anchor=north] at (7.60,4.12) {PI, PDMS, PET};\n",
        encoding="utf-8",
    )
    # The finding names the crossing texts so the post-apply (visual_clash)
    # verifier can confirm they no longer cross — the ledger is blind to them.
    _write_apply_finding(fixture, finding_line=2, target_texts=["PI,", "PDMS,", "PET"])

    payload = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    anchored = [
        c
        for c in payload["candidates"]
        if c.get("source_defect", {}).get("source") == "adjudicated_finding"
    ]
    assert anchored, payload
    assert anchored[0]["source_defect"]["target_texts"] == ["PI,", "PDMS,", "PET"]
