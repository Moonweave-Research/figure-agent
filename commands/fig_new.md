---
description: Scaffold a new figure project under examples/<name>/ with spec.yaml + briefing.md.
---

Create a new figure project.

**Usage**: `/fig_new <figure_name>`

Steps:
1. Create directory `examples/<figure_name>/` with subdirs `previews/`, `build/`, `exports/`.
2. Write `spec.yaml` skeleton:
   ```yaml
   name: <figure_name>
   panels:
     - id: a
       caption: ""
   style_profile: polymer-default
   selected_preview: null
   ```
3. Write `briefing.md` skeleton with prompts:
   - What does this figure show? (1-2 sentences)
   - Domain vocabulary to use (terms, materials, mechanisms)
   - Composition intent (panel layout, flow direction)
   - What MUST NOT appear (sensitive numbers, geometry, conditions)
4. Confirm to user with path to edit briefing.md.

After this, user fills briefing.md, then runs `/fig_prompt`.
