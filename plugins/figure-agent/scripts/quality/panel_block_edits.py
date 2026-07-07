"""Data-driven Panel-F block-edit families for quality-search.

Each YAML entry is one human-observed element iteration: an ordered set of exact
tex-block replacements guarded by predecessor/idempotency/protected-label
signatures. One entry replaces a bespoke ``_panel_f_post_*_replacement`` function.
The stop rule is documented at
``docs/superpowers/specs/panel-block-edit-stop-rule.md``: a new iteration on an
existing panel is a new entry here, never a new Python family.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import IO, Any

import yaml

_DATA_PATH = Path(__file__).with_name("panel_block_edits.yaml")


@dataclass(frozen=True)
class BlockReplacement:
    old: str
    new: str


@dataclass(frozen=True)
class PanelBlockEdit:
    family_id: str
    template_id: str
    panel: str
    requires: tuple[str, ...]
    applied_signature: tuple[str, ...]
    preserve_after: tuple[str, ...]
    replacements: tuple[BlockReplacement, ...]
    protected_labels: tuple[str, ...]
    goal_trigger: tuple[tuple[str, ...], ...]
    goal_hypothesis: Mapping[str, str]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"panel_block_edits: {message}")


def _str_tuple(value: Any, *, field: str, family: str) -> tuple[str, ...]:
    _require(isinstance(value, list), f"{family}.{field} must be a list")
    for item in value:
        _require(isinstance(item, str), f"{family}.{field} entries must be strings")
    return tuple(value)


def _parse_entry(raw: Any, index: int) -> PanelBlockEdit:
    _require(isinstance(raw, dict), f"entry {index} must be a mapping")
    family = str(raw.get("family_id") or "")
    _require(bool(family), f"entry {index} missing family_id")
    template_id = raw.get("template_id")
    _require(isinstance(template_id, str) and bool(template_id), f"{family} missing template_id")
    panel = raw.get("panel")
    _require(isinstance(panel, str) and bool(panel), f"{family} missing panel")

    replacements_raw = raw.get("replacements")
    _require(
        isinstance(replacements_raw, list) and bool(replacements_raw),
        f"{family} needs replacements",
    )
    replacements: list[BlockReplacement] = []
    for pair in replacements_raw:
        _require(isinstance(pair, dict), f"{family} replacement must be a mapping")
        old = pair.get("old")
        new = pair.get("new")
        _require(isinstance(old, str) and bool(old), f"{family} replacement has empty old")
        _require(isinstance(new, str), f"{family} replacement new must be a string")
        _require(old != new, f"{family} replacement old == new")
        replacements.append(BlockReplacement(old=old, new=new))

    applied = _str_tuple(raw.get("applied_signature"), field="applied_signature", family=family)
    _require(bool(applied), f"{family} needs a non-empty applied_signature")

    trigger_raw = raw.get("goal_trigger") or []
    _require(isinstance(trigger_raw, list), f"{family}.goal_trigger must be a list")
    goal_trigger = tuple(
        _str_tuple(group, field="goal_trigger group", family=family) for group in trigger_raw
    )
    hypothesis = raw.get("goal_hypothesis") or {}
    _require(isinstance(hypothesis, dict), f"{family}.goal_hypothesis must be a mapping")

    return PanelBlockEdit(
        family_id=family,
        template_id=template_id,
        panel=panel,
        requires=_str_tuple(raw.get("requires") or [], field="requires", family=family),
        applied_signature=applied,
        preserve_after=_str_tuple(
            raw.get("preserve_after") or [], field="preserve_after", family=family
        ),
        replacements=tuple(replacements),
        protected_labels=_str_tuple(
            raw.get("protected_labels") or [], field="protected_labels", family=family
        ),
        goal_trigger=goal_trigger,
        goal_hypothesis=MappingProxyType(
            {str(key): str(value) for key, value in hypothesis.items()}
        ),
    )


def load_panel_block_edits(source: IO[str] | str | Path) -> list[PanelBlockEdit]:
    """Parse and validate panel-block-edit entries from a YAML stream or path.

    A present-but-unparseable source raises; an empty document yields no entries.
    """
    if isinstance(source, (str, Path)):
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source.read()
    raw = yaml.safe_load(text)
    if raw is None:
        return []
    _require(isinstance(raw, list), "top-level document must be a list of entries")
    entries = [_parse_entry(item, index) for index, item in enumerate(raw)]
    seen: set[str] = set()
    for entry in entries:
        _require(entry.family_id not in seen, f"duplicate family_id {entry.family_id}")
        seen.add(entry.family_id)
    return entries


@lru_cache(maxsize=1)
def load_bundled_panel_block_edits() -> tuple[PanelBlockEdit, ...]:
    """Load the bundled data file. Absent file = no entries; malformed = raise."""
    if not _DATA_PATH.exists():
        return ()
    return tuple(load_panel_block_edits(_DATA_PATH))
