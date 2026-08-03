# Fig1 Electrical Style Adapter v28 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-only Fig1 electrical plot style adapter so Matplotlib-generated evidence plots look less pasted-in and closer to the existing Fig1 schematic grammar.

**Architecture:** Keep `drawsvg` as final compositor and keep v27 fragment import utilities. Add a typed Matplotlib style object with a conservative Fig1 preset, then generate `/tmp` preview artifacts comparing raw v27 Matplotlib fragments with v28 Fig1-adapted fragments. Do not integrate these fragments into `render_fig1_l1.py` until human visual review accepts the direction.

**Tech Stack:** Python 3.12, drawsvg, matplotlib, numpy, existing Fig1 domain payloads, existing v27 SVG fragment utilities.

---

## Non-Negotiable Constraints

- Do not modify, stage, revert, or commit:
  - `experiments/python_svg_semantic_fig1/src/fig1_scene.py`
  - `experiments/python_svg_semantic_fig1/src/semantic_scene.py`
- Do not stage `.claude/`.
- Do not update `verify_fig1_baseline_hash.py`.
- Do not modify `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` in this pass.
- Do not add a new hard gate.
- Do not add RDKit to canonical rendering.
- Keep first-pass outputs in `/tmp`.

## File Structure

### Modify

- `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py`
  - Add `MatplotlibPlotStyle`.
  - Add `fig1_electrical_style()`.
  - Add optional `style` parameters to `pe_hysteresis_fragment()` and `power_law_decay_fragment()`.
  - Preserve existing default behavior when `style` is omitted.

- `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`
  - Add focused tests proving the Fig1 style adapter keeps text, suppresses numeric tick labels, preserves determinism, and does not change the default v27 path.

### Create

- `experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py`
  - Generate `/tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.svg`.
  - Generate `/tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.png`.
  - Compare raw v27 Matplotlib fragments against v28 Fig1-adapted fragments.

## Task 1: Add Fig1 Matplotlib Style Adapter

**Files:**
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`
- Modify: `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py`

- [ ] **Step 1: Write failing tests for the style adapter**

Add this test class to `test_fig1_library_subrenderers.py`:

```python
class MatplotlibStyleAdapterTests(unittest.TestCase):
    def test_fig1_electrical_style_suppresses_numeric_tick_labels(self) -> None:
        from engine.matplotlib_subrenderers import fig1_electrical_style, pe_hysteresis_fragment

        payload = PEHysteresisPlot(
            title="P-E response",
            model="schematic",
            loop_width=128,
            loop_height=86,
            remanence=0.28,
            samples_per_branch=48,
            color="#a81016",
        )

        fragment = pe_hysteresis_fragment(payload, width=168, height=108, style=fig1_electrical_style())

        self.assertIn(">P<", fragment.inner_svg)
        self.assertIn(">E<", fragment.inner_svg)
        self.assertNotIn(">0.0<", fragment.inner_svg)
        self.assertNotIn(">1.0<", fragment.inner_svg)
        self.assertNotIn("−1.0", fragment.inner_svg)

    def test_fig1_decay_style_keeps_semantic_labels(self) -> None:
        from engine.matplotlib_subrenderers import fig1_electrical_style, power_law_decay_fragment

        payload = PowerLawDecayPlot(
            title="Current decay",
            model="power_law",
            slope=-0.72,
            log_t_min=-3,
            log_t_max=3,
            log_i_top=0,
            log_i_bottom=-8,
            samples=64,
            label="extract n",
            color="#0b4bb3",
        )

        fragment = power_law_decay_fragment(payload, width=168, height=108, style=fig1_electrical_style())

        self.assertIn("log t", fragment.inner_svg)
        self.assertIn("log I", fragment.inner_svg)
        self.assertIn("extract n", fragment.inner_svg)
        self.assertNotIn(">0<", fragment.inner_svg)
        self.assertNotIn(">2<", fragment.inner_svg)

    def test_fig1_style_fragments_are_deterministic(self) -> None:
        from engine.matplotlib_subrenderers import fig1_electrical_style, pe_hysteresis_fragment

        payload = PEHysteresisPlot(
            title="P-E response",
            model="schematic",
            loop_width=128,
            loop_height=86,
            remanence=0.28,
            samples_per_branch=48,
            color="#a81016",
        )
        style = fig1_electrical_style()

        first = pe_hysteresis_fragment(payload, width=168, height=108, style=style).inner_svg
        second = pe_hysteresis_fragment(payload, width=168, height=108, style=style).inner_svg

        self.assertEqual(hashlib.sha256(first.encode()).hexdigest(), hashlib.sha256(second.encode()).hexdigest())
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
```

Expected: FAIL with import/signature errors because `fig1_electrical_style` and `style=` do not exist yet.

- [ ] **Step 3: Implement minimal style adapter**

In `engine/matplotlib_subrenderers.py`, add:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class MatplotlibPlotStyle:
    font_size: float
    tick_label_size: float
    line_width: float
    axis_width: float
    tick_width: float
    tick_length: float
    grid_line_width: float
    grid_alpha: float
    show_numeric_tick_labels: bool
    show_grid: bool
    axis_color: str
    grid_color: str
    annotation_color: str
    label_pad: float
    pe_label: str
    decay_slope_label: str


def fig1_electrical_style() -> MatplotlibPlotStyle:
    return MatplotlibPlotStyle(
        font_size=6.8,
        tick_label_size=5.6,
        line_width=1.65,
        axis_width=0.72,
        tick_width=0.55,
        tick_length=2.1,
        grid_line_width=0.28,
        grid_alpha=0.20,
        show_numeric_tick_labels=False,
        show_grid=True,
        axis_color="#1f2933",
        grid_color="#d7dde6",
        annotation_color="#5b6470",
        label_pad=0.8,
        pe_label="P-E loop",
        decay_slope_label="slope -n",
    )
```

