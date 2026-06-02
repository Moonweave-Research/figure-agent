"""Parse text-form sub-region iteration logs.

The sub-region pilot deliberately keeps the source of truth in Markdown
(`subregion_iteration_log.md`) instead of adding a spec.yaml schema. This
helper extracts the active target set and observed patch units from that log.
It does not infer regions, crop images, or edit TikZ.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActiveTargetRow:
    state: str
    raw_id: str
    ids: list[str]
    evidence: str
    notes: str


_RANGE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*?)(\d+)\.\.\1(\d+)$")


def expand_subregion_ids(raw: str) -> list[str]:
    """Expand comma-separated IDs and simple same-prefix ranges.

    `D-1..D-3` becomes `D-1`, `D-2`, `D-3`. Cross-prefix ranges such as
    `C-L1..C-R6` stay literal because the intended intermediate IDs are
    domain-specific, not mechanically knowable.
    """
    ids: list[str] = []
    for token in [part.strip() for part in raw.split(",") if part.strip()]:
        if token.lower() == "none":
            continue
        match = _RANGE_RE.match(token)
        if match:
            prefix, start_text, end_text = match.groups()
            start = int(start_text)
            end = int(end_text)
            step = 1 if end >= start else -1
            ids.extend(f"{prefix}{index}" for index in range(start, end + step, step))
        else:
            ids.append(token)
    return ids


def _section_body(text: str, heading: str) -> str:
    heading_line = f"## {heading}"
    start = text.find(heading_line)
    if start == -1:
        return ""
    body_start = text.find("\n", start)
    if body_start == -1:
        return ""
    next_heading = re.search(r"^##\s+", text[body_start + 1 :], re.MULTILINE)
    if next_heading is None:
        return text[body_start + 1 :]
    return text[body_start + 1 : body_start + 1 + next_heading.start()]


def _markdown_table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-"} for cell in cells):
            continue
        rows.append(cells)
    if rows:
        return rows[1:]  # drop header
    return []


def parse_active_target_rows(text: str) -> list[ActiveTargetRow]:
    rows: list[ActiveTargetRow] = []
    for cells in _markdown_table_rows(_section_body(text, "Active Target Set")):
        if len(cells) < 4:
            continue
        state, raw_id, evidence, notes = cells[:4]
        rows.append(
            ActiveTargetRow(
                state=state,
                raw_id=raw_id,
                ids=expand_subregion_ids(raw_id),
                evidence=evidence,
                notes=notes,
            )
        )
    return rows


def active_subregion_ids(rows: list[ActiveTargetRow]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        if row.state.lower() == "active target":
            ids.extend(row.ids)
    return ids


def iteration_patch_ids(text: str) -> list[str]:
    ids: list[str] = []
    for cells in _markdown_table_rows(_section_body(text, "Iteration Log")):
        if len(cells) < 2:
            continue
        ids.extend(expand_subregion_ids(cells[1]))
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    if not args.log_path.is_file():
        print(f"subregion_active_set.py: missing log: {args.log_path}", file=sys.stderr)
        return 2

    text = args.log_path.read_text(encoding="utf-8")
    rows = parse_active_target_rows(text)
    active_ids = active_subregion_ids(rows)
    patch_ids = iteration_patch_ids(text)

    if args.json or args.format == "json":
        payload = {
            "active_target_count": len(active_ids),
            "active_targets": active_ids,
            "active_target_rows": [asdict(row) for row in rows],
            "iteration_patch_ids": patch_ids,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        active_display = ", ".join(active_ids) if active_ids else "(none)"
        print(f"active_target_count={len(active_ids)}")
        print(f"active_targets={active_display}")
        print(f"iteration_patch_count={len(patch_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
