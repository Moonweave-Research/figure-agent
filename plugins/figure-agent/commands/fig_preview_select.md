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
6. Optionally symlink/copy chosen file to `examples/<name>/selected/`.
7. Confirm the manual vector step: user and/or LLM authors `examples/<name>/<name>.tex`.
8. After the `.tex` file exists, continue with `/fig_compile <name>`.

No automatic ranking in v0.1. User judgment only.
No automatic `.tex` scaffold or preview vectorization in v0.1.