Then:

- Change `pe_hysteresis_fragment(payload, *, width, height)` to accept `style: MatplotlibPlotStyle | None = None`.
- Change `power_law_decay_fragment(payload, *, width, height)` to accept `style: MatplotlibPlotStyle | None = None`.
- Use `plot_style = style or _default_plot_style()`.
- Update `_rc_params(plot_style)`.
- Update `_style_small_axes(ax, plot_style)`.
- If `plot_style.show_numeric_tick_labels` is false, call:

```python
ax.tick_params(labelbottom=False, labelleft=False)
```

- [ ] **Step 4: Run tests and verify pass**

Run the same unittest command. Expected: PASS.

## Task 2: Add v28 Electrical Style Adapter Preview

**Files:**
- Create: `experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py`
- Modify: `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py`

- [ ] **Step 1: Add failing import smoke test**

Add:

```python
class ElectricalStyleAdapterPreviewTests(unittest.TestCase):
    def test_electrical_style_adapter_preview_is_importable(self) -> None:
        import preview_fig1_electrical_style_adapter as preview

        self.assertTrue(str(preview.OUT_DIR).endswith("fig1_v28_electrical_style_adapter"))
        self.assertTrue(callable(preview.build_preview_svg))
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'preview_fig1_electrical_style_adapter'`.

- [ ] **Step 3: Implement preview script**

Create `preview_fig1_electrical_style_adapter.py` with:

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import drawsvg as draw

from engine.domain_primitives import PEHysteresisPlot, PowerLawDecayPlot
from engine.matplotlib_subrenderers import fig1_electrical_style, pe_hysteresis_fragment, power_law_decay_fragment
from engine.svg_fragments import wrapped_fragment_svg


OUT_DIR = Path("/tmp/fig1_v28_electrical_style_adapter")
SVG_OUT = OUT_DIR / "electrical_style_adapter_preview.svg"
PNG_OUT = OUT_DIR / "electrical_style_adapter_preview.png"


def _payloads() -> tuple[PEHysteresisPlot, PowerLawDecayPlot]:
    pe = PEHysteresisPlot(
        title="P-E hysteresis",
        model="parametric_hysteresis",
        loop_width=145.0,
        loop_height=82.0,
        remanence=0.42,
        samples_per_branch=48,
        color="#b20f16",
    )
    decay = PowerLawDecayPlot(
        title="I(t) proportional t^-n",
        model="power_law_loglog",
        slope=-0.72,
        log_t_min=-3.0,
        log_t_max=3.0,
        log_i_top=0.0,
        log_i_bottom=-8.0,
        samples=56,
        label="I(t) ~ t^-n",
        color="#0b4bb3",
        causal_role="experiment_current_decay_to_power_law_exponent",
        extracted_parameter="n",
    )
    return pe, decay


