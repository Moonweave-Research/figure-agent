# Roadmap — v0.1.7 selection_notes integration & superseded v0.2 branches

Status: shipped 2026-04-29 (v0.1.7) → hardened 2026-04-29 (v0.1.7.1 per agent-team mid-review) → superseded by `docs/quality-kernel-goal.md`
Drafted: 2026-04-29
Owner: Moon-python
Predecessor doc: `docs/design-v0.1.md`

**Ship retrospective (2026-04-29)**:
- v0.1.7 landed in 6 commits (`c1c2a01..39c6cf9`) — the planned 5 plus one
  unplanned `chore` commit fixing a ruff E501 line-length finding caught
  by the pre-ship gate.
- v0.1.7.1 followed in 4 commits (`476233e..` through the v0.1.7.1 release
  commit) addressing four findings from a 4-agent mid-review: non-string
  type coercion with stderr warning, empty-after-HTML-strip warning,
  fallback sentinel parity (`(none)` instead of editorial prose), priority
  paragraph reordered before the placeholder + extension clause added.
- All 108 tests green, ruff clean. v0.1.x empirical validation window
  begins now per the section below.

## TL;DR

`spec.yaml.selection_notes` is currently an orphan field — declared, parsed,
but never read by any production script. v0.1.7 plumbs it into the LLM
authoring prompt with HTML-comment stripping (briefing parity) and adds
priority-order instructions to the template so the LLM knows how to weight it
against §6 invariants and §3 composition intent. No new slash command.
`/fig_decompose` is rejected for v0.1 and conditionally deferred to v0.2.

**2026-04-29 update:** this roadmap is historical for the v0.1.7
`selection_notes` work. Its v0.2 orchestration branches are no longer the active
direction. The current product and execution authorities are
`docs/product-spec.md` and `docs/execution-plan.md`.

## Why this exists

Initial discussion (2026-04-29) considered adding a new `/fig_decompose` step
between `/fig_preview_select` and TikZ authoring to capture preview-grounded
element inventory. Repo audit by 4 parallel agents found:

1. The user already writes preview-grounded element inventory by hand into
   `spec.yaml.selection_notes` (see `examples/fig3_trap_schematic_v97/spec.yaml`,
   `examples/fig3_trapping_concept/spec.yaml:9-18`).
2. `selection_notes` is **never** read by any script outside tests.
3. `prompts/llm_author_tikz.md` has no placeholder for it and no priority-order
   instructions for the LLM.

Plumbing this existing hook is sufficient as the first prescription. A new
slash command would duplicate work the user is already doing in spec.yaml.

## Audit findings (evidence base)

### Confirmed (4-agent consensus)

| Finding | Evidence |
|---|---|
| `selection_notes` is orphan in production code | `scripts/inputs.py:15` parses via `yaml.safe_load`; no `.get("selection_notes")` anywhere outside tests |
| `selected_preview` is consumed as filename string only | `scripts/llm_author_prompt.py:93`, `scripts/status.py:162-166` — no pixel/vision/multimodal access |
| No alternative semantic-layer scaffold exists | grep for `inventory|decompos|semantic|reconstruct|element|layer_plan|preview_brief|decomposition` returns 0 production references |
| `parse_briefing` already strips HTML comments | `scripts/inputs.py:49` `_HTML_COMMENT.sub("", ...)` — selection_notes plumbing must mirror this |
| Author-only HTML comment pattern is real | `examples/fig3_trap_schematic_v97/briefing.md:30` has `<!-- AUTHOR NOTE -->`; same pattern will appear in selection_notes |

### Gaps the initial v0.1.7 plan missed

These are required additions found in audit, not feature creep:

1. **Template instruction text (priority order).** Without telling the LLM how
   to weight `selection_notes` vs §6 invariants vs §3 composition intent, even
   correct plumbing leaves the LLM unable to use the field principled-ly.
2. **`/fig_new` scaffold update.** `commands/fig_new.md:17` does not initialize
   `selection_notes` in the spec.yaml output. Future examples will lack the key
   entirely and silently fall through to the fallback string.
