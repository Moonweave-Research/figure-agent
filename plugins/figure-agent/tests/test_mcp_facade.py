from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from hashlib import sha256
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = PLUGIN_ROOT / "mcp" / "figure_agent_server.py"
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "mcp"))

import figure_agent_server  # noqa: E402
from figure_agent_server import ERROR_CATEGORIES  # noqa: E402
from plugin_package_audit import find_mcp_config_issues  # noqa: E402


def _mcp_request(method: str, params: dict | None = None, request_id: int = 1) -> str:
    return json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    )


def _run_mcp_server(
    requests: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 10,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.update(env or {})
    merged_env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    virtual_env = merged_env.pop("VIRTUAL_ENV", None)
    if virtual_env:
        virtual_bin = str(Path(virtual_env) / "bin")
        merged_env["PATH"] = os.pathsep.join(
            entry for entry in merged_env.get("PATH", "").split(os.pathsep) if entry != virtual_bin
        )
    return subprocess.run(
        ["python3", str(MCP_SERVER)],
        input="\n".join(requests) + "\n",
        cwd=cwd,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _response_lines(result: subprocess.CompletedProcess[str]) -> list[dict]:
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def _tool_payload(response: dict) -> dict:
    text = response["result"]["content"][0]["text"]
    return json.loads(text)


def _resource_payload(response: dict) -> dict:
    text = response["result"]["contents"][0]["text"]
    return json.loads(text)


def _write_minimal_fixture(workspace: Path, name: str = "smoke_trap_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_trap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    return fixture


def _write_candidate_fixture(
    workspace: Path,
    name: str = "candidate_demo",
    *,
    with_candidate_defect: bool = True,
) -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: candidate_demo\n"
        "panels:\n"
        "  - id: C\n"
        "    caption: Energy diagram\n"
        "    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    if with_candidate_defect:
        _write_undeclared_candidate_defect(fixture)
    return fixture


def _write_undeclared_candidate_defect(fixture: Path) -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    f"examples/{fixture.name}/{fixture.name}.tex": "sha256:"
                    + sha256((fixture / f"{fixture.name}.tex").read_bytes()).hexdigest()
                },
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "C",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_keep_critique_gate(fixture: Path, tex_line: int) -> None:
    critique = fixture / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1.10\n"
        f"fixture: {fixture.name}\n"
        "findings:\n"
        "  - id: C001\n"
        "    severity: MAJOR\n"
        "    category: label_placement\n"
        "    tex_lines:\n"
        f"    - {tex_line}\n"
        f"    - {tex_line}\n"
        "    observation: Label is too close to a neighboring element.\n"
        "    suggested_fix: Move the label by a bounded amount.\n"
        "    status: open\n"
        "panels: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    critique_hash = "sha256:" + sha256(critique.read_bytes()).hexdigest()
    (fixture / "critique_adjudication.yaml").write_text(
        "schema: figure-agent.critique-adjudication.v1\n"
        f"fixture: {fixture.name}\n"
        f"source_critique_hash: {critique_hash}\n"
        "decisions:\n"
        "  - finding_id: C001\n"
        "    decision: keep\n"
        "    reason: Human kept this bounded finding for candidate search.\n"
        f"    patch_target: examples/{fixture.name}/{fixture.name}.tex "
        f"lines {tex_line}-{tex_line}\n"
        "    evidence: critique.md finding C001 reviewed.\n",
        encoding="utf-8",
    )


def _write_full_candidate_fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\n"
        "panels:\n"
        "  - id: C\n"
        "    caption: Energy diagram\n"
        "    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\documentclass[border=8pt]{standalone}\n"
        "\\usepackage{polymer-paper-preamble}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "% Panel C\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    _write_undeclared_candidate_defect(fixture)
    _write_keep_critique_gate(fixture, tex_line=6)
    return fixture


def _write_panel_candidate_fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
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
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
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


def _assert_common_envelope(payload: dict) -> None:
    assert isinstance(payload["schema"], str)
    assert isinstance(payload["success"], bool)
    assert isinstance(payload["artifacts"], list)
    assert isinstance(payload["duration_ms"], int)
    if not payload["success"]:
        assert isinstance(payload["error"]["category"], str)
        assert isinstance(payload["error"]["message"], str)


def test_mcp_json_starts_server_with_pinned_uv_project() -> None:
    config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["figure-agent"]

    assert server["command"] == "uv"
    assert server["args"][:4] == ["run", "--project", "${CLAUDE_PLUGIN_ROOT}", "python3"]
    assert "${CLAUDE_PLUGIN_ROOT}/mcp/figure_agent_server.py" in server["args"]
    assert server["cwd"] == "${CLAUDE_PLUGIN_ROOT}"
    assert server["env"]["FIGURE_AGENT_PLUGIN_ROOT"] == "${CLAUDE_PLUGIN_ROOT}"
    assert "FIGURE_AGENT_WORKSPACE" not in server["env"]


def test_mcp_tool_subprocesses_do_not_create_plugin_root_uv_venv() -> None:
    source = MCP_SERVER.read_text(encoding="utf-8")
    run_fig_agent_source = source.partition("def _run_fig_agent(")[2].partition("def _bounded(")[0]

    assert '"uv",' not in run_fig_agent_source
    assert '"--project",' not in run_fig_agent_source
    assert 'str(plugin_root / "bin" / "fig-agent")' in run_fig_agent_source


def test_mcp_startup_and_list_tools_are_side_effect_free(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    result = _run_mcp_server(
        [
            _mcp_request("initialize", request_id=1),
            _mcp_request("tools/list", request_id=2),
            _mcp_request("resources/list", request_id=3),
            _mcp_request("resources/templates/list", request_id=4),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(tmp_path / "workspace")},
    )

    responses = _response_lines(result)
    assert [response["id"] for response in responses] == [1, 2, 3, 4]
    tool_names = {tool["name"] for tool in responses[1]["result"]["tools"]}
    assert {
        "figure_agent_doctor",
        "figure_agent_status",
        "figure_agent_next",
        "figure_agent_compile",
        "figure_agent_export",
        "figure_agent_quality_map",
        "figure_agent_context_pack",
        "figure_agent_propose_patch",
        "figure_agent_verify_plan",
        "figure_agent_loop_checkpoint",
        "figure_agent_analyze_figure",
        "figure_agent_propose_improvements",
        "figure_agent_analyze_panel",
        "figure_agent_propose_panel_improvements",
        "figure_agent_render_candidates",
        "figure_agent_rank_candidates",
        "figure_agent_prepare_human_review",
        "figure_agent_compare_candidate",
        "figure_agent_candidate_apply_readiness",
        "figure_agent_evidence_sync_preview",
        "figure_agent_closeout_ready",
        "figure_agent_memory_summary",
        "figure_agent_benchmark_list",
        "figure_agent_benchmark_run_preview",
        "figure_agent_benchmark_compare",
        "figure_agent_quality_next_experiment",
        "figure_agent_benchmark_detectors_preview",
        "figure_agent_apply_candidate",
    } <= tool_names
    assert "figure_agent_next_action" not in tool_names
    assert "figure_agent_closeout_accept" not in tool_names
    assert "figure_agent_force_golden" not in tool_names
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before


def test_mcp_context_pack_preview_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace, name="context_demo")
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    result = _run_mcp_server(
        [
            _mcp_request("initialize", request_id=1),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_context_pack",
                    "arguments": {"name": "context_demo"},
                },
                request_id=2,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    responses = _response_lines(result)
    payload = _tool_payload(responses[1])
    assert payload["schema"] == "figure-agent.mcp.context-pack.v1"
    assert payload["success"] is True
    assert payload["context_pack"]["schema"] == "figure-agent.authoring-context-pack.v1"
    assert payload["context_pack"]["read_only"] is True
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_mcp_render_candidates_schema_exposes_evaluation_arguments(tmp_path: Path) -> None:
    result = _run_mcp_server(
        [_mcp_request("tools/list", request_id=1)],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(tmp_path / "workspace")},
    )

    response = _response_lines(result)[0]
    tools = {tool["name"]: tool for tool in response["result"]["tools"]}
    schema = tools["figure_agent_render_candidates"]["inputSchema"]
    properties = schema["properties"]
    assert schema["additionalProperties"] is False
    assert {"candidate_id", "compile", "export", "crop_panel", "evaluate"} <= set(properties)
    assert properties["candidate_id"]["type"] == "string"
    assert properties["compile"]["type"] == "boolean"
    assert properties["export"]["type"] == "boolean"
    assert properties["crop_panel"]["type"] == "string"
    assert properties["evaluate"]["type"] == "boolean"


def test_mcp_candidate_apply_readiness_schema_is_read_only(tmp_path: Path) -> None:
    result = _run_mcp_server(
        [_mcp_request("tools/list", request_id=1)],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(tmp_path / "workspace")},
    )

    response = _response_lines(result)[0]
    tools = {tool["name"]: tool for tool in response["result"]["tools"]}
    materialize_schema = tools["figure_agent_materialize_candidate_set"]["inputSchema"]
    schema = tools["figure_agent_candidate_apply_readiness"]["inputSchema"]
    accept_schema = tools["figure_agent_accept_candidate"]["inputSchema"]
    assert materialize_schema["additionalProperties"] is False
    assert materialize_schema["required"] == ["name"]
    assert materialize_schema["properties"]["candidate_set"]["type"] == "string"
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["name", "candidate_id", "candidate_set"]
    assert schema["properties"]["candidate_set"]["type"] == "string"
    assert accept_schema["additionalProperties"] is False
    assert accept_schema["required"] == [
        "name",
        "candidate_id",
        "decision",
        "reviewer",
        "rationale",
    ]
    assert accept_schema["properties"]["decision"]["enum"] == ["accept"]


def test_mcp_evidence_and_closeout_schemas_are_read_only(tmp_path: Path) -> None:
    result = _run_mcp_server(
        [_mcp_request("tools/list", request_id=1)],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(tmp_path / "workspace")},
    )

    response = _response_lines(result)[0]
    tools = {tool["name"]: tool for tool in response["result"]["tools"]}
    evidence_schema = tools["figure_agent_evidence_sync_preview"]["inputSchema"]
    closeout_schema = tools["figure_agent_closeout_ready"]["inputSchema"]
    export_schema = tools["figure_agent_export"]["inputSchema"]
    assert evidence_schema["additionalProperties"] is False
    assert closeout_schema["additionalProperties"] is False
    assert export_schema["additionalProperties"] is False
    assert "write" not in evidence_schema["properties"]
    assert "accept_golden" not in closeout_schema["properties"]
    assert "force_golden" not in export_schema["properties"]


