# Bound repair execution: fig3_resistance_mechanism

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v33/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig3_resistance_mechanism/review/failure-first/execution-repair-v32/repaired_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: relation_restore
- Machine finding: {"finding": "upper-left arrow points opposite to the declared carrier path order", "id": "HF015", "subject": "panel_a_arrow_direction_consistency"}
- Change content only between the exact anchor lines [\draw[draw=cBlue, line width=0.75pt, -{Stealth}] (1.12,1.69)--(1.29,1.95);] and [\draw[draw=cBlue, line width=0.75pt, -{Stealth}] (2.37,2.48)--(2.12,2.25);].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [sign-agnostic carrier\\repeated capture $\leftrightarrow$ release].
- Preserve the exact token [retained].
- Preserve the exact token [applied $V$].

## Bound editable source bytes
```tex
\draw[draw=cBlue, line width=0.75pt, -{Stealth}] (1.52,2.93)--(1.27,2.65);
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
