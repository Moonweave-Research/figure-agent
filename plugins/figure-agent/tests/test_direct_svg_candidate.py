from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import yaml
from direct_svg_candidate import (
    DirectSvgCandidateError,
    begin_ledger,
    record_iteration,
    render_candidate,
    semantic_requirements,
    validate_candidate,
    validate_candidate_from_semantic_packet,
)
from PIL import Image


def _write_svg(
    root: Path,
    *,
    semantic_ids: set[str] | None = None,
    live_text: bool = True,
    view_box: bool = True,
    extra_element: str | None = None,
    extra_body: str = "",
) -> Path:
    ids = semantic_ids or set()
    body = "".join(f'<g id="{item}" data-semantic="true"/>' for item in sorted(ids))
    if live_text:
        body += '<text x="4" y="16">editable label</text>'
    if extra_element:
        body += f"<{extra_element}/>"
    body += extra_body
    view_box_attr = ' viewBox="0 0 120 80"' if view_box else ""
    path = root / "candidate.svg"
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg"{view_box_attr}>{body}</svg>',
        encoding="utf-8",
    )
    return path


def _utility_budget() -> dict[str, int]:
    return {"cycles": 3, "wall_minutes_per_panel": 30}


def _iteration_receipt(cycle: int, *, elapsed_minutes: float = 5.0) -> dict[str, object]:
    source_hash = "sha256:" + str(cycle) * 64
    render_hash = "sha256:" + str(cycle + 1) * 64
    source_path = f"runs/panel-c-cycle-{cycle}.svg"
    render_path = f"runs/panel-c-cycle-{cycle}.png"
    return {
        "cycle": cycle,
        "elapsed_minutes": elapsed_minutes,
        "source_path": source_path,
        "source_sha256": source_hash,
        "render_path": render_path,
        "render_sha256": render_hash,
        "command": [
            "uv",
            "run",
            "python",
            "scripts/direct_svg_render.py",
            "--root",
            ".",
            "--svg",
            source_path,
            "--output",
            render_path,
            "--semantic-packet",
            "contract/semantic-packet.yaml",
            "--panel",
            "C",
            "--width",
            "120",
            "--height",
            "80",
            "--fontconfig",
            "contract/fontconfig.xml",
            "--font",
            "contract/font.otf",
        ],
        "runtime_receipt": {
            "schema": "figure-agent.direct-svg-runtime-receipt.v1",
            "path_base": "plugin_root",
            "validation_mode": "declared_relation_coverage",
            "source_path": source_path,
            "source_sha256": source_hash,
            "render_path": render_path,
            "render_sha256": render_hash,
            "semantic_packet": {
                "path": "contract/semantic-packet.yaml",
                "sha256": "sha256:" + "a" * 64,
            },
            "fontconfig": {"path": "contract/fontconfig.xml", "sha256": "sha256:" + "b" * 64},
            "font": {"path": "contract/font.otf", "sha256": "sha256:" + "c" * 64},
            "rsvg": {"executable": "rsvg-convert", "version": "rsvg-convert 1"},
            "python": {"implementation": "CPython", "version": "3.12.0"},
            "pillow": {"version": "12.0.0"},
            "environment": {
                "FONTCONFIG_FILE": "contract/fontconfig.xml",
                "FONTCONFIG_PATH": "contract",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            },
            "producer": {
                "wrapper_path": "scripts/direct_svg_render.py",
                "wrapper_sha256": "sha256:" + "d" * 64,
                "validator_path": "scripts/direct_svg_candidate.py",
                "validator_sha256": "sha256:" + "e" * 64,
                "lock_path": "uv.lock",
                "lock_sha256": "sha256:" + "f" * 64,
                "base_commit": "0" * 40,
                "head_commit": None,
                "head_commit_status": "unavailable_precommit",
            },
            "width": 120,
            "height": 80,
            "publication_acceptance": "not_claimed",
        },
        "tool_model_receipt": {
            "provider": "openai",
            "model": "gpt-test",
            "model_identity_independently_verified": False,
            "snapshot": None,
            "reasoning": None,
            "token_cap": None,
            "compute_cap": None,
            "task": {
                "name": "test",
                "mode": "direct_svg",
                "branch": "test",
                "base_commit": "0" * 40,
            },
            "tools": {
                "authoring": "apply_patch",
                "validation_and_render": "direct_svg_render.py",
                "visual_inspection": "view_image",
                "image_generation": "not_used",
            },
        },
        "correction_reason": "initial" if cycle == 1 else "visual correction",
        "correction_type": "initial" if cycle == 1 else "visual",
        "render_changed_from_prior": cycle > 1,
        "publication_acceptance": "not_claimed",
    }


