# Architecture v0.4 — Build Perception Pack

**Status:** REJECTED (2026-05-08, escalated from REVISION_NEEDED).
v0.4.1 was authored to fix v0.4's 6 BLOCKING issues, then dual-reviewed (Codex + Gemini, `docs/trials/2026-05-08-perception-spec-review-v041-{codex,gemini}.md`). Both reviewers verdicted "needs further revision" — v0.4.1 left 6 BLOCKING issues unresolved (T-junction FP, path reconstruction underspec, probe baseline non-reproducible, coordinate math wrong by ~1.5%, intent enum incomplete, dependency policy contradictory). Three rounds of advisor + dual review converged on the same meta-pattern: topology auto-detection cannot be reduced to invariant PDF geometry — segmentation choice, color tolerance, and T-junction definition all depend on user taste, so the algorithm has no objective ground truth.
**Successor:** the v0.4 line (auto-detection topology pack) is closed. Live successors:
- `architecture-v0.4.2-perception-data-only.md` — descriptive data only (`extract.yaml` + `overlay.png`, no auto-detection claims).
- `architecture-v0.5-per-panel-reference-workflow.md` — per-panel `reference_image` field and reference-grounded `/fig_critique` (the user-as-master workflow this session converged on).

---

**Original Status:** DRAFT (2026-05-08)
**Trigger:** N=2 dogfood on `fig1_overview_v2` revealed that compile-stage checkers (`lint_tex.py`, `check_collisions.py`, `check_visual_clash.py`, `check_layout_drift.py`) all pass while Panel A still reads as visually awkward (dangling polysulfide chain endpoints, sparse triangular DIB layout, floating S-S-S notation). Existing checks are mechanical (palette compliance, bbox overlap, pixel clash) — they cannot surface structural awkwardness like "this chain endpoint should connect to another but doesn't". Vision LLM (L4.5) catches some of this but is unreliable for tier-grade judgment (confirmed across this session). Build stage needs richer perceptual input — both for the agent's later vision call AND for the user's own grind cycle.
**Predecessor:** `architecture-v0.3-llm-figure-quality-judgment.md` (REJECTED 2026-05-08; rejected proposal targeted vision-side ceiling, this spec targets build-side input ceiling — orthogonal axis), `architecture-v0.2-proposal.md` §4 (compile pipeline)
**Active product direction:** `quality-kernel-goal.md`, ongoing fig1_overview_v2 dogfood

---

## 1. Problem Statement

`/fig_compile` runs five quality checks (lint, collision, clash, drift, golden artifacts). All pass for `fig1_overview_v2` Panel A, yet the rendered Panel A is visibly unfinished:

- Three DIB benzene rings in triangular layout. Each has 2 polysulfide chains.
- Six chain endpoints total. **Zero of them terminate at another DIB ring.**
- Briefing §1 calls this a "DIB-linked polysulfide network." The build does not link anything.

Why current checks miss this:

| Check | Looks at | Why blind to Panel A |
|---|---|---|
| `lint_tex.py` | TeX source — `\definecolor` / hex / non-palette colors | source uses palette correctly |
| `check_collisions.py` | `pdftotext -bbox` text labels — bbox IoU > threshold | no labels overlap |
| `check_visual_clash.py` | raster pixels — text on path / fill / clip | no text rides on lines |
| `check_layout_drift.py` | reference OCR vs build text positions | requires `coordinate_hints.yaml` w/ matching labels |

None of these examine **path geometry** (what `\draw` actually drew, where its endpoints are, what they connect to). The PDF contains complete vector data; current pipeline raster-renders to PNG and discards it.

The user observation that triggered this spec:

> "지금 컴파일 판단 기준에서는 얘를 지금 파악을 다 못한다는 건데 어색한 부분을... 형태, 모양, 배치, 그런 것들을 하나부터 열까지 확실하게 봐야 얘가 저것도 판단할 것 같아."

The deficit is not in judgment — it's in **perceptual input bandwidth**. Both author (during grind) and agent (during critique) work from a single rendered PNG plus the .tex source. They lack the structured geometry, the topology, the alignment metrics, and the alternative renders (wireframe, edge-only) that would surface awkwardness mechanically.

