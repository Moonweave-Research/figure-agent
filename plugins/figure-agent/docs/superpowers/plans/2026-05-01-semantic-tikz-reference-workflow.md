# Semantic TikZ Reference Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the active figure-agent workflow explicitly follow `reference PNG -> OCR + palette clusters + optional vtracer structural hints -> coordinate_hints.yaml -> semantic TikZ authoring -> compile / visual QA / drift check`.

**Architecture:** Preserve figure-agent as a quality kernel, not an SVG auto-vectorizer. Layer 2.5 extracts authoring hints from a reference image, Layer 3 reconstructs the figure as semantic TikZ macros/source, and Layers 4-6 verify rendered output against style and reference-drift gates.

**Tech Stack:** Markdown docs, Claude Code plugin command docs, Python pytest contract tests, ripgrep assertions, existing `reference_extract.py`, `llm_author_prompt.py`, `compile.sh`, and `check_layout_drift.py`.

---

## File Structure

- Modify `plugins/figure-agent/docs/architecture-overview.md`
  - Owns the canonical layer contract.
  - Must define Layer 2.5 as authoring-hint extraction and Layer 3 as semantic TikZ reconstruction.
- Modify `plugins/figure-agent/README.md`
  - Owns the user-facing active workflow summary.
  - Must show `/fig_extract` before authoring and must state SVG/path conversion is not the main path.
- Modify `plugins/figure-agent/skills/figure-agent/SKILL.md`
  - Owns agent behavior when using the plugin.
  - Must tell agents to use `coordinate_hints.yaml` as hints and write semantic TikZ instead of raw SVG/path dumps.
- Modify `plugins/figure-agent/commands/fig_extract.md`
  - Owns slash-command behavior for Layer 2.5.
  - Must document OCR, palette clusters, and optional vtracer structural hints.
- Modify `plugins/figure-agent/prompts/llm_author_tikz.md`
  - Owns the LLM authoring contract.
  - Must explicitly forbid SVG-to-TikZ/path-dump output as the final authoring strategy.
- Modify `plugins/figure-agent/tests/test_release_contract.py`
  - Add lightweight documentation contract tests so this workflow does not drift silently again.

Current working tree note: before executing this plan, preserve the already-present changes that remove `fig3_n2_evidence` and fix the current `ruff`/`pytest` failures. Do not restore or revert unrelated files.

---

### Task 1: Add Documentation Contract Tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_release_contract.py`

- [ ] **Step 1: Write failing tests for the workflow contract**

Append these tests to `plugins/figure-agent/tests/test_release_contract.py`:

```python
def test_active_docs_define_semantic_tikz_reference_workflow() -> None:
    docs = "\n\n".join(
        [
            (REPO_ROOT / "docs" / "architecture-overview.md").read_text(),
            (REPO_ROOT / "README.md").read_text(),
            (REPO_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text(),
        ]
    )

    assert "reference PNG -> OCR + palette clusters + optional vtracer structural hints" in docs
    assert "coordinate_hints.yaml -> semantic TikZ authoring" in docs
    assert "SVG-to-TikZ path conversion is not the active workflow" in docs


def test_authoring_prompt_forbids_path_dump_final_source() -> None:
    prompt = (REPO_ROOT / "prompts" / "llm_author_tikz.md").read_text()

    assert "Do not convert SVG paths into the final TikZ source" in prompt
    assert "Do not pass through SVG path output" in prompt
    assert "Do not emit raw traced path clouds" in prompt
    assert "semantic TikZ macros and named drawing constructs" in prompt


def test_authoring_prompt_requires_semantic_first_order() -> None:
    prompt = (REPO_ROOT / "prompts" / "llm_author_tikz.md").read_text()

    assert "Authoring order (semantic-first)" in prompt
    assert "Look at the reference PNG first" in prompt
    assert "Do not start from coordinate_hints alone" in prompt
    assert "Use coordinate_hints.yaml only to refine placement" in prompt
    assert "recover the missing detail" in prompt
    assert "Do not pass through SVG path output" in prompt  # Maps to step 4; independent from forbids test


def test_fig_extract_documents_structural_hints_as_optional() -> None:
    command_doc = (REPO_ROOT / "commands" / "fig_extract.md").read_text()

    assert "optional vtracer structural hints" in command_doc
    assert "structural hints are authoring evidence, not final source" in command_doc
    assert "OCR + palette clusters still remain useful" in command_doc
```

