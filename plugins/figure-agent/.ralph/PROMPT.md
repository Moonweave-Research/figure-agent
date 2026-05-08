# Ralph — figure-agent v0.2 review patch loop

작업 루트: plugins/figure-agent/ (이 세션의 cwd가 여기여야 함)
진행판: REVIEW_PATCH_PLAN.md (단일 진실 원천)

매 iteration:

1. REVIEW_PATCH_PLAN.md를 처음부터 끝까지 Read.
2. 첫 번째 '[ ]' 항목 선택. P0 → P1 → P2 → P3 우선순위 절대 준수 (Dn 번호 순서가 아님).
3. evidence에 적힌 모든 파일을 Read로 재확인. 메모리/추측 금지.
4. 가장 작은 패치 한 개. 무관한 리팩토링 금지. 새 파일은 D8 외 금지. 테스트는 기존 test_*.py에 추가.
5. `uv run pytest -x` 또는 관련 test 파일만 통과 확인.
6. 다른 fixture (특히 examples/golden_trap_depth_picture/, examples/fig3_trap_schematic_v97/) 회귀 시 즉시 롤백. accepted: false 게이트 동작이 D4 외 결함에서 바뀌면 회귀로 본다.
7. fix와 PLAN 갱신을 한 commit에 묶는다:
     git add <변경 파일들> REVIEW_PATCH_PLAN.md
     git commit -m "fix(review): D? <짧은 요약>"
   (`git add -p` 금지 — interactive로 막힘. amend / reset --hard / force push / --no-verify / git rm / rm -rf 금지.)
8. 다음 iteration까지 step 1로 복귀.
9. 모든 P0/P1/P2/P3 라인이 `[x]` · `[SKIP - 사유]` · `[BLOCKED - 메시지]` 중 하나이고 `uv run pytest -x` 통과면 promise 출력 후 종료.

가드레일 (위반 시 즉시 중단):
- examples/*/exports/ 의 git-tracked 파일 수정 금지 (TRACKED_GOLDEN 보호).
- pyproject.toml / uv.lock 수정 금지 (stash로 분리됨).
- D7은 default (a) 따름. parse_spec ValueError 추가가 기존 7개 fixture를 모두 깨면 `[SKIP - multi-style v0.2+ lock]` 처리.
- D8은 docs/ .md 1개만, 코드 0줄.
- 같은 결함 3 iteration 연속 실패 시 `[BLOCKED]` 처리하고 다음으로.

종료 토큰:
<promise>FIGURE_AGENT_REVIEW_8_CLOSED</promise>
