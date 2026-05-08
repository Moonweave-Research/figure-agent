# Architecture v0.4.1 — Build Perception Pack (revised)

**Status:** REJECTED (2026-05-08).
2nd-round dual external review (`docs/trials/2026-05-08-perception-spec-review-v041-{codex,gemini}.md`) found v0.4.1 left 6 BLOCKING issues unresolved:
1. Topology fix does not handle T-junction false positives (chain-to-ring middle-of-path attachment) — Codex+Gemini concur.
2. Path reconstruction guarantees false negatives — two faded chain tails terminate within ~0.12-0.19 cm of each other and form a `cluster size = 2`, never flagged as `lonely`.
3. Coordinate math wrong: `cm_per_source_unit: 1.291` should be `1.271` (`17.8/14.0`); `source_origin_in_pdf_cm: [0.27, 0.27]` should be `[0.141, 0.141]` (border-only).
4. Probe baseline 81 lonely does not reproduce under spec's own endpoint schema (Codex re-ran with proper `pts`: 49 lonely).
5. Intent enum incomplete (5 declared, 2 defined in rules YAML); no mixed-panel handling; manual `bbox_pdf_cm` burden severely underestimated.
6. Dependency policy contradictory (`§7.4` graceful WARN vs `§8` "no graceful skip needed"); `pyproject.toml` has pdfplumber as dev-only.

Beyond mechanical fixes, advisor + reviewer trajectory converged on a deeper finding: the same PDF gives 4 different "lonely endpoint" counts (PyMuPDF 4 / pdfplumber-author 2 / pdfplumber-Codex 49 / user visual 4-6) depending on segmentation, tolerance, and T-junction definition — there is no invariant ground truth the algorithm can converge to.

**Successor:** the v0.4 line is closed.
- `architecture-v0.4.2-perception-data-only.md` — D-1 ship target. Pure descriptive `extract.yaml` + `overlay.png`. No auto-detection, no `topology.yaml`, no intent enum.
- `architecture-v0.5-per-panel-reference-workflow.md` — D-2 strategic shift. `spec.yaml.panels[i].reference_image` for `/fig_critique` reference grounding (user-as-master workflow).

**Predecessor:** `architecture-v0.4-build-perception-pack.md` (REJECTED — same line).
**Active product direction:** `quality-kernel-goal.md`, ongoing fig1_overview_v2 dogfood. See `feedback_perception_spec_rejected.md` memory entry.

---

## Original spec text below (preserved for archival; do NOT implement)


---

## 1. Problem Statement

Same root case as v0.4: `fig1_overview_v2` Panel A's six polysulfide chain termini do not connect to anything despite briefing calling it a "DIB-linked polysulfide network", yet `/fig_compile`'s five existing checks all pass. Build-stage perception input is too narrow.

What v0.4 got wrong, validated by probes:

- v0.4 §1 claimed "the deficit is not in judgment — it's in perceptual input bandwidth." This was overstated. The deficit is partly in input (no path geometry exposure) AND partly in **intent** (no per-panel declaration of what should connect to what). Pure auto-detection of "lonely endpoint = problem" produces both false positives (axis arrowheads, intentional fade-outs) and false negatives (chain segments split into solid+faded paths whose handoff coordinates cluster, hiding the dangling tip).
- v0.4 §6.2 acceptance criteria claimed "Panel A should produce 6+ lonely endpoints." Probe results contradict this:
  - Codex (PyMuPDF, figure-wide): 144 endpoints, 72 over 0.20cm threshold, **4 lonely amber** after color filter — not 6.
  - Author (pdfplumber, Panel A scope): 50 endpoints in Panel A, 20 lonely clusters, **2 lonely amber** — not 6.
- v0.4 §3.1 schema described `pymupdf.get_drawings()` as returning text-and-paths in a single named-op-dict structure. Verification (PyMuPDF docs) showed it returns paths only with tuple-op codes; text requires a separate `get_text("dict")` call.

This spec corrects both the framing (intent-aware tiering) and the implementation claim (probe-validated).

## 2. Three-tier auto-detection model