def _panel(drawing: draw.Drawing, x: float, y: float, title: str) -> None:
    drawing.append(draw.Rectangle(x, y, 335, 245, rx=7, ry=7, fill="#ffffff", stroke="#cfd6df", stroke_width=1.0))
    drawing.append(draw.Text(title, 13, x + 16, y + 28, fill="#1f2933", font_family="Arial", font_weight="bold"))


def build_preview_svg() -> str:
    pe, decay = _payloads()
    drawing = draw.Drawing(1080, 330)
    drawing.append(draw.Rectangle(0, 0, 1080, 330, fill="#f6f8fb"))
    drawing.append(draw.Text("v28 electrical style adapter preview", 18, 28, 32, fill="#182032", font_family="Arial"))

    _panel(drawing, 28, 62, "v27 raw Matplotlib")
    _panel(drawing, 382, 62, "v28 Fig1-adapted")
    _panel(drawing, 736, 62, "v28 compact panel-scale")

    raw_pe = pe_hysteresis_fragment(pe, width=142, height=100)
    raw_decay = power_law_decay_fragment(decay, width=142, height=100)
    style = fig1_electrical_style()
    adapted_pe = pe_hysteresis_fragment(pe, width=142, height=100, style=style)
    adapted_decay = power_law_decay_fragment(decay, width=142, height=100, style=style)
    compact_pe = pe_hysteresis_fragment(pe, width=126, height=88, style=style)
    compact_decay = power_law_decay_fragment(decay, width=126, height=88, style=style)

    drawing.append(draw.Raw(wrapped_fragment_svg(raw_pe, x=48, y=118, semantic_id="preview_raw_pe", kind="PEHysteresisPlot")))
    drawing.append(draw.Raw(wrapped_fragment_svg(raw_decay, x=198, y=118, semantic_id="preview_raw_decay", kind="PowerLawDecayPlot")))
    drawing.append(draw.Raw(wrapped_fragment_svg(adapted_pe, x=402, y=118, semantic_id="preview_adapted_pe", kind="PEHysteresisPlot")))
    drawing.append(draw.Raw(wrapped_fragment_svg(adapted_decay, x=552, y=118, semantic_id="preview_adapted_decay", kind="PowerLawDecayPlot")))
    drawing.append(draw.Raw(wrapped_fragment_svg(compact_pe, x=774, y=124, semantic_id="preview_compact_pe", kind="PEHysteresisPlot")))
    drawing.append(draw.Raw(wrapped_fragment_svg(compact_decay, x=908, y=124, semantic_id="preview_compact_decay", kind="PowerLawDecayPlot")))

    drawing.append(draw.Text("criterion: fewer pasted-in numeric ticks, preserved semantic labels, lighter grid", 11, 398, 282, fill="#5b6470", font_family="Arial"))
    return drawing.as_svg()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text(build_preview_svg(), encoding="utf-8")
    converter = shutil.which("rsvg-convert")
    if converter:
        subprocess.run([converter, "-w", "2160", "-h", "660", str(SVG_OUT), "-o", str(PNG_OUT)], check=True)
    print(f"wrote {SVG_OUT}")
    if PNG_OUT.exists():
        print(f"wrote {PNG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests and preview**

Run:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
uv run --with drawsvg --with matplotlib --with numpy python experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py
python -m xml.etree.ElementTree /tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.svg
```

Expected: tests pass, SVG/PNG are written, XML parse exits 0.

## Verification Matrix

Run after Tasks 1-2:

```bash
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg python -m unittest test_fig1_svg_fragments -v
PYTHONPATH=experiments/python_svg_semantic_fig1/src uv run --with drawsvg --with matplotlib --with numpy --with rdkit python -m unittest test_fig1_library_subrenderers -v
uv run --with drawsvg --with matplotlib --with numpy python experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py
python -m xml.etree.ElementTree /tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.svg
python -m py_compile experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py
git status --short --branch
```

## Stop Criteria

Stop after preview generation. Do not integrate into canonical Fig1 until the user visually reviews:

- `/tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.png`
- `/tmp/fig1_v28_electrical_style_adapter/electrical_style_adapter_preview.svg`

## Self-Review

- Spec coverage: v28 focuses only on electrical foundation, as agreed.
- Scope: No canonical render integration and no baseline hash update.
- Dependency risk: Matplotlib/numpy only; RDKit remains in tests because v27 tests use it, but v28 preview does not require RDKit.
- Existing architecture: v27 fragment utilities remain the bridge, drawsvg remains compositor.
- Known dirty files: legacy dirty files are not part of the edit set.