- [ ] **Step 2: Run tests to verify they fail**

Run from `plugins/figure-agent`:

```bash
uv run pytest tests/test_release_contract.py -v
```

Expected: the new tests fail because the exact contract strings are not present yet.

- [ ] **Step 3: Commit the failing tests**

```bash
git add plugins/figure-agent/tests/test_release_contract.py
git commit -m "test: lock semantic TikZ reference workflow docs"
```

If the repository policy for this cleanup is no intermediate commits, skip the commit command and keep the file staged boundary clear with `git diff -- plugins/figure-agent/tests/test_release_contract.py`.

---

### Task 2: Update the Canonical Architecture Contract

**Files:**
- Modify: `plugins/figure-agent/docs/architecture-overview.md`

- [ ] **Step 1: Replace the layer diagram wording**

In the layer diagram, change Layer 2.5 and Layer 3 to this wording:

```markdown
Layer 2.5: Reference Analysis          (OCR + palette clusters + optional vtracer hints)
   |
   v
Layer 3: Semantic TikZ Authoring       (<name>.tex + polymer-paper-preamble.sty)
```

- [ ] **Step 2: Rewrite the Layer 2.5 section**

Replace the current Layer 2.5 section body with:

```markdown
### Layer 2.5 — Reference Analysis

**Files**: `scripts/reference_extract.py`, `commands/fig_extract.md`,
`tests/test_reference_extract.py`, `examples/<name>/coordinate_hints.yaml`.

This layer runs between Layer 2 (Authoring Intent) and Layer 3 (Semantic
TikZ Authoring). The active workflow is:

```
reference PNG -> OCR + palette clusters + optional vtracer structural hints
-> coordinate_hints.yaml -> semantic TikZ authoring
```

`coordinate_hints.yaml` is an authoring-evidence file, not generated final
source. It can contain:

- `text_labels[]` — OCR-detected labels with pixel bounding boxes and
  confidence scores.
- `palette_shape_clusters{}` — connected components matching the Style Lock
  palette colors.
- `structural_regions{}` — optional vtracer-derived regions such as panel
  arcs, border boxes, chain rows, atom positions, trap levels, plot boxes,
  plot curves, and lobe-like regions.

`structural_regions.status` may be `ok`, `unavailable`, or `failed`.
Unavailable vtracer does not invalidate the workflow: OCR + palette clusters
still remain useful authoring hints, and Layer 3 must continue from the
available evidence.

Layer 2.5 must not be treated as an SVG-to-TikZ conversion layer. VTracer and
SVG-derived paths are allowed only as evidence for approximate placement,
color grouping, and coarse geometry. SVG-to-TikZ path conversion is not the
active workflow because it produces low-level path code without the semantic
macro structure needed for manuscript editing.
```

- [ ] **Step 3: Rewrite the Layer 3 opening**

Replace the first paragraphs of Layer 3 with:

```markdown
### Layer 3 — Semantic TikZ Authoring

**Files**: `examples/<name>/<name>.tex`, `styles/polymer-paper-preamble.sty`,
`styles/tex_template.tex`, `prompts/llm_author_tikz.md`.

A human or LLM authors semantic TikZ source from `briefing.md`, `spec.yaml`,
the reference PNG, and any available `coordinate_hints.yaml`. The output is a
maintainable `.tex` file built from named macros, scoped styles, and readable
TikZ constructs. Raw SVG path dumps, auto-traced path clouds, and direct
SVG-to-TikZ conversion are not acceptable as the final source for the active
workflow.

Use coordinate hints as placement evidence:

- OCR labels guide text content and label positions.
- Palette clusters guide color family and coarse shape placement.
- Optional vtracer structural hints guide panel boxes, chain rows, trap
  levels, and major geometry.

The authoring target is semantic reconstruction, not pixel-for-pixel path
transcription.
```

- [ ] **Step 4: Run the contract test for architecture docs**

Run:

```bash
uv run pytest tests/test_release_contract.py::test_active_docs_define_semantic_tikz_reference_workflow -v
```

Expected: it may still fail until README and SKILL are updated in later tasks.

- [ ] **Step 5: Commit architecture doc update**

```bash
git add plugins/figure-agent/docs/architecture-overview.md
git commit -m "docs: define semantic TikZ reference workflow architecture"
```

