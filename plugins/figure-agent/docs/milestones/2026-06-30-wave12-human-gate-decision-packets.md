# Wave12 Human-Gate Decision Packets

## Operating correction

Human gate does not mean "ask the human to inspect from scratch."

The agent must first produce a narrow decision packet:

1. Current state and validation evidence.
2. Agent recommendation.
3. Concrete alternative choices.
4. Known risks of each choice.
5. Exact follow-up command or patch plan after human feedback.

The human should only need to judge a proposal, add taste/domain feedback, or approve a bounded irreversible step.

## Current queue state

- Automated review-mode executable work: 0
- Review-mode complete fixtures: 13
- Remaining gated fixtures: 1

Remaining gates:

| Fixture | Gate type | Agent interpretation |
| --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | tracked golden / release boundary | Human approved the bounded golden roll-forward, and the agent ran it. The status model still classifies tracked golden as a release-operator gate because golden baselines remain protected by policy. |

Recently closed gates:

| Fixture | Closed by | Current interpretation |
| --- | --- | --- |
| `fig3_trapping_concept` | one TikZ typography polish pass + refreshed critique/adjudication/export | Review-mode complete; remaining acceptance/final-artifact declaration is a future release decision, not an automated review blocker. |
| `fig4_trap_energy_diagram` | local TikZ annotation cleanup + refreshed critique/adjudication/export | Review-mode complete; remaining acceptance/final-artifact declaration is a future release decision, not a known visual-defect blocker. |

## Packet 1: `fig1_overview_v2_pair_001_vault`

Original state before Wave12 patch:

- `render_state=FRESH`
- `critique_state=FRESH`
- `export_state=TRACKED_GOLDEN`
- `workflow_ready=false`
- `critique verdict=ready`

Evidence:

- Current build PNG and tracked export PNG have the same dimensions: `4272x2891`.
- PDF content differs: `diff_pdf_content.py` reported `DIFFER`.
- Image RMSE after same-width resize: `4685.14 (0.0714906)`.
- Detector surface has no text-boundary clashes and no tex assertion issues; many visual/geometry candidates are already adjudication-style evidence in the ready critique.

Agent recommendation before patch:

- Do not ask the human to rediscover the difference from raw files.
- Present current build vs tracked export contact sheet or diff thumbnail, then ask for a roll-forward decision.
- Default recommendation is **roll forward only if the current build is visually acceptable in the contact sheet**, because critique is fresh/ready and the blocker is only tracked golden protection.

Human-facing question:

> I recommend rolling forward the tracked golden export for `fig1_overview_v2_pair_001_vault` if the current build preview looks acceptable. The content/PNG differs from the old golden, but current critique is `ready`. Should I run the bounded golden update?

If approved:

```bash
./plugins/figure-agent/bin/fig-agent export fig1_overview_v2_pair_001_vault --force-golden
./plugins/figure-agent/bin/fig-agent status fig1_overview_v2_pair_001_vault --json
./plugins/figure-agent/bin/fig-agent queue-run --mode review --goal Wave12-human-gate --dry-run --json
```

Wave12 decision/action:

- Human approved replacing the tracked golden export, with the note that future dogfood/critique may continue to refine the figure.
- Agent ran `fig-agent export fig1_overview_v2_pair_001_vault --force-golden`.
- Result: tracked PDF/SVG golden exports were regenerated; status is `render_state=FRESH`, `critique_state=FRESH`, `export_state=TRACKED_GOLDEN`, `workflow_ready=true`.
- Policy note: `TRACKED_GOLDEN` still reports as `force_golden_required` in queue because tracked-golden baselines remain release-protected even after the explicit roll-forward command.

Risk:

- This mutates tracked golden export artifacts. It is reversible in git, but it changes the release baseline and therefore should remain explicit.

## Packet 2: `fig3_trapping_concept`

State:

- `render_state=FRESH`
- `critique_state=FRESH`
- `export_state=FRESH`
- `workflow_ready=true`
- `critique verdict=ready`
- Journal grade: `solid_manuscript`, score `82`, blockers `[]`
- Next quality bottleneck: `polish`

Evidence:

