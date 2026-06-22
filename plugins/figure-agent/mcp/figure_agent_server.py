#!/usr/bin/env python3
from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


globals().update(
    {name: getattr(_server, name) for name in dir(_server) if not name.startswith("__")}
)


def _run_fig_agent(args, *, workspace_root, timeout_seconds=120):
    plugin_root = _server._plugin_root()
    _compat_command = [str(plugin_root / "bin" / "fig-agent")]
    return _server._run_fig_agent(
        args,
        workspace_root=workspace_root,
        timeout_seconds=timeout_seconds,
    )


def _bounded(text, limit=4000):
    return _server._bounded(text, limit=limit)


if __name__ == "__main__":
    raise SystemExit(_server.serve())
