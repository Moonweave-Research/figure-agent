#!/usr/bin/env python3
"""Detector telemetry shim (spec §4 Phase 0d).

compile.sh runs each checker as its own subprocess, so there is no single
dispatch point to record which detectors ran. Each ``check_*.py`` instead calls
``log_detector_run`` once near the end of ``main()`` to append one JSONL record
(name, fired/clean, finding count, optional duration) to a shared log. Telemetry
governs later demotion/pruning of the detector suite.

This is side-effect-light: if the target directory does not exist it is a no-op,
and a failed write is swallowed — telemetry must never raise into a checker.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


def log_detector_run(
    name: str,
    *,
    fired: bool,
    finding_count: int,
    duration_ms: float | None = None,
    log_path: Path | None = None,
) -> bool:
    """Append one JSONL telemetry record for a detector run.

    ``log_path`` defaults to ``build/detector_log.jsonl`` next to the checker's
    output (alongside the pdf). Returns ``True`` when a record was written,
    ``False`` when skipped (missing directory) or on a swallowed write error.
    """
    target = log_path if log_path is not None else Path("build") / "detector_log.jsonl"
    if not target.parent.is_dir():
        return False
    record = {
        "name": name,
        "fired": fired,
        "finding_count": finding_count,
        "duration_ms": duration_ms,
        "ts": time.time(),
    }
    try:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except OSError:
        return False
    return True
