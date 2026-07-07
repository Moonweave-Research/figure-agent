---
audit_input_hash: sha256:10a5351db0893a8f5ef6dd5a26a84c0cc610f229137373acde821c085eae768b
---

# Quality Audit

fixture: fig1_overview_v4_pair_001_vault

## Automated Gate Snapshot

generated-at: 2026-07-03T08:05:00Z
source-fixture: fig1_overview_v3_pair_001_vault
scope: Panel C top-right readability polish for the mobility-edge/shallow label lane.

compile-command: `./bin/fig-agent compile fig1_overview_v4_pair_001_vault`
export-command: `./bin/fig-agent export fig1_overview_v4_pair_001_vault`
status-command: `./bin/fig-agent status fig1_overview_v4_pair_001_vault`

render-state: FRESH
critique-state: FRESH
adjudication-state: FRESH
export-state: FRESH
workflow-ready: true
golden-ready: true
release-ready: true
final-ready: true

0 collision(s)
39 visual clash candidate(s)
0 unresolved visual clash(es)
0 label-path proximity candidate(s)
0 text-boundary clash candidate(s)

tex-assertions: passed
physics-grounding: grounded
critique-lint: passed
audit-evidence: passed

png-sha256: e20fa765e75e9e4fd51e6ec19a0fb9f683f9e5f04c89432a67bda22d1a030c69
export-png-sha256: a92ad1235707f2549097b25e20149acde0aca6d4d28d3a89ddbc1d140637c9c6
export-pdf-sha256: b49fc9da1ea2340decab049895265988f46b5dc83eef2089c4a9bf6e8c3feec4
export-svg-sha256: 639af047fbb7d3ee61c68c7477aea7d77c58326660436c19a248c19369ba9b60
export-tif-sha256: bbc12ea3a084dc535824f1fee44cd60b7da2c1574487609ece493524a86e291b

## Human Review Boundary

This file records automated and host-side evidence for the v4 candidate fixture.
It does not publish the figure, replace any golden source, or create human attestation.

The v4 candidate resolves the observed Panel C top-right readability issue by right-aligning
and demoting `mobility edge`, moving `shallow` into clear whitespace, and pulling the deep escape
curve left/down so the label lane no longer collides with the arrow/caliper cluster.

## Provenance and Publication Compliance

target-venue: unresolved
final-artifact-scope: generated TikZ/PDF/SVG/PNG/TIF export candidate for internal review
ai-generated-image-in-submitted-artifact: unresolved
ai-generated-images-used-as-internal-reference: unresolved
ai-tools-used: figure-agent automated compile/export/check tooling; Codex-assisted host review
disclosure-needed: unresolved
disclosure-draft: unresolved
human-reviewer: unresolved
human-visual-acceptance: false
submission-safe: false