This spec adds a **build-side perception layer** between L4 (compile) and L4.5 (vision critique) that extracts and renders these missing inputs from the build artifacts.

## 2. Architecture Overview

### 2.1 Layer placement — L4.3 inside `/fig_compile`

```
L1 briefing.md         L2 spec.yaml          L2.5 coordinate_hints.yaml
        ↓                    ↓                       ↓
L3 author writes <name>.tex
        ↓
L4 /fig_compile
   ├── (1) lint_tex.py             [existing]
   ├── (2) lualatex → PDF + PNG    [existing]
   ├── (3) check_collisions.py     [existing]
   ├── (4) check_visual_clash.py   [existing]
   ├── (5) check_layout_drift.py   [existing, optional]
   └── (6) perceive_build.py       ★ NEW (L4.3)
            └── build/perception/  ← perception pack
        ↓
L4.5 /fig_critique  (auto-detects perception pack, includes in brief)
        ↓
L5 /fig_export
```

L4.3 is a **post-compile augmentation step**, not a separate slash command. Rationale (from the panel-iteration discussion in this session): users iterate by repeated `.tex edit → /fig_compile → look`, sometimes dozens of times before invoking `/fig_critique`. A separate `/fig_perceive` command would force the user to manually re-invoke after every compile, breaking the iteration loop. Baking into compile means every iteration produces both the figure AND the perception pack atomically.

### 2.2 Outputs — perception pack

4 data YAMLs + 4 render PNGs (or sets) + 1 report:

```
examples/<name>/build/perception/
├── extract.yaml           # vector geometry (texts, paths, fills, colors)
├── topology.yaml          # connectivity graph + per-panel density
├── alignment.yaml         # row baselines, column centers, grid snap
├── style.yaml             # actual color count, font hierarchy, opacity map
├── wireframe.png          # outline-only render (no fills, no text)
├── edge.png               # edge-detected render (curvature inspection)
├── overlay.png            # element bboxes labeled
├── panels/<id>.png        # per-panel crops (when spec.yaml.panels[i].bbox set)
└── report.md              # top-level summary + WARN-tier finding list
```

Each artifact is regenerated atomically per compile. `build/perception/` is git-ignored (derivative, not source).

### 2.3 Two consumers

1. **User during grind** — opens any of the 7 artifacts to debug specific aspects:
   - lumpy bezier curves → `wireframe.png` or `edge.png`
   - misaligned labels → `alignment.yaml` row_baselines
   - dangling chain endpoints → `topology.yaml` lonely_endpoints
   - panel weight imbalance → `topology.yaml` per_panel density
2. **Agent during `/fig_critique`** — `critique_brief.py` auto-detects `build/perception/`, includes summary in brief, attaches additional renders (`wireframe.png`, `overlay.png`, panel crops) via host `Read` tool calls. Vision call now grounded by 6-7 inputs instead of 1.

## 3. Components

### 3.1 Vector geometry extraction (`extract.yaml`)

Source: PDF parsed via `pymupdf` (fitz).

```yaml
schema: figure-agent.perception.extract.v1
fixture: <name>
extracted_at: <ISO-8601>
pdf_size_cm: [width, height]

texts:                                  # every text element
  - id: T001
    bbox_cm: [x, y, w, h]               # PDF coordinate space, cm
    content: "Sulfur-rich polymer"
    font: "Arial"
    size_pt: 7.5
    color: cAmber                       # palette name when matched, else hex

paths:                                  # every \draw / \path / \fill output
  - id: P001
    type: stroke | fill | both
    color: cAmber!85!black
    stroke_weight_pt: 0.85
    commands:                           # list of subpath commands
      - {op: moveto, x: 3.95, y: 8.50}
      - {op: lineto, x: 4.30, y: 8.50}
      - {op: curveto, c1x: 4.30, c1y: 8.40, c2x: 4.65, c2y: 8.40, x: 4.65, y: 8.50}
      ...
    endpoints_cm:                       # extracted: first and last point
      start: [3.95, 8.50]
      end:   [5.00, 8.50]

fills:                                  # closed regions with non-trivial area
  - id: F001
    bbox_cm: [x, y, w, h]
    color: cAmber!10
    area_cm2: 10.74

color_usage:                            # actual color → count
  cAmber!85!black: 47
  cBlue!75!black: 12
  ...

stroke_weights:                         # histogram (pt)
  "0.30": 8
  "0.55": 24
  "0.85": 31
  "1.30": 4
```