def test_mcp_memory_and_benchmark_schemas_are_read_only(tmp_path: Path) -> None:
    result = _run_mcp_server(
        [_mcp_request("tools/list", request_id=1)],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(tmp_path / "workspace")},
    )

    response = _response_lines(result)[0]
    tools = {tool["name"]: tool for tool in response["result"]["tools"]}
    for name in (
        "figure_agent_memory_summary",
        "figure_agent_benchmark_list",
        "figure_agent_benchmark_run_preview",
        "figure_agent_benchmark_compare",
        "figure_agent_quality_next_experiment",
        "figure_agent_benchmark_detectors_preview",
    ):
        schema = tools[name]["inputSchema"]
        assert schema["additionalProperties"] is False
        properties = schema.get("properties", {})
        assert "write" not in properties
        assert "overwrite" not in properties
        assert "path" not in properties


def test_mcp_benchmark_run_preview_does_not_create_benchmark_scratch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "smoke_trap_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_trap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "smoke_trap_demo.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_benchmark_run_preview",
                    "arguments": {"suite": "smoke", "limit": 1},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.benchmark-run-preview.v1"
    assert payload["success"] is True
    assert payload["benchmark_run"]["schema"] == "figure-agent.quality-benchmark-run.v1"
    assert not (workspace / ".scratch" / "figure-agent-benchmarks").exists()


