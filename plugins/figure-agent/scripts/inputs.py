"""Input-file parsing for spec.yaml and briefing.md."""

from __future__ import annotations

import re

import yaml

_SECTION_HEADER = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.MULTILINE)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BLOCKQUOTE = re.compile(r"^>\s.*$", re.MULTILINE)
_FOOTER_RULE = re.compile(r"^---\s*$", re.MULTILINE)

_KNOWN_STYLE_PROFILES = {"polymer-default", "polymer-paper"}


def parse_spec(text: str) -> dict:
    data = yaml.safe_load(text)
    if data is None:
        return {"panels": []}
    if not isinstance(data, dict):
        return {"panels": []}
    panels = data.get("panels", [])
    if not isinstance(panels, list):
        panels = []
    else:
        panels = [p for p in panels if isinstance(p, dict)]
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