`pymupdf` exposes `page.get_drawings()` which returns this structure natively. No new TeX rendering needed — same PDF the user already produced.

### 3.2 Topology analysis (`topology.yaml`)

Computed from `extract.yaml` paths.

```yaml
schema: figure-agent.perception.topology.v1
fixture: <name>

endpoints:
  total: 188
  unique_clusters: 92                   # endpoints within ε=0.15cm merged
  
lonely_endpoints:                       # cluster with exactly 1 endpoint, no neighbor within ε=0.20cm
  - position_cm: [0.85, 7.05]
    path_id: P023
    path_color: cAmber!85!black
    nearest_other_cm: 1.24              # nearest other endpoint
    nearest_other_path: P019
    note: "potential dangling — chain endpoint with no nearby connection"
  - position_cm: [2.40, 7.30]
    path_id: P027
    ...

connected_components:                   # graph: paths sharing endpoints (within ε)
  count: 14                             # disjoint subgraphs
  largest_size: 47                      # paths in biggest component
  isolated_paths: 8                     # 1-element components

per_panel:                              # only when spec.yaml.panels[i].bbox set
  - id: panel_A
    bbox_cm: [0, 5.00, 3.50, 4.00]
    elements_count: 38
    text_count: 6
    path_count: 32
    fill_count: 0
    ink_density_pct: 8.4                # % of panel area with ink
    lonely_endpoints_in_panel: 6
  - id: panel_C
    ...
```

`ε` thresholds are configurable (default 0.20cm for "lonely", 0.15cm for "shared cluster"). Tuning hooks for fixtures with different scales.

### 3.3 Alignment analysis (`alignment.yaml`)

```yaml
schema: figure-agent.perception.alignment.v1
fixture: <name>

row_baselines:                          # text bbox y-baseline groups
  - row_y_cm: 8.50                      # mean baseline
    members: [T003, T007, T012]         # text IDs sharing baseline (within ε=0.05cm)
    spread_cm: 0.018                    # max - min within group
  - row_y_cm: 7.75
    members: [T008, T013]
    spread_cm: 0.005
  - row_y_cm: 0.85
    members: [T040, T041, T042, T043]   # axis labels (likely shared baseline)
    spread_cm: 0.000

column_centers:                         # text bbox center-x groups
  - col_x_cm: 1.45
    members: [T001, T002]               # captions on Panel A
    spread_cm: 0.012

grid_snap:                              # element position histogram on regular grid
  x_grid_candidate_cm: 0.5              # detected if positions cluster on multiples of 0.5
  x_snap_score: 0.78                    # fraction of positions within 0.05cm of grid
  y_grid_candidate_cm: null             # no clean grid detected on y
  y_snap_score: null
```

Surfaces "labels in a column should align but don't" type findings.

### 3.4 Style audit (`style.yaml`)

```yaml
schema: figure-agent.perception.style.v1
fixture: <name>

color_count:
  declared_in_palette: 6                # cAmber, cBlue, cRed, cGray, cLGray, cArmAmber
  actually_used: 8                      # palette + tints/shades
  outliers: []                          # any color not derivable from palette

opacity_map:                            # opacity < 1.0 regions
  - bbox_cm: [7.20, 7.30, 6.40, 1.10]   # the faded polymer backdrop
    opacity: 0.42
    note: "intentional faded backdrop (Panel C)"

font_size_hierarchy:
  observed_sizes_pt: [5.0, 5.5, 6.5, 7.0, 7.5, 8.0, 8.5, 10.0]
  count_per_size: {5.0: 4, 5.5: 8, 6.5: 1, 7.0: 12, 7.5: 14, 8.0: 0, 8.5: 6, 10.0: 1}
  hierarchy_tiers: 4                    # distinct enough sizes to read as hierarchy
  min_readable_pt: 5.0                  # below 5pt would WARN
  outliers: []
```

### 3.5 Wireframe render (`wireframe.png`)

Re-runs lualatex with a TikZ style override that disables fills (`fill=none`) and reduces text to faint placeholders. Result: only stroke geometry visible. Reveals lumpy bezier curves and disconnected paths immediately.

