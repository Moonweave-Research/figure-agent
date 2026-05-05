# Handoff: tikz-refine consolidation + shared compile engine refactor

**Created**: 2026-05-05
**Origin**: figure-agent session, follow-up to v0.2 quality kernel + L3 snippet library work
**figure-agent main HEAD at handoff**: `b3a0ccf` (pushed to origin/main)
**Use this file as the opening context for the new session.**

---

## Goal

Refactor the ResearchOS workspace's TikZ compile pipeline so Athena, figure-agent, and tikz-refine share one compile engine instead of each carrying their own. Target = "option C" from prior architecture discussion: a shared lightweight package that all three import.

## Background — current state, 2026-05-05

- **figure-agent** (plugin at `~/workspace/ResearchOS/[figure-agent]`) has its own lualatex + dvisvgm pipeline (`plugins/figure-agent/scripts/compile.sh` + `export_svg.sh`). Just shipped v0.2.0; do not destabilize.
- **Athena** (`~/workspace/ResearchOS/[Athena]`) is a research-commands project that includes a `compile_tikz` engine consumed internally and by tikz-refine. Athena's identity is research, not figure-making — compile is a utility there, not core.
- **tikz-refine** is currently a skill, **scattered across 4 locations**:
  - Skill definition: `~/.claude/skills/tikz-refine/SKILL.md` (orchestration, global)
  - Compile engine: `[Athena]/...compile_tikz` (function inside Athena)
  - Tests: `[Athena]/tests/test_tikz_refine.py` (in worktree `tikz-v4-rc-local`)
  - Design doc: `[Athena]/docs/02-design/features/tikz-refine-completeness.md`
- **Never been chained** with a figure-agent fixture. The integration story is theoretical until baseline is established.

## Why this work, why now

tikz-refine is being properly developed in this new session. Unifying the compile substrate now prevents tikz-refine from growing on top of fragile cross-project coupling, and pulls scattered tikz-refine assets into one home before the codebase matures further.

---

## First actions — in order

### 0. Create the new project folder + migrate scattered assets

```bash
mkdir ~/workspace/ResearchOS/[tikz-refine]/
```

Migrate:
- Test → `[tikz-refine]/tests/test_tikz_refine.py` (from `[Athena]/tests/test_tikz_refine.py` worktree `tikz-v4-rc-local`)
- Design doc → `[tikz-refine]/docs/design.md` (from `[Athena]/docs/02-design/features/tikz-refine-completeness.md`)
- Skill def → `[tikz-refine]/skills/SKILL.md` (from `~/.claude/skills/tikz-refine/SKILL.md`)
- Leave `~/.claude/skills/tikz-refine/SKILL.md` as a thin pointer (or symlink) so existing `/tikz-refine` invocations still work during migration.

`git init` the new project; first commit: `chore: import scattered tikz-refine assets from skill + Athena`.

### 1. Locate and read all three pipelines side-by-side

- figure-agent: `scripts/compile.sh` + `lint_tex.py` + `check_collisions.py` + `check_visual_clash.py` + `check_layout_drift.py`
- Athena: `grep -r "compile_tikz" ~/workspace/ResearchOS/[Athena]/`
- tikz-refine: `[tikz-refine]/skills/SKILL.md` (after step 0)

### 2. Establish byte-level baseline

Compile the same minimal `.tex` through both Athena and figure-agent. Capture diff in PDF stream + SVG output. **If they diverge, surface the diff before designing the shared engine.** Unification cannot silently regress either consumer.

### 3. Verify tikz-refine end-to-end baseline

Confirm tikz-refine currently runs against Athena. If broken today, fix baseline before refactor — refactoring on a non-functional system is debugging in disguise.

### 4. Draft interface spec for the shared engine

Minimum surface:

```python
def compile(
    tex_path: Path,
    preamble_path: Path | None = None,
    engine: str = "lualatex",
) -> CompileResult:
    """Returns CompileResult{pdf_path, log_path, exit_code, duration}."""
```