def test_candidate_requires_live_text_viewbox_and_semantic_ids(tmp_path: Path) -> None:
    svg = _write_svg(
        tmp_path,
        semantic_ids={"panel_c.real_space"},
        live_text=False,
    )

    with pytest.raises(DirectSvgCandidateError, match="live_text_required"):
        validate_candidate(
            svg,
            required_ids={"panel_c.real_space", "panel_c.energy"},
        )


def test_candidate_requires_explicit_viewbox(tmp_path: Path) -> None:
    svg = _write_svg(tmp_path, view_box=False)

    with pytest.raises(DirectSvgCandidateError, match="view_box_required"):
        validate_candidate(svg, required_ids=set())


def test_candidate_requires_every_semantic_group_id(tmp_path: Path) -> None:
    svg = _write_svg(tmp_path, semantic_ids={"panel_c.real_space"})

    with pytest.raises(DirectSvgCandidateError, match="semantic_id_missing"):
        validate_candidate(
            svg,
            required_ids={"panel_c.real_space", "panel_c.energy"},
        )


def test_candidate_requirements_are_derived_from_semantic_packet(tmp_path: Path) -> None:
    packet = tmp_path / "semantic-packet.yaml"
    packet.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.direct-svg-semantic-packet.v1",
                "panels": ["C", "F"],
                "scientific_objects": {
                    "panel_c": [{"id": "c_object"}],
                    "panel_f": [{"id": "f_object"}],
                },
                "visual_roles": {
                    "panel_c": {
                        "c_object": "object",
                        "c_relation": "declared relation cue",
                    },
                    "panel_f": {"f_object": "object"},
                },
                "text_content": {
                    "panel_c": ["C", "E_C", "ΔE_t^d"],
                    "panel_f": ["F"],
                },
                "object_relations": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    requirements = semantic_requirements(packet, panel="C")

    assert requirements == {
        "required_ids": {"c_object", "c_relation"},
        "required_text": {"C", "E_C", "ΔE_t^d"},
        "relations": set(),
    }