Implementation: prepend `\tikzset{every path/.style={fill=none}, every node/.style={text opacity=0.15}}` before document begin. Rerun lualatex on a temp .tex.

### 3.6 Edge render (`edge.png`)

Canny edge detection on the existing build PNG via OpenCV (or PIL fallback). Produces white-on-black edge map. Stricter than wireframe — surfaces curvature anomalies that survive even fill-removal.

### 3.7 Overlay render (`overlay.png`)

Draw rectangles over the existing build PNG: every text element bbox in cyan with id label, every path bbox in magenta, every fill bbox in yellow. Element placement and bbox boundaries explicit.

Implementation: PIL `ImageDraw.rectangle` reading from `extract.yaml`.

### 3.8 Per-panel crops (`panels/<id>.png`)

When `spec.yaml.panels[i].bbox` is set, crop the build PNG to that bbox at 2x resolution (oversized for detail). Each panel becomes its own sub-PNG.

Implementation: PIL `Image.crop` + `resize(2x)`.

### 3.9 Report (`report.md`)

Top-level human-readable summary aggregating signals across the 4 YAML files. WARN-tier findings ordered by severity:

```markdown
# Build Perception — fig1_overview_v2 (2026-05-08T17:50:00)

## Headline signals

- **Panel A**: 6 lonely endpoints (potential dangling chains). Density 8.4%.
- **Color count**: 8 actual vs 6 declared (within tolerance).
- **Row baselines**: row1 labels {3.40, 3.42, 3.45} σ=0.025 ✓
- **Hero panel C**: density 24%, ink-weight ratio vs sibling avg 1.6× ✓

## Lonely endpoints (potential dangling)

- (0.85, 7.05) Panel A — DIB1 chain end → nearest 1.24cm away
- (2.40, 7.30) Panel A — DIB1 chain end → nearest 1.18cm away
- ... (6 total)

## Alignment outliers

- Column-center group at x=12.50 has spread 0.18cm (5 members) — possible misalignment

## Color outliers

- (none)
```

Reports are advisory — surfacing findings, not gating compile. User reads to grind, agent reads in critique brief.

## 4. Data Flow

### 4.1 Generation order (single `/fig_compile` invocation)

```
.tex
 │
 ├── (1) lint_tex.py                                        [existing]
 ├── (2) lualatex → build/<name>.pdf, build/<name>.png      [existing]
 ├── (3) check_collisions.py                                 [existing]
 ├── (4) check_visual_clash.py                               [existing]
 ├── (5) check_layout_drift.py                               [existing, opt]
 │
 └── (6) perceive_build.py                                  [NEW]
       ├── 6a. _extract_geometry()    → extract.yaml
       ├── 6b. _compute_topology()    → topology.yaml         (depends on 6a)
       ├── 6c. _compute_alignment()   → alignment.yaml        (depends on 6a)
       ├── 6d. _audit_style()         → style.yaml            (depends on 6a)
       ├── 6e. _render_wireframe()    → wireframe.png         (lualatex re-run)
       ├── 6f. _render_edge()         → edge.png              (PIL/OpenCV)
       ├── 6g. _render_overlay()      → overlay.png           (depends on 6a)
       ├── 6h. _crop_panels()         → panels/<id>.png       (when bbox set)
       └── 6i. _write_report()        → report.md             (depends on 6a-6d)
```

### 4.2 Critique brief integration

`scripts/critique_brief.py` extension:

```python
def _perception_pack_path(example_dir: Path) -> Path | None:
    pack = example_dir / "build" / "perception"
    return pack if pack.exists() else None

# In brief generation:
pack = _perception_pack_path(example_dir)
if pack is not None:
    # Append summary section to brief text
    brief += "\n\n## Build perception (auto)\n"
    brief += _summarize_topology(pack / "topology.yaml")
    brief += _summarize_alignment(pack / "alignment.yaml")
    brief += _summarize_style(pack / "style.yaml")
    
    # List additional images for host to Read
    brief += "\n\n## Additional perception views\n"
    brief += f"- `{pack}/wireframe.png`\n"
    brief += f"- `{pack}/overlay.png`\n"
    for panel_png in (pack / "panels").glob("*.png"):
        brief += f"- `{panel_png}`\n"
```