If using a single cleanup commit, leave this uncommitted and continue.

---

### Task 3: Update README and Skill Workflow Surfaces

**Files:**
- Modify: `plugins/figure-agent/README.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`

- [ ] **Step 1: Update the active workflow block in README**

Replace the README active workflow code block with:

```markdown
```
/fig_new <name>          scaffold (briefing + spec)
                         [user saves reference PNG and records it as
                          spec.yaml.reference_image when target matching matters]
/fig_extract <name>      OCR + palette clusters + optional vtracer structural hints
                         -> coordinate_hints.yaml
                         [human/LLM authors semantic TikZ from briefing intent,
                          reference PNG, and coordinate_hints.yaml;
                          SVG-to-TikZ path conversion is not the active workflow]
/fig_compile <name>      Style Lock + PDF/PNG build + collision/clash + drift check
                         (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_export <name>       PDF / SVG (dvisvgm preserves text) / TIFF / PNG
/fig_status [<name>]     stage + accepted-state inference; legacy hints carry a [legacy] marker
```
```

- [ ] **Step 2: Add README policy paragraph after the active workflow block**

Insert:

```markdown
The active authoring contract is semantic reconstruction. `coordinate_hints.yaml`
provides placement evidence, but the final source should be readable TikZ using
shared macros and named drawing constructs. SVG-to-TikZ path conversion is not
the active workflow; it may be used only as a diagnostic or reference aid when
manual geometry inspection is useful.
```

- [ ] **Step 3: Update the active workflow block in SKILL.md**

Apply the same active workflow block used in README to
`plugins/figure-agent/skills/figure-agent/SKILL.md`.

- [ ] **Step 4: Add SKILL authoring rule paragraph**

Under `## Workflow shape`, after the active workflow block, insert:

```markdown
Agent rule: when `coordinate_hints.yaml` exists, read it before authoring or
reviewing `<name>.tex`. Use OCR labels, palette clusters, and optional vtracer
structural hints as evidence for layout and color placement. Do not convert SVG
paths into the final TikZ source; produce semantic TikZ macros and named
drawing constructs that remain editable during manuscript revision.
```

- [ ] **Step 5: Run the docs contract test**

Run:

```bash
uv run pytest tests/test_release_contract.py::test_active_docs_define_semantic_tikz_reference_workflow -v
```

Expected: PASS after README, SKILL, and architecture docs all contain the contract strings.

- [ ] **Step 6: Commit README and skill changes**

```bash
git add plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md
git commit -m "docs: align user workflow with semantic TikZ authoring"
```

If using a single cleanup commit, leave this uncommitted and continue.

---

### Task 4: Update `/fig_extract` Command Contract

**Files:**
- Modify: `plugins/figure-agent/commands/fig_extract.md`

- [ ] **Step 1: Update the description metadata**

Change the frontmatter description to:

```yaml
description: Extract OCR labels, palette clusters, and optional vtracer structural hints from a reference PNG into coordinate_hints.yaml.
```

- [ ] **Step 2: Update the opening paragraph**

Replace the opening paragraph with:

```markdown
Extract authoring hints from the fixture's reference image. Output is written
to `examples/<name>/coordinate_hints.yaml` and feeds semantic TikZ authoring in
Layer 3 plus layout drift validation in Layer 6. The output is evidence for
placement and color reconstruction; structural hints are authoring evidence,
not final source.
```

- [ ] **Step 3: Update the "What it does" list**

Replace the existing five-item list with:

```markdown
1. Resolves `spec.yaml.reference_image` to an absolute path; aborts if missing.
2. Loads the reference as RGB (RGBA / palette PNGs are converted; alpha is dropped).
3. Runs Tesseract OCR for text labels with bounding box and confidence.
4. Runs a palette PIL connected-component pass for each `polymer-paper-preamble`
   palette color, with per-group RGB-distance thresholds and a
   `min_component_pixels` filter.
5. Runs optional vtracer structural hints when the `vtracer` Python package is
   importable. If vtracer is unavailable or fails, OCR + palette clusters still
   remain useful and the command writes `structural_regions.status` as
   `unavailable` or `failed`.
6. Writes the joined result to `coordinate_hints.yaml` with metadata,
   reference SHA-256, extraction parameters, and available hint groups.
```

- [ ] **Step 4: Add schema excerpt for structural regions**

Extend the YAML excerpt with:

```yaml
structural_regions:
  status: ok                   # ok | unavailable | failed
  panel_arcs: []
  border_boxes: []
  chain_rows: []
  s_atoms: []
  trap_levels: []
```

- [ ] **Step 5: Add common error for vtracer**

Add this bullet under "Common errors":

```markdown
- `structural_regions.status: unavailable` — `vtracer` is not importable in the
  current Python environment. This does not block authoring: OCR + palette
  clusters still remain useful placement evidence. Install or enable vtracer
  only when structural hints are needed for a fixture.
```

- [ ] **Step 6: Run the fig_extract contract test**

Run:

```bash
uv run pytest tests/test_release_contract.py::test_fig_extract_documents_structural_hints_as_optional -v
```

Expected: PASS.

- [ ] **Step 7: Commit command doc update**

```bash
git add plugins/figure-agent/commands/fig_extract.md
git commit -m "docs: document optional structural hints in fig_extract"
```

If using a single cleanup commit, leave this uncommitted and continue.

---

### Task 5: Update LLM Authoring Prompt Contract

**Files:**
- Modify: `plugins/figure-agent/prompts/llm_author_tikz.md`

- [ ] **Step 1: Add hard constraint against path dumps**

In `## 2. Hard Constraints`, add this bullet after the scaffolding contract bullet:

```markdown
- Do not convert SVG paths into the final TikZ source. Do not emit raw traced
  path clouds as the main figure body. Use semantic TikZ macros and named
  drawing constructs so the source remains editable.
```

- [ ] **Step 2: Replace section 5b heading and body**

Replace `## 5b. Structural Regions from Reference Image (Layer 2.5)` and its body with:

```markdown
## 5b. Coordinate Hints from Reference Image (Layer 2.5)

When a reference image is provided, follow the authoring order below. When no
reference image is provided (briefing-only fixtures), skip steps 1 and 3 and
author directly from §6 invariants and §3 composition intent.

Authoring order (semantic-first):

1. Look at the reference PNG first. Internally decompose the figure into N
   semantic units: boxes, arrows, curves, labels, groups, axes of symmetry. Do
   not start from coordinate_hints alone. Internally decompose (do not include
   the decomposition in the output; emit only the .tex body per §1).
2. Map each semantic unit to a polymer-paper-preamble macro when one fits;
   plan custom drawing constructs for the remainder.
3. Use coordinate_hints.yaml only to refine placement and color binding,
   not as the source of truth for the figure body.
4. Author semantic TikZ macros. Do not pass through SVG path output.

Important:
- OCR labels guide text content and approximate label boxes.
- Palette clusters guide color families and coarse shape positions.
- Optional structural regions guide major geometry when available.
- Missing hints do not invalidate the reference; recover the missing detail
  by looking at the reference PNG directly.
- The SVG-path prohibition is the §2 Hard Constraint; this section reinforces
  the positive authoring order rather than redefining it (see §2).
- Reconstruct the figure as semantic TikZ macros and named drawing constructs.

{{structural_regions}}
```

Rationale: Without an explicit semantic-first order, an LLM can read
coordinate_hints alone and emit hint-by-hint coordinate dumps that are
technically not SVG paths but are equally non-semantic. Forcing a "look at the
PNG, decompose, then map to macros" sequence makes the reference image — not
the hints file — the source of structural intent.

- [ ] **Step 3: Add output-contract bullet**

Under `## 7. Output Contract`, add:

```markdown
- Use coordinate_hints.yaml as placement evidence when available, but write
  maintainable semantic TikZ rather than path-transcribed output.
```

- [ ] **Step 4: Run the prompt contract test**

Run:

```bash
uv run pytest tests/test_release_contract.py::test_authoring_prompt_forbids_path_dump_final_source -v
```

Expected: PASS.

- [ ] **Step 5: Commit prompt update**

```bash
git add plugins/figure-agent/prompts/llm_author_tikz.md
git commit -m "docs: require semantic TikZ authoring from reference hints"
```

If using a single cleanup commit, leave this uncommitted and continue.

---

### Task 6: Full Verification and Drift Check

**Files:**
- Verify all modified files from Tasks 1-5.

- [ ] **Step 1: Verify no deleted fixture references remain**

Run from repo root:

```bash
rg -n "fig3_n2_evidence|golden_target_002" plugins/figure-agent \
  --glob '!plugins/figure-agent/docs/superpowers/plans/**' || true
```

Expected: no output outside execution-plan history.

- [ ] **Step 2: Verify the new workflow contract strings are present**

Run from repo root:

```bash
rg -n "reference PNG -> OCR \\+ palette clusters \\+ optional vtracer structural hints|coordinate_hints.yaml -> semantic TikZ authoring|SVG-to-TikZ path conversion is not the active workflow" plugins/figure-agent/docs/architecture-overview.md plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md
```

Expected: all three phrases appear in the active docs surface.

- [ ] **Step 3: Run release contract tests**

Run from `plugins/figure-agent`:

```bash
uv run pytest tests/test_release_contract.py -v
```

Expected: all tests in `test_release_contract.py` pass.

- [ ] **Step 4: Run full test suite**

Run:

```bash
uv run pytest
```

Expected: full suite passes. Current baseline after deleting `fig3_n2_evidence` is `207 passed, 4 skipped`. After this plan adds both defensive and constructive test cases (`test_authoring_prompt_requires_semantic_first_order` with new assertion, plus strengthened forbids test), baseline becomes `208 passed, 4 skipped`.

- [ ] **Step 5: Run linter**

Run:

```bash
uv run ruff check .
```

Expected: `All checks passed!`

- [ ] **Step 6: Run plugin validation**

Run:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all three commands print `Validation passed`.

- [ ] **Step 7: Review final diff**

Run from repo root:

```bash
git diff --stat
git diff -- plugins/figure-agent/docs/architecture-overview.md plugins/figure-agent/README.md plugins/figure-agent/skills/figure-agent/SKILL.md plugins/figure-agent/commands/fig_extract.md plugins/figure-agent/prompts/llm_author_tikz.md plugins/figure-agent/tests/test_release_contract.py
git status --short
```

Expected: diff is limited to the workflow docs/prompt/test contract plus the previously intentional `fig3_n2_evidence` removal and priority-1 gate fixes.

- [ ] **Step 8: Commit final workflow cleanup**

If previous tasks were not committed individually, commit the full scoped cleanup:

```bash
git add plugins/figure-agent/docs/architecture-overview.md \
  plugins/figure-agent/README.md \
  plugins/figure-agent/skills/figure-agent/SKILL.md \
  plugins/figure-agent/commands/fig_extract.md \
  plugins/figure-agent/prompts/llm_author_tikz.md \
  plugins/figure-agent/tests/test_release_contract.py \
  plugins/figure-agent/scripts/llm_author_prompt.py \
  plugins/figure-agent/scripts/reference_extract.py \
  plugins/figure-agent/styles/polymer-paper-preamble.sty \
  plugins/figure-agent/tests/test_reference_extract.py \
  plugins/figure-agent/tests/test_status.py
git add -u plugins/figure-agent/docs/macro-audit.md \
  plugins/figure-agent/docs/roadmap-layer3-6.md \
  plugins/figure-agent/examples/fig3_n2_evidence
git commit -m "docs: codify semantic TikZ reference workflow"
```

Expected: commit succeeds. Leave `output/` untracked unless the user explicitly asks to keep or remove it.

---

## Self-Review

- Spec coverage: The plan covers canonical architecture, user README, agent skill behavior, `/fig_extract` command docs, LLM prompt contract, tests, and full verification.
- Placeholder scan: No implementation step depends on unspecified content; every changed text block and command is included explicitly.
- Type consistency: The plan consistently uses `coordinate_hints.yaml`, `text_labels`, `palette_shape_clusters`, `structural_regions`, `semantic TikZ authoring`, and `SVG-to-TikZ path conversion is not the active workflow`.
- Scope check: This is one cohesive docs/prompt/test contract update. It does not add `vtracer` as a dependency and does not implement new extraction behavior.
- Defensive vs constructive contract: Task 5 carries both a negative constraint (no SVG path dump, no raw path clouds) and a positive authoring order (semantic-first: PNG -> internal decompose -> macro map -> refine with hints). Task 1 Step 1 locks both axes with independent tests: `test_authoring_prompt_forbids_path_dump_final_source` validates negative phrasing; `test_authoring_prompt_requires_semantic_first_order` validates positive workflow order. If either wording drifts, the appropriate test fails.
