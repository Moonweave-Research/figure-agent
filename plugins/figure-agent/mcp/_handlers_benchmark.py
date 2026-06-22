from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_benchmark_compare",
    "_benchmark_detectors_preview",
    "_benchmark_list",
    "_benchmark_run_preview",
    "_quality_next_experiment",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
