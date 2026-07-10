# Figure Agent 통합 제품 스펙 및 수행 계획

## 1. 문서 권위

- 상태: **Active**
- 최초 승인일: 2026-07-10
- 현재 구현 허용 범위: **Slice 0 — 기준선 정상화**
- 적용 범위:
  - `plugins/figure-agent`
  - `plugins/figure-agent-py`
  - `experiments/python_svg_semantic_fig1`
- 제품 방향, 아키텍처 경계, 레거시 판정, 실행 순서의 단일 소스는 이 문서다.
- 기존 설계서, handback, phase plan, retrospective는 근거 자료다. 이 문서와 충돌할 때 계획 권위를 갖지 않는다.
- 런타임의 현재 동작은 코드, 스키마, 테스트, 렌더 산출물이 증명한다. 이 문서는 구현되지 않은 동작을 현재 기능처럼 주장하지 않는다.
- 제품 결정이나 Slice 순서를 변경하는 커밋은 이 문서를 같은 변경 단위에서 갱신해야 한다.
- 별도의 경쟁 roadmap이나 authoring spec을 만들지 않는다. 세부 실행 기록은 이 문서의 결정을 링크하고 결과만 기록한다.

### 1.1 권위 우선순위

| 질문 | 권위 |
| --- | --- |
| 제품이 무엇을 지향하는가 | 이 문서 |
| 다음에 어떤 Slice를 수행하는가 | 이 문서 |
| 현재 명령과 파일이 실제로 무엇을 하는가 | 현재 브랜치의 코드와 테스트 |
| 특정 렌더가 합격했는가 | 기계 gate 결과와 명시적 인간 판정 |
| 과거 실험에서 무엇을 배웠는가 | 해당 commit, artifact, handback |

문서와 런타임이 다르면 차이를 결함으로 기록한다. 문서만 고쳐서 구현 완료로 처리하거나, 현재 코드만 보고 제품 방향을 암묵적으로 변경하지 않는다.

## 2. 현재 기준선

이 절은 2026-07-10의 로컬 점검을 기록한다. 변동 가능한 값은 Slice 0 종료 시 다시 고정한다.

| 항목 | 현재 사실 |
| --- | --- |
| 작업 브랜치 | `experiment/python-svg-semantic-fig1` |
| Slice 0C 기록 기준점 | `b6771a51bdc414cacc363569b461f5c4a48449ad` |
| 로컬 `origin/main` | `9d3db7347261229d6a0ce1c09b8893d49cf06e2f` |
| 공통 기반 | `0295760793f6f2659b801a8ed7e687f0acdd76ca` |
| 분기 상태 | 작업 브랜치 전용 80 commits, `origin/main` 전용 1309 commits |
| Python Fig1 gate | Slice 0A branch에서 8/8; `render-parity` 통과 |
| tracked Fig1 SVG hash | `03e51b775bb0dc063e131ecff6f684ab9cb6fd807546df01e01076e5e4d131e1` |
| 재생성 SVG hash | locked toolchain에서 2회 모두 `03e51b775bb0dc063e131ecff6f684ab9cb6fd807546df01e01076e5e4d131e1` |
| Phase 3-C | 구현 commit 후 revert됨; 아이디어 폐기 판정은 아님 |
| Phase 3 문서 | historical로 격하됨; 잔여 체크박스 정리는 Slice 1 salvage audit 대상 |

현재 브랜치와 `origin/main`은 서로 대규모로 분기돼 있다. 검증 없이 merge, rebase, 또는 한쪽의 상태 문서를 다른 쪽에 덮어쓰지 않는다.

## 3. 제품 정의

Figure Agent는 논문용 과학 그림의 **저작 보조와 품질 보증을 연결하는 시스템**이다. 하나의 제품 안에서 두 책임을 분리한다.

### 3.1 Quality Kernel

`plugins/figure-agent`가 현재 담당하는 안정화 계층이다.

- 입력과 출처 기록
- Style Lock
- compile/export
- 시각 및 구조 QA
- acceptance와 release gate
- 재현성과 provenance
- stale artifact와 상태 불일치 진단

저작 도구가 무엇이든 kernel은 동일한 검증 계약을 제공해야 한다.

