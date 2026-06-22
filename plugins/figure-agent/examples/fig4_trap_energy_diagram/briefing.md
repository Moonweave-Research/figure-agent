# Briefing — fig4_trap_energy_diagram

> **Genre**: Nature Communications main-text/SI schematic — clean white background.
> Energy-level diagram + DOS. **Diagnostic intent (2026-06-20)**: figure #4, 3rd
> data point; chosen to STRESS lever B (relational/quantitative correctness).
> Mode: SCHEMATIC ONLY — energy values are illustrative ranges, no numeric ticks.

---

## §1. Topic
황고분자의 **bimodal trap-state 에너지 풍경**: mobility edge(Ec)와 valence band(Ev)
사이 gap 안에, Ec 근처의 **shallow tail traps**(구조적 kink)와 깊은 곳의
**deep S–S radical traps**(화학적 결함)가 공존. 우측에 이 두 군이 만드는 bimodal
trap DOS g(Et)를 같은 에너지 축에 정렬 — real-space 준위 = 분광학적 DOS 피크.

## §2. Domain vocabulary
mobility edge (Ec), valence band (Ev, S 3p lone pairs), band gap (Eg ≈ 2 eV),
tail/shallow traps, deep Coulomb traps, S–S radical, trap density of states g(Et),
capture, Poole–Frenkel thermal/field release, small-polaron hopping.

## §3. Composition intent
좌(에너지 다이어그램) + 우(DOS), 같은 수직 에너지 축 공유.
- **Panel a (좌)**: 수직 E축; vacuum(점선)·Ec·Ev 준위; gap에 shallow 띠(Ec 바로 아래,
  cTeal)와 deep 준위들(red, gap 깊숙이); trapped 전자(dots); capture(↓)·release(↑ 점선)
  화살표; Eg 양방향 화살표.
- **Panel b (우)**: g(Et) bimodal 곡선(밀도=가로, 에너지=세로) — shallow 피크(위)·deep
  피크(아래, 더 큼). 좌측 준위에서 우측 피크로 점선 connector(같은 에너지 = 같은 피크).

## §4. Normalize / avoid literal overfit
- 정확한 eV 수치 tick, 측정값을 결과처럼 박지 말 것 — 범위/정성. (Fig 1(e) 교훈)
- deep trap 깊이: 이론(>1 eV) vs ISPD 측정(~0.74–0.80 eV) **충돌** — 그림은 "deep"로
  정성 유지, 숫자 단정 금지 (lever-B 시험 포인트).

## §5. Style notes
polymer-paper preamble. shallow = blue/teal, deep = **red** (fig1 색 컨벤션 공유),
band/축 = cGray, DOS 곡선 = cAmber. 178mm, 흰 배경.

## §6. Physics invariants
- **shallow는 deep보다 위(얕음)** — 순서 뒤집기 금지.
- **Ec > Ev**, gap Eg ≈ 2 eV (poly(S-r-DIB) ~2.08 eV — 알려진 물질 상수).
- shallow = Ec 근처 tail(0.1–0.3 eV), deep = S–S radical(깊은, >1 eV 이론). 색: shallow blue / deep red.
- g(Et) **bimodal**; shallow 피크 ↔ shallow 띠, deep 피크 ↔ deep 준위 **정렬**(같은 에너지).
- deep 준위에 전하 더 많이(deep-dominated 가능) — 단, schematic.

## §7. Author intent — semantic constraints (for vision critique grounding)
(a) **Must depict**
- gap 안에 **두 개의 구분된 trap 군**(Ec 근처 얕은 띠 + 깊은 red 준위)이 명확히 분리.
- 우측 DOS가 **두 피크**(bimodal)이고 각각 좌측 준위 에너지에 **정렬**(connector로 연결).
- shallow=blue/teal, deep=red 색 일관 (fig1과 동일 컨벤션).
- capture(아래로)·release(위로, 느림) trap 동역학 화살표.
(b) **Must avoid**
- data-plot tone (eV tick 숫자, 측정 곡선) — schematic.
- shallow/deep 깊이 순서 뒤집기, DOS 피크-준위 어긋난 정렬 (= lever-B로 잡아야 할 오류 클래스).
- 측정 deep 깊이(0.74–0.80 eV)를 이론(>1 eV)과 뒤섞어 단정 — 정성 유지.
- 캔틸레버/actuation 요소 (이 figure는 trap 물리 전용).
