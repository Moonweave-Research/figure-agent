# Architecture v0.4.2 — Perception Data Only (D-1)

**Status:** DRAFT (2026-05-08) — handoff to Codex session for implementation
**Predecessors (rejected):** `architecture-v0.4-build-perception-pack.md`, `architecture-v0.4.1-build-perception-pack.md`. See `feedback_perception_spec_rejected.md` for the lesson driving this scope.
**Successor companion:** `architecture-v0.5-per-panel-reference-workflow.md` (D-2).
**Scope owner:** Codex session (implementation), not this session.

---

## 1. Problem Statement

Build-stage agent and user grind both need richer per-shape data from the rendered PDF (path coordinates, text placement, primitive types). v0.4 / v0.4.1 attempted to **judge** that data ("is endpoint X dangling?") and failed twice — same PDF gave 4 different "lonely" counts depending on segmentation, color tolerance, and T-junction rules. The judgment is taste-dependent.

v0.4.2 ships only the **descriptive layer**: extract every primitive pdfplumber emits, and overlay endpoint markers on the rendered PNG so the user can see them. No clustering. No `lonely` boolean. No `topology.yaml`. No `intent_type`. No auto-detection rules.

## 2. Non-Goals (explicit, locked)

- ❌ "Lonely endpoint" detection or any structural-awkwardness judgment.
- ❌ Topology graph, cluster size, dangling-tip detection.
- ❌ `topology.yaml`, `style.yaml`, `alignment.yaml`, `wireframe.png`, `edge.png`, panel crops.
- ❌ Per-panel `intent_type` enum, `intent_rules.yaml`, network/plot/process distinction.
- ❌ Manual `bbox_pdf_cm` author burden (no per-panel coordinate authoring required).
- ❌ Any claim that the pack will catch fig1_overview_v2 Panel A's chain dangling.

The pack is a **data lens**, not a critic. Whatever judgment happens uses this data — but judgment lives in `/fig_critique` (host LLM) or in the user's own grind, not here.

## 3. Outputs (locked: 2 only)

```
build/<name>/
  perception/
    extract.yaml       # every pdfplumber primitive, normalized to one cm convention
    overlay.png        # rendered PNG with endpoint dots + small labels
```

No `report.md`, no `topology.yaml`. The two outputs alone are enough for a user grepping/eyeballing during grind, and enough for the host LLM in `/fig_critique` to reference if it wants.

## 4. extract.yaml schema

```yaml
schema_version: "0.4.2"
source:
  pdf_path: build/<name>/<name>.pdf
  pdf_size_cm: [W, H]              # pdfplumber page.width/72*2.54, etc.
coordinate_space:
  pdf_origin: top_left
  y_axis: down
  units: cm
  # No source-cm mapping. Author works in PDF cm only.
  # If user supplies coordinate_hints.yaml, the existing Layer 2.5
  # mapping handles source↔PDF separately.
primitives:
  lines:
    - id: l_0001
      x0: 1.234
      y0: 5.678
      x1: 2.345
      y1: 5.678
      stroke_rgb: [0.20, 0.40, 0.80]
      linewidth_pt: 0.6
  curves:
    - id: c_0001
      pts: [[x0,y0], [x1,y1], ...]   # full pdfplumber `pts` list
      stroke_rgb: [...]
      linewidth_pt: 0.6
      fill_rgb: null
  rects:
    - id: r_0001
      x0: 0.27
      y0: 0.27
      x1: 17.81
      y1: 10.95
      stroke_rgb: [...]
      fill_rgb: null
  chars:                              # per-char text, NOT word-grouped
    - id: ch_0001
      text: "A"
      x0: 0.40
      y0: 0.45
      x1: 0.58
      y1: 0.62
      fontname: "TeX-..."
      size_pt: 8.0
counts:
  lines: <N>
  curves: <N>
  rects: <N>
  chars: <N>
  endpoints_total: <N>               # 2 * (lines + curves) - rect-shared
```

**Coordinate convention is locked to PDF cm** (top-left origin, y-down). No source-cm conversion is performed by this layer. If/when source mapping is needed downstream, it is computed there using `\resizebox` width and `border` from the .tex (correct math: `cm_per_source = scaled_content_width_cm / source_canvas_cm`; `origin_offset = border_pt * 2.54 / 72`).