The slash command (`commands/fig_critique.md`) Step 2 documentation extends to: "Use Read on `build/<name>.png` AND each `build/perception/*.png` listed in the brief, to maximize perceptual grounding."

### 4.3 Backward compatibility

- Existing fixtures without spec.yaml.panels[i].bbox: panel crops skipped. Other 6 artifacts still produced.
- Existing fixtures without `pymupdf` installed: report-only WARN, perception pack skipped, compile continues.
- Existing critiques: still work without perception pack (auto-detect handles missing case).
- Strict mode (`FIGURE_AGENT_STRICT=1`): perception pack failures DO NOT fail compile. Strict mode applies to existing checkers only.

### 4.4 Fast iteration mode

`FIGURE_AGENT_FAST=1 /fig_compile`:
- Skip step 6e (`_render_wireframe()`) — most expensive (lualatex re-run, 4-6s)
- Skip step 6f (`_render_edge()`) — moderate (1-2s)
- Run remaining: 6a, 6b, 6c, 6d, 6g, 6h, 6i (~2-3s total overhead)

Use case: user iterating .tex changes every 30s. 4-6s wireframe re-run breaks flow. Agent's vision call still benefits from extract/topology/alignment/style YAMLs even without wireframe.

## 5. Implementation Outline

### 5.1 New file

`scripts/perceive_build.py` (~400 lines estimated):

```python
"""perceive_build.py — L4.3 Build Perception Pack generator.

Reads build/<name>.pdf + build/<name>.png + spec.yaml. Produces
build/perception/{extract,topology,alignment,style}.yaml +
{wireframe,edge,overlay}.png + panels/<id>.png + report.md.

Idempotent: regenerates the entire perception/ directory each run.
"""
import argparse, json, math, sys, tempfile
from pathlib import Path
import yaml
from PIL import Image, ImageDraw

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None

try:
    import cv2  # opencv for Canny edge
except ImportError:
    cv2 = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("example_dir", type=Path)
    parser.add_argument("--fast", action="store_true",
                        help="Skip wireframe + edge renders")
    args = parser.parse_args()
    
    if fitz is None:
        print("WARN: pymupdf not available; perception pack skipped", file=sys.stderr)
        return 0
    
    example_dir = args.example_dir.resolve()
    pdf_path = _find_pdf(example_dir)
    spec = _load_spec(example_dir)
    
    pack_dir = example_dir / "build" / "perception"
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    # 6a-d: data extraction
    extract = _extract_geometry(pdf_path)
    topology = _compute_topology(extract, spec)
    alignment = _compute_alignment(extract)
    style = _audit_style(extract, spec)
    
    _write_yaml(pack_dir / "extract.yaml", extract)
    _write_yaml(pack_dir / "topology.yaml", topology)
    _write_yaml(pack_dir / "alignment.yaml", alignment)
    _write_yaml(pack_dir / "style.yaml", style)
    
    # 6e-h: render artifacts
    if not args.fast:
        _render_wireframe(example_dir, pack_dir / "wireframe.png")
        _render_edge(example_dir / "build" / f"{spec['name']}.png", pack_dir / "edge.png")
    
    _render_overlay(
        example_dir / "build" / f"{spec['name']}.png",
        extract,
        pack_dir / "overlay.png",
    )
    _crop_panels(
        example_dir / "build" / f"{spec['name']}.png",
        spec, pack_dir / "panels",
    )
    
    # 6i: human-readable report
    _write_report(pack_dir / "report.md", extract, topology, alignment, style)
    
    return 0
```

### 5.2 Modified files

| File | Change |
|---|---|
| `scripts/compile.sh` | Append: `uv run python3 scripts/perceive_build.py "$EXAMPLE_DIR" ${FAST_FLAG}` after step 5 |
| `scripts/critique_brief.py` | Add `_perception_pack_path()` + brief integration (§4.2) |
| `scripts/inputs.py` | Add optional `panels[i].bbox: list[float]` validation (4-tuple, cm units) |
| `commands/fig_compile.md` | Document step 6 |
| `commands/fig_critique.md` | Document Read tool usage on perception PNGs |
| `pyproject.toml` | Add `pymupdf>=1.23` dependency. `opencv-python` optional |
| `.gitignore` | Add `build/perception/` |

