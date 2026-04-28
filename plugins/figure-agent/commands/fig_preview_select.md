---
description: List previews/, present to user, record selection in spec.yaml.
---

Select a preview to use as compile inspiration.

**Usage**: `/fig_preview_select` (inside examples/<name>/ or --name)

Steps:
1. List `examples/<name>/previews/*.png` and `*.jpg` (alphabetical).
2. If empty, instruct user to run external image gen + save into previews/, then re-run.
3. Display numbered list with file sizes:
   ```
   [1] alpha_01.png (1.2 MB)
   [2] alpha_02.png (1.4 MB)
   [3] gemini_v3.jpg (980 KB)
   ```
4. Ask user to pick by number.
5. Update `spec.yaml`: `selected_preview: <filename>`.
6. Optionally symlink/copy chosen file to `examples/<name>/selected/`.
7. Confirm with next step suggestion: `/fig_compile`.

No automatic ranking in v0.1. User judgment only.
