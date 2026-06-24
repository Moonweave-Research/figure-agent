from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_bounded",
    "_bundle_diagnostics",
    "_dependency_diagnostics",
    "_examples_dir",
    "_fixture_lock",
    "_json_payload_from_result",
    "_operation_in_progress",
    "_plugin_root",
    "_run_fig_agent",
    "_run_fig_agent_enveloped",
    "_run_json_fig_agent_tool",
    "_run_workspace_json_fig_agent_tool",
    "_tool_env",
    "_workspace_diagnostics",
    "_workspace_root",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
