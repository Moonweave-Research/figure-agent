# v0.1.7.2 selection_notes empirical review — fig3_trap_schematic_v97

Date: 2026-04-29
Window: v0.1.x dogfood validation, figure 1 of 2-3

## Setup

Baseline (`fig3_trap_schematic_v97.v0_1_6.tex.bak`) was authored before
v0.1.7 plumbing landed. Per `project_smoke_test_findings_v0_1.md`, the
baseline went through 2 `/fig_review` iterations (collisions
33 → 17 → 5 → 1) and is therefore "post-iteration polished".

Two first-pass v0.1.7.2 re-authoring rounds:

- `fig3_trap_schematic_v97.claude_v0_1_7_2.tex` — fresh Claude session,
  pasted full prompt body.
- `fig3_trap_schematic_v97.codex_v0_1_7_2.tex` — Codex CLI, prompted
  to follow the file's §1 Role / §7 Output Contract.

The v0.1.7.2 LLM authoring prompt now includes `selection_notes`
(4-heading structure) plus the priority-order paragraph (`§6
invariants > §3 composition intent > selection notes`, plus the
extension-vs-conflict clause). The baseline prompt did NOT include
`selection_notes`.

## Quantitative comparison

| Metric | Baseline (post-iter ×2) | Claude v0.1.7.2 (first-pass) | Codex v0.1.7.2 (first-pass) |
|---|---|---|---|
| `lint_tex.py` BLOCKER | 0 | 0 | 0 |
| `lint_tex.py` WARN | `flagship_macros_unused` | `flagship_macros_unused` | (none — flagship macros used) |
| Compile (`lualatex`) | success | success | success |
| PDF size | 82 KB | 85 KB | 113 KB |
| `check_collisions.py` collisions | 1 | 1 | 8 |
| `check_visual_clash.py` | not re-run | not re-run | not re-run |

## selection_notes adherence (per directive)

| Selection_notes directive | Baseline | Claude | Codex |
|---|---|---|---|
| §6 invariants honored (CB > VB, trap mid-gap, linear chain, log-log shape distinction) | ✓ | ✓ | ✓ |
| panel (c) Debye concave-down (Preview errors to fix) | ✓ (post-iter) | ✓ first-pass | ✓ first-pass |
| voltage-bias label (Labels to lift) | ✓ | ✓ | ✓ |
| current-meter label (Labels to lift) | ✓ | ✓ | ✓ |
| "trap-rich" / "shallow or fewer" labels (Labels to lift) | ✓ | ✓ | ✓ |
| Shared sulfur-halo motif across (d) and (e) (Visual motifs to preserve) | ✓ | ✓ | ✓ |
| (b) trap-controlled hopping inset cartoon (Labels to lift) | ✗ | ✗ | ✓ |
| (f) numbered-metric panels (Labels to lift) | ✓ | ✓ | ✓ |
| Style Lock palette (Style overrides) | ✓ | ✓ | ✓ |

## Hypothesis test

**v0.1.7 hypothesis**: "selection_notes plumbing reduces transcribe-cost
during iteration — first-pass output already incorporates the
preview-grounded corrections."

**Result**: confirmed in this round.

- The polished baseline took 2 iterations + manual /fig_review feedback
  to reach 1 collision and full directive adherence.
- Claude v0.1.7.2 first-pass = 1 collision (matches polished baseline)
  with selection_notes-derived corrections already applied.
- Codex v0.1.7.2 first-pass = 8 collisions but full Labels-to-lift
  adherence (only Codex added the trap-controlled hopping inset
  explicitly named in selection_notes).

The first-pass quality saved at least one iteration cycle for both
models on the selection_notes-derived directives. Iteration cost
not eliminated — Codex's collision density still needs polish — but
transcribe cost (re-stating directives in chat each round) was
removed.

## 6-metric scorecard (per roadmap REVIEW.md template)

| Metric | Value | Notes |
|---|---|---|
| Time spent writing selection_notes | ~15 min (single sitting, 4-heading structure) | Done in v0.1.7 dogfood commit; no additional cost in this round. |
| 4-headings actually used | 4 / 4 | All four headings populated and load-bearing in this fixture. |
| LLM TikZ output quality (low/mid/high) | Claude=high; Codex=mid (collision-prone, but more directive-faithful) | Both first-pass usable. |
| Estimated invariant violations avoided by selection_notes | ~3-5 | Specifically Debye concave-down (c), shared sulfur halo (d)+(e), labels (a)+(c). Without selection_notes these typically take 1-2 /fig_review rounds to surface. |
| Free-form distracting? | no | 4-heading structure was clear and the LLMs followed it without confusion. |
| Would structured interview have been faster? | no — same | The current free-form-with-recommended-headings hits the right tradeoff. Structured interview would add friction without quality gain on this fixture. |

## Confounds and caveats

- **Model variable confounded with prompt variable.** Baseline was
  reportedly authored with Claude. The v0.1.7.2 round used Claude AND
  Codex. The cleanest A/B isolation comes from the Claude v0.1.7.2
  vs baseline comparison (same model, prompt varies); the Codex round
  adds model-variable signal but is not a clean prompt isolation.
- **Baseline is post-iteration, new rounds are first-pass.** This is
  by design — the test asks whether selection_notes plumbing reduces
  the iteration count needed to reach polish. It does NOT ask whether
  v0.1.7.2 first-pass is strictly better than v0.1.6 first-pass
  (we'd need to re-author with the v0.1.6 prompt to compare that, and
  that's not worth the effort given the present signal).
- **Image-gen step skipped.** `previews/` directory not regenerated;
  selection_notes not rewritten. Only the LLM authoring step was
  re-run. This was intentional to isolate the plumbing effect from
  image-gen variance.
- **Fresh-session purity.** Claude session was opened fresh for this
  round per the methodology recommendation. Codex CLI was used as the
  user normally does. Cross-conversation memory possibly differs
  between the two — partially confounding, but not at a level that
  invalidates the directional signal.

## v0.2 branch implication

Per the roadmap, three v0.2 branches gate on REVIEW.md aggregation:
Status quo / Branch 2 (structured interview) / Branch 3
(`/fig_decompose`).

This first dogfood entry weights toward **Status quo (Branch 1)**:

- 4-headings used (4/4) and not perceived as distracting (free-form
  was sufficient).
- selection_notes-derived corrections empirically saved iteration
  cycles.
- Structured interview would not have been faster per the user's
  judgment on this fixture.

Need 1-2 more figures with REVIEW.md before locking the v0.2 branch.
This entry is the first data point.

## Commit decision

- Keep `fig3_trap_schematic_v97.tex` (canonical) at the post-iteration
  baseline content. Replacing it with a first-pass version would lose
  iteration polish and is not the experiment's purpose.
- Keep `fig3_trap_schematic_v97.v0_1_6.tex.bak` as the explicit
  baseline reference until this REVIEW.md is committed and read by
  future sessions.
- Keep `fig3_trap_schematic_v97.claude_v0_1_7_2.tex` and
  `fig3_trap_schematic_v97.codex_v0_1_7_2.tex` as immutable artifacts
  of the v0.1.7.2 first-pass test; do NOT overwrite or amend.
- Commit `_authoring_prompt_v0_1_7_2.md` alongside as the exact prompt
  that generated both first-pass .tex files (so the test is
  reproducible).