def test_mcp_quality_next_experiment_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_quality_next_experiment",
                    "arguments": {},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.quality-next-experiment.v1"
    assert payload["success"] is True
    command = payload["next_experiment"]["recommendation"]["command"]
    assert command == "fig-agent benchmark-run --suite smoke --json"
    assert not (workspace / ".scratch").exists()


def test_mcp_export_rejects_force_golden_before_running_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace, name="export_demo")

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_export",
                    "arguments": {"name": "export_demo", "force_golden": True},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.export.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "unsupported_operation"
    assert payload["error"]["message"] == "force_golden_requires_cli_closeout_accept"
    assert "stdout" not in payload


def test_mcp_compile_reports_operation_in_progress(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace, name="compile_demo")
    lock_root = fixture / "build" / ".mcp-locks"
    lock_root.mkdir(parents=True)
    (lock_root / "mutation.lock").write_text(
        json.dumps({"operation": "export"}),
        encoding="utf-8",
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compile",
                    "arguments": {"name": "compile_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.compile.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "operation_in_progress"
    assert payload["operation"] == "export"


def test_mcp_next_returns_read_only_state_router_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace, name="next_demo")
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_next",
                    "arguments": {"name": "next_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert payload["schema"] == "figure-agent.mcp.next.v1"
    assert payload["success"] is True
    assert payload["next_result"]["schema"] == "figure-agent.next.v1"
    assert payload["next_result"]["writes"] == []
    assert payload["next_result"]["alternatives"][0]["command"] == (
        "fig-agent status next_demo --json"
    )
    assert after == before


def test_mcp_next_returns_public_command_and_write_metadata(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace, name="next_demo")
    (fixture / "next_demo.tex").write_text("\\node at (0,0) {demo};\n", encoding="utf-8")

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_next",
                    "arguments": {"name": "next_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    next_payload = payload["next_result"]["next"]
    assert payload["schema"] == "figure-agent.mcp.next.v1"
    assert payload["success"] is True
    assert next_payload["action"] == "run_compile"
    assert next_payload["command"] == "fig-agent compile next_demo"
    assert next_payload["writes"] is True


def test_mcp_propose_improvements_reports_no_op_on_pure_refusal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_candidate_fixture(workspace, with_candidate_defect=False)

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_propose_improvements",
                    "arguments": {"name": "candidate_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    propose = _tool_payload(_response_lines(result)[0])
    assert propose["schema"] == "figure-agent.mcp.propose-improvements.v1"
    assert propose["candidate_set"]["candidates"] == []
    assert propose["candidate_set"]["refusals"]
    assert propose["success"] is False
    assert propose["no_op"] is True
    assert propose["refusals"] == propose["candidate_set"]["refusals"]


def _write_real_candidate_fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels:\n  - id: A\n    reference_image: reference/panel_a.png\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    build = fixture / "build"
    build.mkdir()
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "A",
                    }
                ],
                "source_hashes": {
                    f"examples/{name}/{name}.tex": "sha256:"
                    + sha256((fixture / f"{name}.tex").read_bytes()).hexdigest()
                },
            }
        ),
        encoding="utf-8",
    )
    return fixture


