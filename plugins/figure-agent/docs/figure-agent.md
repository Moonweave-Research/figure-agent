<!-- FIGURE_AGENT:AUTHORITY -->
# Figure Agent Product Contract and Execution Roadmap

**Status:** Active and authoritative

**Effective date:** 2026-07-15

**Committed baseline:** `c6a28e40` (`codex/figure-agent-closed-loop-reset`)

This is the sole product specification and forward execution authority for
Figure Agent. Other specifications, plans, roadmaps, milestone notes, fixture
reviews, and generated packets are implementation references or historical
evidence. They cannot change product direction or the next implementation step.

The baseline names a reproducible starting commit, not a release, quality, or
publication verdict. A clean worktree at this commit passed 235 targeted
baseline tests. Future claims require fresh evidence from the implementation
slice that makes the claim.

## 1. Outcome

Figure Agent does not compete with an LLM as a second general drawing model.
The LLM remains free to interpret the scientific narrative, propose a
composition, choose an analogy, and author editable TikZ or another declared
representation.

Figure Agent complements that capability where an unconstrained LLM is
reliably weak:

- preserving scientific objects, relations, and forbidden implications;
- seeing the rendered artifact at whole-figure, panel, object, and zoom scales;
- detecting collisions, clipping, broken paths, weak hierarchy, and ownership
  ambiguity;
- attributing a visible defect to an exact semantic object and editable source;
- repairing one bounded region without silently changing neighboring meaning;
- reproducing the result from declared inputs and tool versions; and
- separating machine evidence from human scientific and publication judgment.

The operating rule is:

> Let the LLM propose freely. Make Figure Agent constrain, observe, localize,
> repair, reproduce, and prove.

Figure production is not Figure Agent product development. A hand-tuned
fixture may be valuable evidence, but it becomes a product capability only when
the same declared mechanism transfers across materially different figure
families without fixture coordinates or hidden human edits.

## 2. Product boundaries

### 2.1 Representation roles

- **TikZ/TeX** is the current default editable publication-authoring path.
- **SVG** is a derived export, inspection, interchange, or bounded fragment
  surface. Direct-SVG generation is not an active backend-development target.
- **Python** is the control plane for contracts, compilation, observation,
  attribution, repair transactions, provenance, and evaluation. It is not a
  replacement illustration language.
- **PDF and PNG** are rendered evidence surfaces, not editable authority.
- Exact chemical structures and quantitative plots should use their domain
  authorities when needed; the general LLM must not imitate them freehand when
  a deterministic renderer or data pipeline owns the truth.

Backend selection is closed until comparative evidence demonstrates a concrete
failure that the current control plane cannot address. Do not add a renderer,
an Illustrator clone, a whole-page composition grammar, or fixture-specific
handcrafted coordinates to reusable code during the closed-loop slices.

### 2.2 Knowledge and model boundaries

Read-only authoring context packs are durable paper-specific knowledge
compilation. They may bind explicit paper-local files, Style Lock tokens,
reviewed visual assets, semantic objects, relations, and protected invariants.
They are not LLM prompt plumbing, prompt-loop revival, generation execution, or
automatic physics detection.

The plugin may prepare crops and structured briefs for host vision review, but
the host performs that review outside the plugin. Figure Agent accepts the
result only through a receipt that binds the actor, model or tool, request hash,
transcript hash, and exact inspected artifacts. It does not treat a detector, a
model critique, or a numerical score as scientific truth. Ambiguity remains
visible and routes to the responsible human.

## 3. Closed-loop architecture

The canonical attempt lifecycle is:

```text
scientific task + references + declared invariants
                         |
                         v
              context and authoring packet
                         |
                         v
                 free LLM authoring
                         |
                         v
          deterministic compile and render
                         |
                         v
      machine checks + perception + review crops
                         |
                         v
             fresh host vision critique
                         |
                         v
          adjudicated actionable finding
                         |
                         v
        exact semantic and source attribution
                         |
                         v
       human-authorized bounded repair packet
                         |
                         v
          materialize, compile, and re-render
                         |
                         v
      fresh post-repair visual and regression review
                         |
                         v
        named human development-baseline verdict
```

