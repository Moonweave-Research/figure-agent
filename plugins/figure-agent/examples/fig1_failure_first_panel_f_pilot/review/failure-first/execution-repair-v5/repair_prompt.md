# Bound repair execution: fig1_failure_first_panel_f_pilot

## Single-attempt boundary
- Return one JSON object matching the bound response schema.
- Do not use filesystem or shell tools.
- Put only the replacement content between the anchors in the replacement_utf8 field.
- Put a concise factual description in the change_summary field.
- The controller will materialize a validated candidate at [examples/fig1_failure_first_panel_f_pilot/review/failure-first/execution-repair-v5/repaired_generated.tex].
- Reproduce the complete bound source from [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v3/verified_generated.tex] below.
- Perform one repair attempt only.
- Do not compile, render, or run a gate.
- Do not inspect any historical source or review artifact.
- Do not overwrite the bound source or any existing artifact.
- Change at most six source lines in one source block.

## Exact editable boundary
- Repair family: local_reposition
- Machine finding: {"finding": "The strict detector confirms that source in the source-return label overlaps sample in the no-contact label. Reposition only these two adjacent label declarations; preserve their exact text and all circuit, ground, sample, force, and electrode geometry.", "id": "HF003", "subject": "panel_f_source_sample_text_collision"}
- Change content only between the exact anchor lines [  \draw[cGray, line width=0.38pt] (1.08,0.43) -- (1.42,0.43);] and [\end{tikzpicture}].
- Keep both anchor lines byte-identical.
- Do not act on ambiguous or unbound findings.

## Protected scientific invariants
- Preserve the exact token [source return].
- Preserve the exact token [sample has no electrical contact].
- Preserve the exact token [floating cantilever].
- Preserve the exact token [driven electrode].
- Preserve the exact token [air gap].

## Bound editable source bytes
```tex
  \node[smalllabel, anchor=west] at (1.66,0.60) {source return};
  \node[note, anchor=east] at (5.15,0.80) {sample has no electrical contact};
\end{scope}
```

## Provenance boundary
- Declared model: gpt-5.5
- feedback_rounds: 1
- manual_repairs: 0
- publication_acceptance: not_claimed
