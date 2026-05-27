# Issue 56 - Journal Art-Direction Playbook

Status: design proposed

Design spec:
`../specs/2026-05-27-journal-art-direction-playbook-design.md`

## Problem

`figure-agent` now catches many structural, semantic, zoom, reference,
publication, and workflow failures. It also has fixture-local aesthetic intent
and paper-wide aesthetic context. The remaining gap is more specific:

```text
How does the host LLM decide whether a technically correct figure still feels
generic, immature, unprofessional, or not yet journal-art-directed?
```

Without a reusable journal art-direction vocabulary, critiques can still say
"looks polished" or "needs polish" without naming the actual design failure:
weak hierarchy, slide-like typography, cramped white space, toy schematic
patterns, preset macro feel, excessive decoration, or the wrong polish route.

## Goal

Add an optional, explicit `journal_art_direction_playbook` pack that grounds
`/fig_critique` in reusable journal-level taste language and forces concrete
accounting when the fixture opts in.

The feature should make abstract qualities operational:

- professional vs childish;
- clean vs generic;
- restrained vs decorative;
- authoritative typography vs slide-like labels;
- white-space breathing vs crowding;
- deliberate hierarchy vs flat panels;
- bounded hand-crafted polish vs uncontrolled visual effects;
- TikZ patch vs SVG polish vs semantic backport vs human art-direction review.

## Non-Goals

- No automatic drawing.
- No automatic SVG polish.
- No score gate or journal-acceptance guarantee.
- No external reference scraping.
- No accepted/golden/export/publication mutation.
- No global default playbook applied to all fixtures.

## Proposed Scope

Implement in narrow slices:

1. **Issue 56A - Parser and Freshness**
   - `scripts/journal_art_direction_playbook.py`
   - explicit `spec.yaml.journal_art_direction_playbook` opt-in
   - pack resolution from
     `examples/_journal_art_direction_playbooks/<playbook_id>.yaml`
   - critique input hash participation

2. **Issue 56B - Brief and Documentation**
   - `## Journal Art-Direction Playbook`
   - exact playbook anchor list
   - route rules and human-review triggers
   - command/skill docs

3. **Issue 56C - Critique Schema v1.12 and Lint Accountability**
   - `journal_art_direction_playbook_audit`
   - reject generic or incomplete accounting
   - preserve legacy v1.10/v1.11 critiques when no playbook is declared

4. **Issue 56D - Loop Surfacing**
   - read-only `journal_art_direction_playbook_summary`
   - no new mutation path
   - no new stop boundary unless existing gates are activated

5. **Issue 56E - Dogfood and Closeout**
   - prove the playbook catches generic art-direction prose
   - prove playbook changes stale critiques
   - prove no source/export/accepted/golden mutation occurs

## Key Design Constraints

- A fixture must opt in through `spec.yaml.journal_art_direction_playbook`.
- Playbook ids must be safe ids, not paths.
- The pack lives in `examples/_journal_art_direction_playbooks/`.
- The playbook complements, not replaces:
  - `aesthetic_intent.yaml`;
  - `paper_aesthetic_context`;
  - `critique_reference_pack.yaml`;
  - SVG polish readiness.
- The critique schema/rubric should bump to v1.12 only for opted-in playbook
  fixtures.
- Existing v1.10 and v1.11 critiques remain parseable when no playbook is
  declared.
- Playbook route recommendations cannot bypass `/fig_loop` or `/fig_driver`
  readiness gates.

## Acceptance

- Design spec is reviewed before implementation.
- Each coding slice uses TDD.
- Fixtures without `spec.yaml.journal_art_direction_playbook` keep current
  behavior.
- Playbook changes participate in critique freshness.
- `/fig_critique` emits an explicit playbook section when opted in.
- `critique_lint.py` rejects critiques that ignore the playbook or cite anchors
  without current-artifact evidence.
- `journal_art_direction_playbook_audit` enumerates every declared
  `design_center[]` item exactly once for v1.12 critiques.
- No source, export, accepted, golden, or publication provenance is mutated.

## Review Questions

1. Does the playbook create a missing reusable journal-design vocabulary, or is
   it duplicating fixture aesthetic intent?
2. Is the v1.12 output field worth the schema bump, or should the first
   implementation start with anchor-only lint in existing slots?
3. Are the pack limits small enough for reliable host-LLM attention?
4. Can generic "looks polished" prose still pass?
5. Can `ready_for_svg_polish` be over-promoted by the playbook?

## Current Recommendation

Start with Issues 56A-C after design approval. They provide the durable contract:
parser, freshness, brief, schema, and lint accountability. Keep Issue 56D/E as
the next follow-up unless dogfood shows loop surfacing is needed immediately.
