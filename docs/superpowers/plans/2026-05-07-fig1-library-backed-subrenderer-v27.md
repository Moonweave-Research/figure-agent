# Fig1 Library-Backed Subrenderer v27 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether Fig1 visual quality improves by using domain libraries for the parts they are good at, without replacing the existing semantic scene, scaffold contract, drawsvg compositor, or hard gates.

**Architecture:** Keep `drawsvg` as the canonical final compositor and semantic metadata carrier. Add a small SVG-fragment layer that can import library-generated SVG fragments into controlled scaffold boxes, then run two bounded spikes: Matplotlib for electrical plots and RDKit for the sulfur origin glyph. Do not integrate either fragment into the tracked canonical Fig1 SVG until preview evidence and human review say it is better.

**Tech Stack:** Python 3.12, drawsvg, matplotlib, numpy, RDKit, svgutils-style SVG fragment handling, existing Fig1 semantic scene/gates.

---

## Non-Negotiable Constraints

- Do not modify, stage, revert, or commit:
  - `experiments/python_svg_semantic_fig1/src/fig1_scene.py`
  - `experiments/python_svg_semantic_fig1/src/semantic_scene.py`
- Do not stage `.claude/`.
- Do not update the baseline hash until the user visually accepts a canonical rendered SVG.
- Do not add a new hard gate in v27.
- Do not replace `drawsvg` as the final compositor.
- Do not pixel-trace the reference PNG.
- Keep semantic payloads and scaffold local boxes as the source of truth.
- Keep all first-pass library outputs in `/tmp` until review.
- If canonical integration would require new runtime deps in normal gates, surface that explicitly before editing gate dependency lists.

## File Structure

### Create

- `experiments/python_svg_semantic_fig1/src/engine/svg_fragments.py`
  - Owns deterministic SVG fragment cleanup: strip outer `<svg>`, prefix ids, wrap fragment in semantic/subrenderer metadata, count basic SVG tags for tests.

- `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py`
  - Owns Matplotlib-generated electrical plot fragments for `PEHysteresisPlot` and `PowerLawDecayPlot`.
  - Must set `svg.fonttype = "none"` so labels remain SVG `<text>` where possible.

- `experiments/python_svg_semantic_fig1/src/engine/rdkit_subrenderers.py`
  - Owns RDKit-generated sulfur molecule fragments.
  - Must tolerate RDKit path-only atom labels by wrapping output with semantic metadata.

- `experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py`
  - Generates `/tmp/fig1_v27_library_subrenderers/` preview SVG/PNG artifacts only.
  - Does not modify `fig1_reference_semantic.svg`.

- `experiments/python_svg_semantic_fig1/src/test_fig1_svg_fragments.py`
  - Unit tests for fragment cleanup, id prefixing, metadata wrapping, and bbox visibility.

- `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`
  - Unit tests for Matplotlib/RDKit fragment generation, determinism, and text/metadata preservation.

### Modify Only If Preview Is Accepted Later

- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
  - Possible future canonical integration point for electrical panel internals and/or origin molecule glyph.
  - Do not touch during the first spike unless the user approves integration after preview.

- `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py`
  - Possible future dependency-list update if canonical renderer imports RDKit.
  - Do not touch during the first spike.

---

## Task 1: Add SVG Fragment Utilities

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/engine/svg_fragments.py`
- Test: `experiments/python_svg_semantic_fig1/src/test_fig1_svg_fragments.py`

- [ ] **Step 1: Write failing tests for fragment cleanup and metadata wrapping**

Create `experiments/python_svg_semantic_fig1/src/test_fig1_svg_fragments.py`:

```python
from __future__ import annotations

import unittest

from engine.svg_fragments import (
    SvgFragment,
    basic_svg_tag_counts,
    prefix_svg_ids,
    strip_outer_svg,
    wrapped_fragment_svg,
)


