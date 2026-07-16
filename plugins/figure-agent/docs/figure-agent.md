<!-- FIGURE_AGENT:AUTHORITY -->
# Figure Agent Product Contract and Execution Roadmap

**Status:** Active and authoritative

**Effective date:** 2026-07-16

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
- [x] Define attempt identity, parent-child lineage, freshness, actor boundary,
  and terminal-state fields without adding a new renderer or workflow shell.
- [x] Reject stale adjudication, ambiguous attribution, and missing repair
  evidence at the supported critique-to-target bridge.
- [x] Express and prove the complete lifecycle, including unadjudicated and
  unbound starts, through one shared attempt-state contract.

**Exit:** tests express the full state transition from authored render through
post-repair re-review, including every fail-closed boundary.

### R2 — Connect critique to bounded repair

- [x] Convert one adjudicated visual finding into declared semantic object and
  relation references.
- [x] Bind one supported machine-backed visual finding to exact source
  attribution, one editable selector, and declared protected invariants.
- [x] Carry that binding through the existing repair packet, materialization,
  finalization, rollback, and bounded edit-budget surfaces as one transaction.
- [x] Keep ambiguous or evidence-missing bridge inputs as fail-closed stops.
- [x] Route unbound semantic or relation findings to an explicit human handoff.

**Exit:** one reviewed finding can produce a safe repair transaction without
chat-only coordinates or hidden source selection.

### R3 — Require fresh post-repair vision and regression evidence

- [x] Build a post-repair review request that binds verified repaired-source and
  render hashes plus full, target, neighboring, and print-scale artifacts.
- [x] Fail closed when review artifacts drift, required inspection roles are
  missing, the target remains unresolved, or regression is present or uncertain.
- [x] Require a hash-valid external host-review execution receipt before a
  non-uncertain response can advance to visual re-review pending human judgment.
- [x] Wire fresh crops and a request-bound host handoff into the canonical run
  without performing or impersonating the external host review.
- [x] Consume a receipt-bound external host response through the same run.
- [x] Controlled-fault replay on maintained Fig3 source proves current v4 rejects
  a target fix that creates a declared neighboring collision.
- [x] Preserve hash-bound before/after evidence; execute identity-safe, crash-recoverable rollback with explicit legacy opt-in.
- [ ] Repeat on a prospective real defect; controlled fault is not acceptance.

**Exit:** `machine_repaired` cannot become `visually_re_reviewed` without fresh
post-repair evidence.

### R4 — Make the lifecycle the canonical run path

- [ ] Route the existing canonical run through R1-R3 state transitions.
- [x] Project the unique hash-validated current attempt into `status`, `drive`,
  and default `run`; fail closed on invalid, ambiguous, stale, or symlinked
  lineage instead of falling through to a legacy loop.
- [x] Wire `machine_repaired -> post_review_requested` through default `run`:
  plan-only writes nothing; execute creates the bound request/crops/state and
  stops before host invocation.
- [ ] Wire remaining safe deterministic transitions through default `run` one
  at a time without synthesizing host, scientific, or human evidence.
- [x] Stop at host-vision, scientific, human authorization, accepted/golden,
  release, and publication boundaries.
- [ ] Keep historical `drive`, `loop`, `improve`, queue, and specialist commands
  as internal compatibility adapters rather than competing workflows.
- [x] Preserve exact actor, evidence references, allowed/forbidden scope, and
  `publication_acceptance` through queue and plan-only queue-run projections;
  aggressive candidate search may not cross a human boundary.
- [ ] Give every remaining specialist/internal adapter an explicit canonical
  successor and evidence contract before compacting the surface.
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

Reuse the established compile/export, perception, critique, attribution, repair,
materialization, provenance, and human-review surfaces.

The code is a bounded R1-R3 foundation with the first R4 canonical-routing
slice, not a completed closed loop. Its shared attempt-state contract binds
identity, append-only lineage, live freshness, phase evidence roles, actor
separation, legal transitions, and terminal development outcomes. The default
status/run path now discovers one authoritative current attempt without mtime,
projects its exact actor/path/hash, and stops rather than selecting a legacy
loop when the next transition is not yet wired. Evidence-role presence is not
domain validation or actor authentication; adapters must validate each receipt
against recorded identity.

One exact adjudicated binding now crosses packet compilation, human-authorized
materialization, rollback, and finalization. New packets use v4 authority;
stored v3 packets require explicit compatibility and cannot enter post-repair
review directly. Finalization and rollback revalidate current v4 authority;
rollback also revalidates hash-bound failed detector evidence under a recoverable lock.

The binding now hash-binds declared semantic object and relation references to
the same editable selector as the repair target. Missing semantic authority,
ambiguous attribution, or missing references can emit only a named
`human_attributor` handoff; they cannot create a repair binding or packet.

Default `run` now advances one validated `machine_repaired` state to a bound
`post_review_requested` state and stops at `host_llm`; it does not invoke the
host or discover a response automatically. The explicit inbound R3 path
consumes a receipt-bound external host response. The maintained-Fig3
controlled-fault replay is mechanism evidence only, not an actual defect or
publication verdict; prospective real-defect proof and the remaining R4-R5
work are still pending.

The closed-loop slices bind their handoffs through these narrow evidence
contracts rather than another workflow shell:

- `figure-agent.repair-materialization-preview.v1`;
- `figure-agent.repair-materialization-receipt.v2`;
- `figure-agent.repair-execution-packet.v4`;
- `figure-agent.repair-authority-contract.v1`;
- `figure-agent.closed-loop-attempt-state.v1`;
- `figure-agent.closed-loop-current-state.v1`;
- `figure-agent.adjudicated-repair-binding.v1`;
- `figure-agent.semantic-finding-attribution.v1`;
- `figure-agent.attribution-handoff.v1`;
- `figure-agent.post-repair-visual-review-request.v1`;
- `figure-agent.host-review-execution-receipt.v1`;
- `figure-agent.post-repair-visual-review-response.v1`; and
- `figure-agent.post-repair-visual-review-receipt.v1`.
