---
description: Conversational interview to scaffold a new figure (schematic) and auto-fill briefing.md + spec.yaml.
---

> **Shared entry point.** `/fig_new` scaffolds the per-figure folder for both
> the active quality-kernel workflow and the frozen v0.1 image-gen orchestration
> path. After this command the user picks their path:
> - active: author `<name>.tex` directly from briefing intent + optional `reference_image`, then `/fig_compile`;
> - legacy: `/fig_prompt` → external image-gen → `/fig_preview_select` → author `<name>.tex`, then `/fig_compile`.
>
> See `docs/architecture-overview.md` for the layer model.

Create a new figure project via a conversational interview. **Do not just dump a markdown
template and ask the user to fill it in an editor** — that defeats the purpose of the plugin.
Run a 6-question interview in chat, write each answer into `briefing.md` as it arrives.

**Usage**: `/fig_new <name>`

Run from the plugin root.

## Step 1 — Scaffold

Create directory `examples/<name>/` (`<name>` maps to `examples/<name>/`) with:
- subdirs `previews/`, `build/`, `exports/` (each containing `.gitkeep`)
- `spec.yaml` skeleton (`name`, `panels: []`, `style_profile: polymer-default`,
  `selected_preview: null`)
- `briefing.md` skeleton with 6 empty sections (Topic / Vocabulary / Composition /
  Normalize / Style notes / Physics invariants), each prefaced with `## N. <title>`
  and an HTML-comment TODO hint

## Step 2 — Run the interview

Ask the user the following six questions, one per turn (or all at once if user asks for it).
After each answer, **write the answer into the corresponding section of `briefing.md`**
(strip the HTML-comment TODO when overwriting). For §3, also propagate panel structure into
`spec.yaml`.

1. **§1 Topic** — "이 figure가 무엇을 보여주나요? (1-2 문장으로 한 줄 요지)"
2. **§2 Domain vocabulary** — "어떤 도메인 용어를 써야 하나요? (재료/메커니즘/구조/물리 용어)"
3. **§3 Composition intent** — "panel 구성과 element 배치는? (2-panel 비교 / 단일 / 좌→우
   흐름 / 등)"
4. **§4 Normalize / avoid literal overfit** — "외부 imagegen이 숫자/샘플명/조건에 과하게 끌려가면 안 되는 항목은? (예: 정확 수치, sample code, dimension, count)"
5. **§5 Style notes** — "추가 style preference 있나요? (없으면 'skip' 응답)"
6. **§6 Physics invariants** — "그림이 반드시 지켜야 하는 물리/개념 제약은? (예:
   trap level 위치, arrow 방향, 보존해야 할 관계. 이 섹션은 prompt normalization에서
   일반화하지 않고 그대로 보존되므로 짧고 개념 중심으로 작성)"

## Step 3 — Scope-drift check (CRITICAL)

**After §1 and §3 answers**, scan the user's text for data-plot red flags. If detected, halt
the interview and ask the user to confirm scope before continuing.

Red-flag patterns:
- Quantitative variable symbols (`n`, `τ`, `V`, `I`, `T`, `t`, `E_t`, `g(E_t)`, etc.)
- "vs <axis>" phrasing or "sweep" / "ratio" terminology
- Measurement keywords: "raw + fit", "error bar", "peak position", "DOS curves",
  "discharge time", "power-law decay"
- Numerical sweep ranges (S60-S85, 70/30, 25-100°C, etc.)

When matched, surface the conflict to the user explicitly:

> "이 답변에 정량 데이터 신호 (`<matched terms>`) 가 보입니다. figure-agent는 schematic 전용
> (개념도, 메커니즘 다이어그램, 비교 도식)이고 data plot은 영역 밖입니다. 두 옵션:
>
> (A) schematic으로 reframe — qualitative shape만, 수치/축 tick 없이 개념 흐름만 표현
> (B) figure-agent 밖으로 redirect — matplotlib 또는 Graph_making_hub로 data plot 작성
>
> 어느 길로 가시겠습니까?"

Continue the interview only after explicit confirmation. Do NOT silently proceed with a data
figure intent.

## Step 4 — Confirm and hand off

After all 6 sections are filled (and any scope-drift conflicts resolved), tell the user:

> "briefing 완료 ─ examples/<name>/briefing.md 에 기록됨. /fig_prompt <name> 실행하시면 normalized
> prompt 생성합니다. 또는 briefing 더 손볼 부분 있으시면 알려주세요."

`selected/` is optional in v0.1. `/fig_new` does not need to create it; `/fig_preview_select`
may create a copy or symlink there for convenience.

## Lesson — why this matters

In 2026-04-28 fig3_trapping_concept dogfooding, the first attempt drifted to a 4-panel data
figure (S60-S85 sweep, n vs composition, ISPD DOS, τ_d) before the user caught the scope
mismatch six steps later. The interview did not check for data-plot signals, so the plugin
proceeded all the way through prompt generation, image gen, and a final-vector recommendation
for real data before reset. Step 3 above is the gate that catches this within the interview
itself.

Next: /fig_prompt <name>
