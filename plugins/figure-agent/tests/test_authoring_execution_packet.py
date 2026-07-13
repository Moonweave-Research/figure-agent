from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import authoring_execution_packet
import authoring_execution_preflight
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
    execution_cwd: str = ".",
) -> tuple[dict[str, object], str]:
    return authoring_execution_packet.compile_authoring_execution_packet(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        model_id="gpt-5.5",
        budget_contract=budget_contract,
        blank_start=blank_start,
        output_path=output_path,
        execution_cwd=execution_cwd,
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
    assert "Trap energy diagram" in prompt
    assert "Charge trapping" in prompt
    assert "Do not create an intermediate subdirectory" in prompt
    assert "Use only the preamble palette tokens" in prompt
    assert "Keep every explicit line width at or above 0.25pt" in prompt
    assert r"Do not use local \tiny or \scriptsize font overrides" in prompt
    assert packet["allowed_repository_read_paths"] == [
        "AGENTS.md",
        "styles/polymer-paper-preamble.sty",
    ]
    assert "Read repository file content only from [AGENTS.md]" in prompt
    assert "[styles/polymer-paper-preamble.sty]" in prompt
    assert packet["style_lock_authoring_requirements"] == [
        "Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, "
        "cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, "
        "white, and gray.",
        "Keep every explicit line width at or above 0.25pt.",
        r"Do not use local \tiny or \scriptsize font overrides.",
    ]


def test_binds_repo_relative_execution_cwd_into_packet_and_prompt(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    packet, prompt = _compile(workspace, execution_cwd="plugins/figure-agent")

    assert packet["execution_cwd"] == "plugins/figure-agent"
    assert packet["repository_output_path"] == (
        "plugins/figure-agent/examples/context_demo/review/failure-first/"
        "execution-binding-v1/control_generated.tex"
    )
    assert packet["allowed_repository_read_paths"] == [
        "plugins/figure-agent/AGENTS.md",
        "plugins/figure-agent/styles/polymer-paper-preamble.sty",
    ]
    assert "Do not change directory before resolving paths." in prompt
    assert (
        "Write exactly one new source to "
        "[plugins/figure-agent/examples/context_demo/review/failure-first/"
        "execution-binding-v1/control_generated.tex]."
    ) in prompt
    assert "Before resolving the output path, change directory" not in prompt


def test_compiles_orro_plan_from_bound_packet_without_prompt_or_scope_drift(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    packet, prompt = _compile(workspace, execution_cwd="plugins/figure-agent")

    workflow, role_lanes = authoring_execution_packet.compile_orro_execution_plans(
        packet,
        goal="Execute the control packet once without repair.",
        lane_id="context-control-v1-author",
    )

    assert workflow["kind"] == "orro-workflow-plan"
    assert workflow["goal"] == "Execute the control packet once without repair."
    assert role_lanes["kind"] == "orro-role-lane-plan"
    assert role_lanes["workflow_plan_hash"] == hashlib.sha256(
        json.dumps(
            workflow,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    lane = role_lanes["lanes"][0]
    expected_scope = [
        "plugins/figure-agent/examples/context_demo/review/failure-first/"
        "execution-binding-v1/control_generated.tex"
    ]
    assert lane["prompt"] == prompt
    assert lane["model"] == "gpt-5.5"
    assert lane["granted_write_scope"] == expected_scope
    assert lane["region"] == expected_scope
    assert lane["role_capability"]["write_scope"] == expected_scope
    assert lane["may_execute"] is True
    assert lane["may_verify"] is False
    assert role_lanes["boundary"]["role_lane_plan_is_proof"] is False


def test_orro_plan_rejects_packet_hash_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    packet, _ = _compile(workspace)
    packet["model_id"] = "different-model"

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="packet hash drift",
    ):
        authoring_execution_packet.compile_orro_execution_plans(
            packet,
            goal="Execute once.",
            lane_id="context-control-v1-author",
        )


def test_rejects_unsafe_execution_cwd(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="execution cwd",
    ):
        _compile(workspace, execution_cwd="../figure-agent")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("blank_start", "/tmp/blank.txt", "repo-relative"),
        ("blank_start", "examples/context_demo/../context_demo/review/blank.txt", "unsafe"),
        ("budget_contract", "examples/context_demo/review/missing.yaml", "regular file"),
        (
            "output_path",
            "examples/context_demo/review/other/control_generated.tex",
            "execution-binding-v",
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


def test_accepts_a_new_versioned_attempt_directory(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    packet, _ = _compile(
        workspace,
        output_path=(
            "examples/context_demo/review/failure-first/execution-binding-v2/"
            "control_generated.tex"
        ),
    )

    assert packet["output_path"].endswith("execution-binding-v2/control_generated.tex")


def test_accepts_declared_comparable_arm_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    packet, prompt = _compile(
        workspace,
        output_path=(
            "examples/context_demo/review/failure-first/comparable-v2/"
            "verified_generated.tex"
        ),
    )

    assert packet["output_path"].endswith(
        "comparable-v2/verified_generated.tex"
    )
    assert "Use only the preamble palette tokens" in prompt
    assert (
        "Write exactly one new source to "
        "[examples/context_demo/review/failure-first/comparable-v2/"
        "verified_generated.tex]."
    ) in prompt


def test_rejects_undeclared_comparable_output_name(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="declared comparable arm",
    ):
        _compile(
            workspace,
            output_path=(
                "examples/context_demo/review/failure-first/comparable-v2/"
                "invented_generated.tex"
            ),
        )


def test_resolves_declared_comparable_packet_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    path = authoring_execution_packet.resolve_attempt_artifact_path(
        workspace,
        "context_demo",
        (
            "examples/context_demo/review/failure-first/comparable-v2/"
            "verified_packet.json"
        ),
        suffix=".json",
    )

    assert path == (
        workspace
        / "examples/context_demo/review/failure-first/comparable-v2/"
        "verified_packet.json"
    )


def test_rejects_undeclared_comparable_packet_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    with pytest.raises(
        authoring_execution_packet.AuthoringExecutionPacketError,
        match="declared comparable artifact",
    ):
        authoring_execution_packet.resolve_attempt_artifact_path(
            workspace,
            "context_demo",
            (
                "examples/context_demo/review/failure-first/comparable-v2/"
                "invented_packet.json"
            ),
            suffix=".json",
        )


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


def _write_arm(
    workspace: Path,
    arm: str,
    *,
    model_id: str = "gpt-5.5",
) -> tuple[Path, Path]:
    output = (
        "examples/context_demo/review/failure-first/execution-binding-v1/"
        f"{arm}_generated.tex"
    )
    packet, prompt = authoring_execution_packet.compile_authoring_execution_packet(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
        model_id=model_id,
        budget_contract="examples/context_demo/review/budget.yaml",
        blank_start="examples/context_demo/review/blank.txt",
        output_path=output,
    )
    attempt = workspace / "examples/context_demo/review/failure-first/execution-binding-v1"
    packet_path = attempt / f"{arm}_packet.json"
    prompt_path = attempt / f"{arm}_prompt.md"
    authoring_execution_packet.write_authoring_execution_packet(
        packet_path,
        prompt_path,
        packet=packet,
        prompt=prompt,
    )
    return packet_path, prompt_path


def test_preflight_accepts_equal_contracts_with_disjoint_outputs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    control, _ = _write_arm(workspace, "control")
    treatment, _ = _write_arm(workspace, "treatment")

    result = authoring_execution_preflight.preflight_authoring_pair(
        control,
        treatment,
    )

    assert result["schema"] == "figure-agent.authoring-execution-preflight.v1"
    assert result["decision"] == "pass"
    assert result["filesystem_read_isolation"] == "unavailable"
    assert result["control"]["packet_sha256"] != result["treatment"]["packet_sha256"]
    assert result["control"]["packet_path"] == (
        "examples/context_demo/review/failure-first/execution-binding-v1/"
        "control_packet.json"
    )
    assert not Path(result["control"]["prompt_path"]).is_absolute()


def test_preflight_rejects_unequal_model_contract(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    control, _ = _write_arm(workspace, "control")
    treatment, _ = _write_arm(workspace, "treatment", model_id="other-model")

    with pytest.raises(
        authoring_execution_preflight.AuthoringExecutionPreflightError,
        match="model_id mismatch",
    ):
        authoring_execution_preflight.preflight_authoring_pair(control, treatment)


def test_preflight_rejects_prompt_byte_drift(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    control, control_prompt = _write_arm(workspace, "control")
    treatment, _ = _write_arm(workspace, "treatment")
    control_prompt.write_text("drifted\n", encoding="utf-8")

    with pytest.raises(
        authoring_execution_preflight.AuthoringExecutionPreflightError,
        match="prompt byte drift",
    ):
        authoring_execution_preflight.preflight_authoring_pair(control, treatment)


def test_authoring_packet_and_preflight_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)
    attempt_rel = "examples/context_demo/review/failure-first/execution-binding-v1"
    env = os.environ.copy()
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    for arm in ("control", "treatment"):
        result = subprocess.run(
            [
                str(PLUGIN_ROOT / "bin" / "fig-agent"),
                "authoring-packet",
                "context_demo",
                "--model-id",
                "gpt-5.5",
                "--budget-contract",
                "examples/context_demo/review/budget.yaml",
                "--blank-start",
                "examples/context_demo/review/blank.txt",
                "--output-path",
                f"{attempt_rel}/{arm}_generated.tex",
                "--packet-out",
                f"{attempt_rel}/{arm}_packet.json",
                "--prompt-out",
                f"{attempt_rel}/{arm}_prompt.md",
                "--json",
            ],
            cwd=PLUGIN_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        prompt = workspace / attempt_rel / f"{arm}_prompt.md"
        assert payload["prompt"]["utf8"] == prompt.read_text(encoding="utf-8")
        assert payload["prompt"]["sha256"] == _sha256_text(
            prompt.read_text(encoding="utf-8")
        )

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-preflight",
            "--control",
            f"{attempt_rel}/control_packet.json",
            "--treatment",
            f"{attempt_rel}/treatment_packet.json",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"] == "pass"

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "authoring-orro-plan",
            "--packet",
            f"{attempt_rel}/control_packet.json",
            "--goal",
            "Execute the control packet once without repair.",
            "--lane-id",
            "context-control-v1-author",
            "--workflow-out",
            ".witnessd/plans/control-workflow.json",
            "--role-lane-out",
            ".witnessd/plans/control-role-lanes.json",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["publication_acceptance"] == "not_claimed"
    assert (
        payload["role_lane_plan"]["lanes"][0]["prompt"]
        == json.loads(
            (workspace / attempt_rel / "control_packet.json").read_text(
                encoding="utf-8"
            )
        )["prompt"]["utf8"]
    )
    assert (workspace / ".witnessd/plans/control-workflow.json").is_file()
    assert (workspace / ".witnessd/plans/control-role-lanes.json").is_file()