def test_candidate_validates_live_notation_and_explicit_relations(
    tmp_path: Path,
) -> None:
    packet = tmp_path / "semantic-packet.yaml"
    packet.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.direct-svg-semantic-packet.v1",
                "panels": ["C", "F"],
                "scientific_objects": {
                    "panel_c": [{"id": "c_source"}, {"id": "c_target"}],
                    "panel_f": [],
                },
                "visual_roles": {
                    "panel_c": {"c_source": "source", "c_target": "target"},
                    "panel_f": {},
                },
                "text_content": {"panel_c": ["E_C", "ΔE_t^d"], "panel_f": []},
                "object_relations": [
                    {
                        "subject": "c_source",
                        "predicate": "acts_on",
                        "object": "c_target",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    svg = tmp_path / "candidate.svg"
    svg.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">
        <g id="c_source"><text x="4" y="16">E<tspan baseline-shift="sub">C</tspan></text></g>
        <g id="c_target"><text x="4" y="36">ΔE
        <tspan baseline-shift="sub">t</tspan>
        <tspan baseline-shift="super">d</tspan></text></g>
        <path data-subject="c_source" data-predicate="acts_on" data-object="c_target" d="M0 0L1 1"/>
        </svg>""",
        encoding="utf-8",
    )

    result = validate_candidate_from_semantic_packet(svg, packet, panel="C")
    assert result["validated_relations"] == [
        ["c_source", "acts_on", "c_target"],
    ]

    svg.write_text(
        svg.read_text(encoding="utf-8").replace(
            'data-predicate="acts_on"',
            'data-predicate="contains"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(DirectSvgCandidateError, match="semantic_relation_undeclared"):
        validate_candidate_from_semantic_packet(svg, packet, panel="C")


def test_semantic_relations_are_scoped_by_subject_panel_membership(tmp_path: Path) -> None:
    packet = tmp_path / "semantic-packet.yaml"
    packet.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.direct-svg-semantic-packet.v1",
                "panels": ["C", "F"],
                "scientific_objects": {
                    "panel_c": [{"id": "c_a"}, {"id": "c_b"}],
                    "panel_f": [{"id": "f_a"}],
                },
                "visual_roles": {"panel_c": {"c_a": "a", "c_b": "b"}, "panel_f": {"f_a": "a"}},
                "text_content": {"panel_c": ["C"], "panel_f": ["F"]},
                "object_relations": [
                    {"subject": "c_a", "predicate": "acts_on", "object": "c_b"},
                    {"subject": "f_a", "predicate": "manifests", "object": "c_b"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    assert semantic_requirements(packet, panel="C")["relations"] == {("c_a", "acts_on", "c_b")}
    assert semantic_requirements(packet, panel="F")["relations"] == {("f_a", "manifests", "c_b")}


@pytest.mark.parametrize("remove_all", [False, True])
def test_candidate_requires_complete_declared_relation_coverage(
    tmp_path: Path, remove_all: bool
) -> None:
    packet = tmp_path / "semantic-packet.yaml"
    packet.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.direct-svg-semantic-packet.v1",
                "panels": ["C", "F"],
                "scientific_objects": {"panel_c": [{"id": "c_a"}, {"id": "c_b"}], "panel_f": []},
                "visual_roles": {"panel_c": {"c_a": "a", "c_b": "b"}, "panel_f": {}},
                "text_content": {"panel_c": ["C"], "panel_f": []},
                "object_relations": [
                    {"subject": "c_a", "predicate": "acts_on", "object": "c_b"},
                    {"subject": "c_b", "predicate": "coexists_with", "object": "c_a"},
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    relations = (
        "" if remove_all else '<g data-subject="c_a" data-predicate="acts_on" data-object="c_b"/>'
    )
    svg = _write_svg(
        tmp_path, semantic_ids={"c_a", "c_b"}, extra_body=f'<text x="1" y="2">C</text>{relations}'
    )

    with pytest.raises(DirectSvgCandidateError, match="semantic_relation_missing"):
        validate_candidate_from_semantic_packet(svg, packet, panel="C")


@pytest.mark.parametrize("forbidden", ["script", "image", "foreignObject"])
def test_candidate_rejects_unsafe_elements(tmp_path: Path, forbidden: str) -> None:
    svg = _write_svg(tmp_path, extra_element=forbidden)

    with pytest.raises(DirectSvgCandidateError, match="forbidden_svg_element"):
        validate_candidate(svg, required_ids=set())


def test_candidate_allows_only_fragment_local_gradient_urls(tmp_path: Path) -> None:
    local = _write_svg(
        tmp_path,
        extra_body=(
            '<defs><linearGradient id="local-gradient"/></defs>'
            '<rect width="20" height="20" fill="url(#local-gradient)"/>'
        ),
    )
    assert validate_candidate(local, required_ids=set())

    external = _write_svg(
        tmp_path,
        extra_body='<rect width="20" height="20" fill="url(https://example.com/a.svg)"/>',
    )
    with pytest.raises(DirectSvgCandidateError, match="external_url_forbidden"):
        validate_candidate(external, required_ids=set())


def test_iteration_ledger_enforces_cycle_budget() -> None:
    ledger = begin_ledger(_utility_budget(), started_at="2026-07-11T00:00:00Z")
    for cycle in range(1, 4):
        ledger = record_iteration(ledger, _iteration_receipt(cycle))

    with pytest.raises(DirectSvgCandidateError, match="cycle_budget_exceeded"):
        record_iteration(ledger, _iteration_receipt(4))


def test_iteration_ledger_enforces_wall_time_budget() -> None:
    ledger = begin_ledger(_utility_budget(), started_at="2026-07-11T00:00:00Z")

    with pytest.raises(DirectSvgCandidateError, match="wall_time_budget_exceeded"):
        record_iteration(ledger, _iteration_receipt(1, elapsed_minutes=31.0))


def test_iteration_ledger_requires_sequential_cycles() -> None:
    ledger = begin_ledger(_utility_budget(), started_at="2026-07-11T00:00:00Z")

    with pytest.raises(DirectSvgCandidateError, match="cycle_sequence_invalid"):
        record_iteration(ledger, _iteration_receipt(2))


@pytest.mark.parametrize("missing", sorted(_iteration_receipt(1)))
def test_iteration_receipt_requires_every_declared_key(missing: str) -> None:
    receipt = _iteration_receipt(1)
    del receipt[missing]
    with pytest.raises(DirectSvgCandidateError, match="iteration_receipt_incomplete"):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


def test_iteration_receipt_rejects_unknown_keys() -> None:
    receipt = _iteration_receipt(1)
    receipt["unexpected"] = True
    with pytest.raises(DirectSvgCandidateError, match="iteration_receipt_keys_invalid"):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("source_path", "/tmp/source.svg", "iteration_path_invalid"),
        ("render_path", "../render.png", "iteration_path_invalid"),
        ("source_sha256", "not-a-hash", "iteration_hash_invalid"),
        ("command", ["rsvg-convert"], "iteration_command_invalid"),
        ("render_changed_from_prior", "false", "iteration_receipt_type_invalid"),
    ],
)
def test_iteration_receipt_rejects_bad_types_paths_and_hashes(
    field: str, value: object, error: str
) -> None:
    receipt = _iteration_receipt(1)
    receipt[field] = value
    with pytest.raises(DirectSvgCandidateError, match=error):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


def test_iteration_receipt_rejects_nested_hash_mismatch() -> None:
    receipt = _iteration_receipt(1)
    runtime = copy.deepcopy(receipt["runtime_receipt"])
    assert isinstance(runtime, dict)
    runtime["source_sha256"] = "sha256:" + "9" * 64
    receipt["runtime_receipt"] = runtime
    with pytest.raises(DirectSvgCandidateError, match="iteration_runtime_mismatch"):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


@pytest.mark.parametrize("missing", sorted(_iteration_receipt(1)["runtime_receipt"]))
def test_runtime_receipt_requires_every_declared_key(missing: str) -> None:
    receipt = _iteration_receipt(1)
    runtime = copy.deepcopy(receipt["runtime_receipt"])
    assert isinstance(runtime, dict)
    del runtime[missing]
    receipt["runtime_receipt"] = runtime
    with pytest.raises(DirectSvgCandidateError, match="iteration_runtime_receipt_invalid"):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


@pytest.mark.parametrize("missing", sorted(_iteration_receipt(1)["tool_model_receipt"]))
def test_tool_model_receipt_requires_every_declared_key(missing: str) -> None:
    receipt = _iteration_receipt(1)
    tool_model = copy.deepcopy(receipt["tool_model_receipt"])
    assert isinstance(tool_model, dict)
    del tool_model[missing]
    receipt["tool_model_receipt"] = tool_model
    with pytest.raises(DirectSvgCandidateError, match="iteration_tool_model_receipt_invalid"):
        record_iteration(begin_ledger(_utility_budget(), started_at="now"), receipt)


@pytest.mark.skipif(shutil.which("rsvg-convert") is None, reason="rsvg-convert missing")
def test_render_candidate_is_repeatable_and_rgb(tmp_path: Path) -> None:
    svg = _write_svg(
        tmp_path,
        extra_body='<rect x="20" y="20" width="40" height="30" fill="#336699"/>',
    )
    fontconfig = tmp_path / "fonts.conf"
    fontconfig.write_text(
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
        "<fontconfig><cachedir>font-cache</cachedir></fontconfig>",
        encoding="utf-8",
    )
    output = tmp_path / "candidate.png"

    first = render_candidate(
        svg,
        output,
        width=120,
        height=80,
        fontconfig_file=fontconfig,
    )
    second = render_candidate(
        svg,
        output,
        width=120,
        height=80,
        fontconfig_file=fontconfig,
    )

    assert first["source_sha256"] == second["source_sha256"]
    assert first["render_sha256"] == second["render_sha256"]
    assert first["fontconfig_sha256"] == second["fontconfig_sha256"]
    assert first["publication_acceptance"] == "not_claimed"
    with Image.open(output) as image:
        assert image.mode == "RGB"
        assert image.size == (120, 80)
