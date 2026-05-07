---
description: Report Fig1 Python SVG artifact and gate status.
---

Report current Fig1 Python SVG status.

**Usage**: `/pyfig_status_fig1`

Run from the plugin root:

```bash
python3 scripts/pyfig.py status-fig1
```

This checks tracked artifact presence, SHA-256 hashes, and the current Fig1
gate result. It does not compile TikZ and does not inspect `examples/*.tex`.