The first implementation priority is the missing connection from observed
critique to attributable bounded repair and then to a fresh post-repair visual
review. Existing detectors, crops, attribution modules, repair transactions,
and provenance artifacts should be reused before adding new mechanisms.

Zero-feedback authoring remains useful only as a controlled benchmark arm. It
must not be presented as the normal Figure Agent workflow. In an A/B/C
comparison:

- **A** is raw LLM authoring from the neutral scientific task;
- **B** is the same LLM and task plus Figure Agent's declared contracts; and
- **C** is the hash-bound child of B after exact attribution and bounded repair,
  not a third independent authoring call.

## 4. Evidence contract

Every attempt must bind the scientific task, model, budget, source commit,
starting artifact, context packet, generated artifact, renderer/toolchain,
review inputs, and resulting evidence by hash. A line number alone is never
source identity; use a stable selector and fail closed on missing, duplicated,
or stale anchors.

Evidence remains layered:

1. **Machine-valid:** schemas, hashes, compilation, declared assertions, and
   deterministic checks pass.
2. **Visually re-reviewed:** the current render and review crops are fresh, and
   post-repair regression review is complete.
3. **Human development accepted:** a named reviewer accepts the current
   artifact as a development baseline.
4. **Publication accepted:** an external editorial outcome outside Figure
   Agent's authority.

No lower state implies a higher one. Machine gates and model critiques must use
`publication_acceptance: not_claimed` unless a separate external record exists;
even then, the external record is evidence rather than plugin authority.

Capability promotion requires two materially different figure families,
prospectively recorded correction time, named human outcomes, no semantic or
relation regression, and reproducible evidence. Rejected and neutral attempts
remain useful failure-corpus records.

## 5. Executable roadmap

Execute one slice at a time with the smallest failing test first. Keep each
slice reviewable and do not open the next slice until its stop conditions and
verification are recorded.

### R0 — Establish the authority baseline

- [x] Start from committed baseline `c6a28e40` in a clean worktree.
- [x] Collapse product specification and execution direction into this file.
- [x] Preserve previous authorities in place as legacy evidence.
- [x] Run authority, package, and entrypoint contract tests after consolidation.

**Exit:** exactly one active authority marker exists and every agent entrypoint
routes here.

### R1 — Specify the closed-loop attempt state

- [x] Add bounded failing-first contract tests for adjudicated repair binding and
  hash-bound post-repair visual-review evidence.
- [ ] Define attempt identity, parent-child lineage, freshness, actor boundary,
  and terminal-state fields without adding a new renderer or workflow shell.
- [x] Reject stale adjudication, ambiguous attribution, and missing repair
  evidence at the supported critique-to-target bridge.
- [ ] Express and prove the complete lifecycle, including unadjudicated and
  unbound starts, through one shared attempt-state contract.

**Exit:** tests express the full state transition from authored render through
post-repair re-review, including every fail-closed boundary.

### R2 — Connect critique to bounded repair

- [ ] Convert one adjudicated visual finding into declared semantic object and
  relation references.
- [x] Bind one supported machine-backed visual finding to exact source
  attribution, one editable selector, and declared protected invariants.
- [ ] Carry that binding through the existing repair packet, materialization,
  finalization, rollback, and bounded edit-budget surfaces as one transaction.
- [x] Keep ambiguous or evidence-missing bridge inputs as fail-closed stops.
- [ ] Route unbound semantic or relation findings to an explicit human handoff.

**Exit:** one reviewed finding can produce a safe repair transaction without
chat-only coordinates or hidden source selection.

### R3 — Require fresh post-repair vision and regression evidence

- [x] Build a post-repair review request that binds verified repaired-source and
  render hashes plus full, target, neighboring, and print-scale artifacts.
- [x] Fail closed when review artifacts drift, required inspection roles are
  missing, the target remains unresolved, or regression is present or uncertain.