### 5.3 New tests

`tests/test_perceive_build.py`:

| Test | Purpose |
|---|---|
| `test_extract_geometry_smoke` | extract.yaml has texts/paths/fills lists, valid YAML |
| `test_topology_lonely_endpoint_detection` | synthetic fixture with known dangling path → exactly 1 lonely endpoint reported |
| `test_topology_per_panel_density` | bbox-defined panels → density % matches expected ink coverage |
| `test_alignment_baseline_grouping` | 3 labels at y=2.50, 2.51, 2.52 → grouped (within ε=0.05cm) |
| `test_alignment_baseline_separation` | label at y=2.50 vs y=2.80 → separate groups |
| `test_style_color_count` | known palette + 2 derived shades → actually_used=palette+2 |
| `test_overlay_render_smoke` | overlay.png exists, dimensions match build PNG |
| `test_panel_crop` | bbox-defined panel → panels/<id>.png exists, correct dimensions |
| `test_fast_mode_skips_wireframe` | FAST=1 → wireframe.png NOT generated, others present |
| `test_missing_pymupdf_graceful` | mocked import failure → WARN, exit 0, compile continues |

`tests/test_critique_brief.py` extension:

| Test | Purpose |
|---|---|
| `test_brief_includes_perception_when_present` | perception/ exists → brief text contains "Build perception" section |
| `test_brief_omits_perception_when_absent` | no perception/ → brief unchanged from current behavior |

### 5.4 Compile time impact

Priori estimate (revisit post-trial):

| Step | Time |
|---|---|
| 6a extract_geometry (pymupdf) | ~0.5s |
| 6b-d topology + alignment + style (computed from 6a) | ~1.0s |
| 6e wireframe (lualatex re-run) | ~4-6s |
| 6f edge (Canny) | ~1-2s |
| 6g overlay (PIL) | ~0.5s |
| 6h panel crops | ~0.3s × N panels |
| 6i report | ~0.1s |
| **Total (full mode)** | **+7-10s** |
| **Total (fast mode)** | **+2-3s** |

Current compile baseline ~12-15s → 19-25s (full) or 14-18s (fast).

## 6. Testing — Trial protocol

### 6.1 Smoke fixtures

| Fixture | Purpose |
|---|---|
| `golden_trap_depth_picture` | known-good baseline. Perception pack should produce reasonable counts (low lonely endpoints, balanced density) |
| `fig1_overview_v2` | active dogfood. Panel A should produce 6+ lonely endpoints (the trigger case for this spec) |
| `dogfood_power_law_trap_pipeline` | quantitative plot archetype. Lonely endpoints expected (curve termini are normal) — verify topology check does NOT FP-flag them |

### 6.2 Acceptance criteria

- **Geometry extract**: extract.yaml contains every visible text element from build PNG (verified by manual count on golden fixture), bbox positions within 0.05cm of pdftotext output (cross-check with `check_collisions.py`).
- **Topology**: lonely endpoint detection correctly flags the 6 dangling chains in fig1_overview_v2 Panel A. False positive rate <10% on golden fixture (i.e., ≤2 spurious lonely flags).
- **Alignment**: row_baselines correctly groups Panel A's "Sulfur-rich polymer" caption with the matching DIB labels (within ε).
- **Style**: actually_used color count is within ±2 of declared palette + intentional shades on golden fixture.
- **Wireframe**: visually distinguishes Panel A's polysulfide chains from connection lines (curvature visible).
- **Compile time**: full mode +7-10s on a representative fixture (`fig1_overview_v2`), fast mode +2-3s.

### 6.3 Anti-cases (negative tests)

- `dogfood_power_law_trap_pipeline`: I(t) curve has 1 endpoint at panel edge (axis terminus). Topology should NOT flag this as lonely if the endpoint is on a panel edge (within 0.1cm of panel.bbox boundary). Edge-of-panel suppression rule.
- Fixture without `panels[i].bbox`: per-panel density skipped cleanly, no crash.
- Fixture without reference: alignment / topology / style still work; only layout-drift-related signals absent.

## 7. Open Issues & Future Scope

### 7.1 Decisions deferred to implementation plan

