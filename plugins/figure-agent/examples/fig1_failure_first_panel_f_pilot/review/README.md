# Panel F failure-first review packet

This packet compares the tracked historical raw fork, an attribution-only
verified state with identical pixels, and one bounded repaired state. The
repaired state removes the false grounded-electrode implication and replaces
the oversized fixed clamp with one understated metal contact attached to the
cantilever. It does not change the cantilever, electrode, air-gap, or Coulomb
force relations.

The tracked `generated_receipt.json` binds the actual PDF page geometry and all
whole/panel/object-relation/zoom/overlay inputs. The hashes remain `null` in
`authority.yaml`; only the generated receipt may contain their computed values.

Reproduction from `plugins/figure-agent`:

```sh
bash scripts/compile.sh \
  examples/fig1_failure_first_panel_f_pilot/review/states/raw.tex
bash scripts/compile.sh \
  examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex
uv run python -c 'from pathlib import Path; from scripts.quality.review_evidence_pack import build_review_evidence_pack; build_review_evidence_pack(Path("examples/fig1_failure_first_panel_f_pilot"))'
uv run python -c 'from pathlib import Path; from scripts.quality.review_evidence_receipt import build_review_evidence_receipt; f=Path("examples/fig1_failure_first_panel_f_pilot"); build_review_evidence_receipt(f, f / "review" / "generated_receipt.json")'
```

The strict compile currently exits 1 on inherited whole-figure detector
findings. This is recorded in `machine_gate.yaml`; it is not rewritten as a
publication or human acceptance claim.

The pilot is intentionally absent from `benchmarks/llm_failure_corpus.yaml`
until a named human reviews these exact bound inputs. The corpus remains
reviewed-evidence-only rather than learning from a machine-authored verdict.
