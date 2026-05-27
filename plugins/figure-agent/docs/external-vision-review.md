# External Vision Review Evidence

`external_vision_review.yaml` is an optional local evidence file for attaching
an independent visual second opinion to a fixture. It is an import contract, not
a provider integration.

## Opt-In

A fixture participates only when `examples/<name>/spec.yaml` declares:

```yaml
external_vision_review: true
```

Without that explicit opt-in, `external_vision_review.yaml` is ignored by
critique input hashing, `/fig_critique` brief generation, and `/fig_loop`.

## File Location

```text
examples/<name>/external_vision_review.yaml
```

The plugin never calls Gemini, Claude, OpenAI, or any other provider to create
this file. A human or outer agent may write it after reviewing local render
artifacts.

## Schema

```yaml
schema: figure-agent.external-vision-review.v1
fixture: <name>
reviewer: "<human/model/tool name>"
reviewed_at: "<ISO-ish timestamp>"
confidence: low | medium | high
reviewed_artifact:
  path: build/<name>.png
  hash: sha256:<hash>
reviewed_crops:
  - crop_id: <crop id or image id>
    path: build/audit_crops/<crop>.png
    hash: sha256:<hash>
findings:
  - id: EV001
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<what external reviewer saw>"
    evidence_ref: "<crop id, path, or note>"
    suggested_action: patch | human_review | revise_briefing | accept_simplification
conflicts:
  - external_finding_id: EV001
    host_finding_id: C001
    summary: "<conflict requiring human reconciliation>"
```

All paths must be relative safe paths under the fixture. Hashes use the same
`sha256:<digest>` convention as the rest of the quality-manifest layer.

## Freshness

When opted in, the review file participates in the critique input hash. Changing
it makes the current `critique.md` stale through the existing hash-freshness
contract.

`/fig_loop` also checks the hashes inside the review:

- `fresh`: all declared artifacts exist and match their hashes;
- `stale`: at least one declared artifact hash no longer matches;
- `missing_artifact`: at least one declared artifact path is absent;
- `invalid`: the review file or opt-in declaration is malformed.

Stale, missing, or invalid review evidence is surfaced as action-required state
unless an existing human gate is already active. It must not silently pass as
current evidence.

## Conflict Semantics

Conflicts do not make the external reviewer correct. A fresh review with one or
more `conflicts[]` entries routes `/fig_loop` to `human_gate_required`, because
the host critique and external reviewer disagree and a human must reconcile the
evidence.

External review findings do not:

- mutate source, exports, accepted, or golden artifacts;
- override host critique, adjudication, or release gates;
- create hidden auto-patch behavior;
- become mandatory for fixtures that did not opt in.

## Brief Behavior

When opted in and valid, `/fig_critique` includes an
`External Second-Opinion Vision Review` section. The host LLM should use it as
evidence and explicitly discuss conflicts, but it must not silently choose a
winner between host and external judgments.
