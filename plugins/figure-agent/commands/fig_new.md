---
description: Conversational interview to scaffold a new figure (schematic) and auto-fill briefing.md + spec.yaml.
---

> **Shared entry point.** `/fig_new` scaffolds the per-figure folder for the
> active quality-kernel workflow. After this command, author `<name>.tex`
> directly from briefing intent plus optional `reference_image`,
> optional per-panel `panels[].reference_image` + `panels[].bbox_pdf_cm`,
> and `coordinate_hints.yaml`, then run `/fig_compile`.
>
> See `docs/architecture-overview.md` for the layer model.

Create a new figure project via a conversational interview. **Do not just dump a markdown
template and ask the user to fill it in an editor** — that defeats the purpose of the plugin.
Run a 7-question interview in chat, write each answer into `briefing.md` as it arrives.

**Usage**: `/fig_new <name>`

Run from the plugin root.

## Step 1 — Scaffold

Create directory `examples/<name>/` (`<name>` maps to `examples/<name>/`) with:
- subdirs `previews/`, `build/`, `exports/` (each containing `.gitkeep`)
- `spec.yaml` skeleton (`name`, `panels: []`, `style_profile: polymer-default`)
- `briefing.md` skeleton with 7 empty sections (Topic / Vocabulary / Composition /
  Normalize / Style notes / Physics invariants / Author intent), each prefaced with
  `## N. <title>` and an HTML-comment TODO hint. Section 7 is the cheap-intervention
  payload that grounds `/fig_critique` against generic-best-practice drift; `critique_brief.py`
  reads §7 verbatim into the vision brief.

## Step 2 — Run the interview

Ask the user the following seven questions, one per turn (or all at once if user asks for it).
After each answer, **write the answer into the corresponding section of `briefing.md`**
(strip the HTML-comment TODO when overwriting). For §3, also propagate panel structure into
`spec.yaml`. If the user already has fixed per-panel references, optionally record each
panel's `reference_image` path under `panels[]`; leave `bbox_pdf_cm` absent until the user
runs `fig-agent helper spec_bbox_helper.py <name> --panel id=<id> x=<x0>,<x1> y=<y0>,<y1>`.

1. **§1 Topic** — "이 figure가 무엇을 보여주나요? (1-2 문장으로 한 줄 요지)"
2. **§2 Domain vocabulary** — "어떤 도메인 용어를 써야 하나요? (재료/메커니즘/구조/물리 용어)"
3. **§3 Composition intent** — "panel 구성과 element 배치는? (2-panel 비교 / 단일 / 좌→우
   흐름 / 등)"
4. **§4 Normalize / avoid literal overfit** — "외부 imagegen이 숫자/샘플명/조건에 과하게 끌려가면 안 되는 항목은? (예: 정확 수치, sample code, dimension, count)"
5. **§5 Style notes** — "추가 style preference 있나요? (없으면 'skip' 응답)"
6. **§6 Physics invariants** — "그림이 반드시 지켜야 하는 물리/개념 제약은? (예:
   trap level 위치, arrow 방향, 보존해야 할 관계. 이 섹션은 prompt normalization에서
   일반화하지 않고 그대로 보존되므로 짧고 개념 중심으로 작성)"
7. **§7 Author intent — semantic constraints (for vision critique grounding)** —
   "vision critique이 generic best-practice로 표류하지 않도록 author intent를 두 항목으로 명시:
   (a) **Must depict** — 반드시 시각적으로 식별 가능해야 할 의미 단위 (예: 'polymer
   chain은 wave가 아닌 monomer-level chemistry로 보여야 함').
   (b) **Must avoid** — generic style heuristic으로 잘못 추가될 수 있는 변경 (예: '비대칭이
   narrative point — 대칭 ellipsis 추가 금지').
   짧은 bullet 몇 개로 OK; semantic_assertions / snippets used 등 세부는 .tex 작성 후 보강.
   이 섹션이 비어 있으면 critique이 N=1 dogfood처럼 generic-best-practice drift로 떨어짐
   (golden_trap_depth_picture: §7 없을 때 F1_w=0.244 → §7+reference attach 후 0.981)."

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

After all 7 sections are filled (and any scope-drift conflicts resolved), tell the user:

> "briefing 완료 ─ examples/<name>/briefing.md 에 기록됨. target matching이 필요하면
> figure-level reference PNG를 저장하고 spec.yaml.reference_image를 기록한 뒤
> /fig_extract <name>을 실행하세요. multi-panel target matching이 필요하면
> panel reference PNG를 reference/ 아래에 저장하고 panels[].reference_image를 기록한 뒤
> spec_bbox_helper로 bbox_pdf_cm를 계산하세요. 이후 semantic TikZ를 작성하고
> /fig_compile <name>으로 검증합니다. /fig_critique 실행 시 §7 Author intent +
> reference image가 자동으로 vision brief에 첨부되어 generic-best-practice drift를
> 막습니다 (panel reference가 있으면 panel crop/reference pair도 함께 첨부)."

`selected/` is not part of the active workflow. Historical preview-selection
metadata is ignored by current stage inference.

## Lesson — why this matters

In 2026-04-28 fig3_trapping_concept dogfooding, the first attempt drifted to a 4-panel data
figure (S60-S85 sweep, n vs composition, ISPD DOS, τ_d) before the user caught the scope
mismatch six steps later. The interview did not check for data-plot signals, so the plugin
proceeded all the way through prompt generation, image gen, and a final-vector recommendation
for real data before reset. Step 3 above is the gate that catches this within the interview
itself.

Next: author semantic TikZ from `briefing.md`; if target matching matters, run `/fig_extract <name>` first.