def test_mcp_propose_improvements_keeps_success_on_real_candidate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_real_candidate_fixture(workspace)

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_propose_improvements",
                    "arguments": {"name": "candidate_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    propose = _tool_payload(_response_lines(result)[0])
    assert propose["schema"] == "figure-agent.mcp.propose-improvements.v1"
    assert propose["candidate_set"]["candidates"]
    assert propose["success"] is True
    assert "no_op" not in propose


def test_mcp_benchmark_detectors_preview_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_benchmark_detectors_preview",
                    "arguments": {
                        "name": "smoke_label_overlap_demo",
                        "suite": "smoke",
                    },
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(PLUGIN_ROOT)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.benchmark-detectors-preview.v1"
    assert payload["success"] is True
    assert payload["detector_reports"]["schema"] == ("figure-agent.benchmark-detectors-preview.v1")
    assert payload["detector_reports"]["reports"][0]["state"] == "available"
    assert not (workspace / ".scratch").exists()


def test_mcp_export_rejects_force_golden_argument(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_export",
                    "arguments": {"name": "smoke_trap_demo", "force_golden": True},
                },
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    _assert_common_envelope(payload)
    assert payload["success"] is False
    assert payload["error"]["category"] == "unsupported_operation"
    assert payload["error"]["message"] == "force_golden_requires_cli_closeout_accept"


def test_mcp_doctor_reports_plugin_cwd_as_workspace_missing() -> None:
    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {"name": "figure_agent_doctor", "arguments": {}},
            )
        ],
        cwd=PLUGIN_ROOT,
        env={
            "FIGURE_AGENT_WORKSPACE": "",
            "CLAUDE_PROJECT_DIR": "",
        },
    )

    payload = _tool_payload(_response_lines(result)[0])
    _assert_common_envelope(payload)
    assert payload["schema"] == "figure-agent.mcp.doctor.v1"
    assert payload["bundle"]["state"] == "ok"
    assert payload["bundle"]["plugin_root_kind"] in {
        "source_tree",
        "installed_cache",
        "unpacked_zip",
        "unknown",
    }
    assert isinstance(payload["bundle"]["unexpected_cache_state"], list)
    assert payload["workspace"]["state"] == "missing"
    assert payload["workspace"]["workspace_root"] is None
    assert payload["workspace"]["workspace_source"] == "missing"


def test_mcp_status_rejects_invalid_fixture_before_path_join(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)
    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_status",
                    "arguments": {"name": "../outside"},
                },
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    _assert_common_envelope(payload)
    assert payload["schema"] == "figure-agent.mcp.status.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "invalid_fixture_name"


def test_mcp_tool_call_rejects_non_object_arguments() -> None:
    for arguments in ([], ["not", "an", "object"]):
        result = _run_mcp_server(
            [
                _mcp_request(
                    "tools/call",
                    {"name": "figure_agent_status", "arguments": arguments},
                )
            ],
            cwd=PLUGIN_ROOT,
        )

        payload = _tool_payload(_response_lines(result)[0])
        _assert_common_envelope(payload)
        assert payload["success"] is False
        assert payload["error"]["category"] == "invalid_request"


def test_mcp_tool_call_rejects_non_object_params() -> None:
    for params in ([], ["not", "an", "object"]):
        result = _run_mcp_server(
            [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": params,
                    }
                )
            ],
            cwd=PLUGIN_ROOT,
        )

        payload = _tool_payload(_response_lines(result)[0])
        _assert_common_envelope(payload)
        assert payload["success"] is False
        assert payload["error"]["category"] == "invalid_request"


def test_mcp_error_categories_match_design_doc() -> None:
    doc = (PLUGIN_ROOT / "docs" / "mcp-facade-design.md").read_text(encoding="utf-8")
    error_section = doc.partition("Use stable error categories:")[2].partition(
        "Each failure should return:"
    )[0]
    documented = {
        line.strip()[3:-1]
        for line in error_section.splitlines()
        if line.strip().startswith("- `") and line.strip().endswith("`")
    }

    assert ERROR_CATEGORIES <= documented


def test_mcp_resource_patterns_are_templates_not_literal_resources() -> None:
    result = _run_mcp_server(
        [
            _mcp_request("resources/list", request_id=1),
            _mcp_request("resources/templates/list", request_id=2),
        ],
        cwd=PLUGIN_ROOT,
    )

    resources_response, templates_response = _response_lines(result)
    assert resources_response["result"]["resources"] == []
    templates = templates_response["result"]["resourceTemplates"]
    assert templates
    assert all(template["mimeType"] == "application/json" for template in templates)
    assert any(template["uriTemplate"] == "figure://{name}/build/png" for template in templates)
    assert any(template["uriTemplate"] == "figure://{name}/exports/pdf" for template in templates)
    assert any(template["uriTemplate"] == "figure://{name}/exports/tif" for template in templates)
    assert any(
        template["uriTemplate"] == "figure://{name}/audit/undeclared-geometry"
        for template in templates
    )
    assert any(
        template["uriTemplate"] == "figure://{name}/audit/evidence-graph" for template in templates
    )


def test_mcp_resource_read_returns_metadata_for_existing_artifact(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace)
    export = fixture / "exports" / "smoke_trap_demo.pdf"
    export.parent.mkdir()
    export.write_bytes(b"%PDF-1.7\n")

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://smoke_trap_demo/exports/pdf"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.resource-metadata.v1"
    assert payload["success"] is True
    assert payload["exists"] is True
    assert payload["path"] == "examples/smoke_trap_demo/exports/smoke_trap_demo.pdf"
    assert payload["media_type"] == "application/pdf"
    assert payload["size_bytes"] == len(b"%PDF-1.7\n")
    assert payload["sha256"].startswith("sha256:")


def test_mcp_resource_read_returns_missing_metadata_without_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://smoke_trap_demo/audit/undeclared-geometry"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["success"] is True
    assert payload["exists"] is False
    assert payload["path"] == "examples/smoke_trap_demo/build/undeclared_geometry.json"


def test_mcp_resource_read_exposes_virtual_evidence_graph_metadata(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace)

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://smoke_trap_demo/audit/evidence-graph"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["success"] is True
    assert payload["virtual"] is True
    assert payload["content_schema"] == "figure-agent.audit-evidence-graph.v1"


