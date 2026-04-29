---
description: List examples/<name>/previews/, present to user, record selection in spec.yaml.
---

Select a preview to use as compile inspiration.

**Usage**: `/fig_preview_select <name>`

Run from the plugin root.
`<name>` maps to `examples/<name>/`.

Steps:
1. List `examples/<name>/previews/*.png`, `*.jpg`, and `*.jpeg` (alphabetical).
2. If empty, instruct user to run external image gen + save into `examples/<name>/previews/`, then re-run.
3. Display numbered list with file sizes:
   ```
   [1] alpha_01.png (1.2 MB)
   [2] alpha_02.png (1.4 MB)
   [3] gemini_v3.jpg (980 KB)
   ```
4. Ask user to pick by number.
5. Update `examples/<name>/spec.yaml`: `selected_preview: <filename>`.
6. **Recommended: write `selection_notes` in `spec.yaml`.** Free-form is
   accepted, but the 4-heading template below tends to translate well into
   the LLM authoring prompt (it is plumbed verbatim with HTML-comment
   stripping; priority order in the template is `§6 invariants > §3
   composition intent > selection notes`):
   ```yaml
   selection_notes: |
     Visual motifs to preserve:
       - <e.g. green polymer chain + amber trap halo>
     Preview errors to fix in TikZ:
       - <e.g. panel (c) Debye curve must be concave-down, not near-linear>
     Labels to lift:
       - <e.g. "voltage-bias / current-meter" from chatgpt_web_v01>
     Style overrides:
       - <e.g. polymer-paper-preamble Style Lock palette wins over preview palette>
   ```
   Author-only notes (TODOs, contingency, status reminders) can be wrapped
   in `<!-- ... -->` HTML comments — they are stripped before the prompt
   is rendered, mirroring `briefing.md` behavior.
7. Optionally symlink/copy chosen file to `examples/<name>/selected/`.
8. Confirm the manual vector step: user and/or LLM authors `examples/<name>/<name>.tex`.
   Starter: `cp styles/tex_template.tex examples/<name>/<name>.tex`.
9. After the `.tex` file exists, continue with `/fig_compile <name>`.

No automatic ranking in v0.1. User judgment only.
No automatic `.tex` scaffold or preview vectorization in v0.1.

Next: run `uv run python3 scripts/llm_author_prompt.py examples/<name>` to generate the LLM authoring prompt, paste into a code-capable LLM, save the response as examples/<name>/<name>.tex, then /fig_compile <name>.