The honest scope of build-side perception:

| Tier | Auto-detection | What it covers (this fixture) |
|---|---|---|
| **T1 — fully auto** | No user input beyond .tex + briefing as today | Color count (declared vs actual), font size hierarchy distribution, text bbox + content + baseline groups, path geometry extraction (every `\draw` output), per-panel ink density when bbox provided, cross-panel weight balance, stroke weight histogram |
| **T2 — auto with one-time intent declaration per panel** | User adds `intent_type` to `spec.yaml.panels[i]` ONCE per fixture (~5-7 lines for a multi-panel figure); subsequent compiles auto-check | `intent_type: network` → flag dangling endpoints inside panel<br>`intent_type: plot` → exclude axis arrowheads from "lonely" count<br>`intent_type: process` → flag missing inter-panel arrows<br>`intent_type: composite` → density imbalance threshold loosened |
| **T3 — not auto, user judges** | Aesthetic / composition / domain taste | "Looks unfinished", "hero placement appropriate", "this amber is too saturated" |

T1 always runs and produces structured data. T2 runs when intent declared and produces gated findings. T3 stays user.

This is the v0.4 framing corrected: not "geometry mechanically surfaces awkwardness" (overclaim) but "geometry surfaces measurable deviations; intent gates which deviations count as problems."

## 3. Architecture Overview

### 3.1 Layer placement (unchanged from v0.4)

L4.3 inside `/fig_compile` post-step. No new slash command (per panel-iteration loop preservation discussion).

```
L4 /fig_compile
   ├── (1) lint_tex.py             [existing]
   ├── (2) lualatex → PDF + PNG    [existing]
   ├── (3) check_collisions.py     [existing]
   ├── (4) check_visual_clash.py   [existing]
   ├── (5) check_layout_drift.py   [existing, optional]
   └── (6) perceive_build.py       ★ NEW (L4.3)
            └── build/perception/
        ↓
L4.5 /fig_critique (auto-detects perception pack)
```

### 3.2 MVP scope (downscoped from v0.4)

Codex BLOCKING #6 said v0.4's 4 YAMLs + 4 render PNGs in one ~400-line script was too much before validating the core question (does build geometry reliably catch Panel A's broken network?). Agree.

v0.4.1 MVP delivers:

```
examples/<name>/build/perception/
├── extract.yaml           # T1 — vector geometry (paths, texts, fills, colors)
├── topology.yaml          # T1 baseline + T2 intent-gated findings
├── overlay.png            # T1 — element bbox overlay (single annotated view)
└── report.md              # T1+T2 summary with WARN-tier findings
```