class SvgFragmentTests(unittest.TestCase):
    def test_strip_outer_svg_keeps_inner_content(self) -> None:
        source = '<?xml version="1.0"?><svg width="10" height="10" viewBox="0 0 10 10"><defs><path id="p"/></defs><g><text>A</text></g></svg>'

        inner = strip_outer_svg(source)

        self.assertIn("<defs>", inner)
        self.assertIn("<text>A</text>", inner)
        self.assertNotIn("<svg", inner)
        self.assertNotIn("</svg>", inner)

    def test_prefix_svg_ids_updates_references(self) -> None:
        source = '<defs><clipPath id="clip"><path id="path_a"/></clipPath></defs><g clip-path="url(#clip)"><use href="#path_a"/></g>'

        prefixed = prefix_svg_ids(source, "fig1_test")

        self.assertIn('id="fig1_test_clip"', prefixed)
        self.assertIn('id="fig1_test_path_a"', prefixed)
        self.assertIn("url(#fig1_test_clip)", prefixed)
        self.assertIn('href="#fig1_test_path_a"', prefixed)
        self.assertNotIn('id="clip"', prefixed)

    def test_wrapped_fragment_exposes_semantic_metadata(self) -> None:
        fragment = SvgFragment(
            inner_svg='<text x="1" y="2">P-E</text>',
            view_box="0 0 100 50",
            width=100,
            height=50,
            subrenderer="matplotlib",
            role="electrical-pe-plot",
        )

        wrapped = wrapped_fragment_svg(fragment, x=10, y=20, semantic_id="pe_hysteresis", kind="PEHysteresisPlot")

        self.assertIn('data-semantic-id="pe_hysteresis"', wrapped)
        self.assertIn('data-semantic-kind="PEHysteresisPlot"', wrapped)
        self.assertIn('data-subrenderer="matplotlib"', wrapped)
        self.assertIn('data-fragment-role="electrical-pe-plot"', wrapped)
        self.assertIn('<svg x="10.000" y="20.000"', wrapped)
        self.assertIn("<text", wrapped)

    def test_basic_svg_tag_counts_counts_core_tags(self) -> None:
        counts = basic_svg_tag_counts('<svg><path/><path/><text>A</text><g><clipPath/></g></svg>')

        self.assertEqual(counts["path"], 2)
        self.assertEqual(counts["text"], 1)
        self.assertEqual(counts["clipPath"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg python -m unittest test_fig1_svg_fragments -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.svg_fragments'`.

- [ ] **Step 3: Implement fragment utilities**

Create `experiments/python_svg_semantic_fig1/src/engine/svg_fragments.py`:

```python
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Mapping


_ID_RE = re.compile(r"""id=(['"])([^'"]+)\1""")
_SVG_OPEN_RE = re.compile(r"^\s*(?:<\?xml[^>]*>\s*)?(?:<!--.*?-->\s*)?<svg\b[^>]*>", re.DOTALL)


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
        updated = updated.replace(f"xlink:href=\"#{old_id}\"", f"xlink:href=\"#{new_id}\"")
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
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg python -m unittest test_fig1_svg_fragments -v
```

Expected: PASS.

---

## Task 2: Add Matplotlib Electrical Fragment Generator

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py`
- Test: `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`

- [ ] **Step 1: Write failing tests for text preservation and determinism**

Create the Matplotlib section of `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`:

```python
from __future__ import annotations

import hashlib
import unittest

from engine.domain_primitives import PEHysteresisPlot, PowerLawDecayPlot


class MatplotlibSubrendererTests(unittest.TestCase):
    def test_pe_fragment_preserves_svg_text(self) -> None:
        from engine.matplotlib_subrenderers import pe_hysteresis_fragment

        payload = PEHysteresisPlot(title="P-E response", model="schematic", loop_width=128, loop_height=86, remanence=0.28, samples_per_branch=48, color="#a81016")

        fragment = pe_hysteresis_fragment(payload, width=180, height=120)

        self.assertEqual(fragment.subrenderer, "matplotlib")
        self.assertEqual(fragment.role, "electrical-pe-plot")
        self.assertIn("<text", fragment.inner_svg)
        self.assertIn(">P<", fragment.inner_svg)
        self.assertIn(">E<", fragment.inner_svg)
        self.assertIn("<path", fragment.inner_svg)

    def test_decay_fragment_preserves_log_labels(self) -> None:
        from engine.matplotlib_subrenderers import power_law_decay_fragment

        payload = PowerLawDecayPlot(title="Current decay", model="power_law", slope=-0.72, log_t_min=-3, log_t_max=3, log_i_top=0, log_i_bottom=-8, samples=64, label="extract n", color="#a81016")

        fragment = power_law_decay_fragment(payload, width=180, height=120)

        self.assertEqual(fragment.subrenderer, "matplotlib")
        self.assertEqual(fragment.role, "electrical-decay-plot")
        self.assertIn("<text", fragment.inner_svg)
        self.assertIn("log t", fragment.inner_svg)
        self.assertIn("log I", fragment.inner_svg)
        self.assertIn("<path", fragment.inner_svg)

    def test_matplotlib_fragments_are_deterministic(self) -> None:
        from engine.matplotlib_subrenderers import pe_hysteresis_fragment

        payload = PEHysteresisPlot(title="P-E response", model="schematic", loop_width=128, loop_height=86, remanence=0.28, samples_per_branch=48, color="#a81016")

        first = pe_hysteresis_fragment(payload, width=180, height=120).inner_svg
        second = pe_hysteresis_fragment(payload, width=180, height=120).inner_svg

        self.assertEqual(hashlib.sha256(first.encode()).hexdigest(), hashlib.sha256(second.encode()).hexdigest())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy python -m unittest test_fig1_library_subrenderers -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.matplotlib_subrenderers'`.

- [ ] **Step 3: Implement Matplotlib fragment generator**

Create `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py`:

```python
from __future__ import annotations

import io
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from engine.domain_primitives import PEHysteresisPlot, PowerLawDecayPlot
from engine.svg_fragments import SvgFragment, prefix_svg_ids, strip_outer_svg


_VIEWBOX_RE = re.compile(r"""viewBox=["']([^"']+)["']""")


def pe_hysteresis_fragment(payload: PEHysteresisPlot, *, width: float, height: float) -> SvgFragment:
    with mpl.rc_context(_rc_params()):
        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        field, polarization = _pe_points(payload)
        ax.plot(field, polarization, color=payload.color, lw=1.8)
        ax.axhline(0, color="#5b6470", lw=0.7, alpha=0.55)
        ax.axvline(0, color="#5b6470", lw=0.7, alpha=0.55)
        ax.set_xlabel("E", labelpad=1)
        ax.set_ylabel("P", labelpad=1, rotation=0)
        ax.yaxis.set_label_coords(-0.10, 0.92)
        ax.text(0.63, 0.78, "P-E loop", transform=ax.transAxes, color=payload.color, fontsize=7)
        _style_small_axes(ax)
        return _fragment_from_figure(fig, width=width, height=height, role="electrical-pe-plot", prefix="fig1_pe")


def power_law_decay_fragment(payload: PowerLawDecayPlot, *, width: float, height: float) -> SvgFragment:
    with mpl.rc_context(_rc_params()):
        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        log_t = np.linspace(payload.log_t_min, payload.log_t_max, max(2, payload.samples))
        log_i_start = payload.log_i_top - 0.34
        log_i = np.clip(log_i_start + payload.slope * (log_t - payload.log_t_min), payload.log_i_bottom, payload.log_i_top)
        ax.plot(log_t, log_i, color=payload.color, lw=1.8)
        ax.set_xlabel("log t", labelpad=1)
        ax.set_ylabel("log I", labelpad=1, rotation=0)
        ax.yaxis.set_label_coords(-0.14, 0.92)
        ax.text(0.56, 0.68, payload.label, transform=ax.transAxes, color=payload.color, fontsize=7)
        ax.text(0.62, 0.44, "slope -n", transform=ax.transAxes, color="#5b6470", fontsize=6.5)
        _style_small_axes(ax)
        return _fragment_from_figure(fig, width=width, height=height, role="electrical-decay-plot", prefix="fig1_decay")


def _pe_points(payload: PEHysteresisPlot) -> tuple[np.ndarray, np.ndarray]:
    samples = max(24, payload.samples_per_branch)
    coercive = max(0.12, min(0.43, payload.remanence * 0.62))
    saturation = 0.94
    forward = np.linspace(-1.0, 1.0, samples)
    reverse = np.linspace(1.0, -1.0, samples)
    p_forward = saturation * np.tanh(2.85 * (forward + coercive))
    p_reverse = saturation * np.tanh(2.85 * (reverse - coercive))
    return np.concatenate([forward, reverse]), np.concatenate([p_forward, p_reverse])


def _rc_params() -> dict[str, object]:
    return {
        "svg.fonttype": "none",
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.linewidth": 0.7,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.4,
        "ytick.major.size": 2.4,
    }


def _style_small_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=6, pad=1)
    ax.grid(True, color="#d7dde6", lw=0.35, alpha=0.55)
    ax.margins(x=0.04, y=0.08)


def _fragment_from_figure(fig: plt.Figure, *, width: float, height: float, role: str, prefix: str) -> SvgFragment:
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", bbox_inches="tight", pad_inches=0.015, metadata={"Date": None})
    plt.close(fig)
    svg = buffer.getvalue()
    view_box = _view_box(svg)
    inner = prefix_svg_ids(strip_outer_svg(svg), prefix)
    return SvgFragment(inner_svg=inner, view_box=view_box, width=width, height=height, subrenderer="matplotlib", role=role)


def _view_box(svg_text: str) -> str:
    match = _VIEWBOX_RE.search(svg_text)
    if not match:
        raise RuntimeError("Matplotlib SVG did not include viewBox")
    return match.group(1)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy python -m unittest test_fig1_library_subrenderers -v
```

Expected: PASS for Matplotlib tests.

---

## Task 3: Add RDKit Sulfur Fragment Generator

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/engine/rdkit_subrenderers.py`
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`

- [ ] **Step 1: Add failing RDKit tests**

Append to `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`:

```python

class RdkitSubrendererTests(unittest.TestCase):
    def test_s8_fragment_generates_svg_paths(self) -> None:
        from engine.rdkit_subrenderers import s8_ring_fragment

        fragment = s8_ring_fragment(width=130, height=110)

        self.assertEqual(fragment.subrenderer, "rdkit")
        self.assertEqual(fragment.role, "origin-s8-ring")
        self.assertIn("<path", fragment.inner_svg)
        self.assertGreaterEqual(fragment.inner_svg.count("<path"), 8)

    def test_s8_fragment_is_deterministic(self) -> None:
        from engine.rdkit_subrenderers import s8_ring_fragment

        first = s8_ring_fragment(width=130, height=110).inner_svg
        second = s8_ring_fragment(width=130, height=110).inner_svg

        self.assertEqual(hashlib.sha256(first.encode()).hexdigest(), hashlib.sha256(second.encode()).hexdigest())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.rdkit_subrenderers'`.

- [ ] **Step 3: Implement RDKit fragment generator**

Create `experiments/python_svg_semantic_fig1/src/engine/rdkit_subrenderers.py`:

```python
from __future__ import annotations

import re

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from engine.svg_fragments import SvgFragment, prefix_svg_ids, strip_outer_svg


_VIEWBOX_RE = re.compile(r"""viewBox=["']([^"']+)["']""")


def s8_ring_fragment(*, width: float, height: float) -> SvgFragment:
    mol = Chem.MolFromSmiles("S1SSSSSSS1")
    if mol is None:
        raise RuntimeError("RDKit failed to parse S8 ring SMILES")
    AllChem.Compute2DCoords(mol)
    drawer = rdMolDraw2D.MolDraw2DSVG(int(width), int(height))
    options = drawer.drawOptions()
    options.clearBackground = False
    options.bondLineWidth = 1.6
    options.fixedFontSize = 13
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend="")
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    view_box = _view_box(svg)
    inner = prefix_svg_ids(strip_outer_svg(svg), "fig1_rdkit_s8")
    return SvgFragment(inner_svg=inner, view_box=view_box, width=width, height=height, subrenderer="rdkit", role="origin-s8-ring")


def _view_box(svg_text: str) -> str:
    match = _VIEWBOX_RE.search(svg_text)
    if not match:
        return "0 0 100 100"
    return match.group(1)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
```

Expected: PASS.

---

## Task 4: Add `/tmp` Preview Script Without Touching Canonical Fig1

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py`
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`

- [ ] **Step 1: Add preview script smoke test**

Append to `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`:

```python

class LibraryPreviewScriptTests(unittest.TestCase):
    def test_preview_script_is_importable(self) -> None:
        import preview_fig1_library_subrenderers as preview

        self.assertTrue(str(preview.OUT_DIR).endswith("fig1_v27_library_subrenderers"))
        self.assertTrue(callable(preview.build_preview_svg))
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'preview_fig1_library_subrenderers'`.

- [ ] **Step 3: Implement preview script**

Create `experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py`:

```python
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import drawsvg as draw

from engine.domain_primitives import PEHysteresisPlot, PowerLawDecayPlot
from engine.matplotlib_subrenderers import pe_hysteresis_fragment, power_law_decay_fragment
from engine.rdkit_subrenderers import s8_ring_fragment
from engine.svg_fragments import wrapped_fragment_svg


OUT_DIR = Path("/tmp/fig1_v27_library_subrenderers")
SVG_OUT = OUT_DIR / "library_subrenderer_spike.svg"
PNG_OUT = OUT_DIR / "library_subrenderer_spike.png"


def build_preview_svg() -> str:
    drawing = draw.Drawing(760, 320)
    drawing.append(draw.Rectangle(0, 0, 760, 320, fill="#ffffff"))
    drawing.append(draw.Text("v27 library-backed subrenderer spike", 18, 28, 34, fill="#182032", font_family="Arial"))

    pe = PEHysteresisPlot(title="P-E response", model="schematic", loop_width=128, loop_height=86, remanence=0.28, samples_per_branch=48, color="#a81016")
    decay = PowerLawDecayPlot(title="Current decay", model="power_law", slope=-0.72, log_t_min=-3, log_t_max=3, log_i_top=0, log_i_bottom=-8, samples=64, label="extract n", color="#a81016")

    s8 = s8_ring_fragment(width=150, height=130)
    pe_fragment = pe_hysteresis_fragment(pe, width=210, height=145)
    decay_fragment = power_law_decay_fragment(decay, width=210, height=145)

    drawing.append(draw.Text("RDKit S8", 12, 70, 78, fill="#5b6470", font_family="Arial"))
    drawing.append(draw.Raw(wrapped_fragment_svg(s8, x=40, y=95, semantic_id="preview_s8_ring", kind="SulfurPolymerOrigin")))

    drawing.append(draw.Text("Matplotlib P-E", 12, 270, 78, fill="#5b6470", font_family="Arial"))
    drawing.append(draw.Raw(wrapped_fragment_svg(pe_fragment, x=240, y=92, semantic_id="preview_pe_hysteresis", kind="PEHysteresisPlot")))

    drawing.append(draw.Text("Matplotlib log decay", 12, 525, 78, fill="#5b6470", font_family="Arial"))
    drawing.append(draw.Raw(wrapped_fragment_svg(decay_fragment, x=500, y=92, semantic_id="preview_power_decay", kind="PowerLawDecayPlot")))

    return drawing.as_svg()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text(build_preview_svg())
    converter = shutil.which("rsvg-convert")
    if converter:
        subprocess.run([converter, "-w", "1520", "-h", "640", str(SVG_OUT), "-o", str(PNG_OUT)], check=True)
    print(f"wrote {SVG_OUT}")
    if PNG_OUT.exists():
        print(f"wrote {PNG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run preview script**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with rdkit python experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py
```

Expected:

```text
wrote /tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.svg
wrote /tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.png
```

- [ ] **Step 5: Visually inspect preview**

Run:

```bash
open /tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.png
```

Expected: a side-by-side preview containing RDKit S8, Matplotlib P-E plot, and Matplotlib log-decay plot.

---

## Task 5: Compare Library Fragments Against Current Panel Crops

**Files:**
- Create: `/tmp/fig1_v27_library_subrenderers/README.md`
- No tracked source changes.

- [ ] **Step 1: Generate current canonical Fig1 render**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
```

Expected: render succeeds and updates current dirty preview artifacts.

- [ ] **Step 2: Generate library preview**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with rdkit python experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py
```

Expected: `/tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.png` exists.

- [ ] **Step 3: Record comparison notes in `/tmp`**

Create `/tmp/fig1_v27_library_subrenderers/README.md` with this exact structure:

```markdown
# Fig1 v27 Library Subrenderer Spike Notes

## Matplotlib Electrical Fragment

- Better than current drawsvg plot:
- Worse than current drawsvg plot:
- Integration risk:
- Verdict: accept / reject / revise

## RDKit Origin Fragment

- Better than current drawsvg molecule:
- Worse than current drawsvg molecule:
- Integration risk:
- Verdict: accept / reject / revise

## Dependency Decision

- Matplotlib is already in the current Fig1 gate uv command.
- RDKit is not in the current Fig1 gate uv command.
- If RDKit is accepted for canonical rendering, update gate dependency handling in a separate explicit commit.
```

- [ ] **Step 4: Stop for human review**

Send the user:

```text
v27 library spike preview is ready:
- /tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.png
- /tmp/fig1_v27_library_subrenderers/library_subrenderer_spike.svg

No canonical Fig1 SVG integration has been made yet. Please review whether Matplotlib electrical plots and RDKit S8 are visually better than the current drawsvg versions.
```

---

## Task 6: Optional Canonical Integration Only After User Accepts Preview

**Files:**
- Modify: `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py`
- Modify only if RDKit is accepted: `experiments/python_svg_semantic_fig1/src/verify_fig1_render_parity.py`
- Modify only if RDKit is accepted: docs/manifest files that list runtime dependencies
- Test: existing Fig1 tests and gates.

- [ ] **Step 1: Integrate Matplotlib electrical fragments first**

Replace only the internals of `_draw_pe_hysteresis` and `_draw_power_law_decay` with wrapped Matplotlib fragments. Preserve:

- the same semantic object ids
- the same `p.begin_semantic_group` / `p.end_semantic_group` semantic envelope or equivalent wrapper
- causal role metadata that current semantic/causal verifiers need
- existing panel bounds and scaffold boxes

Implementation rule:

```python
from engine.matplotlib_subrenderers import pe_hysteresis_fragment, power_law_decay_fragment
from engine.svg_fragments import wrapped_fragment_svg
```

Use the current `_evidence_badge_rect(scene, obj.id).inset(4, 16)` as the fragment placement box.

- [ ] **Step 2: Run focused tests**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy python -m unittest test_fig1_library_subrenderers test_fig1_render_parity -v
```

Expected: PASS except baseline hash is not part of this command.

- [ ] **Step 3: Render and visually inspect**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
open experiments/python_svg_semantic_fig1/fig1_reference_semantic.png
```

Expected: electrical panel looks more plot-like, labels do not collide, and whole figure still reads as Fig1.

- [ ] **Step 4: Run gates, expect only baseline hash failure until accepted**

Run:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
```

Expected: all gates pass except `baseline-hash`, unless the user has already accepted and hash has been updated.

- [ ] **Step 5: Stop for visual acceptance**

Do not update `verify_fig1_baseline_hash.py` until the user accepts the new canonical render.

---

## Verification Matrix

Run after Tasks 1-4:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg python -m unittest test_fig1_svg_fragments -v
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
uv run --with drawsvg --with matplotlib --with numpy --with rdkit python experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py
python -m py_compile experiments/python_svg_semantic_fig1/src/engine/svg_fragments.py experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py experiments/python_svg_semantic_fig1/src/engine/rdkit_subrenderers.py experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py
git status --short --branch
```

Run only after canonical integration is approved:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
git status --short --branch
```

If RDKit becomes part of canonical rendering, update every canonical render/gate command that imports `render_fig1_l1.py` to include `--with rdkit`, or add RDKit as a declared project dependency in a separate explicit dependency decision.

---

## Stop / Continue Criteria

### Continue to canonical integration if:

- Matplotlib plot fragments look clearly more credible than the current electrical panel.
- Labels remain legible and do not collide.
- SVG text is preserved or metadata shims keep the visual report useful.
- Fragment insertion does not break semantic group bboxes.

### Reject or revise the library path if:

- Matplotlib output feels pasted-in or stylistically inconsistent with the rest of Fig1.
- RDKit molecule depiction is chemically cleaner but visually too dense or too foreign to the panel.
- Fragment SVG adds too much nondeterministic noise.
- Existing visual report/bbox logic cannot reason about imported fragments without a large parser rewrite.

### Do not proceed if:

- Canonical gates would require a broad dependency/governance rewrite.
- The preview does not improve the actual figure when viewed, even if the code is cleaner.
- The change only improves implementation elegance but not visual quality.

---

## Self-Review

- Spec coverage: The plan checks the user's concern that we are hand-drawing too much by testing Matplotlib and RDKit as bounded subrenderers.
- Scope: First-pass output is `/tmp` only. Canonical Fig1 integration is explicitly gated by human review.
- Dependency risk: RDKit is isolated from normal gates until accepted. Matplotlib is lower risk because the current render path already uses Matplotlib/Numpy in verification commands.
- Existing architecture: Semantic payload, scaffold contract, drawsvg compositor, render parity, and baseline hash remain intact.
- Known dirty files: Legacy dirty files are excluded from planned edits.
- No new hard gate: v27 adds tests and preview artifacts only.
