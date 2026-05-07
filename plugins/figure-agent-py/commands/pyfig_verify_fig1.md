---
description: Run the Fig1 Python SVG verifier gate suite.
---

Run all Fig1 gates.

**Usage**: `/pyfig_verify_fig1`

Run from the plugin root:

```bash
python3 scripts/pyfig.py verify-fig1
```

This dispatches `experiments/python_svg_semantic_fig1/src/run_fig1_gates.py`
under `uv` with the Python render dependencies.

If render parity or baseline hash fails after an intentional visual/source
change, run `/pyfig_render_fig1`, inspect the artifacts, then rerun this gate.