def test_mcp_resource_read_blocks_symlink_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace)
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"secret")
    export_dir = fixture / "exports"
    export_dir.mkdir()
    (export_dir / "smoke_trap_demo.pdf").symlink_to(outside)

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://smoke_trap_demo/exports/pdf"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["success"] is False
    assert payload["blocked"] is True
    assert payload["reason"] == "path_escape"
    assert "sha256" not in payload


def test_mcp_resource_read_rejects_unknown_resource_uri(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://smoke_trap_demo/raw/tex"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["success"] is False
    assert payload["error"]["category"] == "unsupported_operation"


def test_mcp_quality_map_and_propose_patch_are_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace, name="quality_demo")
    (fixture / "quality_demo.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    report = fixture / "build" / "text_boundary_clash.json"
    report.parent.mkdir()
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": "quality_demo",
                "candidates": [{"id": "TB001", "text": "label-a"}],
                "total": 1,
            }
        ),
        encoding="utf-8",
    )
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {"name": "figure_agent_quality_map", "arguments": {"name": "quality_demo"}},
                request_id=1,
            ),
            _mcp_request(
                "tools/call",
                {"name": "figure_agent_propose_patch", "arguments": {"name": "quality_demo"}},
                request_id=2,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    quality_payload = _tool_payload(_response_lines(result)[0])
    propose_payload = _tool_payload(_response_lines(result)[1])
    assert quality_payload["schema"] == "figure-agent.mcp.quality-map.v1"
    assert quality_payload["success"] is True, quality_payload
    assert quality_payload["ledger"]["schema"] == "figure-agent.quality-defect-ledger.v1"
    assert propose_payload["schema"] == "figure-agent.mcp.propose-patch.v1"
    assert propose_payload["success"] is True
    assert propose_payload["plan"]["schema"] == "figure-agent.quality-patch-plan.v1"
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


def test_mcp_candidate_read_only_tools_and_apply_blocks_without_acceptance(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_candidate_fixture(workspace, with_candidate_defect=False)
    before_tex = (fixture / "candidate_demo.tex").read_text(encoding="utf-8")

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_analyze_figure",
                    "arguments": {"name": "candidate_demo"},
                },
                request_id=1,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_propose_improvements",
                    "arguments": {"name": "candidate_demo"},
                },
                request_id=2,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_apply_candidate",
                    "arguments": {"name": "candidate_demo", "candidate_id": "CAND001"},
                },
                request_id=3,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    analyze = _tool_payload(_response_lines(result)[0])
    propose = _tool_payload(_response_lines(result)[1])
    apply = _tool_payload(_response_lines(result)[2])
    assert analyze["schema"] == "figure-agent.mcp.analyze-figure.v1"
    assert analyze["success"] is True
    assert analyze["intent"]["schema"] == "figure-agent.intent-model.v1"
    assert propose["schema"] == "figure-agent.mcp.propose-improvements.v1"
    assert propose["success"] is False
    assert propose["no_op"] is True
    assert propose["candidate_set"]["schema"] == "figure-agent.candidate-set.v1"
    assert apply["schema"] == "figure-agent.mcp.apply-candidate.v1"
    assert apply["success"] is False
    assert apply["error"]["category"] == "unsupported_operation"
    # Apply now runs the real gate: a fixture with no rendered/accepted candidate is
    # refused before any mutation, not deterministically refused for all callers.
    assert "candidate_manifest" in apply["error"]["message"]
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == before_tex


def test_mcp_candidate_render_rank_review_flow(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_candidate_fixture(workspace)
    memory_dir = fixture / "build" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "quality_memory_index.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.quality-memory-index.v1",
                "families": {
                    "bounded_coordinate_offset": {
                        "attempts": 3,
                        "recommended_prior": 0.2,
                    }
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_render_candidates",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_set": "build/candidates/candidate_set.json",
                        "candidate_id": "CAND001",
                        "compile": True,
                        "export": True,
                        "crop_panel": "C",
                        "evaluate": True,
                    },
                },
                request_id=1,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_rank_candidates",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_set": "build/candidates/candidate_set.json",
                    },
                },
                request_id=2,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_prepare_human_review",
                    "arguments": {"name": "candidate_demo", "candidate_id": "CAND001"},
                },
                request_id=3,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    render = _tool_payload(_response_lines(result)[0])
    rank = _tool_payload(_response_lines(result)[1])
    review = _tool_payload(_response_lines(result)[2])
    assert (fixture / "build" / "candidates" / "candidate_set.json").is_file()
    assert render["schema"] == "figure-agent.mcp.render-candidates.v1"
    assert render["success"] is True
    assert render["render_result"]["schema"] == "figure-agent.candidate-render-result.v1"
    assert render["render_result"]["rendered"][0]["render_manifest"] == (
        "build/candidates/CAND001/render_manifest.json"
    )
    assert rank["schema"] == "figure-agent.mcp.rank-candidates.v1"
    assert rank["success"] is True
    assert rank["rank_result"]["schema"] == "figure-agent.candidate-rank-result.v1"
    assert rank["rank_result"]["scores"][0]["render_status"] != "not_rendered"
    assert rank["rank_result"]["scores"][0]["scores"]["memory_prior"] == 0.2
    assert review["schema"] == "figure-agent.mcp.prepare-human-review.v1"
    assert review["success"] is True
    assert review["review_packet"]["schema"] == "figure-agent.candidate-review-packet.v1"
    assert review["review_packet"]["render_manifest_path"] == (
        "build/candidates/CAND001/render_manifest.json"
    )


