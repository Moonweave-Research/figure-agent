# Fig3 shape-profile experiment handoff

This attempt is `ineligible_execution_unbound_and_not_renderable`. ORRO produced both exact one-pass
TikZ sources, but normal and strict compilation both exited 1 for each arm at
`missing_polymer_paper_preamble`. The generated sources were preserved without
manual repair. No PDF, PNG, or layout report exists.

The executed ORRO inline prompts do not byte-match the declared Markdown prompt
files, so this is not a hash-bound controlled comparison. Per-arm execution
receipts bind the actual prompt, transcript, and source hashes and record the
mismatch; the next run must execute the declared prompt bytes directly.

The external evidence root is
`.witnessd/runs/fig3-shape-profile-20260713-sequential`. Its final Depone
proofcheck passes for persisted execution evidence only; it does not validate
the figure. The handoff and report were written before the final proofcheck
rerun, so the report itself records a binding-mismatch limitation. Exact hashes
are bound in `shape_profile_comparison.yaml`; no key or secret path is copied.

Human visual review is blocked and not applicable to this attempt. A new
controlled run must first repair the shared authoring packet/preamble contract,
then regenerate both arms from the same blank start. Do not repair either saved
source and do not infer profile benefit from source text alone.

Publication acceptance is not claimed.
