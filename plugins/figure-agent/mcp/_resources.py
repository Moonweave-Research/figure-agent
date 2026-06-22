from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_artifact_descriptor",
    "_candidate_manifest_metadata",
    "_parse_figure_uri",
    "_path_metadata",
    "_resource_metadata",
    "_resource_specs",
    "_resource_templates",
    "_sha256_file",
    "_status_artifacts",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
