from __future__ import annotations

from . import figure_agent_server as _server

globals().update(
    {name: getattr(_server, name) for name in dir(_server) if not name.startswith("__")}
)
