"""Issue the compile receipt a real build writes, for filesystem fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import compile_run  # noqa: E402

STARTED_AT = "2026-01-01T00:00:00Z"


def issue_compile_run(
    build_dir: Path,
    *,
    source_tex: Path,
    render_pdf: Path | None = None,
    strict_requested: bool = False,
    state: str = compile_run.PASSED,
    run_id: str | None = None,
    engine: str = "lualatex",
) -> str:
    """Write build/compile_run.json for a fixture and return its run id."""
    resolved = run_id or f"run-{build_dir.parent.name}"
    payload = compile_run.build_receipt(
        run_id=resolved,
        started_at=STARTED_AT,
        engine=engine,
        strict_requested=strict_requested,
        state=state,
        source_tex=source_tex,
        render_pdf=render_pdf,
    )
    compile_run.write_receipt(
        output=compile_run.receipt_path(build_dir),
        payload=payload,
    )
    return resolved
