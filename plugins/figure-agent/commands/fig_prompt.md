---
description: Generate redacted external image-gen prompt from spec.yaml + briefing.md. HALTS workflow.
---

Generate prompt for external image-gen tool.

**Usage**: `/fig_prompt` (run inside a figure's examples/<name>/ directory or pass --name)

Steps:
1. Read `spec.yaml` + `briefing.md`.
2. Run redaction: strip numbers+units, generalize geometry, remove experimental conditions.
   (Use `scripts/redact.py` once implemented — for v0.1 stub, list manual redactions in output.)
3. Compose ONE prompt block:
   - Opening: "Create a clean white-background Nature-style scientific schematic."
   - Topic line (from briefing.md)
   - Include: bullet list of what must appear (from briefing.md, redacted)
   - Style: minimal, elegant, no unnecessary text, consistent colors, balanced composition
   - Do NOT include: numerical values, experimental conditions, dimensional annotations
4. Print:
   ```
   === REDACTED PROMPT (copy below for external tool) ===
   <prompt body>
   === END PROMPT ===

   Redaction audit:
   - <list of items removed>

   ⚠️ Review for any remaining sensitive content before sending to external service.

   Next steps:
   1. Copy prompt above into your image-gen tool of choice.
   2. Generate 3-5 candidates.
   3. Save into examples/<name>/previews/ (any filename).
   4. Run /fig_preview_select to continue.
   ```
5. HALT. Do not call any API. Do not generate images.

This is a manual gate. The slash exits and user works externally.