@pytest.mark.render
def test_mcp_candidate_lifecycle_closes_without_cli_fallback(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_full_candidate_fixture(workspace)
    tex_path = fixture / "candidate_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compile",
                    "arguments": {"name": "candidate_demo", "strict": False},
                },
                request_id=1,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_materialize_candidate_set",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_set": "build/candidates/panel_C_candidate_set.json",
                        "panel_id": "C",
                        "family": "label-repair",
                    },
                },
                request_id=2,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_render_candidates",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_set": "build/candidates/panel_C_candidate_set.json",
                        "candidate_id": "CAND001",
                        "compile": True,
                        "export": True,
                        "crop_panel": "C",
                        "evaluate": True,
                    },
                },
                request_id=3,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_accept_candidate",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_id": "CAND001",
                        "candidate_set": "build/candidates/panel_C_candidate_set.json",
                        "decision": "accept",
                        "reviewer": "mcp-test",
                        "rationale": "Rendered candidate evidence reviewed in the MCP-only chain.",
                    },
                },
                request_id=4,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_apply_candidate",
                    "arguments": {
                        "name": "candidate_demo",
                        "candidate_id": "CAND001",
                        "candidate_set_path": "build/candidates/panel_C_candidate_set.json",
                    },
                },
                request_id=5,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
        timeout=90,
    )

    compiled, materialized, rendered, accepted, applied = [
        _tool_payload(response) for response in _response_lines(result)
    ]
    assert compiled["schema"] == "figure-agent.mcp.compile.v1"
    assert compiled["success"] is True
    assert materialized["schema"] == "figure-agent.mcp.materialize-candidate-set.v1"
    assert materialized["success"] is True
    assert materialized["candidate_set_path"] == "build/candidates/panel_C_candidate_set.json"
    assert (fixture / "build" / "candidates" / "panel_C_candidate_set.json").is_file()
    assert rendered["schema"] == "figure-agent.mcp.render-candidates.v1"
    assert rendered["success"] is True
    assert (fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json").is_file()
    assert accepted["schema"] == "figure-agent.mcp.accept-candidate.v1"
    assert accepted["success"] is True, json.dumps(accepted, indent=2, sort_keys=True)
    assert accepted["acceptance"]["path"] == "build/candidates/CAND001/acceptance.json"
    assert applied["schema"] == "figure-agent.mcp.apply-candidate.v1"
    assert applied["status"] in {
        "applied",
        "applied_with_failed_verification",
        "rolled_back",
    }, json.dumps(
        applied,
        indent=2,
        sort_keys=True,
    )
    assert applied["success"] is (applied["status"] == "applied")
    assert applied["apply_result"]["status"] == applied["status"]
    assert applied["apply_result"]["post_apply"]["compile"]["returncode"] == 0
    if applied["status"] in {"applied_with_failed_verification", "rolled_back"}:
        assert "post-apply verification failed" in applied["error"]["message"]
    assert tex_path.read_text(encoding="utf-8") != before


def test_mcp_panel_candidate_tools_and_resources(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_panel_candidate_fixture(workspace)
    candidate_set = fixture / "build" / "candidates" / "panel_C_candidate_set.json"
    subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "candidates",
            "candidate_demo",
            "--panel",
            "C",
            "--family",
            "energy-trap-alignment",
            "--json",
            "--output",
            "build/candidates/panel_C_candidate_set.json",
        ],
        cwd=workspace,
        env={
            **os.environ,
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "render-candidates",
            "candidate_demo",
            "--candidate-set",
            "build/candidates/panel_C_candidate_set.json",
        ],
        cwd=workspace,
        env={
            **os.environ,
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=True,
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_analyze_panel",
                    "arguments": {"name": "candidate_demo", "panel_id": "C"},
                },
                request_id=1,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_propose_panel_improvements",
                    "arguments": {
                        "name": "candidate_demo",
                        "panel_id": "C",
                        "family": "energy-trap-alignment",
                    },
                },
                request_id=2,
            ),
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compare_candidate",
                    "arguments": {"name": "candidate_demo", "candidate_id": "CAND001"},
                },
                request_id=3,
            ),
            _mcp_request(
                "resources/read",
                {"uri": "figure://candidate_demo/panel/C/intent"},
                request_id=4,
            ),
            _mcp_request(
                "resources/read",
                {"uri": "figure://candidate_demo/candidates/CAND001/manifest"},
                request_id=5,
            ),
            _mcp_request(
                "resources/templates/list",
                request_id=6,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    responses = _response_lines(result)
    analyze = _tool_payload(responses[0])
    propose = _tool_payload(responses[1])
    compare = _tool_payload(responses[2])
    panel_resource = _resource_payload(responses[3])
    manifest_resource = _resource_payload(responses[4])
    templates = {item["uriTemplate"] for item in responses[5]["result"]["resourceTemplates"]}
    assert candidate_set.is_file()
    assert analyze["schema"] == "figure-agent.mcp.analyze-panel.v1"
    assert analyze["success"] is True
    assert analyze["panel_model"]["schema"] == "figure-agent.candidate-panel-model.v1"
    assert analyze["panel_model"]["selector_count"] == 5
    assert propose["schema"] == "figure-agent.mcp.propose-panel-improvements.v1"
    assert propose["success"] is True
    assert propose["candidate_set"]["candidates"][0]["family"] == "energy-trap-alignment"
    assert compare["schema"] == "figure-agent.mcp.compare-candidate.v1"
    assert compare["success"] is True
    assert compare["review_packet"]["panel"] == "C"
    assert compare["review_packet"]["visual_review"]["status"] == "missing_render"
    assert panel_resource["virtual"] is True
    assert panel_resource["recommended_tool"] == "figure_agent_analyze_panel"
    assert manifest_resource["exists"] is True
    assert "figure://{name}/panel/{panel_id}/intent" in templates
    assert "figure://{name}/candidates/{candidate_id}/manifest" in templates
    assert "figure://{name}/candidates/{candidate_id}/review" in templates


def test_mcp_candidate_manifest_resource_rejects_manifest_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_candidate_fixture(workspace)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    outside = fixture / "outside.json"
    outside.write_text('{"secret": true}\n', encoding="utf-8")
    (sandbox / "candidate_manifest.json").symlink_to(outside)

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://candidate_demo/candidates/CAND001/manifest"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.resource-metadata.v1"
    assert payload["success"] is False
    assert payload["blocked"] is True
    assert payload["reason"] == "sandbox_symlink_forbidden:candidate_manifest.json"
    assert "sha256" not in payload


def test_mcp_candidate_manifest_resource_rejects_sandbox_ancestor_symlink(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_candidate_fixture(workspace, with_candidate_defect=False)
    exports = fixture / "exports"
    exports.mkdir()
    build = fixture / "build"
    build.symlink_to(exports)
    sandbox = exports / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (sandbox / "candidate_manifest.json").write_text('{"secret": true}\n', encoding="utf-8")

    result = _run_mcp_server(
        [
            _mcp_request(
                "resources/read",
                {"uri": "figure://candidate_demo/candidates/CAND001/manifest"},
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _resource_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.resource-metadata.v1"
    assert payload["success"] is False
    assert payload["blocked"] is True
    assert payload["reason"] == "sandbox_symlink_forbidden:build"
    assert "sha256" not in payload


def test_mcp_candidate_render_reports_operation_in_progress(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_candidate_fixture(workspace)
    lock_root = fixture / "build" / ".mcp-locks"
    lock_root.mkdir(parents=True)
    (lock_root / "mutation.lock").write_text(
        json.dumps({"operation": "export"}),
        encoding="utf-8",
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_render_candidates",
                    "arguments": {"name": "candidate_demo"},
                },
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.render-candidates.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "operation_in_progress"
    assert payload["operation"] == "export"


def test_mcp_notifications_do_not_emit_response_frames() -> None:
    result = _run_mcp_server(
        [
            json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {}}),
            _mcp_request("tools/list", request_id=1),
        ],
        cwd=PLUGIN_ROOT,
    )

    responses = _response_lines(result)
    assert [response["id"] for response in responses] == [1]


def test_mcp_invalid_json_does_not_kill_server() -> None:
    result = _run_mcp_server(
        [
            "{not json",
            _mcp_request("tools/list", request_id=1),
        ],
        cwd=PLUGIN_ROOT,
    )

    parse_error, tools_response = _response_lines(result)
    assert parse_error["id"] is None
    assert parse_error["error"]["code"] == -32700
    assert tools_response["id"] == 1


def test_mcp_non_object_json_request_does_not_kill_server() -> None:
    result = _run_mcp_server(
        [
            "[]",
            _mcp_request("tools/list", request_id=1),
        ],
        cwd=PLUGIN_ROOT,
    )

    invalid_request, tools_response = _response_lines(result)
    assert invalid_request["id"] is None
    assert invalid_request["error"]["code"] == -32600
    assert tools_response["id"] == 1


def test_mcp_mutating_tool_missing_fixture_is_side_effect_free(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)
    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compile",
                    "arguments": {"name": "missing_demo"},
                },
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    _assert_common_envelope(payload)
    assert payload["success"] is False
    assert payload["error"]["category"] == "fixture_missing"
    assert not (workspace / "examples" / "missing_demo").exists()


def test_mcp_mutating_tool_reports_operation_in_progress(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace)
    lock_root = fixture / "build" / ".mcp-locks"
    lock_root.mkdir(parents=True)
    (lock_root / "mutation.lock").write_text(
        json.dumps({"operation": "export"}),
        encoding="utf-8",
    )
    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compile",
                    "arguments": {"name": "smoke_trap_demo"},
                },
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    _assert_common_envelope(payload)
    assert payload["success"] is False
    assert payload["error"]["category"] == "operation_in_progress"
    assert payload["operation"] == "export"


def test_cowork_zip_includes_mcp_contract(tmp_path: Path) -> None:
    output_dir = tmp_path / "dist"
    package_result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "scripts" / "package_cowork_plugin.py"),
            "--output",
            str(output_dir),
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert package_result.returncode == 0, package_result.stderr
    zip_path = output_dir / "figure-agent-cowork-0.9.3.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert ".mcp.json" in names
    assert "mcp/figure_agent_server.py" in names


def test_package_audit_accepts_plugin_root_mcp_config() -> None:
    assert find_mcp_config_issues(PLUGIN_ROOT) == []


def test_package_audit_rejects_workspace_relative_mcp_scripts(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    (plugin / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "figure-agent": {
                        "command": "python3",
                        "args": ["scripts/mcp_server.py"],
                        "cwd": ".",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    issues = find_mcp_config_issues(plugin)
    assert any("workspace-relative script path" in issue for issue in issues)
    assert any("cwd must not depend on user workspace" in issue for issue in issues)


def _run_fig_agent_cli(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return subprocess.run(
        [sys.executable, str(FIG_AGENT), *args],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _build_apply_ready_candidate(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: candidate_demo\n"
        "panels:\n"
        "  - id: C\n"
        "    caption: Energy diagram\n"
        "    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    _write_undeclared_candidate_defect(fixture)
    candidates = _run_fig_agent_cli(
        workspace,
        "candidates",
        name,
        "--json",
        "--output",
        "build/candidates/candidate_set.json",
    )
    assert candidates.returncode == 0, candidates.stderr
    render = _run_fig_agent_cli(
        workspace,
        "render-candidates",
        name,
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--candidate-id",
        "CAND001",
        "--compile",
        "--export",
        "--evaluate",
        "--json",
    )
    assert render.returncode == 0, render.stderr

    sandbox = fixture / "build" / "candidates" / "CAND001"
    manifest_path = sandbox / "candidate_manifest.json"
    render_manifest_path = sandbox / "render_manifest.json"
    (fixture / f"{name}.tex").write_text(
        "\\documentclass[border=8pt]{standalone}\n"
        "\\usepackage{polymer-paper-preamble}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    source_hash = "sha256:" + sha256((fixture / f"{name}.tex").read_bytes()).hexdigest()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0]["source_sha256"] = source_hash
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
    render_manifest["stages"] = {
        "compile": {"status": "success"},
        "export": {"status": "success"},
        "crop": {"status": "success"},
        "evaluate": {"status": "rendered_needs_human_review"},
    }
    render_manifest_path.write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    accept = _run_fig_agent_cli(
        workspace,
        "accept-candidate",
        name,
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--decision",
        "accept",
        "--reviewer",
        "local-user",
        "--rationale",
        "Rendered evidence reviewed.",
        "--json",
    )
    assert accept.returncode == 0, accept.stderr
    return fixture


def test_mcp_apply_candidate_mutates_tex_and_honors_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _build_apply_ready_candidate(workspace)
    monkeypatch.setenv("FIGURE_AGENT_PLUGIN_ROOT", str(PLUGIN_ROOT))
    monkeypatch.setenv("FIGURE_AGENT_WORKSPACE", str(workspace))

    tex_path = fixture / "candidate_demo.tex"
    before = tex_path.read_text(encoding="utf-8")

    applied = figure_agent_server._apply_candidate(
        {"name": "candidate_demo", "candidate_id": "CAND001"}
    )

    assert applied["schema"] == "figure-agent.mcp.apply-candidate.v1"
    assert applied["status"] in {
        "applied",
        "applied_with_failed_verification",
        "rolled_back",
    }, applied
    assert applied["success"] is (applied["status"] == "applied")
    after = tex_path.read_text(encoding="utf-8")
    apply_result = applied["apply_result"]
    rolled_back = bool(
        apply_result.get("post_apply", {}).get("class_verifiers", {}).get("rolled_back")
    )
    if rolled_back:
        # Autonomy: a failed-verification fix is auto-rolled-back, so the working
        # tree is restored to its pre-apply content rather than left mutated.
        assert after == before
    else:
        assert after != before
    assert apply_result["status"] == applied["status"]
    if applied["status"] == "applied":
        assert applied.get("error") is None
        assert apply_result["post_apply"]["compile"]["returncode"] == 0
    elif applied["status"] == "rolled_back":
        assert "post-apply verification failed" in applied["error"]["message"]
        assert "automatically rolled back" in applied["error"]["message"]
        assert "working tree unchanged" not in applied["error"]["message"]
    else:
        assert "post-apply verification failed" in applied["error"]["message"]
        assert any(check["status"] == "failed" for check in apply_result["post_apply"].values())

    # Second apply behavior depends on whether the first mutation persisted:
    # rolled_back remains re-applicable, applied/applied_with_failed_verification is terminal.
    blocked = figure_agent_server._apply_candidate(
        {"name": "candidate_demo", "candidate_id": "CAND001"}
    )
    if applied["status"] == "rolled_back":
        assert blocked["status"] in {"applied", "applied_with_failed_verification", "rolled_back"}
        return
    assert blocked["success"] is False
    # A pristine refusal must be distinguishable at the envelope top level from a
    # mutated-but-unverified apply: status is surfaced and the message says the
    # working tree is unchanged (vs the rollback-needed wording for the mutated case).
    assert blocked["status"] == "blocked"
    assert "working tree unchanged" in blocked["error"]["message"]
    assert "rollback" not in blocked["error"]["message"]
    blocked_result = blocked["apply_result"]
    assert blocked_result["status"] == "blocked"
    assert any(
        diagnostic["code"] == "already_applied" for diagnostic in blocked_result["diagnostics"]
    )


class TestVersionConsistency:
    """SERVER_VERSION in server code matches pyproject.toml."""

    def test_server_version_matches_pyproject(self) -> None:
        import tomllib

        pyproject = PLUGIN_ROOT / "pyproject.toml"
        pyproject_version = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"][
            "version"
        ]
        assert figure_agent_server.SERVER_VERSION == pyproject_version, (
            f"figure_agent_server.SERVER_VERSION={figure_agent_server.SERVER_VERSION!r} "
            f"≠ pyproject.toml version={pyproject_version!r}"
        )