### 3.2 Authoring Layer

`plugins/figure-agent-py`와 `experiments/python_svg_semantic_fig1`에서 검증 중인 저작 계층이다.

- 승인된 scaffold
- 과학적 의미를 보존하는 typed semantic payload
- 계산 가능한 geometry
- 수정 가능한 vector source
- 결정론적 SVG 합성
- 사람과 agent가 특정 의미 단위를 수정할 수 있는 stable ID

Authoring Layer는 현재 실험 상태다. 두 번째 실제 figure에서 재사용성을 증명하기 전에는 기본 제품 계층으로 승격하지 않는다.

### 3.3 통합 제품 경계

```text
의도와 과학적 주장
  -> reference authority 분류
  -> 승인된 scaffold
  -> semantic payload scene
  -> editable vector source와 render
  -> Quality Kernel 검증
  -> 인간 시각 판정
  -> 명시적 acceptance
  -> export와 provenance
```

Kernel과 Authoring Layer는 한 제품의 계층이지만 독립적으로 교체 가능해야 한다. Kernel은 Python authoring에 종속되지 않고, Authoring Layer는 kernel의 acceptance를 스스로 선언하지 않는다.

## 4. 목표와 비목표

### 4.1 목표

1. 과학적 의미와 시각적 구조를 편집 가능한 source로 유지한다.
2. 동일 입력과 고정된 환경에서 byte-identical vector source를 재생성한다.
3. 저작 도구와 QA/release 판단을 분리한다.
4. reference, scaffold, payload, source, export 사이의 provenance를 추적한다.
5. 실제 서로 다른 figure family에서 재사용 가능한 authoring boundary를 증명한다.
6. 사람이 최종 시각 판단과 acceptance를 소유한다.
7. 과거 실험의 유효한 부분을 현재 역량으로 재평가해 흡수한다.

### 4.2 현재 비목표

- blank canvas에서 publication-grade composition을 완전 자동 생성
- reference PNG의 path 또는 pixel tracing
- 실측 데이터 생성, fitting, 또는 Graph-making workflow 대체
- SVG와 TikZ 동시 지원을 선결 조건으로 설정
- LLM이나 자동 metric이 인간 acceptance를 대신하는 것
- 하나의 Fig1 성공만으로 범용 authoring engine을 선언하는 것
- 모든 과거 코드를 유지하기 위한 호환 계층 추가

비목표는 영구 폐기가 아니다. 해당 가설의 진입 조건이 충족되면 이 문서의 의사결정 게이트를 통해 다시 활성화할 수 있다.

## 5. 설계 원칙

### 5.1 Scaffold-first는 기본 가설이지 교리가 아니다

현재 가장 강한 근거는 좋은 composition scaffold를 먼저 승인하고 semantic payload를 그 안에 결합하는 방식이다. 그러나 과거 semantic-first probe의 품질 부족을 접근 자체의 영구 실패로 판정하지 않는다. 더 나은 constraint solver, model capability, layout representation으로 재실험할 수 있다.

### 5.2 과학적 의미와 composition 권위를 분리한다

- semantic payload: 대상, 관계, 물리량, 부호, 인과 주장
- scaffold: panel, local box, flow anchor, hero hierarchy, reading order
- style: typography, stroke, palette, spacing, material treatment
- renderer: 위 계약을 source로 변환

한 계층이 다른 계층의 사실을 암묵적으로 소유하지 않는다.

### 5.3 기계 검증과 인간 판정을 분리한다

기계 gate가 검증할 수 있는 것은 schema, containment, invariant, artifact freshness, deterministic replay다. 미학적 완성도, 논문 전달력, reference 사용의 적절성은 명시적 인간 판정이 필요하다.

### 5.4 보이는 결과가 최종 증거다

설정, schema, test wiring만으로 시각 기능 완료를 주장하지 않는다. source 변화가 실제 SVG/PNG/PDF 픽셀 또는 편집 가능한 구조에 도달했음을 확인한다.

### 5.5 레거시를 능력 한계와 구조 한계로 분해한다

