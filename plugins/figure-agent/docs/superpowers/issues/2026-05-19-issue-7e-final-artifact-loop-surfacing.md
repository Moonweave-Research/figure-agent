# Issue 7E: Final Artifact Loop Surfacing

**Status:** completed in commits `e593453`, `0904592`.
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Teach `/fig_loop` to surface final-artifact state and recommend the next
single action without editing SVG, exports, source, critique, accepted state, or
golden contracts.

## Public behavior

`/fig_loop` should remain verify-only. It may report:

- final-artifact state and kind
- stale or invalid polish blockers
- blocked polish state when semantic backport is declared
- whether semantic backport is required
- whether human review is needed before final acceptance
- one recommended next action

## Stop behavior

- stale or invalid final artifact: status action required
- blocked final artifact with semantic backport required: agent action required
  before polish can be final
- uncertain semantic preservation: human review required
- final artifact fresh but `accepted: false`: manual approval required

## Acceptance criteria

- [ ] existing loop output remains backward compatible.
- [ ] no-polish fixtures keep current loop behavior.
- [ ] polished-SVG fixtures surface final-artifact state.
- [ ] stale/invalid polish blocks final acceptance.
- [ ] `BLOCKED` polish state routes to semantic backport instead of manifest
  repair.
- [ ] semantic backport blocks final acceptance.
- [ ] loop does not edit SVG, source, exports, critique, accepted state, or
  golden contracts.

## Out of scope

- Auto-polish.
- Multi-target polish batching.
- Accepted gate implementation.
- Export mutation.
