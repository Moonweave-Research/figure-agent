# Quality Audit: fig1_overview_v2_pair_001_vault

**Date:** 2026-05-18
**Last verified:** 2026-05-18T14:59:52Z
**Decision:** accepted: false
**submission-safe:** false

This audit records the current dogfood state after the critique-heading parser
fix, v1.2 critique refresh, Panel A collision-budget fix, and tracked-golden
roll-forward. It is intentionally not a manuscript-submission acceptance record.

## Build Evidence

| Check | Command | Result |
|---|---|---|
| Compile/render | `bash scripts/compile.sh examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex` | PASS, exit 0. Generated `build/fig1_overview_v2_pair_001_vault.pdf` and `.png`. |
| Collision budget | same compile command | PASS. `OK: no collisions found in fig1_overview_v2_pair_001_vault.pdf (127 words)`. |
| Visual clash scan | same compile command | REPORT-ONLY. `53 visual clash candidate(s)`. These are accepted as detector candidates for this dogfood state, not unresolved accepted-mode blockers. |
| Unresolved visual clash budget | manual audit of detector candidates against current v1.2 critique/adjudication | PASS. `0 unresolved visual clash(es)`. |
| Critique freshness | `uv run python3 scripts/status.py fig1_overview_v2_pair_001_vault` | PASS after critique refresh. `critique: fresh`. |
| Export roll-forward | `uv run python3 scripts/run_export.py fig1_overview_v2_pair_001_vault --force-golden` | PASS. Regenerated tracked PDF/SVG/PNG/TIFF exports from current source. |
| Golden artifact basic gate | `uv run python3 scripts/check_golden_artifacts.py examples/fig1_overview_v2_pair_001_vault --no-require-accepted` | PASS. Required PDF/SVG/PNG/TIFF artifacts are present and well-formed. |
| E2E smoke | `uv run python3 scripts/fig_e2e_smoke.py fig1_overview_v2_pair_001_vault --repeat 5 --goal "acceptance-gate prepared final smoke"` | PASS. All five runs ended in the same manual acceptance gate with `render=FRESH`, `critique=FRESH`, `export=TRACKED_GOLDEN`, and `workflow_ready=true`. |

OK: no collisions found in fig1_overview_v2_pair_001_vault.pdf (127 words)
53 visual clash candidate(s)
0 unresolved visual clash(es)

## Golden Contract Result

`spec.yaml` now declares a `golden_contract` for the tracked fixture:

- Required rendered labels are present in the exported PDF.
- Source inventory floors pass for panel letters, inter-panel arrows, row-2
  spokes, shallow/deep trap loops, energy trap lines, surface-charge markers,
  and cantilever-charge markers.
- The contract is a reproducibility gate, not a visual-style guarantee.

The fixture remains `accepted: false`; `accepted: true` is deliberately reserved
for a separate human acceptance and publication-safety decision.

## Theory Guard Result

| Guard | Result | Evidence |
|---|---|---|
| TG-A-001 Panel A linear topology | PASS | `theory_guard.md` records the linear poly(S-r-DIB) topology lock; current source keeps the open-chain/polymer-chain semantics. |
| TG-C-001 Panel C shallow/deep traps | PASS | Current source and critique preserve the same-matrix shallow/deep trap framing. |
| TG-CFG-001 C/F/G color consistency | PASS | C/F shallow/deep and trapped-charge colors remain consistent with the theory guard. |
| TG-D-001 non-Debye Panel D tail | PASS | Current source keeps the power-law tail above the Debye reference at long time. |
| TG-G-001 Coulomb-only Panel G legacy guard | PASS / remapped | v8.6 merged G into Column F; current F preserves Coulomb as the dominant force cue and Maxwell as lower-tier baseline. |
| TG-G-002 Maxwell-vs-Coulomb tiering | PASS | Column F keeps Maxwell as lower-tier baseline and Coulomb repulsion as the stronger result cue. |
| TG-ROW2-001 independent evidence spokes | PASS | Row 2 remains three independent spokes: kinetic, ISPD, mechanical. |
| TG-B-001 composition labels only in Panel B | PASS | Composition labels remain confined to the composition panel context. |
| TG-EF-001 E/F paired ISPD line | PASS | Current source preserves `V_s(t)`, ISPD flow, and `g(E_t)` derived-DOS semantics. |
| TG-PUB-001 publication compliance | OPEN | Target-venue policy and human provenance statement are not supplied. This blocks `accepted: true`. |

No unresolved theory BLOCKER is known inside the current figure semantics. The
publication compliance guard remains open because it is a human/venue-policy
gate, not a TikZ patch.

## Vision Critique And Adjudication

Fresh `critique.md` verdict is `ready` under schema
`figure-agent.critique.v1.2`.

- BLOCKER findings: 0.
- MAJOR findings: 0.
- MINOR/NIT patch findings: 0 active.
- `critique_adjudication.yaml` is fresh against the current critique hash and
  has no open decisions because no patchable finding remains.

The acceptance-gate collision fix moved the Panel A `inverse vulcanization`
label left to clear the S8 lower-left vertex. This did not change the story,
theory guard, or panel roles.

## Provenance and Publication Compliance

- Every declared reference role is documented in `reference/reference_pack.md`
  or the per-panel `spec.yaml` comments.
- `reference/codex_gen_overview_v1.png` is retained as style/layout evidence,
  not as a literal scientific source.
- D/E/F panel references are used as apparatus grammar/style anchors, not as
  copied panel content.
- No external image-generation or web API call was introduced by this audit
  update.
- Target venue is not declared.
- Human provenance statement is not attached.

submission-safe: false

Because target venue and provenance are missing, this audit explicitly blocks
`accepted: true` and any claim that the figure is submission-safe.

## Acceptance Decision

`accepted: false` remains correct.

Do not set `accepted: true` until all of the following are true:

1. Fresh compile/export/status pass after the final source change.
2. `scripts/check_golden_artifacts.py examples/fig1_overview_v2_pair_001_vault --require-accepted`
   has no failures except those caused solely by `accepted: false` and
   `submission-safe: false`.
3. Target journal or venue policy is checked for AI-assisted figure/provenance
   requirements.
4. Human provenance and visual acceptance are recorded in this file.
5. `spec.yaml` is changed to `accepted: true` only in the same commit as the
   final passing audit.
