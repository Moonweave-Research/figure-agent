from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_context_pack",
    "_memory_summary",
    "_next",
    "_propose_patch",
    "_quality_map",
    "_status",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