과거 결과가 약했다는 사실만으로 아이디어를 폐기하지 않는다. 당시 구현 능력, 도구, dependency, prompt, reference 품질, verifier 과적합을 독립 변수로 본다.

## 6. Reference Authority 계약

모든 외부 이미지, 스케치, 기존 figure는 사용 전에 다음 authority를 항목별로 선언한다.

| Authority | 허용 사용 |
| --- | --- |
| `scientific_ground_truth` | 과학적 내용과 관계 검증 |
| `layout_evidence` | panel 배치, flow, hierarchy |
| `style_evidence` | 색, stroke, typography, material treatment |
| `content_reference` | 명시된 object나 annotation의 내용 |
| `anti_reference` | 복제하면 안 되는 topology, claim, geometry, style |

하나의 reference가 모든 항목의 ground truth라고 가정하지 않는다. 예를 들어 layout과 style은 참조하되 network topology는 `anti_reference`일 수 있다. 이 경계는 scaffold나 scene 작성 전에 machine-readable manifest와 human-readable briefing에 모두 남긴다.

## 7. Authoring 계약

### 7.1 필수 입력

- figure intent와 scientific claims
- reference authority manifest
- 승인된 scaffold 또는 승인 대기 중인 scaffold candidate
- semantic payload scene
- style profile
- provenance metadata

### 7.2 Scaffold 계약

최소 필드:

- schema version
- canvas
- panel ID와 role
- panel bounds
- local object slots
- object-to-slot binding
- flow anchors와 reading order
- hero 또는 primary focus
- reference provenance
- human scaffold sign-off

모든 relation endpoint와 reading-order target은 실제 선언된 ID를 참조해야 한다. 존재하지 않는 ID, 암묵적 panel, 미선언 claim reference를 허용하지 않는다.

### 7.3 Semantic scene 계약

각 object는 최소한 다음을 가진다.

- stable semantic ID
- versioned object kind
- typed payload
- panel 또는 slot binding
- 관계와 claim reference
- source provenance
- renderer-neutral geometry parameter 또는 계산 규칙

Fig-specific policy는 reusable engine schema에 섞지 않는다. 재사용 가능한 object와 특정 figure의 시각 policy를 별도 모듈과 별도 gate로 유지한다.

### 7.4 출력 계약

Authoring Layer는 다음을 출력한다.

- editable vector source
- rendered review artifact
- semantic/scaffold manifest
- source-to-artifact hash와 toolchain identity
- machine gate report
- human-review packet

출력만으로 acceptance를 설정하지 않는다.

## 8. 상태와 Acceptance 계약

### 8.1 단일 machine authority

현재 kernel 호환 기간에는 `spec.yaml.accepted`를 인간 acceptance의 유일한 machine-readable authority로 사용한다.

- `QUALITY_AUDIT.md`, critique, report, status 출력은 파생 자료다.
- 파생 문서에 독립적인 top-level `accepted` 또는 `submission-safe` truth를 두지 않는다.
- 파서가 Markdown 전체에서 임의의 `true` 하나를 검색해 합격시키는 동작을 허용하지 않는다.
- 파생 자료가 acceptance와 모순되면 gate가 실패해야 한다.
- acceptance 변경은 명시적인 인간 행위와 audit event를 요구한다.

별도 state service는 현재 필수 아키텍처가 아니다. 단일 파일 방식이 실제 동시성, 복구, 감사 요구를 충족하지 못한다는 반복 증거가 생길 때 제안한다.

### 8.2 상태 표현

상태 문자열을 여러 문서가 경쟁적으로 정의하지 않는다. 운영 표시는 authoritative fields와 artifact evidence에서 계산한다.

- authoring readiness
- render freshness
- machine gate result
- human review requirement
- acceptance
- export/release readiness

각 값은 서로 독립적으로 보고한다. `machine gates pass`는 `human accepted` 또는 `release ready`와 동의어가 아니다.

## 9. 검증 계약

### 9.1 기계 gate

최소 검증 범주:

- schema와 ID referential integrity
- semantic/physics invariant
- scaffold containment와 object binding
- source-artifact render parity
- 현재 Python SVG renderer의 byte-identical source hash
- provenance completeness
- stale artifact 탐지
- kernel compile/export 계약
- acceptance authority의 유일성과 모순 부재