- [x] Require a hash-valid external host-review execution receipt before a
  non-uncertain response can advance to visual re-review pending human judgment.
- [ ] Wire crop generation, machine checks, and receipt-bound external host
  review orchestration into the canonical run; the plugin must not perform or
  impersonate the host review itself.
- [ ] Prove on a real fixture that a repair cannot fix one target while creating
  or worsening another declared defect.
- [ ] Preserve before/after evidence and rollback information.

**Exit:** `machine_repaired` cannot become `visually_re_reviewed` without fresh
post-repair evidence.

### R4 — Make the lifecycle the canonical run path

- [ ] Route the existing canonical run through R1-R3 state transitions.
- [ ] Stop at host-vision, scientific, human authorization, accepted/golden,
  release, and publication boundaries.
- [ ] Keep historical `drive`, `loop`, `improve`, queue, and specialist commands
  as internal compatibility adapters rather than competing workflows.
- [ ] Expose a compact default command surface only after compatibility tests
  prove no evidence path is lost.

**Exit:** a new agent can start from status, execute all safe deterministic work,
and receive one truthful next actor/action without selecting among overlapping
workflow shells.

### R5 — Cross-family proof and capability promotion

- [ ] Replay the closed loop on the maintained complex Fig1 and Fig3 families.
- [ ] Use the same model/task/budget rules for A and B; derive C only from B.
- [ ] Record prospective human correction minutes and blinded named verdicts.
- [ ] Measure defect reduction, new-defect rate, semantic preservation,
  reproducibility, and transfer without fixture-specific imports.
- [ ] Promote only the narrow mechanisms supported by both families.

**Exit:** the evidence demonstrates reduced correction burden without reducing
the LLM's open-ended authoring capability. Otherwise retain the mechanism as
experimental or retire it.

## 6. Mandatory stop conditions

The workflow must stop and report the required actor when any of these holds:

- the render, crop manifest, critique, adjudication, selector, or parent hash is
  missing or stale;
- attribution is ambiguous, unbound, or resolves to more than one editable
  target;
- protected scientific invariants or the repair budget are incomplete;
- the proposed edit crosses its declared semantic or source boundary;
- compile, semantic, collision, neighboring-region, or visual regression checks
  fail after repair;
- the repair makes another confirmed defect worse or introduces a new one;
- the decision requires scientific interpretation, aesthetic preference,
  accepted/golden promotion, release authority, or publication judgment; or
- the next change would add a renderer, broad grammar, dependency, public API,
  or materially larger product surface without new comparative evidence.

Do not work around a stop by weakening a gate, relabeling a third generation as
repair, estimating retrospective correction time, or claiming that machine
success is publication acceptance.

## 7. Current implementation boundary

Reuse the established compile/export spine, perception packs, critique briefs,
adjudication, visual and source attribution, repair policy/plan/apply,
authoring-repair materialization/finalization, provenance, and human review
artifacts.

The current code is a bounded R1-R3 foundation, not a completed closed loop.
It can create an exact adjudicated-repair binding for one supported attribution
path and can prepare and finalize hash-bound post-repair visual-review evidence.
Those internal compatibility commands do not yet provide full attempt identity,
parent-child lineage, actor/state transitions, canonical orchestration of the
external host review, canonical `run` wiring, or cross-family proof.

The next ordered work is to complete the shared attempt identity and lineage
contract, then carry the existing binding and visual-review surfaces through one
repair transaction and the canonical run path. Do not reinterpret the checked
foundation items above as satisfying an R1, R2, or R3 exit condition.

The closed-loop slices bind their handoffs through these narrow evidence
contracts rather than another workflow shell:

- `figure-agent.repair-materialization-preview.v1`;
- `figure-agent.repair-materialization-receipt.v2`;
- `figure-agent.adjudicated-repair-binding.v1`;
- `figure-agent.post-repair-visual-review-request.v1`;
- `figure-agent.host-review-execution-receipt.v1`;
- `figure-agent.post-repair-visual-review-response.v1`; and
- `figure-agent.post-repair-visual-review-receipt.v1`.