3. **Documentation of the field.** `selection_notes` is not mentioned in
   `docs/design-v0.1.md`, `commands/fig_preview_select.md`, README.md, AGENTS.md,
   CLAUDE.md, or SKILL.md. Users won't know to use it without doc updates.
4. **Test coverage.** Existing tests would silently pass if the placeholder were
   added but the substitution dict missed it. New tests required.

### Test fragility surface

| Risk | Location | Mitigation |
|---|---|---|
| `examples/fig3_trapping_concept/spec.yaml` is hardcoded-asserted | `tests/test_inputs.py:138-163` `test_parse_spec_real_fig3_fixture_pinned` | Do not modify this fixture in v0.1.7 |
| Existing LLM author tests don't verify selection_notes plumbing | `tests/test_llm_author_prompt.py:19-28, 62-75` | Add 4 new tests (Commit 2 below) |

## v0.1.7 — Commit-by-commit plan

Five commits, each independently reviewable.

### Commit 1 — core plumbing

Files:

- `scripts/inputs.py`
  - No code change. Confirm `_HTML_COMMENT` is importable (it is — module-level
    private but accessible).

- `scripts/llm_author_prompt.py`
  - Update import: `from inputs import parse_briefing, parse_spec, _HTML_COMMENT`
  - After `sections = parse_briefing(...)` (line ~80), insert:
    ```python
    selection_notes_raw = spec.get("selection_notes", "") or ""
    selection_notes = _HTML_COMMENT.sub("", selection_notes_raw).strip() or "(none — only preview filename selected)"
    ```
  - Add to substitutions dict: `"{{selection_notes}}": selection_notes`

- `prompts/llm_author_tikz.md`
  - In §6 (Spec Context), after `### Selected preview` block, insert:
    ```markdown
    ### Selection notes (preview-grounded authoring guide)

    {{selection_notes}}

    These notes refine §3 composition intent with preview-specific element
    placement, palette use, and corrections. Priority order: §6 invariants >
    §3 composition intent > selection notes. When selection notes conflict
    with §6, honor §6 and ignore the conflicting note.
    ```

### Commit 2 — tests

File: `tests/test_llm_author_prompt.py`. Add 4 tests:

1. `test_selection_notes_plumbed_when_present`
   - tmp_path fixture with spec.yaml containing multi-line `selection_notes`
   - assert body substring appears in `build_prompt()` output

2. `test_selection_notes_strips_html_comments`
   - tmp_path fixture with `selection_notes: "<!-- internal -->visible text"`
   - assert "internal" not in output, "visible text" in output

3. `test_selection_notes_fallback_when_absent`
   - tmp_path fixture with spec.yaml missing the key entirely
   - assert fallback string `"(none — only preview filename selected)"` in output
   - assert no `{{` literal in output

4. `test_selection_notes_preserves_backslashes`
   - tmp_path fixture with `selection_notes: "use \\frac{1}{2} ratio"`
   - assert backslashes survive substitution (str.replace, not regex)

### Commit 3 — UX & scaffold docs

- `commands/fig_preview_select.md`
  - In step 5, add recommended (not enforced) 4-heading template:
    ```yaml
    selection_notes: |
      Visual motifs to preserve:
        - ...
      Preview errors to fix in TikZ:
        - ...
      Labels to lift:
        - ...
      Style overrides:
        - ...
    ```
  - Note free-form is acceptable; structure is recommendation only.

- `commands/fig_new.md`
  - In the spec.yaml scaffold output (line ~17), add `selection_notes: ""`
    placeholder between `selected_preview: null` and end of file.

- `docs/design-v0.1.md`
  - In the spec.yaml field description list (around line 160), add
    `selection_notes` with one-line description.

### Commit 4 — dogfood fixture refresh (selective)

- `examples/fig3_trap_schematic_v97/spec.yaml`
  - Reorganize existing `selection_notes` into the 4-heading structure.
    Preserve all content; reformatting only.