- Scientific/content axes pass.
- Detector surface has no text-boundary clashes, no label-path candidates, and no tex assertion issues.
- Original open finding C001 was `NIT/style`: typography/header/caption polish for high-impact journal finish.

Agent recommendation:

- Treat the current artifact as scientifically acceptable.
- Ask the human to choose quality target, not to inspect from scratch.
- Default recommendation is **accept for review / solid-manuscript use**, and defer high-impact typography polish unless this figure is intended as a flagship visual.

Human-facing question:

> `fig3_trapping_concept` is scientifically ready and scored solid-manuscript (`82`) with no blockers. The only open item is optional high-impact typography polish. Should we lock this as acceptable for review, or spend another pass on typography hierarchy?

Choices:

- Accept current figure for review/solid-manuscript use.
- Request one TikZ polish pass for title/caption hierarchy.
- Escalate to a broader visual redesign only if this is meant to be a flagship/cover-level schematic.

Risk:

- Accepting now may leave it less polished than a high-impact graphical abstract, but no current evidence says the scientific message is wrong.

Wave12 decision/action:

- Human chose the TikZ polish pass.
- Agent replaced large two-line headers with compact one-line titles, quieted panel backgrounds, and tightened bottom captions to concise result statements.
- Refreshed critique/adjudication/export evidence.
- Current state: `render_state=FRESH`, `critique_state=FRESH`, `export_state=FRESH`, `workflow_ready=true`, review-mode action `complete`.
- Updated critique: C001 is `resolved`; `journal_polish=pass`; `publication_readiness=pass`; next quality bottleneck is `human_policy`.

## Packet 3: `fig4_trap_energy_diagram`

State:

- `render_state=FRESH`
- `critique_state=FRESH`
- `export_state=FRESH`
- `workflow_ready=true`
- `critique verdict=revise`
- Journal grade: `solid_manuscript`, score `74`, blockers `C001`, `C002`
- Next quality bottleneck: `label_semantics`

Evidence:

- Scientific plausibility passes.
- Semantic assertion passes.
- C001: shallow-trap label region is crowded by release guide/rule geometry.
- C002: deep-trap label block is crowded by vertical/rule geometry.
- Critique route says this is a local TikZ patch, not SVG polish.

Agent recommendation:

- Do not ask the human whether to accept this figure yet.
- First run a bounded TikZ cleanup:
  - Move shallow-trap labels farther right/up or add subtle text backing.
  - Shift deep-trap label block right/down.
  - Shorten/shift nearby guide/rule extents so labels are not crossed at print scale.
- Then compile, refresh critique/adjudication if needed, export, and rerun queue.

Wave12 action taken:

- Added subtle white label backing for dense annotation labels.
- Moved shallow/deep label blocks out of the Eg arrow lane.
- Moved the Eg label to the left of the gap arrow.
- Started DOS connector rules after the corresponding label blocks so they no longer cut through text.
- Refreshed critique/adjudication/export evidence.

Current state after patch:

- `render_state=FRESH`
- `critique_state=FRESH`
- `export_state=FRESH`
- `workflow_ready=true`
- `critique verdict=ready`
- Journal grade: `solid_manuscript`, score `80`, blockers `[]`
- Review queue classification: complete in review mode; remaining gate is acceptance/final-artifact declaration.

Human-facing question after patch preview:

> I cleaned the shallow/deep annotation crowding without changing the energy ordering or DOS story. Does this label placement match your intended visual emphasis, or should the labels stay closer to the energy levels even if readability is tighter?

Risk:

- Moving labels can slightly weaken proximity to their targets; keep connectors or backing subtle so semantic binding remains clear.

## Workflow rule to bake into future human gates

Every human gate should be transformed into one of:

- **approval packet**: "I recommend approving X because evidence A/B; approve or reject?"
- **choice packet**: "There are two viable directions; I recommend A because tradeoff; choose A/B."
- **patch proposal packet**: "I found a concrete issue; I recommend this bounded patch; after patch, review this before acceptance."

It should never be:

- "Please inspect everything and tell me what to do."
- "Human required" without an agent recommendation.
- "Acceptance not declared" without a concrete acceptance candidate or a concrete reason not to accept.
