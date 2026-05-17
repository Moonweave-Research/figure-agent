---
description: Vision critique of compiled figure via host Claude Code (no external API). Writes structured critique.md (YAML front-matter + Markdown summary) for one fixture.
---

Generate a structured vision critique for a compiled figure using the **host Claude Code main loop** as the vision LLM. No external Anthropic API call; subscription tokens only.

**Usage**: `/fig_critique <name>`

`<name>` maps to `examples/<name>/`.

Prerequisites:
- `examples/<name>/build/<name>.png` exists (run `/fig_compile <name>` first)
- `examples/<name>/briefing.md` exists

Steps:

1. Run `uv run python3 scripts/critique_brief.py examples/<name>` to obtain the brief. The script verifies the build PNG is fresh against render sources (`<name>.tex`, `briefing.md`, `spec.yaml`, `polymer-paper-preamble.sty`); reference images, `coordinate_hints.yaml`, and authoring context are critique inputs and do not require a recompile by themselves. It then emits the briefing context, optional reference-conditioned authoring context, the line-numbered TikZ source, and the severity/category rubric. If `spec.yaml.panels[]` declares both `reference_image` and `bbox_pdf_cm`, the brief also lists panel crop/reference image pairs for panel-grounded critique; if either field is missing, it emits a WARN and skips that panel comparison. If a participating reference path is missing (`spec.yaml.reference_image`, or panel `reference_image` with `bbox_pdf_cm`), STOP and fix the path or add the file before critique/export.

2. Use the **Read** tool on `examples/<name>/build/<name>.png` to load the rendered figure into the conversation. If the brief contains `## Per-panel reference contexts`, also Read every listed panel build crop and panel reference image. The host model inspects the images directly; do not call any external vision API.

3. Apply the rubric from the brief — Sections A (physics correctness) and B (aesthetic placement) — and produce structured findings. For each finding, identify:
   - `severity`: BLOCKER / MAJOR / MINOR / NIT
   - `category`: physics / label_placement / whitespace / hierarchy / palette / style
   - `tex_lines`: the source line numbers that need revision (cite from the line-numbered .tex in the brief)
   - `observation`: what is wrong, citing what is visible in the PNG
   - `suggested_fix`: a concrete edit to `<name>.tex`

4. Use the **Write** tool to create `examples/<name>/critique.md` with this exact format (YAML front-matter then Markdown body — schema v1):

```markdown
---
schema: figure-agent.critique.v1
fixture: <name>
generated_at: <ISO-8601 timestamp>
verdict: ready | revise | block
panels:
  - id: <panel id>
    findings:
      - id: P001
        severity: MAJOR
        category: structural
        tex_lines: [42, 57]
        observation: "panel crop omits the ring geometry present in the panel reference"
        suggested_fix: "add the missing ring motif inside the panel bbox"
        status: open
findings:
  - id: C001
    severity: MAJOR
    category: physics
    tex_lines: [42, 57]
    observation: "trap depth arrow direction contradicts briefing §6"
    suggested_fix: "reverse arrow and relabel Et axis"
    status: open
---

# Vision Critique — <name>

<one-paragraph overall verdict, then per-finding prose discussion>
```

Use `panels: []` when no panel-level reference comparison was available. Keep cross-panel and whole-figure issues in top-level `findings:`; do not move existing figure-level findings under `panels:`.

`verdict` rules:
- `ready` — zero BLOCKER and zero MAJOR findings
- `revise` — any MAJOR or MINOR findings (or NIT-only)
- `block` — at least one BLOCKER physics violation that makes the figure unsuitable for manuscript use

5. **STOP.** Critique is **report-only**. Do not auto-edit `<name>.tex`; do not stage patches; do not re-compile. The author reads `critique.md`, decides which findings to apply, and edits manually. Auto-apply automation is gated on N=5+ dogfood accuracy ≥ 80% per `docs/architecture-v0.2-proposal.md` §7.

Cost: 0원 (subscription tokens only). The plugin orchestrates; the host Claude Code main loop reads the PNG and produces the critique. `skills/figure-agent/SKILL.md` policy: delegate vision tasks to the host main loop; never call an external vision API directly.