- `examples/fig3_trapping_concept/spec.yaml` — **DO NOT MODIFY**.
  `tests/test_inputs.py:138-163` hardcoded-asserts the current text.

- `examples/smoke_trap_demo/spec.yaml` — leave as-is. Single-line form is
  intentional fixture diversity (covers short-form path).

### Commit 5 — version & changelog

- `pyproject.toml` — bump `0.1.6` → `0.1.7`.

- `CHANGELOG.md` — new entry:
  ```markdown
  ## 0.1.7 (2026-04-29)

  - feat(llm_author_prompt): plumb spec.yaml selection_notes into LLM
    authoring prompt with HTML-comment stripping (briefing parity).
  - feat(prompts/llm_author_tikz): add priority order text — §6 invariants >
    §3 composition intent > selection notes.
  - feat(fig_new): scaffold spec.yaml with empty selection_notes key.
  - docs(fig_preview_select): document 4-heading recommended template.
  - docs(design-v0.1): add selection_notes to spec.yaml field list.
  - test: 4 new tests covering plumbing, HTML strip, fallback, backslash safety.
  ```

## Pre-ship gate

```bash
cd "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent"

# 1. All tests green
uv run pytest tests/ -v

# 2. Each example renders prompt cleanly (selection_notes body must appear,
#    no {{ literal, no HTML comments leaking)
uv run python3 scripts/llm_author_prompt.py examples/fig3_trap_schematic_v97
uv run python3 scripts/llm_author_prompt.py examples/fig3_trapping_concept
uv run python3 scripts/llm_author_prompt.py examples/smoke_trap_demo

# 3. Compile regression (existing examples still produce identical PDFs)
bash scripts/compile.sh examples/fig3_trapping_concept/fig3_trapping_concept.tex
bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex
bash scripts/compile.sh examples/fig3_trap_schematic_v97/fig3_trap_schematic_v97.tex
```

Manual verification:

- Spot-check rendered prompt for the 4-heading example — heading structure
  preserved, priority order text appears.
- Spot-check rendered prompt for fig3_trapping_concept — original free-form
  text appears verbatim.
- Construct one test spec.yaml with `<!-- AUTHOR -->` in selection_notes,
  verify it does NOT appear in rendered prompt.

## v0.1.x — empirical validation window (2-4 weeks post-ship)

No code changes. Data collection only.

For each new figure authored with v0.1.7, append `examples/<name>/REVIEW.md`:

```markdown
# v0.1.7 selection_notes empirical review — <example_name>

- Time spent writing selection_notes (minutes):
- Number of 4-headings actually used (0-4):
- LLM TikZ output quality contribution (low/mid/high):
- Estimated invariant violations avoided by selection_notes:
- Was free-form distracting (yes/no):
- Would structured interview have been faster (yes/no/same):
- Notes:
```

Aggregate after 2-3 figures. Decision input for v0.2 branching.

## v0.2 — trigger-based decision branches (superseded)

These branches are superseded by the quality-kernel direction. Keep them as
historical context only; do not implement them unless future dogfooding proves a
repeated non-transient need after the kernel is credible.

### Branch 1 — Status quo
**Trigger:** free-form distracting ≤1 case, avg 4-headings used ≥3, LLM
quality mid+ in ≥2 cases.
**Action:** No selection_notes work. Move to other v0.2 milestones.

### Branch 2 — Structured interview in `/fig_preview_select`
**Trigger:** free-form distracting ≥2 cases, OR avg 4-headings used ≤2, OR
user repeats same meta-questions every figure.
**Action:** Extend `/fig_preview_select` with bidirectional interview —
heading-by-heading prompts that auto-serialize to spec.yaml. No new slash.
**Scope:** ~3-4 days. `commands/fig_preview_select.md` + new
`scripts/interview_selection_notes.py` + tests.
**Risk:** interview length adds friction. Build skip option from day one.

