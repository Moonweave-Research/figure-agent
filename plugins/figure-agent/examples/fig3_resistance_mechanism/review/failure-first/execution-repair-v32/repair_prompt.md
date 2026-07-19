# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v32/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v31/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: label_reflow
- Machine finding: {"finding": "two capture release boxes duplicate the external transition key and obscure the carrier path", "id": "HF014", "subject": "panel_a_duplicate_transition_labels"}
- Change content only between the exact anchor lines [  {sign-agnostic carrier\\repeated capture $\leftrightarrow$ release};] and [\node[compact label, anchor=south east, fill=white, inner sep=1pt]].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [sign-agnostic carrier\\repeated capture $\leftrightarrow$ release].
- Preserve the exact token [retained].
- Preserve the exact token [applied $V$].

## Bound editable source bytes
```tex
\node[compact label, align=center, fill=white, inner sep=1pt] at (1.70,2.18)
  {capture\\release};
\node[compact label, align=center, fill=white, inner sep=1pt] at (2.76,2.70)
  {capture\\release};
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
