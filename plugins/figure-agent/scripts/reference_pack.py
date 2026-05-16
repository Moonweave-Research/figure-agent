"""Parse and validate role-typed reference packs.

`reference/reference_pack.md` is the manual boundary between usable visual
evidence and forbidden transfer. This parser keeps that Markdown form but makes
the role table machine-checkable for critique/export acceptance tooling.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceRole:
    source: str
    roles: list[str]
    use: str
    do_not_transfer: str


def _strip_inline_code(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("`") and stripped.endswith("`"):
        return stripped[1:-1]
    return stripped


def _markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-"} for cell in cells):
            continue
        rows.append(cells)
    if rows:
        return rows[1:]
    return []


def parse_reference_roles(text: str) -> list[ReferenceRole]:
    entries: list[ReferenceRole] = []
    for cells in _markdown_table_rows(text):
        if len(cells) < 4:
            continue
        source, role_text, use, do_not_transfer = cells[:4]
        roles = [role.strip() for role in role_text.split(",") if role.strip()]
        entries.append(
            ReferenceRole(
                source=_strip_inline_code(source),
                roles=roles,
                use=use.strip(),
                do_not_transfer=do_not_transfer.strip(),
            )
        )
    return entries


def anti_reference_entries(entries: list[ReferenceRole]) -> list[ReferenceRole]:
    return [entry for entry in entries if "anti_reference" in entry.roles]


def reference_pack_failures(pack_path: Path) -> list[str]:
    if not pack_path.is_file():
        return [f"missing reference pack: {pack_path}"]

    entries = parse_reference_roles(pack_path.read_text(encoding="utf-8"))
    if not entries:
        return ["reference pack has no Reference Roles table rows"]

    failures: list[str] = []
    for entry in entries:
        if not entry.source:
            failures.append("reference row missing file/source")
            continue
        if not entry.roles:
            failures.append(f"reference row missing role: {entry.source}")
        if not entry.do_not_transfer:
            failures.append(f"reference row missing Do Not Transfer boundary: {entry.source}")
    if not anti_reference_entries(entries):
        failures.append("reference pack has no anti_reference row")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_path", type=Path)
    parser.add_argument("--json", action="store_true", help="emit parsed roles as JSON")
    args = parser.parse_args(argv)

    failures = reference_pack_failures(args.pack_path)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    entries = parse_reference_roles(args.pack_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps([asdict(entry) for entry in entries], indent=2, sort_keys=True))
    else:
        print(f"reference_count={len(entries)}")
        print(f"anti_reference_count={len(anti_reference_entries(entries))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
