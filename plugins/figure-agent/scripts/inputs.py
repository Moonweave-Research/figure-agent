"""Input-file parsing for spec.yaml and briefing.md."""

from __future__ import annotations

import re

import yaml

_SECTION_HEADER = re.compile(r"^##\s+§?(\d+)\.\s+(.+)$", re.MULTILINE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BLOCKQUOTE = re.compile(r"^>\s.*$", re.MULTILINE)
_FOOTER_RULE = re.compile(r"^---\s*$", re.MULTILINE)

_KNOWN_STYLE_PROFILES = {"polymer-default", "polymer-paper"}


def _normalize_panel(panel: dict, index: int) -> dict:
    normalized = dict(panel)
    panel_id = normalized.get("id", f"index {index}")
    reference_image = normalized.get("reference_image")
    if reference_image is not None and not isinstance(reference_image, str):
        raise ValueError(f"panels[{panel_id!r}].reference_image must be a string path")

    bbox = normalized.get("bbox_pdf_cm")
    if bbox is None:
        return normalized
    if not isinstance(bbox, list | tuple) or len(bbox) != 4:
        raise ValueError(f"panels[{panel_id!r}].bbox_pdf_cm must be a list of four numbers")
    try:
        normalized_bbox = [float(value) for value in bbox]
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"panels[{panel_id!r}].bbox_pdf_cm must be a list of four numbers"
        ) from exc
    x0, y0, x1, y1 = normalized_bbox
    if x1 <= x0 or y1 <= y0:
        raise ValueError(
            f"panels[{panel_id!r}].bbox_pdf_cm must be [x0, y0, x1, y1] with x1>x0, y1>y0"
        )
    normalized["bbox_pdf_cm"] = normalized_bbox
    return normalized


def parse_spec(text: str) -> dict:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid spec.yaml: {exc}") from exc
    if data is None:
        return {"panels": []}
    if not isinstance(data, dict):
        return {"panels": []}
    panels = data.get("panels", [])
    if not isinstance(panels, list):
        panels = []
    else:
        panels = [
            _normalize_panel(panel, index)
            for index, panel in enumerate(panels)
            if isinstance(panel, dict)
        ]
    data["panels"] = panels
    profile = data.get("style_profile")
    if profile is not None and profile not in _KNOWN_STYLE_PROFILES:
        raise ValueError(
            f"Unknown style_profile {profile!r}; known: {sorted(_KNOWN_STYLE_PROFILES)}"
        )
    return data


def parse_briefing(text: str) -> dict[int, tuple[str, str]]:
    first_section = _SECTION_HEADER.search(text)
    if first_section is not None:
        preamble = _BLOCKQUOTE.sub("", text[: first_section.start()])
        text = preamble + text[first_section.start() :]
    else:
        text = _BLOCKQUOTE.sub("", text)
    sections: dict[int, tuple[str, str]] = {}
    matches = list(_SECTION_HEADER.finditer(text))
    for i, m in enumerate(matches):
        n = int(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]
        # Cut at first horizontal rule — footer instructions live below the rule.
        rule = _FOOTER_RULE.search(section_text)
        if rule is not None:
            section_text = section_text[: rule.start()]
        body = _HTML_COMMENT.sub("", section_text).strip()
        sections[n] = (title, body)
    return sections