### 9.2 인간 review

인간 reviewer는 다음을 명시적으로 판정한다.

- scientific story가 읽히는가
- visual hierarchy가 의도와 맞는가
- reference authority 경계를 위반하지 않았는가
- text/shape 관계가 실제 크기에서 읽히는가
- figure가 manuscript context에서 사용 가능한가

`human review required`는 실패가 아니라 정상 상태다. recommendation packet, critique, 자동 metric은 acceptance artifact가 아니다.

### 9.3 성공 주장 기준

| 주장 | 필요한 증거 |
| --- | --- |
| deterministic | 깨끗한 환경에서 반복 재생성 결과가 동일 |
| reusable | 두 번째 실제 figure가 Fig1 전용 모듈 없이 같은 engine 경계를 사용 |
| visually improved | 동일 입력의 before/after와 인간 판정 |
| kernel integrated | kernel이 authoring output을 compile/export/QA하고 provenance를 보존 |
| production ready | 최소 두 figure family, 전체 gate, human acceptance, clean replay |

## 10. 레거시 흡수 정책

### 10.1 판정 상태

모든 과거 아이디어, commit, probe, revert는 다음 중 하나로 기록한다.

- `adopt`: 현재 근거로 바로 흡수
- `retest`: 당시 구현 조건의 영향을 분리하기 위해 재실험
- `hold`: 가치가 가능하지만 현재 제품 목표의 선결 조건이 아님
- `retire`: 현재 제약과 충돌하거나 통제된 재실험에서도 가설이 기각됨

`revert됨`, `시각 결과가 약했음`, `당시 test 실패`만으로 `retire`하지 않는다.

### 10.2 재실험 기록

각 항목은 다음을 남긴다.

- 원래 가설
- 당시 구현과 관찰 결과
- 실패 가능 원인
- 현재 달라진 역량 또는 도구
- 최소 재실험
- 비교 baseline
- visible artifact
- 채택/보류/폐기 판정과 근거

재실험은 실행 전에 다음을 고정한다.

- 동일한 input, payload, scaffold, style profile
- 고정된 dependency와 toolchain
- 기존 구현 baseline과 새 구현 treatment
- primary outcome과 사전 실패 기준
- 첫 유효 실행 후 허용되는 corrective iteration 최대 두 번

basic correctness, reproducibility, 또는 artifact 생성에 실패한 실행은
아이디어의 구조적 실패 증거로 사용하지 않는다. 유효 실행을 만들지 못하면
`hold`로 남긴다. `retire`는 제품 hard constraint와 직접 충돌하거나, basic
gate를 통과한 matched comparison이 두 corrective iteration 뒤에도 사전 실패
기준을 벗어나지 못할 때만 허용한다.

### 10.3 초기 재평가 후보

| 후보 | 초기 상태 | 재평가 질문 |
| --- | --- | --- |
| reference-scaffold-first | `adopt` as default hypothesis | 두 번째 실제 figure에서도 composition 품질을 유지하는가 |
| pure semantic-first composition | `retest` | 현재 constraint/model로 승인 가능한 scaffold를 생성할 수 있는가 |
| Matplotlib SVG fragments | `retest` | style adapter, panel geometry, version pinning으로 compact하고 결정론적인 fragment가 되는가 |
| RDKit scientific fragments | `adopt` with boundary | chemistry 의미를 보존하면서 전체 figure style에 통합되는가 |
| dual SVG/TikZ backend | `hold` | 실제 소비자가 두 backend를 요구하고 scene contract가 안정됐는가 |
| automated visual metrics | `adopt` as advisory only | 인간 판정을 대체하지 않고 회귀 탐지에 기여하는가 |

## 11. 수행 계획

항상 하나의 Slice만 `in progress`가 될 수 있다. 다음 Slice는 이전 Slice의 종료 조건과 기록된 decision gate를 통과해야 시작한다.

### Slice 0 — 기준선과 권위 정상화

목표: 재실험 가능한 녹색 기준선과 모순 없는 문서/상태 authority를 만든다.

Slice 0은 분기 오염을 막기 위해 세 작업 단위로 나눈다.

