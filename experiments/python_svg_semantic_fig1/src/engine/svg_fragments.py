from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Mapping


_ID_RE = re.compile(r"""id=(['"])([^'"]+)\1""")
_SVG_OPEN_RE = re.compile(r"^\s*(?:<\?xml[^>]*>\s*)?(?:<!DOCTYPE[^>]*>\s*)?(?:<!--.*?-->\s*)?<svg\b[^>]*>", re.DOTALL)


@dataclass(frozen=True)
class SvgFragment:
    inner_svg: str
    view_box: str
    width: float
    height: float
    subrenderer: str
    role: str


def strip_outer_svg(svg_text: str) -> str:
    text = _SVG_OPEN_RE.sub("", svg_text.strip(), count=1)
    return re.sub(r"</svg>\s*$", "", text, count=1).strip()


def prefix_svg_ids(svg_text: str, prefix: str) -> str:
    ids = [match.group(2) for match in _ID_RE.finditer(svg_text)]
    updated = svg_text
    for old_id in sorted(set(ids), key=len, reverse=True):
        new_id = f"{prefix}_{old_id}"
        updated = updated.replace(f'id="{old_id}"', f'id="{new_id}"')
        updated = updated.replace(f"id='{old_id}'", f"id='{new_id}'")
        updated = updated.replace(f"url(#{old_id})", f"url(#{new_id})")
        updated = updated.replace(f'href="#{old_id}"', f'href="#{new_id}"')
        updated = updated.replace(f"href='#{old_id}'", f"href='#{new_id}'")
        updated = updated.replace(f'xlink:href="#{old_id}"', f'xlink:href="#{new_id}"')
        updated = updated.replace(f"xlink:href='#{old_id}'", f"xlink:href='#{new_id}'")
    return updated


def wrapped_fragment_svg(fragment: SvgFragment, *, x: float, y: float, semantic_id: str, kind: str) -> str:
    return (
        f'<g data-semantic-id="{html.escape(semantic_id, quote=True)}" '
        f'data-semantic-kind="{html.escape(kind, quote=True)}" '
        f'data-subrenderer="{html.escape(fragment.subrenderer, quote=True)}" '
        f'data-fragment-role="{html.escape(fragment.role, quote=True)}">'
        f'<svg x="{x:.3f}" y="{y:.3f}" width="{fragment.width:.3f}" height="{fragment.height:.3f}" '
        f'viewBox="{html.escape(fragment.view_box, quote=True)}" overflow="visible">'
        f"{fragment.inner_svg}"
        "</svg></g>"
    )


def basic_svg_tag_counts(svg_text: str) -> Mapping[str, int]:
    return {
        "svg": svg_text.count("<svg"),
        "g": svg_text.count("<g"),
        "path": svg_text.count("<path"),
        "text": svg_text.count("<text"),
        "defs": svg_text.count("<defs"),
        "clipPath": svg_text.count("<clipPath"),
    }
