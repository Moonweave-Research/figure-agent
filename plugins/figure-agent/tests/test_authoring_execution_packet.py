from __future__ import annotations

import hashlib
import json
from pathlib import Path

import authoring_execution_packet
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_context_fixture(workspace: Path, name: str = "context_demo") -> Path:
    fixture = workspace / "examples" / name
    review = fixture / "review"
    review.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"""
name: {name}
title: Context Demo
style_profile: polymer-paper
authoring_context_pack:
  enabled: true
panels:
  - id: C
    caption: Trap energy diagram
    semantic_claims:
      - id: trap-depth
        claim: Deep traps are harder to escape than shallow traps.
    locked_invariants:
      - id: energy-up
        invariant: Energy increases upward in the trap diagram.
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("## Topic\nCharge trapping\n", encoding="utf-8")
    (fixture / "design.md").write_text("Use compact visual grammar.\n", encoding="utf-8")
    (fixture / "authoring_plan.md").write_text(
        "Panel C should read as deep trap first.\n",
        encoding="utf-8",
    )
    (review / "budget.yaml").write_text(
        "schema: figure-agent.authoring-budget.v1\nmax_attempts: 1\n",
        encoding="utf-8",
    )
    (review / "blank.txt").write_text("", encoding="utf-8")
    return fixture


def _compile(
    workspace: Path,
    *,
    blank_start: str = "examples/context_demo/review/blank.txt",
    budget_contract: str = "examples/context_demo/review/budget.yaml",
    output_path: str = (
        "examples/context_demo/review/failure-first/execution-binding-v1/"
        "control_generated.tex"
    ),
) -> tuple[dict[str, object], str]:
    return authoring_execution_packet.compile_authoring_execution_packet(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        model_id="gpt-5.5",
        budget_contract=budget_contract,
        blank_start=blank_start,
        output_path=output_path,
    )


def test_compiles_canonical_packet_and_prompt(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    packet, prompt = _compile(workspace)

    assert packet["schema"] == "figure-agent.authoring-execution-packet.v1"
    assert packet["prompt"]["utf8"] == prompt
    assert packet["prompt"]["sha256"] == _sha256_text(prompt)
    assert packet["mandatory_source_requirements"] == [
        r"\documentclass[tikz,border=4pt]{standalone}",
        r"\usepackage{tikz}",
        r"\usepackage{polymer-paper-preamble}",
    ]
    assert packet["packet_sha256"] == authoring_execution_packet.canonical_packet_sha256(
        packet
    )
    assert prompt.endswith("\n")
    assert "feedback_rounds: 0" in prompt
    assert "manual_repairs: 0" in prompt
    assert "publication_acceptance: not_claimed" in prompt


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("blank_start", "/tmp/blank.txt", "repo-relative"),
        ("blank_start", "examples/context_demo/../context_demo/review/blank.txt", "unsafe"),
        ("budget_contract", "examples/context_demo/review/missing.yaml", "regular file"),
        (
            "output_path",
            "examples/context_demo/review/other/control_generated.tex",
            "execution-binding-v1",
        ),
        (
            "output_path",
            "examples/context_demo/review/failure-first/execution-binding-v1/out.pdf",
            ".tex",
        ),
    ],
)
def test_rejects_unsafe_or_invalid_paths(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    kwargs = {field: value}

    with pytest.raises(authoring_execution_packet.AuthoringExecutionPacketError, match=message):
        _compile(workspace, **kwargs)


def test_rejects_intermediate_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    linked = fixture / "linked-review"
    linked.symlink_to(fixture / "review", target_is_directory=True)

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="symlink",
    ):
        _compile(
            workspace,
            blank_start="examples/context_demo/linked-review/blank.txt",
        )


def test_rejects_existing_generated_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_context_fixture(workspace)
    output = (
        fixture
        / "review"
        / "failure-first"
        / "execution-binding-v1"
        / "control_generated.tex"
    )
    output.parent.mkdir(parents=True)
    output.write_text("already here\n", encoding="utf-8")

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="output path already exists",
    ):
        _compile(workspace)


def test_rejects_duplicate_mandatory_requirements() -> None:
    prompt = "\n".join(
        [
            r"\documentclass[tikz,border=4pt]{standalone}",
            r"\documentclass[tikz,border=4pt]{standalone}",
            r"\usepackage{tikz}",
            r"\usepackage{polymer-paper-preamble}",
        ]
    )
    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="duplicate mandatory source requirement",
    ):
        authoring_execution_packet._validate_prompt_requirements(prompt)


def test_rejects_prompt_missing_preamble() -> None:
    prompt = "\n".join(
        [
            r"\documentclass[tikz,border=4pt]{standalone}",
            r"\usepackage{tikz}",
        ]
    )
    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="missing mandatory source requirement",
    ):
        authoring_execution_packet._validate_prompt_requirements(prompt)


def test_write_rejects_packet_hash_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    packet, prompt = _compile(workspace)
    packet["model_id"] = "changed-after-hash"

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="packet hash drift",
    ):
        authoring_execution_packet.write_authoring_execution_packet(
            workspace
            / "examples/context_demo/review/failure-first/execution-binding-v1/packet.json",
            workspace
            / "examples/context_demo/review/failure-first/execution-binding-v1/prompt.md",
            packet=packet,
            prompt=prompt,
        )


def test_write_rejects_prompt_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    packet, prompt = _compile(workspace)

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="prompt hash drift",
    ):
        authoring_execution_packet.write_authoring_execution_packet(
            workspace
            / "examples/context_demo/review/failure-first/execution-binding-v1/packet.json",
            workspace
            / "examples/context_demo/review/failure-first/execution-binding-v1/prompt.md",
            packet=packet,
            prompt=prompt + "changed\n",
        )


def test_write_persists_canonical_json_and_rejects_second_write(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    packet, prompt = _compile(workspace)
    attempt = workspace / "examples/context_demo/review/failure-first/execution-binding-v1"
    packet_path = attempt / "packet.json"
    prompt_path = attempt / "prompt.md"

    authoring_execution_packet.write_authoring_execution_packet(
        packet_path,
        prompt_path,
        packet=packet,
        prompt=prompt,
    )

    assert packet_path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(packet_path.read_text(encoding="utf-8")) == packet
    assert prompt_path.read_text(encoding="utf-8") == prompt
    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="already exists",
    ):
        authoring_execution_packet.write_authoring_execution_packet(
            packet_path,
            prompt_path,
            packet=packet,
            prompt=prompt,
        )