| Issue | Default | Trigger to revisit |
|---|---|---|
| Lonely endpoint ε threshold | 0.20cm | If trial flags too many or too few in golden fixture |
| Edge-of-panel suppression | within 0.10cm of bbox edge → not lonely | If quantitative-plot fixtures FP-flag axis termini |
| Wireframe text opacity | 0.15 | If wireframe text is too prominent / invisible |
| Connected components threshold | report only if ≥3 isolated components | Domain-tuneable |
| Color outlier definition | colors that are not within 5% RGB distance of any declared palette color | If palette tints/shades trigger false outliers |

### 7.2 Out of scope for v0.4

- **Domain-aware checks** (chemistry valence, energy diagram conventions): require domain rule encoding. Separate spec when needed.
- **Reference-grounded SSIM / diff**: requires reference-build alignment which is non-trivial. Separate spec.
- **Per-panel briefing §7 split**: if author writes panel-specific semantic_intent, topology check can validate against intent. Tracked as separate spec (per-panel reference workflow).
- **Style-transfer / Inkscape polish automation**: `architecture_reset_2026_05_03` Gap 2. Separate spec when ready.

### 7.3 Known limitations

- **PDF parser dependency**: pymupdf has its own bbox computation; may differ slightly (~0.05cm) from pdftotext used by `check_collisions.py`. Cross-check during trial; document divergence if material.
- **Coordinate system**: pymupdf returns PDF-native points (1/72 inch). Conversion to cm uses standard 2.54cm/inch. Document this in extract.yaml header.
- **Wireframe re-render flake**: TikZ + style override may produce slightly different output than original (e.g., text bbox shift). Document; not a correctness issue (wireframe is for human grind, not for measurement).
- **Single-rater perception evaluation**: same as v0.3 critique rubric — author self-assesses whether perception pack signals are useful. Multi-rater calibration deferred.

## 8. Decision History (this brainstorming session)

| Decision | Choice | Reason |
|---|---|---|
| What's missing in build-stage checks? | Path geometry / connectivity / alignment | User question after Panel A awkward despite clean compile |
| Layer placement (separate slash vs integrated)? | Inside `/fig_compile` post-step | User: "panel iteration loop stays in build stage; need vision broadening DURING build, not after" |
| Macro-mining direction (sister archive scan)? | REJECTED | User: "macro form isn't paper-grade quality anyway. Per-panel reference is better" |
| Spike scope — vector geometry only vs comprehensive? | Comprehensive (7 artifacts) | User: "전수 점검 후 정리" — broaden vision input fully on first try, avoid piecemeal |
| Domain rules (chemistry/physics) included? | Out of scope | Generic perception first; domain rules layer on top later |
| Per-panel reference image workflow? | Separate spec | Adjacent feature; not a perception input issue |
| Reference SSIM included? | Out of scope | Alignment problem non-trivial; single number low information |
| Compile time budget? | Accept +7-10s default, +2-3s fast mode | iteration loop preserved via FAST flag |

## 9. Sources / Calibration

This spec is build-side data extraction; no external industry-survey calibration required (unlike v0.3 critique rubric which calibrated against LLM-as-judge literature). Primary sources are the existing repo:

- `scripts/check_collisions.py` — uses pdftotext for text bbox extraction (existing precedent for PDF parsing in this repo)
- `scripts/check_visual_clash.py` — uses raster + numpy for pixel analysis (existing precedent for build-PNG inspection)
- `scripts/reference_extract.py` — uses Tesseract + K-means + vtracer on reference PNG (parallel architecture for reference-side perception, this spec is build-side parallel)
- `architecture-overview.md` §149 — `structural_regions` schema (similar concept for reference image; this spec applies analogous shape to build artifacts)

External library dependencies:

- `pymupdf` — MIT license, mature PDF parsing, ships with prebuilt wheels
- `Pillow` — already in dependency tree
- `opencv-python` — optional, MIT license, only for edge detection (PIL fallback acceptable)

---

_v0.4 spec authored 2026-05-08 from session brainstorming chain. Targets build-side perception input ceiling distinct from v0.3 (REJECTED) which targeted vision-side judgment ceiling. Two are orthogonal axes; neither replaces the other. Trial ships with `fig1_overview_v2` Panel A as the headline validation case (6 lonely endpoints expected; FN from current pipeline confirmed)._
