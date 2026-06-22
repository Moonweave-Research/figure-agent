from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "ERROR_CATEGORIES",
    "PROTOCOL_VERSION",
    "SERVER_NAME",
    "SERVER_VERSION",
    "_call_tool",
    "_error",
    "_list_tools",
    "_tool_envelope",
    "_tool_result",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
