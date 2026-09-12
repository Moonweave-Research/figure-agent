"""Input-file parsing for spec.yaml and briefing.md."""

from __future__ import annotations

import math
import re

import yaml

_SECTION_HEADER = re.compile(r"^##\s+§?(\d+)\.\s+(.+)$", re.MULTILINE)
_NAMED_SECTION_HEADER = re.compile(r"^##\s+(?!§?\d+\.\s+)([^#].+?)\s*$", re.MULTILINE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BLOCKQUOTE = re.compile(r"^>\s.*$", re.MULTILINE)
_FOOTER_RULE = re.compile(r"^---\s*$", re.MULTILINE)

_KNOWN_STYLE_PROFILES = {"polymer-default", "polymer-paper"}


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("spec mapping keys must be strings")
        if key in mapping:
            raise ValueError(f"duplicate spec key {key!r} at line {key_node.start_mark.line + 1}")
        mapping[key] = loader.construct_object(value_node)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _finite_values(value: object, path: str = "spec") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path} must be finite")
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_values(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite_values(item, f"{path}[{index}]")


def normalize_bbox_pdf_cm(value: object, *, label: str) -> list[float]:
    """Normalize a PDF-cm bbox without applying fixture-specific offsets."""
    if not isinstance(value, list | tuple) or len(value) != 4:
        raise ValueError(f"{label} must be a list of four numbers")
    try:
        if any(isinstance(item, bool) for item in value):
            raise ValueError("boolean coordinate")
        normalized = [float(item) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a list of four numbers") from exc
    if not all(math.isfinite(item) for item in normalized):
        raise ValueError(f"{label} must contain finite numbers")
    x0, y0, x1, y1 = normalized
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"{label} must be [x0, y0, x1, y1] with x1>x0, y1>y0")
    return normalized


def _normalize_panel(panel: dict, index: int) -> dict:
    normalized = dict(panel)
    panel_id = normalized.get("id", f"index {index}")
    reference_image = normalized.get("reference_image")
    if reference_image is not None and not isinstance(reference_image, str):
        raise ValueError(f"panels[{panel_id!r}].reference_image must be a string path")

    bbox = normalized.get("bbox_pdf_cm")
    if bbox is None:
        return normalized
    normalized["bbox_pdf_cm"] = normalize_bbox_pdf_cm(
        bbox,
        label=f"panels[{panel_id!r}].bbox_pdf_cm",
    )
    return normalized


def parse_spec(text: str) -> dict:
    try:
        data = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid spec.yaml: {exc}") from exc
    if data is None:
        return {"panels": []}
    if not isinstance(data, dict):
        raise ValueError("spec.yaml root must be a mapping")
    _finite_values(data)
    for key in ("accepted", "semantic_contract_required"):
        if key in data and data[key] is not None and not isinstance(data[key], bool):
            raise ValueError(f"{key} must be a boolean")
    panels = data.get("panels", [])
    if not isinstance(panels, list):
        raise ValueError("panels must be a list")
    else:
        if any(not isinstance(panel, dict) for panel in panels):
            raise ValueError("every panels entry must be a mapping")
        panels = [_normalize_panel(panel, index) for index, panel in enumerate(panels)]
        ids = [panel["id"] for panel in panels if "id" in panel]
        if any(not isinstance(value, str) or not value.strip() for value in ids):
            raise ValueError("panel ids must be non-empty strings")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate panel id")
    data["panels"] = panels
    profile = data.get("style_profile")
    if profile is not None and profile not in _KNOWN_STYLE_PROFILES:
        raise ValueError(
            f"Unknown style_profile {profile!r}; known: {sorted(_KNOWN_STYLE_PROFILES)}"
        )
    return data


def parse_briefing(text: str) -> dict[int | str, tuple[str, str]]:
    first_section = _SECTION_HEADER.search(text)
    if first_section is not None:
        preamble = _BLOCKQUOTE.sub("", text[: first_section.start()])
        text = preamble + text[first_section.start() :]
    else:
        text = _BLOCKQUOTE.sub("", text)
    sections: dict[int | str, tuple[str, str]] = {}
    matches = list(_SECTION_HEADER.finditer(text))
    named_matches = list(_NAMED_SECTION_HEADER.finditer(text))
    all_matches = sorted(matches + named_matches, key=lambda match: match.start())
    intro = text[: all_matches[0].start()] if all_matches else text
    intro = re.sub(r"^#.*$|^---\s*$", "", _HTML_COMMENT.sub("", intro), flags=re.MULTILINE)
    if intro.strip():
        sections["preamble"] = ("Preamble", intro.strip())
    for i, m in enumerate(all_matches):
        numbered = m in matches
        title = (m.group(2) if numbered else m.group(1)).strip()
        start = m.end()
        end = all_matches[i + 1].start() if i + 1 < len(all_matches) else len(text)
        section_text = text[start:end]
        # Cut at first horizontal rule — footer instructions live below the rule.
        rule = _FOOTER_RULE.search(section_text)
        if rule is not None:
            section_text = section_text[: rule.start()]
        body = _HTML_COMMENT.sub("", section_text).strip()
        key: int | str = int(m.group(1)) if numbered else title.casefold()
        sections[key] = (title, body)
    return sections