#### Slice 0A — Python 실험 기준선

1. Python Fig1 `render-parity` 7/8 실패를 재현하고 원인을 수정한다.
2. dependency와 renderer identity를 기록하고 clean replay를 검증한다.
3. Phase 3-B/3-C의 실제 git 상태와 문서 상태를 맞춘다.

최소 검증:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with rdkit \
  --with shapely --with svgelements --with svgpathtools \
  python plugins/figure-agent-py/scripts/pyfig.py verify-fig1
```

#### Slice 0B — Public main acceptance authority

1. 이 SSOT commit SHA를 task context에 고정한다.
2. `origin/main` 기준의 별도 clean worktree와 별도 `codex/` branch에서 수행한다.
3. accepted fixture인 `fig1_overview_v2_pair_001_vault`와
   `fig1_overview_v4_pair_001_vault`의 audit authority를 확인한다.
4. 모순된 `QUALITY_AUDIT.md`가 publication gate를 통과하는 regression을
   `tests/test_publication_gate.py`에 먼저 추가한다.
5. parser가 정확히 하나의 구조화된 값만 허용하거나, 파생 audit에서
   acceptance field를 제거한다.
6. `spec.yaml.accepted`와 파생 문서가 모순되면 fail-closed로 처리한다.
7. main 기반 수정 commit과 검증 결과를 Slice 0C에서 이 문서에 기록한다.

최소 검증은 `plugins/figure-agent`에서 실행한다.

```bash
uv run pytest tests/test_publication_gate.py tests/test_golden_artifact_checks.py -q
uv run ruff check scripts/publication_gate.py scripts/checks/check_golden_artifacts.py \
  tests/test_publication_gate.py tests/test_golden_artifact_checks.py
