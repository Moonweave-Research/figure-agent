from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_is_safe_fixture_name",
    "_is_safe_panel_id",
    "_validated_workspace",
    "_validated_workspace_and_name",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
