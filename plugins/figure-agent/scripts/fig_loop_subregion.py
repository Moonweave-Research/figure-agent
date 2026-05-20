"""Active sub-region target helper for fig_loop."""

from __future__ import annotations

from pathlib import Path

from subregion_active_set import active_subregion_ids, parse_active_target_rows


def active_subregion_target(example_dir: Path) -> dict[str, str | None] | None:
    log_path = example_dir / "subregion_iteration_log.md"
    if not log_path.is_file():
        return None
    rows = parse_active_target_rows(log_path.read_text(encoding="utf-8"))
    active_ids = active_subregion_ids(rows)
    if not active_ids:
        return None
    return {
        "finding_id": None,
        "patch_target": active_ids[0],
        "reason": "active sub-region target",
    }
