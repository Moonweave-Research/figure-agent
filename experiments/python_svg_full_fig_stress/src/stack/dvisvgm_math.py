from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import drawsvg as draw


_ID_RE = re.compile(r"id='([^']+)'|id=\"([^\"]+)\"")


def math_svg(
    latex_math: str,
    *,
    x: float,
    y: float,
    width: float,
    prefix: str,
    color: str = "#111111",
) -> draw.Raw:
    svg_text, natural_width, natural_height = _render_latex_to_svg(latex_math)
    svg_text = _prefix_ids(svg_text, prefix)
    svg_text = _sort_path_defs(svg_text)
    height = width * natural_height / natural_width
    inner = _strip_outer_svg(svg_text)
    return draw.Raw(
        f'<svg x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'viewBox="0 0 {natural_width:.3f} {natural_height:.3f}" overflow="visible">'
        f'<g fill="{color}" color="{color}">{inner}</g></svg>'
    )


def _render_latex_to_svg(latex_math: str) -> tuple[str, float, float]:
    with tempfile.TemporaryDirectory(prefix="python_svg_math_") as tmp:
        work = Path(tmp)
        tex_path = work / "math.tex"
        tex_path.write_text(
            "\\documentclass{standalone}\n"
            "\\usepackage{amsmath}\n"
            "\\begin{document}\n"
            f"${latex_math}$\n"
            "\\end{document}\n"
        )
        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-output-directory",
                str(work),
                str(tex_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        svg_path = work / "math.svg"
        subprocess.run(
            ["dvisvgm", "--pdf", str(work / "math.pdf"), "-n", "-o", str(svg_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        svg_text = svg_path.read_text()
    view_box_match = re.search(r"viewBox=['\"]0 0 ([0-9.]+) ([0-9.]+)['\"]", svg_text)
    if not view_box_match:
        raise RuntimeError("dvisvgm output did not include an expected viewBox")
    natural_width = float(view_box_match.group(1))
    natural_height = float(view_box_match.group(2))
    return svg_text, natural_width, natural_height


def _strip_outer_svg(svg_text: str) -> str:
    text = re.sub(r"^\s*<\?xml[^>]*>\s*", "", svg_text)
    text = re.sub(r"^\s*<!--.*?-->\s*", "", text, flags=re.DOTALL)
    text = re.sub(r"^<svg[^>]*>", "", text.strip(), count=1)
    return re.sub(r"</svg>\s*$", "", text)


def _prefix_ids(svg_text: str, prefix: str) -> str:
    ids = [match.group(1) or match.group(2) for match in _ID_RE.finditer(svg_text)]
    updated = svg_text
    for old_id in ids:
        new_id = f"{prefix}_{old_id}"
        updated = updated.replace(f"id='{old_id}'", f"id='{new_id}'")
        updated = updated.replace(f'id="{old_id}"', f'id="{new_id}"')
        updated = updated.replace(f"#{old_id}'", f"#{new_id}'")
        updated = updated.replace(f'#{old_id}"', f'#{new_id}"')
    return updated


def _sort_path_defs(svg_text: str) -> str:
    def replace_defs(match: re.Match[str]) -> str:
        content = match.group(1)
        paths = re.findall(r"<path\b[^>]*/>", content)
        if not paths:
            return match.group(0)
        return "<defs>\n" + "\n".join(sorted(paths)) + "\n</defs>"

    return re.sub(r"<defs>\s*(.*?)\s*</defs>", replace_defs, svg_text, flags=re.DOTALL)