## 5. overlay.png

Render = build/<name>.png with:
- Small filled dot (radius ~3 px) at each line/curve endpoint, color-matched to the stroke (so red strokes get red dots, etc.).
- Tiny ID label (3-4 chars, e.g., `c_0001`) next to each dot at small font.
- No clustering visualization. No "lonely" highlighting. No bbox boxes.

Output via PIL or matplotlib over the existing build PNG. No additional render of the PDF.

## 6. Pipeline & Layer

New step in `/fig_compile` after PDF emit, before `/fig_critique`. Tentative skill ID: `extract_perception_pack` (or fold into `compile.py` post-step).

```
L4 lualatex compile  →  L4.1 perception extract (NEW, this spec)  →  L4.5 critique
```

**Trigger:** every `/fig_compile` run that produces a PDF. Always-on, not optional.

**Failure policy:** if pdfplumber import fails, **hard fail with clear error** (`pdfplumber required for perception pack — uv add pdfplumber`). No "graceful skip and warn" — that path was the v0.4.1 contradiction.

**Dependency:** add `pdfplumber>=0.11.4` to runtime dependencies in `pyproject.toml` (currently dev-only). MIT license, no AGPL concerns.

## 7. Probe baseline (single fixture, descriptive only)

For `fig1_overview_v2/build/fig1_overview_v2.pdf` as of 2026-05-08:

| Field | Value |
|---|---|
| pdf_size_cm | [18.08, 11.22] |
| lines | 46 |
| curves | 120 |
| rects | 10 |
| chars | 277 |
| endpoints_total | 332 |

These are sanity-check values, not regression gates. If a re-run gives different numbers because the .tex changed, that's expected — there's no "Panel A produces N lonely" claim to defend.

## 8. Acceptance criteria

1. `uv run pytest` continues to pass (no new failures).
2. Running `/fig_compile fig1_overview_v2` produces `build/fig1_overview_v2/perception/extract.yaml` and `overlay.png`.
3. extract.yaml validates against the §4 schema.
4. overlay.png loads in any image viewer; endpoint dots are visible.
5. Per-fixture probe rerun for fig1_overview_v2 reproduces §7 counts within ±2 (small drift OK from pdfplumber version updates).
6. `/fig_critique` is unchanged in behavior — it does NOT have to consume the pack in v0.4.2. (Optional follow-up in v0.4.3: add a single line to `critique_brief.py` that says "perception pack at `build/.../perception/extract.yaml` if useful.")

## 9. What this does NOT solve

- Does not catch Panel A dangling chains automatically. User catches them by eyeballing overlay.png (the dots show where endpoints are; the user sees "those don't connect to anything").
- Does not provide a "lonely score" or any other auto-judgment.
- Does not address mixed-intent panels (no intent enum at all).
- Does not provide source-cm coordinates.

These are intentional. The corresponding workflow lives in `architecture-v0.5-per-panel-reference-workflow.md`.

## 10. Codex session implementation notes

- New file: `scripts/perception_pack.py`. Single function `build_perception_pack(name: str) -> None` that reads `build/<name>/<name>.pdf` and writes the two outputs.
- Wire into `/fig_compile` after the existing checks.
- Tests: `tests/test_perception_pack.py` with the §7 fixture as a regression case (counts only, no topology assertions).
- Add pdfplumber to runtime deps. Update `uv.lock`.
- Do NOT add new commands or skills. The pack is internal to `/fig_compile`.

## 11. Out-of-scope reminders

If during implementation the temptation arises to "while we're at it, also flag X":
- "this endpoint looks lonely" → STOP. Out of scope. v0.4 line is closed for that.
- "let's group lines/curves into paths" → STOP. Out of scope. Just dump raw primitives.
- "let's auto-detect panel bboxes from the rect grid" → STOP. v0.5 handles panels via spec.yaml, not auto-discovery.

If a feature feels like "obvious next step" but isn't in §3-§5, it belongs in v0.4.3 or later, not this MVP.
