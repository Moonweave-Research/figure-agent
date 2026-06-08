from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER = PLUGIN_ROOT / "mcp" / "figure_agent_server.py"

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "mcp"))

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
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.update(env or {})
    merged_env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    return subprocess.run(
        [sys.executable, str(MCP_SERVER)],
        input="\n".join(requests) + "\n",
        cwd=cwd,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
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


def _assert_common_envelope(payload: dict) -> None:
    assert isinstance(payload["schema"], str)
    assert isinstance(payload["success"], bool)
    assert isinstance(payload["artifacts"], list)
    assert isinstance(payload["duration_ms"], int)
    if not payload["success"]:
        assert isinstance(payload["error"]["category"], str)
        assert isinstance(payload["error"]["message"], str)


def test_mcp_json_starts_server_without_uv() -> None:
    config = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["figure-agent"]

    assert server["command"] == "python3"
    assert "uv" not in server["args"]
    assert "${CLAUDE_PLUGIN_ROOT}/mcp/figure_agent_server.py" in server["args"]
    assert server["cwd"] == "${CLAUDE_PLUGIN_ROOT}"
    assert server["env"]["FIGURE_AGENT_PLUGIN_ROOT"] == "${CLAUDE_PLUGIN_ROOT}"
    assert "FIGURE_AGENT_WORKSPACE" not in server["env"]


def test_mcp_tool_subprocesses_do_not_create_plugin_root_uv_venv() -> None:
    source = MCP_SERVER.read_text(encoding="utf-8")
    run_fig_agent_source = source.partition("def _run_fig_agent(")[2].partition(
        "def _bounded("
    )[0]

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
        "figure_agent_compile",
        "figure_agent_export",
        "figure_agent_quality_map",
        "figure_agent_propose_patch",
        "figure_agent_verify_plan",
        "figure_agent_next_action",
        "figure_agent_loop_checkpoint",
    } <= tool_names
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before


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
    assert any(
        template["uriTemplate"] == "figure://{name}/build/png" for template in templates
    )
    assert any(
        template["uriTemplate"] == "figure://{name}/exports/pdf" for template in templates
    )
    assert any(
        template["uriTemplate"] == "figure://{name}/exports/tif" for template in templates
    )
    assert any(
        template["uriTemplate"] == "figure://{name}/audit/undeclared-geometry"
        for template in templates
    )
    assert any(
        template["uriTemplate"] == "figure://{name}/audit/evidence-graph"
        for template in templates
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
    assert quality_payload["success"] is True
    assert quality_payload["ledger"]["schema"] == "figure-agent.quality-defect-ledger.v1"
    assert propose_payload["schema"] == "figure-agent.mcp.propose-patch.v1"
    assert propose_payload["success"] is True
    assert propose_payload["plan"]["schema"] == "figure-agent.quality-patch-plan.v1"
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before


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
