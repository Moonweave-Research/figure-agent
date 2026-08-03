# Canonical figure and repository consolidation — 2026-08-03

**Status:** repository evidence; not product authority and not publication
acceptance.

## Canonical authoring baselines

The paper map and durable handoff now identify exactly three current authoring
baselines:

| Figure | Fixture | Editable source | Source SHA-256 | Render SHA-256 |
|---|---|---|---|---|
| Fig1 | `fig1_updated_agent_redraw_v1` | `review/failure-first/comparable-v3-repair-c5/repaired.tex` | `11476b64a5bb1faea15f7f7c713f90b3edd11cf7daf07cf4945cb2fbf9daf223` | `7166d92ffa3e4aae6fe1ea371694f0401138722ba437b6cab9dc0df13fa00d5c` |
| Fig2 | `fig2_charge_transport_mechanism` | `fig2_charge_transport_mechanism.tex` | `2a5cd930f3c9f09db53b295f14bba5921af420b9e5619821b2e597438841dbb1` | `a6c3c54d6d1cf79a2ceb1bada4db8698cd0109e05e1f5bfe5f8c24ec0a1d3abd` |
| Fig5 | `fig5_cantilever_actuation_artifact_v2` | `fig5_cantilever_actuation_artifact_v2.tex` | `493932a6847e391ca47d151730f8fece421b6e935ccf378d491d4901e35bbc53` | `3b3639f607ceb2c5a57047c7c8cca30f671125a0cd35e8a5869c89f2c207b591` |

Fig3 and Fig4 remain planned without active fixtures. The earlier
`fig4_trap_energy_diagram` fixture is classified as a superseded diagnostic
trial. Active authoring status does not imply human or publication acceptance.

## Preserved historical work

Dirty or untracked historical work was preserved outside the canonical main
line before cleanup:

| Archive ref | Commit | Preserved scope |
|---|---|---|
| `archive/fig1-v5f-wip-20260803` | `204ca9dd` | residual Fig1 visual edits, experience evidence, and quarantined quality-search WIP |
| `archive/wave0-queue-wip-20260803` | `472954e8` | detached Wave 0 queue-bottleneck experiment |
| `archive/python-svg-plans-20260803` | `100c4d3c` | Python-SVG visual grammar and subrenderer plans |
| `archive/svg-first-prototype-20260803` | `aff32c33` | SVG-first plugin source, fixtures, and tests without generated environments |

Each ref also has a matching `snapshot/*-20260803` annotated tag. Earlier
Fig1 authority, Slice 2, and style-guide evidence remains under the existing
`archive/*-20260729` refs.

A verified Git bundle preserves the pre-prune local branch and tag namespace:

- path: `/Users/choemun-yeong/workspace/ResearchOS/figure-agent-archives/figure-agent-local-refs-20260803.bundle`
- refs: 188
- size: 128 MiB
- SHA-256: `c403748f6ad987b2c2c4b61a07e6ce9ce7df3b113f24e01d46c51858d8114937`
- verification: `git bundle verify` passed and reported complete history

A second verified bundle captures the current canonical `main` after export
source-of-truth and SVG-fidelity hardening:

- path: `/Users/choemun-yeong/workspace/ResearchOS/figure-agent-archives/figure-agent-main-baselines-20260803-6a84d238.bundle`
- ref: `main` at `6a84d238`
- size: 87 MiB
- SHA-256: `b6cb788e674686b34d07a382a975b24418952cc60abf45f20c974aadc83287df`
- verification: `git bundle verify` passed and reported complete history

Ten legacy stash entries were converted to annotated
`snapshot/stashes/*` tags before removing the mutable stash reflog. A dedicated
bundle preserves all ten tag refs and their complete histories:

- path: `/Users/choemun-yeong/workspace/ResearchOS/figure-agent-archives/figure-agent-stashes-20260803.bundle`
- refs: 10 annotated `snapshot/stashes/*` tags
- size: 107 MiB
- SHA-256: `8f1f2a7cedfdeaee87ab6b52215aa65a64477d661b604bb26a83a8ba805e76f6`
- verification: `git bundle verify` passed and reported complete history

## Cleanup performed

- Reduced registered Git worktrees to the canonical repository root on
  `main`.
- Removed clean archived Fig1-authority and Slice 2 worktrees.
- Preserved and removed the detached Wave 0, Python-SVG, and SVG-first
  experiment worktrees.
- Rebuilt the three canonical figures in the root worktree before removing the
  duplicate `fig3-dogfood` worktree; all three PNG hashes matched byte-for-byte.
- Removed the nested witness runner and moved its untracked build output and
  `.witnessd` runtime state to Trash. The latter contained local authentication
  and process-state files and was not suitable as repository evidence.
- Moved two redundant Fig1 WIP patch files and obsolete local plugin marketplace
  metadata to Trash. Their meaningful source changes are preserved in archive
  commits.
- Removed 139 noncanonical local branch refs after the verified bundle was
  created. The remaining local branches are `main` and explicit `archive/*`
  refs.
- Replaced ten mutable legacy stash entries with named snapshot tags and a
  verified standalone bundle; no stash entry remains as an unnamed work queue.
- Removed six local Fig5 archive refs already contained in `main` and mirrored
  on `origin`; retained nine local `archive/*` refs with independent historical
  commits.
- Added `.codex/` to `.gitignore` so machine-specific absolute MCP paths cannot
  become accidental repository changes.

## Verification

- `pytest -q tests/test_current_sulfur_paper_handoff.py tests/test_plan_consistency.py`: 16 passed.
- `./bin/fig-agent plan-check --strict`: blocking 0; Fig3 and Fig4 planned-missing advisories only.
- Strict Fig1 compile: passed; semantic contract, print-size contract, collision,
  text-boundary, label-path, semantic assertion, geometry, and physics checks passed.
- Strict Fig2 compile: passed with 2 geometry assertions and grounded physics.
- Strict Fig5 compile: passed with 5 geometry assertions and grounded physics.
- SVG-first archive verification: 22 tests passed; Ruff passed after lockfile-based
  local Node dependency installation.
- Root worktree: canonical sources, regenerated build evidence, and fresh
  candidate-aware exports are present on `main`.
- Exported SVG glyphs are outlined to preserve PDF text spacing across SVG
  renderers; TeX remains the editable text authority.

## Open human and synchronization gates

- Fig1 has a fresh current-candidate render and export and remains
  `candidate_only`; critique is not required for this fixture and its human gate
  remains pending.
- Fig2 and Fig5 have fresh render, critique, adjudication, and export evidence.
- All three fixtures complete deterministic closeout with no blocking step, but
  remain `acceptance=NOT_DECLARED`, `release_ready=false`, and
  `final_ready=false` pending explicit human review.
- Local `main` is 395 commits ahead of `origin/main`; this cleanup did not push
  or create a publication/release claim.
