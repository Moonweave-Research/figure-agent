from __future__ import annotations

try:
    from . import _legacy_server as _server
except ImportError:
    import _legacy_server as _server


_NAMES = (
    "_analyze_figure",
    "_analyze_panel",
    "_apply_candidate",
    "_candidate_apply_readiness",
    "_compare_candidate",
    "_prepare_human_review",
    "_propose_improvements",
    "_propose_panel_improvements",
    "_rank_candidates",
    "_render_candidates",
)
globals().update({name: getattr(_server, name) for name in _NAMES})
