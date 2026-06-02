"""Tests for parsing text-form sub-region iteration logs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from subregion_active_set import (  # noqa: E402
    active_subregion_ids,
    expand_subregion_ids,
    iteration_patch_ids,
    main,
    parse_active_target_rows,
)


def test_expand_subregion_ids_expands_same_prefix_ranges() -> None:
    ids = expand_subregion_ids("D-1..D-3, E-1..E-2, Row2-BR2")

    assert ids == ["D-1", "D-2", "D-3", "E-1", "E-2", "Row2-BR2"]


def test_expand_subregion_ids_keeps_cross_prefix_ranges_literal() -> None:
    ids = expand_subregion_ids("C-L1..C-R6")

    assert ids == ["C-L1..C-R6"]


def test_parse_active_target_rows_reads_markdown_table() -> None:
    log = """
## Active Target Set

| State | Sub-region ID | Evidence | Notes |
|---|---|---|---|
| active target | G-2, G-7 | review | patch electrode and gap |
| named but stable | D-1..D-3 | log | stable |

## Iteration Log
"""

    rows = parse_active_target_rows(log)

    assert rows[0].state == "active target"
    assert rows[0].ids == ["G-2", "G-7"]
    assert rows[1].ids == ["D-1", "D-2", "D-3"]
    assert active_subregion_ids(rows) == ["G-2", "G-7"]


def test_pilot_log_currently_has_empty_active_set() -> None:
    log_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "fig1_overview_v2_pair_001_vault"
        / "subregion_iteration_log.md"
    )

    rows = parse_active_target_rows(log_path.read_text(encoding="utf-8"))

    assert active_subregion_ids(rows) == []


def test_iteration_patch_ids_reads_observed_patch_units() -> None:
    log = """
## Iteration Log

| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |
|---|---|---|---|---|---|
| v7 | D-1..D-3, Row2-BR2 | uneven | normalized widths | improved | watch labels |
| v7 | G-1, G-2 | overpowering | shortened electrode | fits | recheck |
"""

    assert iteration_patch_ids(log) == ["D-1", "D-2", "D-3", "Row2-BR2", "G-1", "G-2"]


def test_cli_accepts_format_json_alias(tmp_path: Path, capsys) -> None:
    log_path = tmp_path / "subregion_iteration_log.md"
    log_path.write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-1..D-2 | review | patch |\n",
        encoding="utf-8",
    )

    exit_code = main([str(log_path), "--format", "json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["active_targets"] == ["D-1", "D-2"]
