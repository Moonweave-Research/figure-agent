# Human Decision Dogfood Wave A/B Integration Review

Date: 2026-06-30

Scope: worker-3 tests/review integration lane for the human decision dogfood
roadmap. This review covers the boundary between durable human decision records,
queue-derived human decision digests, and existing release/style queue semantics.

## Boundaries checked

- Decision records are durable project state, but validation is read-only: schema
  checks must not edit figure source, accepted state, final artifacts, exports, or
  golden artifacts.
- Style-direction decisions are not release acceptance. A style packet can record
  preference or request polish/redesign, but it must not authorize release-state
  or golden mutation.
- Release acceptance and golden roll-forward are separate protected decisions.
  Accepting the current generated export must not imply `--force-golden`.
- Queue digests are generated from live queue rows and retain the source packet
  recommendation/risk. They should be short human-facing summaries, not a second
  hand-written roadmap.
- `fig5_actuation_mechanism` remains isolated from strategy work while stale or
  dirty. It belongs in the digest as an excluded row unless explicitly assigned.

## Edge cases now covered by regression tests

- Unknown decision kinds are rejected by the decision-record validator.
- A style-direction record cannot use release or golden mutation boundaries.
- A release-acceptance record cannot silently authorize golden mutation.
- The human-decision digest groups queue rows into accept-current, bounded TikZ
  polish, SVG-polish-evidence-missing, redesign benchmark, and dirty/stale
  exclusion buckets.
- The digest marks `fig5_actuation_mechanism` as excluded instead of treating it
  as a strategic style decision candidate.

## Integration risks for leader reconciliation

1. Worker-1 and worker-2 may choose different names for decision-record fields or
   digest groups. Keep the executable names in `fig_queue.py` as the merge source
   of truth, or migrate tests and docs together in one reconciliation commit.
2. Digest grouping is deliberately conservative. Rows without a release decision
   packet, style packet, polish blocker, or human/release actor are omitted rather
   than guessed into a human decision bucket.
3. Full redesign remains benchmark-gated. The digest can expose a redesign bucket,
   but choosing that bucket is still a human decision and should not start source
   edits automatically.
4. CLI display work should preserve the existing queue JSON/table contract: adding
   `human_decision_digest` to queue JSON is append-only, while table output remains
   unchanged unless a later CLI slice explicitly adds digest formatting.

## Verification intent

Use the focused queue tests as the contract guard, then run the queue smoke from
`plugins/figure-agent` to prove digest generation remains read-only over current
fixtures.