### Branch 3 — `/fig_decompose` slash command
**Trigger:** ① Branch 2's free-form/structured can't capture a layer that
emerges (SVG layer plan, Illustrator group hierarchy, multi-preview blend
mapping), OR ② quantitative evidence ≥2 cases shows selection_notes fundamentally
insufficient.
**Action:** Workflow expands 6→7 steps. New artifact:
`examples/<name>/decomposition.{md,yaml}`.
**Scope:** ~1-2 weeks. New slash + new artifact format + new test surface.
**Default:** indefinitely deferred until trigger conditions met.

## v0.2 candidate milestone bundle

Other deferred items found in audit. Priority is now reset by the quality-kernel
goal, not by selection-notes aggregation.

| Item | Source | Estimate |
|---|---|---|
| Multi-style profile (`spec.yaml.style_profile` + multi `.sty`) | memory `project_multi_style_deferred.md` | 3-5d |
| selection_notes Branch 2 or 3 (per above) | superseded by quality-kernel direction | deferred indefinitely |
| Runtime `Next:` footer in command scripts (6 affected) | `CHANGELOG.md:66` | 1-2d |
| `prompt_gen` re-exports removal (backwards-compat shim) | `CHANGELOG.md:70-71` | 0.5d |
| `redact.py` → `normalize.py` rename | `CHANGELOG.md:74` | 0.5d |
| `scripts/` proper Python package | `CHANGELOG.md:72` | 1d |
| Prompt-quality scoring before image-gen | superseded by quality-kernel direction | deferred indefinitely |
| Visual contact-sheet/ranking helper for previews | superseded by quality-kernel direction | deferred indefinitely |
| `/fig_review` v0.2-deferred → shipped doc sync | audit Agent 1 §F.6 | 0.5d |

## Risk register

| Risk | Trigger | Mitigation |
|---|---|---|
| LLM ignores `selection_notes` after plumbing | post-ship | Priority order text in template (Commit 1) |
| `<!-- AUTHOR NOTE -->` leak from selection_notes | post-ship | HTML strip test (Commit 2 #2) |
| `test_parse_spec_real_fig3_fixture_pinned` breaks | Commit 4 | fig3_trapping_concept untouched (locked) |
| New examples lack `selection_notes` key | post-ship, new figure | `/fig_new` scaffold init (Commit 3) |
| No empirical signal for v0.2 branch decision | 4 weeks post-ship | REVIEW.md template (v0.1.x window) |
| User skips 4-heading recommendation | v0.1.x window | Triggers Branch 2. Don't enforce in v0.1.7. |
| selection_notes contradicts §6 invariants | any | Priority text directs §6 win. lint_tex BLOCKER catches palette/font. |

## Out of scope (explicit rejections)

- Auto-vectorization (PNG → SVG path trace). Plugin identity rules this out
  (`README.md:10`, `docs/design-v0.1.md:107`).
- Vision-LLM call from inside the plugin. Identity rules out image-gen API
  use; same logic applies to vision input.
- Hard structural enforcement of selection_notes headings. v0.1 stays
  free-form-with-recommendation; structured interview is Branch 2 v0.2.
- Renaming `selection_notes` field. Breaking change. Treat name as fixed.

## Timeline

```
2026-04-29  v0.1.7 commits 1-5 (1-2 days, this week)
2026-05-02  v0.1.7 ship + memory project_smoke_test_findings_v0_1.md update
2026-05-02 → 2026-05-30  v0.1.x dogfood: 2-3 new figures + REVIEW.md each
~2026-05-30  v0.2 branch decision (data-driven)
2026-06    v0.2 milestone bundle ship
```

## Open decisions (require user sign-off before Commit 1)

- (A) Approve 5-commit plan as written?
- (B) Priority text wording: `§6 invariants > §3 composition intent > selection notes` — keep, or refine?
- (C) Include Commit 4 (fig3_trap_schematic_v97 spec.yaml 4-heading reformat)?
- (D) REVIEW.md template metrics — accept, or add/remove fields?