Cut from v0.4:
- `alignment.yaml`, `style.yaml` — defer to v0.4.2 (Codex BLOCKING #6: too many components in one script)
- `wireframe.png` — defer (Codex #6: most expensive step at 4-6s lualatex re-run; redundant with overlay for chain-connectivity question)
- `edge.png` — defer (Gemini + Codex agreed: redundant with wireframe for stated problem)
- `panels/<id>.png` — defer to per-panel reference workflow spec (different feature)

This MVP is large enough to validate the core thesis (build-side geometry can detect Panel A dangling when intent-gated), small enough to ship in one spike. Full `perception/` directory re-expands in v0.4.2 if MVP validates.

## 4. Components

### 4.1 Vector geometry extraction (`extract.yaml`)

**Library: pdfplumber** (MIT license, MIT-compatible deps: pdfminer.six MIT, cryptography Apache-2.0). Replaces PyMuPDF (AGPL/Commercial dual) per Gemini BLOCKING #1.

Input: `examples/<name>/build/<name>.pdf`
Output: `extract.yaml` with vector data and coordinate-space metadata.

```yaml
schema: figure-agent.perception.extract.v2
fixture: <name>
extracted_at: <ISO-8601>
extractor: pdfplumber
extractor_version: "0.11.9"

# Coordinate space — explicit per Codex BLOCKING #2 (v0.4 left this implicit)
coordinate_space:
  pdf_page_size_cm: [18.08, 11.22]      # PDF point space converted to cm via 2.54/72
  pdf_page_size_pt: [512.57, 318.06]    # raw PDF points (1/72 inch)
  source_canvas_cm: [14.0, 9.0]         # TikZ source canvas (from .tex \fill comment)
  resizebox_target_mm: 178              # from .tex \resizebox{178mm}{!}
  border_pt: 4                          # from .tex \documentclass[border=4pt]
  cm_per_source_unit: 1.291             # PDF cm = source TikZ unit × this scale
  source_origin_in_pdf_cm: [0.27, 0.27] # PDF cm position of TikZ (0,0)

# All coordinates below are PDF cm unless explicitly noted.

texts:                                  # from page.chars merged via extract_words()
  - id: T001
    bbox_cm: [x, y, w, h]
    content: "Sulfur-rich polymer"
    fontname: "Arial"
    size_pt: 7.5
    color: [0.51, 0.41, 0.10]           # RGB tuple from non_stroking_color

paths:                                  # from page.lines + page.curves + page.rects
  - id: P001
    type: line | curve | rect
    bbox_cm: [x, y, w, h]
    stroking_color: [r, g, b]           # raw RGB
    non_stroking_color: [r, g, b]
    linewidth_pt: 0.85
    # Type-dependent payload:
    line_payload:                       # only when type=line
      start_cm: [x, y]
      end_cm: [x, y]
    curve_payload:                      # only when type=curve
      pts_count: 10
      pts_cm: [[x1,y1], [x2,y2], ...]   # full bezier control point sequence
    rect_payload:                       # only when type=rect
      filled: true | false
```

Notes on pdfplumber API (per Gemini BLOCKING #2):
- `page.chars` returns per-character; merge into words via `page.extract_words()` with bbox aggregation. Text is a separate code path from paths — schema reflects this.
- `page.lines`, `page.curves`, `page.rects` are flat object lists. No native "drawing item" grouping (PyMuPDF would have grouped by `\draw` call). Path reconstruction (chaining sequential segments) is the algorithm's job — described in topology.yaml below.
- pdfplumber uses RGB float tuples [0.0–1.0]; conversion to palette names (cAmber, cBlue, etc.) happens in topology / report layer via tolerance match against `polymer-paper-preamble.sty` `\definecolor` declarations.

### 4.2 Topology analysis (`topology.yaml`) — T1 baseline + T2 intent gating

Computed from `extract.yaml`. Two-stage:

**Stage 1 — baseline (T1, always runs):**

```yaml
schema: figure-agent.perception.topology.v1
fixture: <name>

baseline:
  total_path_segments: 176              # lines + curves + rects from pdfplumber
  total_endpoints: 332                  # path start + end (segment-level)
  endpoint_clusters: 193                # endpoints within ε=0.15cm merged
  lonely_clusters: 81                   # cluster size=1 with no neighbor within ε=0.20cm
  
  # Path reconstruction (Codex BLOCKING #3 fix): identify connected curve sequences
  # whose endpoints chain (curve_n.end ≈ curve_{n+1}.start within ε=0.05cm).
  # External path endpoints = first segment's start + last segment's end of each chain.
  reconstructed_paths: 47               # contiguous segment chains identified
  external_path_endpoints: 94           # 2 per reconstructed path
  external_lonely: 28                   # external endpoints with no neighbor within ε=0.20cm
```

**Stage 2 — intent-gated findings (T2, runs when `spec.yaml.panels[i].intent_type` set):**

```yaml
intent_gated:
  - panel_id: panel_A
    intent_type: network                # declared in spec.yaml
    bbox_cm: [0.27, 6.55, 4.66, 11.08]  # PDF cm
    elements_in_panel: 38
    external_endpoints_in_panel: 18
    
    # network rule: flag dangling chain termini
    findings:
      - id: TF001
        severity: MAJOR
        cue: dangling_chain_terminus
        position_cm: [0.79, 9.56]        # PDF cm
        path_id: P024
        path_color_match: cAmber!85!black
        nearest_other_path_distance_cm: 0.92
        observation: |
          Reconstructed path P024 (amber stroke, length 1.20cm) has external
          endpoint at (0.79, 9.56) with no other path within 0.92cm.
          Panel A intent_type=network requires chain termini to attach to
          ring/chain at distance ≤ 0.20cm.
      ...

  - panel_id: panel_D
    intent_type: plot
    findings:
      # plot rule: axis arrows are expected lonely terminations; suppress
      - id: TF010
        severity: INFO
        cue: axis_terminus_suppressed
        count: 4
        observation: "4 axis arrowhead endpoints suppressed per intent_type=plot"
      # plot rule: data lines extending past panel bbox are flagged
      ...
```

Intent-type → rule mapping (initial set):

| `intent_type` | Activated rules |
|---|---|
| `network` | dangling_chain_terminus (lonely amber endpoint inside panel = MAJOR) |
| `plot` | axis_terminus_suppressed (lonely endpoint at panel edge = INFO, not MAJOR) |
| `process` | missing_inter_panel_arrow (panel boundary should have ≥1 outbound arrow) |
| `composite` | density_imbalance_relaxed (sub-panel ink density tolerance widened 2×) |
| `other` | T1 baseline only, no intent-gated findings |

Intent-type → rule mapping is a YAML table at `docs/perception-intent-rules.yaml`, separate from spec so future intent types can be added without spec change. RRD-style: trial reveals new patterns → catalog extends.

### 4.3 Overlay render (`overlay.png`)

PIL-rendered overlay of build PNG with:
- Cyan rectangles around every text element + ID label
- Magenta rectangles around every reconstructed path bbox + path-id label
- Yellow circles at lonely endpoint positions (from topology.yaml.baseline.external_lonely)

Single annotated view replacing v0.4's wireframe + edge + overlay (Codex BLOCKING #6: redundant). Edge inspection deferred — overlay is enough for the MVP question.

### 4.4 Report (`report.md`)

Top-level human-readable summary. Format:

```markdown
# Build Perception — fig1_overview_v2 (2026-05-08T...)

## Summary
- pdfplumber extraction OK (176 path segments, 277 chars, 47 reconstructed paths)
- T1 baseline: 81 lonely endpoints, 28 external lonely
- T2 intent: panel_A=network → 4 dangling chain termini flagged MAJOR

## T1 baseline signals
- Color count: 8 actual vs 6 declared (within tolerance)
- Per-panel density: A=8%, B=12%, C=24%, D=15%, E=4%, F=11%, G=6% [HERO=C ✓]

## T2 intent-gated findings (panel_A=network)
TF001 MAJOR — dangling chain terminus at (0.79, 9.56)
  Path P024 amber, length 1.20cm. Nearest other 0.92cm away.
TF002 MAJOR — dangling chain terminus at (3.27, 9.56)
...

## Panels with intent_type unset (T1 only, no intent-gated findings)
- panel_E, panel_F (no intent declared)
```

## 5. Schema additions

### 5.1 spec.yaml extension (T2 enabler)

```yaml
panels:
  - id: panel_A
    caption: "Sulfur-rich polymer"
    column: 1
    role: supporting
    intent_type: network              # ★ NEW (optional)
    bbox_pdf_cm: [0.27, 6.55, 4.66, 11.08]  # ★ NEW (optional, PDF cm units)
```

`intent_type`: enum {network, plot, process, composite, other}. Optional — when absent, T2 stage skipped for that panel; T1 still runs.

`bbox_pdf_cm`: optional 4-tuple. When absent, panel-scoped findings skipped; figure-wide findings still report. Author writes once per fixture (~5-7 panels × ~1 minute each = 5-10 min one-time).

Auto-computation of `bbox_pdf_cm` from `column` + `width_ratio` is a v0.4.2 feature (deferred). v0.4.1 requires manual entry — explicit acknowledgment of small author burden, ROI clear.

### 5.2 inputs.py (`parse_spec`)

Add validation for the two new optional fields. Schema unchanged when absent.

```python
KNOWN_INTENT_TYPES = {"network", "plot", "process", "composite", "other"}

# Inside parse_spec():
for panel in panels:
    if "intent_type" in panel:
        if panel["intent_type"] not in KNOWN_INTENT_TYPES:
            raise ValueError(f"Unknown intent_type {panel['intent_type']!r} for panel {panel['id']}")
    if "bbox_pdf_cm" in panel:
        bbox = panel["bbox_pdf_cm"]
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox)):
            raise ValueError(f"bbox_pdf_cm must be 4-element numeric list for panel {panel['id']}")
```

### 5.3 docs/perception-intent-rules.yaml (new external file)

Per intent_type → activated rules. Editable by user (adding rules without touching spec or scripts).

```yaml
schema: figure-agent.perception.intent_rules.v1

network:
  - rule_id: dangling_chain_terminus
    severity: MAJOR
    description: "External path endpoint inside panel with no neighbor within 0.20cm"
    color_filter:
      stroke_must_match: any            # any color triggers; tighten via override
    suppress_on:
      - position_within: 0.10cm of panel edge

plot:
  - rule_id: axis_terminus_suppressed
    severity: INFO
    description: "External path endpoint near panel edge, expected for axis arrows"
    suppress_on:
      - position_within: 0.30cm of panel edge

# More intent_types added as RRD evidence accumulates
```

## 6. Data Flow

### 6.1 Pipeline (single `/fig_compile`)

```
.tex
 │
 ├── (1)-(5) existing checks                              [unchanged]
 │
 └── (6) perceive_build.py
       ├── 6a. extract: pdfplumber → extract.yaml
       │    Read page.chars / page.lines / page.curves / page.rects
       │    Convert to PDF cm; emit YAML.
       │
       ├── 6b. reconstruct: chain segments → reconstructed_paths
       │    Group sequential segments where end_n ≈ start_{n+1} within ε=0.05cm.
       │    External endpoints = first.start, last.end.
       │
       ├── 6c. baseline_topology: lonely cluster detection
       │    Cluster external endpoints within ε=0.20cm; size=1 → lonely.
       │
       ├── 6d. intent_gated: load intent_rules.yaml; for each panel with
       │       intent_type set, apply matching rules → findings.
       │
       ├── 6e. render_overlay: PIL on build/<name>.png + extract.yaml
       │       → build/perception/overlay.png
       │
       └── 6f. write_report: combine 6a-6d + render summary → report.md
```

### 6.2 critique_brief.py integration

Codex BLOCKING #5: current `critique_brief.py:generate_for()` returns single multi-line f-string. The integration is NOT simple `brief +=` concatenation — must thread perception summary into the f-string template.

Fix in implementation plan: refactor `generate_for()` to assemble brief in named sections, append perception section as one of those:

```python
def generate_for(...):
    sections = [
        _briefing_section(briefing),
        _line_numbered_tex_section(tex_path),
        _reference_section(spec, ...),
        _perception_section(example_dir),    # NEW — reads build/perception/*
        _rubric_section(),
    ]
    return "\n\n".join(s for s in sections if s)
```

`_perception_section()` returns "" when `build/perception/` absent (pre-existing fixtures), maintaining backward compat.

### 6.3 Path normalization (Codex BLOCKING #5)

Existing `critique_brief.py` normalizes asset paths to `examples/<name>/...` form. Perception pack paths use same convention: `examples/<name>/build/perception/overlay.png`. Path normalization helper extended trivially.

### 6.4 Coordinate-system reconciliation (Codex BLOCKING #2)

`check_collisions.py` uses pdftotext bbox (different convention). `extract.yaml` uses pdfplumber bbox. Both sit in PDF point space but with different y-axis conventions in some cases.

Solution: both checkers normalize to the same convention (PDF cm, origin at top-left, y increasing downward). Add a `coordinate_space` block to `extract.yaml` (already in §4.1 schema) so downstream consumers can reconcile.

## 7. Testing

### 7.1 Probe-validated empirical baseline

| Quantity | Source | Value |
|---|---|---|
| pdfplumber lines | author probe | 46 |
| pdfplumber curves | author probe | 120 |
| pdfplumber rects | author probe | 10 |
| pdfplumber chars | author probe | 277 |
| Total endpoints (segment-level) | author probe | 332 |
| External endpoints (after reconstruction) | not yet measured (algorithm spike) | TBD in MVP trial |
| Panel A lonely amber (naive ε=0.20cm) | author probe | 2 |
| Figure-wide lonely amber (Codex PyMuPDF) | Codex probe | 4 |
| Expected dangling chain termini in Panel A (visual count) | author manual | 4 in-panel + 2 panel-edge |

### 7.2 Acceptance criteria — realistic

Per v0.4 review, "≤2 spurious flags on golden" was unsubstantiated. Replace with measurable criteria post-implementation:

| Layer | Criterion | Method |
|---|---|---|
| Extract | extract.yaml line count matches `pdfplumber.open(pdf).pages[0].lines` directly | unit test |
| Extract | text bbox positions within 0.05cm of pdftotext bboxes (cross-check) | unit test on golden |
| Reconstruction | 6 polysulfide chains (3 DIB × 2 each) detected as 6 reconstructed_paths | unit test on fig1_overview_v2 |
| Reconstruction | each reconstructed chain has exactly 2 external endpoints | unit test |
| Baseline topology | naive lonely count matches author's pdfplumber probe (332 endpoints, 81 lonely) | regression test |
| Intent-gated network | panel_A with intent_type=network produces ≥3 MAJOR findings on fig1_overview_v2 | trial validation (not strict pass/fail) |
| Intent-gated plot | axis arrowheads suppressed when intent_type=plot | trial validation |

The "Panel A produces N lonely endpoints" claim is **dropped** as a fixed acceptance number. The MVP trial measures what the algorithm actually produces and documents it. Strict thresholds enter only after multi-fixture validation.

### 7.3 Trial protocol

```
1. Implement perceive_build.py per §4 + §6
2. Annotate spec.yaml: panel_A.intent_type=network, panel_D.intent_type=plot, others=other
3. Run /fig_compile fig1_overview_v2 → record perception/topology.yaml output
4. Author manually annotates: which findings are TP / FP / FN
5. Compute precision/recall on intent-gated findings only (T1 is descriptive, not evaluated)
6. Repeat for golden_trap_depth_picture (no network intent → minimal findings expected)
7. Repeat for dogfood_power_law_trap_pipeline (intent_type=plot → axis suppression validation)
```

If Step 4 finds intent-gated precision < 0.5 on first fixture, algorithm spike before promoting to v0.4.2 expansion.

### 7.4 Anti-cases

- pdfplumber missing / install fail → graceful WARN exit, compile continues. Verified by mocking import error.
- Panel without `intent_type` → T2 skipped, T1 still produces extract / topology baseline.
- Panel with `bbox_pdf_cm` mis-specified (out of page) → WARN, skip panel-scoped checks for that panel only.

## 8. v0.4 → v0.4.1 BLOCKING resolution map

| v0.4 BLOCKING | Fix in v0.4.1 |
|---|---|
| Gemini #1: PyMuPDF AGPL not MIT | §4.1 — pdfplumber (MIT) |
| Gemini #2: get_drawings() doesn't return text | §4.1 — separate text + paths code paths via `page.chars`/`extract_words` and `page.lines`/`page.curves` |
| Gemini #3: Topology FP on macro endpoints | §4.2 — path reconstruction (chain sequential segments via endpoint matching) before lonely detection |
| Codex #1: Orthogonality overclaim | §1 + §2 — three-tier model. v0.4.1 explicitly says geometry alone is insufficient; intent declaration gates findings |
| Codex #2: Topology unproven on actual fixture | §7.1 — probe-validated counts substituted; "≤2 spurious flags on golden" claim deleted |
| Codex #3: pymupdf API description wrong | §4.1 — pdfplumber-specific schema, no claim of single-call native dict |
| Codex #4: License + dependency contradiction | §4.1 — pdfplumber required (no AGPL question), no graceful-skip needed for required dep |
| Codex #5: critique_brief.py f-string structure | §6.2 — sectioned refactor approach |
| Codex #6: Scope too large | §3.2 — MVP downscoped to extract + topology + overlay + report. wireframe / edge / alignment / style deferred to v0.4.2 |
| Codex #7: report-only language overstated | §7.2 — "Panel A 6 lonely" hard claim dropped; trial-validation framing |

## 9. Out of scope (intentional, separate specs later)

- **alignment.yaml + style.yaml** — v0.4.2 expansion after MVP validates extract/topology
- **wireframe.png + edge.png + panels/** — deferred per Codex #6
- **Auto bbox computation** from spec.yaml.panels[i].column + width_ratio — v0.4.2
- **Domain rule encoding** (chemistry valence, energy diagram convention) — separate spec
- **Reference-grounded SSIM / diff** — separate spec, alignment-non-trivial
- **Per-panel reference image workflow** — adjacent feature, separate spec
- **`/fig_extract` parity** (build-side vs reference-side same script) — refactor candidate post-v0.4.2

## 10. Decision History

| Decision | Choice | Reason |
|---|---|---|
| v0.4 → v0.4.1 transition | Major revision (not full reject) | 3 of 6 BLOCKING are spec-text errors fixable in revision; algorithm direction salvageable with intent-gating |
| Library | pdfplumber (MIT) | License clean + spec-fact accurate. PyMuPDF MIT claim was wrong; AGPL infect-risk noted but personal-use OK; swap is easier than license carve-out |
| Topology approach | Path reconstruction + intent-gated rules | Naive segment-endpoint clustering FP-explodes (probe). Reconstruction groups segments into paths; intent gates which lonelies count |
| MVP scope | extract + topology + overlay + report only | Codex #6: must validate core thesis before 7-output expansion |
| Acceptance numbers | Probe-validated, no fixed "Panel A = 6" claim | v0.4 made unsubstantiated numerical claims; v0.4.1 measures and documents instead |
| Auto vs intent | T1 + T2 (intent declaration) + T3 (user) | Pure auto unprovable; user-judges-everything is what user pushed back against. T1/T2 split is the honest compromise |
| Coordinate space | Explicit pdf_page_size_cm + source_origin_in_pdf_cm | Codex #2: v0.4 left coord mapping implicit |

## 11. Sources / Empirical evidence

Probes recorded in this spec (cite for trust):

- **pdfplumber probe on fig1_overview_v2.pdf** (author, 2026-05-08): 46 lines, 120 curves, 10 rects, 277 chars, 332 endpoints, 81 lonely (figure-wide), 2 lonely amber in Panel A scope. Validates pdfplumber API works and produces measurable data. Reveals naive ε=0.20cm + amber filter is insufficient (only 2 of expected 4-6 dangling caught).

- **PyMuPDF probe on fig1_overview_v2.pdf** (Codex review, 2026-05-08): 169 paths, 144 stroke endpoints, 72 over 0.20cm, 4 lonely amber (figure-wide). Different segmentation model than pdfplumber, but converges on conclusion that naive algorithm under-counts visually-obvious dangling.

- **PyMuPDF license verification** (Gemini review, 2026-05-08): PyPI metadata shows AGPL/Commercial dual, not MIT. v0.4 §9 was factually wrong.

External:
- pdfplumber documentation: https://github.com/jsvine/pdfplumber (MIT)
- PyMuPDF licensing: https://pypi.org/project/PyMuPDF/ (AGPL/Commercial dual)
- pdfminer.six (pdfplumber dep): https://pypi.org/project/pdfminer.six/ (MIT)

---

_v0.4.1 spec authored 2026-05-08 after v0.4 dual external review. Targets the same build-side perception ceiling as v0.4 but with corrected scope (MVP), corrected dependency (pdfplumber MIT), corrected algorithm (path reconstruction + intent-gating), and probe-validated empirical baselines instead of unsubstantiated numerical claims. Memory `feedback_evidence_check_before_spec` reinforced: v0.4 wrote spec without probe; v0.4.1 spec was written after probe._
