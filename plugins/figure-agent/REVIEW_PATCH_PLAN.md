# figure-agent v0.2 review — patch plan

각 항목은 fix + PLAN 갱신이 한 commit. 완료 시 `[ ]` → `[x] (commit <sha7>)`.

## P0 — correctness (export 무결성)

- [x] **D1** `scripts/run_export.py` FRESH 판정이 exports/<name>.pdf 하나만 본다. (commit 2f32aa4)
  evidence: `scripts/export_freshness.py:46-54`. SVG/TIFF/PNG 누락 시 `_regenerate` 미호출.
  fix: `compute_export_state`가 4개 artifact(PDF/SVG/TIFF/PNG) 모두 존재 + PDF 컨텐츠 fresh를 요구. 누락은 `STALE`.
  test: `tests/test_export_freshness.py` 신규 — PDF만 있고 SVG 없을 때 STALE.

- [x] **D2** `scripts/critique_brief.py`가 `spec.yaml.reference_image`를 무시. (commit 2a4a160)
  evidence: `scripts/critique_brief.py:61-70`.
  fix: `_reference_image_path`가 먼저 `parse_spec(...)["reference_image"]` 시도, 없을 때만 디렉터리 fallback.
  test: `tests/test_critique_brief.py` 신규 — `reference_image: reference/foo.png` 선언 시 그것을 사용.

- [x] **D3** critique freshness 소스 셋이 `spec.yaml`, reference image, `coordinate_hints.yaml` 누락. (commit 95cbad8)
  evidence: `scripts/critique_brief.py:73-77` + `scripts/status.py:13` 주석의 정합 약속.
  fix: `scripts/critique_brief.py:_critique_source_paths` + `scripts/status.py:_source_paths` 둘 다에 spec.yaml + 해석된 reference_image + coordinate_hints.yaml 추가 (존재할 때만).
  test: `tests/test_critique_brief.py` + `tests/test_status.py` 양쪽에 신규 케이스.

## P1 — gate 잘못 발사

- [SKIP - empirical: exports/ 자체가 비어 있어 artifact missing 단계가 먼저 끊김. golden_contract 판정에 도달하지 않음. /fig_export 미실행 fixture들이 대상이므로 gate 로직 fix가 불필요.] **D4**

- [x] **D5** TRACKED_GOLDEN ↔ `/fig_status stale_export` 안내 충돌. (commit e2520fd)
  evidence: `scripts/status.py:204` (`_NEXT_4_STALE`) vs `scripts/run_export.py:77-83` (TRACKED_GOLDEN skip).
  fix: status가 `exports_substate == TRACKED_GOLDEN` + stale 동시일 때 `_NEXT_4_TRACKED_STALE` 분기 — "tracked golden artifact는 의도적 stale; rolling forward 시 `/fig_export <name> --force-golden`".
  test: `tests/test_status.py` 신규.

## P2 — 데이터 모델 정확성

- [x] **D6** `coordinate_hints.yaml`이 `extraction_version: 0.1`로 남아도 stale 미감지. (commit 0a28044)
  evidence: `scripts/reference_extract.py:77` `EXTRACTION_VERSION="0.3"`. 실제 사례: `examples/fig3_trap_schematic_v97/coordinate_hints.yaml:2`. 문서 drift: `commands/fig_extract.md:41`.
  fix: `scripts/status.py:_append_reference_image_check`가 hints의 `metadata.extraction_version`를 `EXTRACTION_VERSION`과 비교; 불일치 시 `coordinate_hints_outdated` note. 문서 예시도 `"0.3"`으로 갱신.
  test: `tests/test_status.py` 신규 — 0.1 hints에서 `coordinate_hints_outdated` 출력. 기존 `tests/test_status.py:295,314`의 0.1 픽스처는 outdated 기대값으로 갱신.

- [x] **D7** `style_profile`이 dead metadata. (commit 6cb4bfc)
  evidence: 7개 fixture가 spec.yaml에 `polymer-default` 또는 `polymer-paper` 선언. 코드 어디서도 키 미읽음.
  fix: `scripts/inputs.py:parse_spec`에 known-set ({"polymer-default","polymer-paper"}) 검증 ValueError. `scripts/status.py`에 알 수 없는 값일 때 `style_profile_unknown` note. lint_tex.py는 건드리지 않음.
  test: `tests/test_inputs.py` — 알 수 없는 값에 ValueError. `tests/test_status.py` — note 출력. **기존 모든 fixture의 style_profile 값이 known-set 안에 있는지 확인 필수.** 만약 알 수 없는 값이 있으면 `[SKIP - multi-style v0.2+ lock]`.

## P3 — 새 layer (큰 결정, 문서만)

- [x] **D8** L5.5 post-export visual critic 부재. (commit 2c9d175)
  evidence: `commands/fig_critique.md`는 `build/<name>.png`만 본다. dvisvgm SVG → rsvg-convert PNG 경로의 export PNG는 별개.
  scope: spec만. 구현은 보류.
  fix: `docs/architecture-v0.2.1-l5_5-export-critic.md` 작성 — 트리거 시점, 입력(`exports/<name>.png` + 동일 brief), output 경로(`exports_critique.md`), report-only N=5+ 게이트, freshness 입력 셋(D3와 정합).
  test: 없음 (문서 PR).

## 게이트

모든 P0/P1/P2/P3 항목 처리 후 `uv run pytest -x` 통과 시:
1. `git log --oneline | head -10` 출력.
2. `<promise>REVIEW_CLOSED</promise>`