Out of scope (stays in figure-agent):
- Style Lock / palette enforcement
- dvisvgm SVG export with text preservation
- Visual clash + collision detection (deterministic, project-specific)

Out of scope (stays in tikz-refine):
- Vision loop, coordinate auto-fix, save logic

### 5. Choose engine package location

Suggested: `~/workspace/ResearchOS/[tikz-engine]/` as a 5th sibling under ResearchOS root (alongside `[Athena]/`, `[figure-agent]/`, `[Graph_making_hub]/`, `[tikz-refine]/`).

### 6. Migration order

1. **Athena** first (simplest, smallest blast radius). Regression test: byte-equivalent compile output for a fixed `.tex` corpus.
2. **figure-agent** second. Feature branch only — main must remain green. Regression test: existing test suite passes; export_freshness + golden artifact contracts unchanged.
3. **tikz-refine** last. Update to import shared engine; drop direct Athena coupling.

---

## Constraints / priors

- figure-agent's Style Lock + dvisvgm text-preservation must **not** move into shared engine. Project-specific gates stay in figure-agent.
- tikz-refine stays separate from figure-agent (decided 2026-05-05: quality kernel ≠ auto-fix loop). Do not merge.
- Don't merge tikz-refine into Athena either — Athena's research identity shouldn't bloat with figure tools.
- Work on a feature branch in figure-agent. Existing v0.2 test suite must remain green throughout.
- **Read at session start**: `.claude/projects/-Users-choemun-yeong-workspace-ResearchOS--figure-agent-/memory/MEMORY.md` for project context, especially `session_handoff_2026_05_05.md`, `architecture_v0_2_redesign.md`, `feedback_macro_vs_snippet_dichotomy.md`.

## Definition of done

- `[tikz-refine]/` project exists with consolidated test + design + skill assets, and own `pyproject.toml`.
- `[tikz-engine]/` shared package exists with minimal test (compiles a sample, asserts PDF + log).
- All three consumers (Athena, figure-agent, tikz-refine) import from `[tikz-engine]/`. No duplicate lualatex invocations remain.
- End-to-end demo: figure-agent fixture → `/fig_compile` → `/fig_critique` surfaces a layout issue → `/tikz-refine` attempts auto-fix → `/fig_compile` re-validates. Captured as a regression test.
- figure-agent existing test suite (188 at v0.2 release + match_snippet tests added 2026-05-05) still green.
- This handoff doc moves from `[figure-agent]/docs/handoff/` to `[tikz-refine]/docs/` once the new project folder exists.

## What NOT to do

- Don't expand the shared engine's scope. It is a compile primitive, not a quality kernel.
- Don't merge any two of {Athena, figure-agent, tikz-refine}. Each retains its identity.
- Don't proceed past step 0 without verifying baseline (steps 2-3).
- Don't fabricate paths — verify before relying.
- Don't touch figure-agent's main branch directly during refactor; use a feature branch.
- Don't migrate tikz-refine assets in-place via `git mv` from inside Athena — Athena's history shouldn't carry tikz-refine commits forward. Copy + commit fresh in `[tikz-refine]/`.

## Estimated time

3–5 days (option C scope).

---

## Author trace

This handoff is the planned successor to figure-agent session 2026-05-05. Relevant commits on `origin/main`:

- `d9c6885` docs(snippets): seed INDEX.yaml v0.1 metadata schema
- `8a13e6e` docs(snippets): INDEX.yaml v0.2 — briefing_hooks + anti_patterns
- `7504969` feat(snippets): add briefing→snippet matcher prototype
- `82435e1` fix(snippets): exclude §7 Must-avoid subsections from matcher
- `d8d243f` fix(snippets): tighten briefing_hooks for polymer_chain + band_with_traps
- `41c63df` test(snippets): truth-anchored regression test for match_snippet
- `f389d64` fix(lint): exempt snippet smoke fixtures from flagship_macros_unused
- `b3a0ccf` docs(snippets): record process_3column tinted-fill contrast pitfall