```

#### Slice 0C — 문서와 branch 경계

1. current branch와 public main의 역할을 명시하고 무검증 병합을 금지한다.
2. active README와 문서 pointer가 이 문서를 가리키게 한다.
3. Slice 0A와 0B 결과 commit을 이 문서의 결정 기록에 남긴다.
4. `git diff --check`와 링크 존재 검사를 수행한다.

종료 조건:

- Python Fig1 gate 8/8
- 같은 환경에서 두 번 생성한 Python SVG가 byte-for-byte 동일함
- Phase 3 문서가 active execution authority에서 제거됨
- 모순된 audit에 대한 regression test와 관련 acceptance targeted test가 통과함
- Slice 0A와 0B가 서로의 분기 이력을 혼합하지 않고 검증됨
- 변경 범위와 무관한 사용자 파일은 보존됨

#### Slice 0 결과 기록 — 2026-07-10

Slice 0은 두 격리 branch에서 수행했고, 이 문서 branch에는 결과와
권위 포인터만 기록한다. 두 branch의 이력을 검증 없이 merge하거나 rebase하지
않는다.

| 단위 | 기준 | 결과 commit | 검증 요약 |
| --- | --- | --- | --- |
| Slice 0A — Python 실험 기준선 | `4f50af8f0679f9997faed01b6581b6742f577fc3` | `388505f3ebbf414b03c7223345fb86672252b719` on `codex/slice0a-python-parity` | locked direct deps에서 `pyfig.py verify-fig1` 8/8, focused render-parity unittest 8 OK, tracked SVG hash 보존 |
| Slice 0B — Public main acceptance authority | `origin/main` `9d3db7347261229d6a0ce1c09b8893d49cf06e2f` | `6258ca07de2fbe7979ffee221a191d722f160dea` on `codex/slice0b-public-main-acceptance` | `tests/test_publication_gate.py` + `tests/test_golden_artifact_checks.py` 74 passed, scoped Ruff clean |

Slice 0A의 render identity는 다음 direct dependency contract로 고정됐다.

```text
drawsvg==2.4.1
matplotlib==3.10.9
numpy==2.5.1
rdkit==2026.3.3
shapely==2.1.2
svgelements==1.9.6
svgpathtools==1.7.2
```

동일 locked environment에서 `svg_text_for_scene(build_scene())`을 두 번
독립 실행한 결과는 모두 tracked SVG hash와 동일했다.

```text
03e51b775bb0dc063e131ecff6f684ab9cb6fd807546df01e01076e5e4d131e1
```

Slice 0B의 실제 accepted fixtures는 둘 다 `spec.yaml`에 `accepted: true`를
갖는다. 현재 checkout에서는 full artifact gate가 export 누락에서 먼저
실패한다. publication parser 자체는 `fig1_overview_v2_pair_001_vault`의
`QUALITY_AUDIT.md`에서 `contradictory_submission_safe`를 보고하며,
`fig1_overview_v4_pair_001_vault`는 기존처럼 `missing_submission_safe_true`와
`missing_disclosure_needed`를 보고한다. public human audit나
`spec.yaml.accepted`는 수정하지 않았다.

변경되지 않은 사용자 파일은 보존했다. 2026-07-10 현재 본 작업 branch에는
작업 전부터 존재한 untracked `.agents/`, 세 개의 2026-05-07 plan 파일,
`plugins/figure-agent/docs/STYLE_GUIDE.md`가 남아 있다.

Phase 3 문서는 active 실행 queue가 아니라 historical input으로 격하됐다.
체크박스 잔여 상태와 실제 commit/revert history의 세부 reconciliation은
Slice 1 legacy salvage audit에서 수행한다.

다음 진입 가능한 단위는 Slice 1이다. Slice 1은 구현이 아니라 legacy salvage
audit이며, 과거 실험을 `adopt/retest/hold/retire` 후보와 최소 재실험으로
정리한다.

### Slice 1 — Legacy Salvage Audit

진입 조건: Slice 0 종료.

목표: 과거 실험을 현재 역량으로 재평가할 우선순위 목록으로 변환한다.

작업:

1. Python semantic experiment의 design, probe, handback, Phase 3 commit/revert를 inventory한다.
2. 각 항목을 `adopt/retest/hold/retire`로 임시 분류한다.
3. `retest` 항목마다 하나의 독립 가설과 최소 실험을 정의한다.
4. 결과 판단에 필요한 before/after artifact와 human question을 정한다.

종료 조건:

- 모든 주요 legacy 항목에 근거 링크와 판정 상태가 있음
- `retire`에는 구조적 충돌 또는 통제된 재실험 근거가 있음
- 다음 Slice에서 실행할 재실험이 세 개 이하로 제한됨

### Slice 2 — 핵심 가설 재실험

진입 조건: Slice 1에서 우선순위 승인.

기본 재실험 후보:

1. Matplotlib scientific fragment의 deterministic/style-preserving 구현
2. 제한된 semantic-first scaffold candidate 생성
3. RDKit fragment와 전체 style의 통합

각 실험은 별도 branch 또는 격리된 fixture에서 수행한다. 한 실험의 verifier를 다른 실험의 성공을 위해 완화하지 않는다.

종료 조건:

- 각 가설에 baseline, 새 artifact, machine result, human verdict가 있음
- 성공한 부분은 재사용 경계가 설명됨
- 실패한 부분은 접근 한계와 구현 한계가 분리됨
- 모든 `retire` 판정이 사전 실패 기준과 bounded corrective iteration 기록을 가짐
- 두 번째 실제 figure에 사용할 조합이 선택됨

### Slice 3 — 두 번째 실제 Figure Vertical Slice

진입 조건: Slice 2 조합 선택.

목표: synthetic probe가 아닌 실제 figure에서 authoring boundary를 검증한다.

작업:

1. Fig1과 다른 composition/semantic pressure를 가진 실제 figure를 선택한다.
2. reference authority manifest를 작성한다.
3. 사람이 scaffold를 승인한다.
4. Fig1 전용 policy import 없이 scene과 renderer를 구성한다.
5. SVG/source, review artifact, provenance를 생성한다.
6. machine gate와 human review를 수행한다.

종료 조건:

- 동일 engine contract로 두 번째 figure가 생성됨
- 모든 object와 relation이 declared ID에 결합됨
- hard semantic/physics/scaffold gate 통과
- artifact가 clean environment에서 재현됨
- 인간이 composition-grade scaffold와 review artifact를 명시적으로 판정함
- Fig1 전용 special case가 reusable engine에 추가되지 않음

### Slice 4 — Quality Kernel 연동

진입 조건: Slice 3 성공.

목표: Authoring Layer 출력이 기존 kernel의 검증과 release 흐름을 통과하게 한다.

작업:

1. authoring output manifest를 kernel input contract에 매핑한다.
2. source, reference, scaffold, payload, export hash를 provenance chain으로 연결한다.
3. compile/export/status에서 SVG authoring source를 정식으로 구분한다.
4. acceptance authority와 review packet 경계를 검증한다.

종료 조건:

- TikZ fixture와 SVG authoring fixture가 같은 kernel 원칙 아래 검증됨
- authoring tool이 acceptance를 설정할 수 없음
- kernel status가 machine/human/release 상태를 혼합하지 않음
- release artifact에서 provenance를 역추적할 수 있음

### Slice 5 — 일반화와 제품 승격 판단

진입 조건: Slice 4 성공.

판정 질문:

- 두 figure family에서 반복 가능한가
- 새 figure 추가 시 scaffold와 payload만 주로 바뀌는가
- engine 변경이 Fig-specific 예외보다 적은가
- 사용자 수정 비용이 기존 직접 저작보다 실제로 낮은가
- kernel 연동이 저작 backend에 종속되지 않는가
- dual backend 또는 자동 composition의 실제 수요가 증명됐는가

가능한 결정:

- Authoring Layer를 정식 제품 계층으로 승격
- 제한된 figure family용 도구로 유지
- 성공한 primitive와 verifier만 kernel에 흡수
- 추가 실제 figure가 필요하므로 실험 연장

## 12. 중지와 확장 조건

다음 상황에서는 자동으로 범위를 확장하지 않는다.

- dependency 추가가 필요한 경우
- public API 또는 fixture schema를 깨야 하는 경우
- current branch와 main의 대규모 병합이 필요한 경우
- 인간 reference authority 또는 acceptance가 필요한 경우
- 실제 figure/data의 사용 권한이 불명확한 경우
- verifier를 약화해야만 artifact가 통과하는 경우

같은 실패가 반복되면 증거를 보존하고 접근을 바꾼다. 통과를 위해 데이터를 조작하거나 baseline을 이유 없이 갱신하지 않는다.

## 13. 보안과 입력 안전

- TikZ, SVG, PDF, PPT 등 외부 입력은 신뢰하지 않는다.
- TeX command execution, 외부 resource URL, SVG script/event handler, path traversal을 명시적으로 제한한다.
- render process에는 시간, 메모리, 출력 크기 제한을 둔다.
- provenance에는 입력 hash와 toolchain version을 기록하되 secret, token, private URL을 포함하지 않는다.
- 새로운 ingest surface는 threat model과 negative fixture 없이 정식화하지 않는다.

## 14. 문서 운영 규칙

- 현재 Slice는 바로 실행 가능한 수준으로 유지하고, 후속 Slice는 진입·종료 경계 중심으로 유지한다.
- 실험별 긴 로그와 이미지 비교는 별도 handback에 둘 수 있지만 이 문서의 결정을 링크하고 결과만 기록한다.
- 완료된 Slice는 결과 commit, verification command, artifact 경로, 남은 위험을 이 문서에 요약한다.
- 미결정 사항은 빈칸이나 임시 표기로 두지 않는다. 기본값과 재개 조건을 함께 기록한다.
- 이전 문서를 삭제하지 않는다. 잘못된 사실이 아니라면 역사적 provenance로 보존한다.

## 15. 현재 결정 기록

### 2026-07-10 — 통합 SSOT 채택

- Figure Agent를 quality kernel과 authoring layer의 통합 제품으로 정의한다.
- 이 문서를 제품 스펙과 수행 계획의 단일 권위로 사용한다.
- 과거 revert와 약한 artifact를 영구 실패 판정으로 사용하지 않는다.
- 현재 기본 architecture 가설은 reference-scaffold-first다.
- 다음 수행 단위는 Slice 0이며, 전체 authoring system 구현은 허용되지 않는다.
- Python authoring layer의 제품 승격은 두 번째 실제 figure와 kernel 연동 증거 이후에만 결정한다.
