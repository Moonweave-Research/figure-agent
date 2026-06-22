from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = ("_closeout_ready", "_doctor", "_evidence_sync_preview", "_verify_plan")
globals().update({name: getattr(_server, name) for name in _NAMES})
