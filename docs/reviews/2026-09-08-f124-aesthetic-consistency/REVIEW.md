# F1·F2·F4 스키메틱 미감·표기 일관성 검수

검수일: 2026-09-08. 범위: 등록된 F1 전체, F2(a) 도식 및 F2 조립 PDF에서의 배치, F4 rev12 독립 도식과 해당 캡션. 소스·정본·승인 상태는 변경하지 않았다.

**판정: 기본 완성도는 높지만, 세 그림을 한 논문의 최종 세트로 승인하기에는 표기와 의미의 교차 불일치가 남아 있다. 전면 재작도보다 좁은 범위의 타이포그래피·용어·기호 수정이 적합하다.**

## 대상과 검수 방식

정본 권위는 `/Volumes/LabShare/ResearchOS-data/02_Surfur_Polymer/docs/figure_set/FIGURE_REGISTRY.yaml`이다. Drive의 F1 CURRENT와 schematic_registry 일부는 더 오래된 파일을 가리킨다. 아래 NAS PDF를 직접 읽었으며, F1/F2 조립/F4 PDF 해시가 등록 해시와 일치한다. F2(a) 독립 PDF는 등록 빌더가 사용하는 assets 폴더의 자산이다.

| 대상 | PDF, figure_set 기준 경로 | SHA-256 앞 12자리 |
|---|---|---|
| F1 | fig1/F01__registered_overview_M1_260907/fig1_overview_M1.pdf | 1e7d70596689 |
| F2a | fig2/assets/fig2a_mechanism_260807.pdf | f64afd80fb3c |
| F2 조립 | fig2/results/figures/fig2_charge_transport/fig2_charge_transport_4panel_260729.pdf | 98ef28606325 |
| F4 | fig4/schematic_260906/fig4a_ispd_schematic_260906m.pdf | 035ca760f6dc |

PDF 내부 글꼴·문자 span·크기·색·벡터 선폭·이미지 객체를 추출했다. 전체 4종, 세 도식의 세부 진단 확대 12종과 흑백 3종을 실제로 열어 비교했다. 이 확대는 이번 PDF에서 직접 만든 진단용 뷰이며 기존 Figure Agent의 정식 crop receipt를 대체하지 않는다. 180 mm 배치의 2페이지 벡터 비교 PDF도 생성하고 두 페이지 렌더를 확인했다. 종이에 출력한 물리 교정은 수행하지 않았다. 비교 PDF를 출력할 경우 Actual size/100%를 선택하고 50 mm 자를 확인해야 한다.

## 글꼴과 크기

| 항목 | F1 | F2a | F4 |
|---|---:|---:|---:|
| 자연 크기 mm | 180.00 × 162.40 | 180.02 × 51.00 | 180.00 × 47.58 |
| 패널 문자 | 7.97 bold | 조립본이 8.00 bold로 부여 | 7.97 bold |
| 제목/소제목 | 6.97 regular | 6.46 bold | 6.97 regular |
| 주요 라벨 | 6.48 | 5.97 | 6.18 |
| 보조 문구 | 5.78 | 5.53 | 5.58–5.78 |
| 최소 문자 | 5.03 | **4.18** | 5.48 |

모든 독립 도식의 실제 텍스트는 Arial 계열이며 PDF에 임베드되어 있다. Helvetica/Computer Modern/Times 혼입은 발견하지 않았다. F1의 비례 기호 ∝ 한 개는 ArialUnicodeMS이다. ArialMT와 동일한 파일은 아니지만 Arial 계열의 기호 보완이며 눈에 띄는 서체 이탈로 보이지 않는다.

F2a의 `E_app`와 `J_mob` 아래첨자 app/mob가 각각 4.177 pt이다. 소스에 적힌 5.0 pt 이상 선언만 세면 놓치는 값이다. `textsubscript`의 추가 축소와 resizebox 결과를 PDF span에서 측정한 것이다. F2 조립본은 이 도식을 폭 179.959 mm, 약 600 dpi 이미지로 넣으므로 조립 후에도 사실상 같은 크기다.

공식 Nature Communications 배포 가이드는 같은 Arial/Helvetica 계열과 최종 크기에서 약 5–8 pt를 권장한다. 5 pt를 모든 아래첨자에 대한 절대 불합격 규정으로 해석하지는 않되, 이 세트는 F1/F4가 이미 작은 기호를 5 pt 이상 확보했으므로 F2도 약 5.0–5.2 pt로 맞추는 것이 합리적이다. 나머지 본문 6.0–6.5 pt 차이는 위계 안의 차이이며 글자 크기를 무조건 하나로 만들 필요는 없다.

출처: https://www.nature.com/documents/ncomms-submission-guide.pdf (접근일 2026-09-08, 문서 표기 개정일 2019-05-03). 측정 원자료: `font_spans.csv`, `measurements.json`, `*_pdffonts.txt`.

## 우선 수정·조정 항목

### P1-01 — F4 캡션의 ISPD 풀네임 오류

F1 caption은 **Isothermal surface-potential decay**, F4 caption 첫 문장은 **Inductive surface-potential decay**이다. ISPD의 명칭과 전위 센서의 유도형 측정 원리를 혼동했다. F4를 **Isothermal surface-potential decay (ISPD)**로 정정하고, 센서 원리를 설명할 때만 inductive/non-contact electrostatic voltmeter를 사용한다.

근거: F1 `caption.md`, F4 `fig4a_caption.md:3`. 원문 연구 논문도 Isothermal Surface Potential Decay를 사용한다: https://pmc.ncbi.nlm.nih.gov/articles/PMC6410272/ (section 3.4). 검수는 명칭 확인에만 이 논문을 사용하며, 그 실험 장치나 모델을 본 논문의 장치로 가져오지 않았다.

### P1-02 — 충전·이송·접지 서사가 두 그림에서 다름

F1(e)는 needle–counter-electrode의 두 단자 충전 후 **manual transfer**하고, 측정 위치에서만 후면의 earth ground를 표시한다. F1 caption도 이를 명시한다. F4는 충전 때부터 모든 단계에 ground가 있고, caption은 시편을 **left undisturbed**, 후면을 **ground throughout**라고 한다.

이는 단순 2D/3D 스타일 차이가 아니다. 동일 프로토콜이면 어느 실제 충전·이송·측정 절차가 맞는지 실험 Methods와 연결하여 한 가지로 맞춰야 한다. 다른 실험 프로토콜이면 각 그림이 어느 프로토콜을 설명하는지 명시해야 한다. 최신 F1 정본에 더 구체적인 회로 계약이 있지만, 그것만으로 F4 데이터의 실제 하드웨어를 추정하지 않았다.

F4의 `isolate`도 주의할 표현이다. 그림은 시편을 전기적으로 고립시키지 않고 코로나 소스를 제거한다. 해당 단계가 뜻하는 행동에 맞춰 `remove source` 또는 `source removal`을 권한다. 원래의 다섯 단계와 순서는 유지할 수 있다.

### P1-03 — F4의 음전하 표기와 감쇠 축의 부호 해석

F4(a–d)는 마이너스 전하 마커이고 caption도 negative corona라고 한다. 그런데 (e)는 가로축 위에서 아래로 감소하는 곡선에 `V_s`만 붙는다. 전위의 크기를 뜻한다면 그래프 축을 `|V_s|`로 표시해야 한다. 부호 있는 전위라면 실제 음전위가 기준값으로 접근하는 방향을 반영해야 한다. 축에 수치가 없으므로 확정적인 수치 오류라기보다 **signed potential과 magnitude의 구분 누락**으로 판정한다. 센서가 측정하는 물리량 자체의 표기 `V_s`까지 모두 절댓값으로 바꿀 필요는 없다.

### P1-04 — F2a의 4.18 pt 아래첨자

위 측정 표 참조. `E_app`와 `J_mob`의 의미 구분을 지는 문자이므로 명시 크기로 올리고 실제 조립본에서 다시 읽어야 한다. 전체 도식을 늘리는 대신 두 아래첨자의 크기·기준선을 조정한다.

### P2-01 — shallow/deep 기호가 현행 F1과 F4에서 불일치

F1(c)는 **파랑 원 = shallow, 빨강 사각 = deep**이며 에너지 상태 도식도 같은 기호를 쓴다. F4(c)는 **파랑/빨강 원**, 빈 site는 열린 원이다. 흑백에서는 F1은 기호만으로 추적되지만 F4의 채워진 두 범주는 안정적으로 구분되지 않는다.

이전 F4 critique의 “F1과 같은 원형을 유지한다”는 근거는 지금 선택된 M1과 맞지 않는다. 과거의 원형 선호를 지우거나 자동으로 선택을 뒤집지는 않되, 현재 세트 기준의 미결로 다시 기록해야 한다. 권장안은 F4의 깊은 점유 site만 사각으로 맞추고 내부 마이너스와 빈 site의 열린 원은 유지하는 것이다. 도형 넓이·크기를 맞춰 트랩 양 차이로 읽히지 않도록 한다.

### P2-02 — F2a에 제작자의 설명이 노출됨

`field held on throughout; growing occupancy weakens the mobile-current cue`는 물리량을 설명하기보다 “전류를 나타내는 그림 기호를 약하게 그렸다”는 제작 메모다. 세 그림 중 가장 명백하게 자동 작성 문구처럼 느껴지는 지점이다.

도면에는 **`under constant applied field`**처럼 조건만 남기고, 점유율 증가와 전류 기여의 관계는 근거 수준을 보존한 working-model caption으로 옮기는 것을 권한다. 이를 단정적인 “trapping suppresses leakage”로 치환하면 과학적 주장이 강해지므로 피해야 한다. `qualitative output`은 **`schematic current response`**로, `early fit`은 **`early-time extrapolation`**로 다듬으면 실제 측정 fit으로 읽힐 여지도 줄어든다.

### P2-03 — 색의 역할이 바뀜

F1(c)/F4(c)의 파랑·빨강은 깊이 범주인데, F2는 파랑을 유전 분극과 인가장에, 붉은색 계열을 모든 점유 트랩과 전류 곡선에 쓴다. F1(e/f)의 빨강은 깊이와 관계없는 전하·응답이기도 하며 이 예외는 F1 caption에 이미 적혀 있다.

같은 RGB를 강제로 적용하는 것이 해결책은 아니다. **에너지 깊이는 blue/red로, 깊이 미지정 점유·장치·전류 표시는 중립색으로** 정리하는 것이 가장 명확하다. F2의 점유 여부는 이미 막대+점의 형태로 구분되므로 형태를 보존하면서 색 역할을 정리할 수 있다. 정량 패널의 조성 색은 별도 의미 축이므로 일괄 변경 대상이 아니다.

### P2-04 — 제목과 설명문 어조의 세트 차이

F1 제목은 첫 글자 대문자의 7 pt regular, F2의 상단 물체 이름은 소문자 6.46 pt bold, F4는 소문자 동사의 7 pt regular이다. F2의 물체 이름은 하위 범주 제목이므로 다른 역할임을 인정할 수 있지만, 세트 전용 타입 규칙에는 분리해서 기록할 필요가 있다.

권장 공통 규칙: 패널 문자 8 pt bold, 패널 제목 7 pt regular, 물체·범주 이름 6–6.5 pt(필요할 때만 bold), 주요 라벨 6–6.5 pt, 보조 문구 5.5–5.8 pt, 작은 기호 약 5 pt 이상. 문장 첫 글자 대소문자를 한 가지로 정하되 동사형 방법 순서와 명사형 overview 제목까지 억지로 똑같게 만들지는 않는다.

F4 하단은 `charge lands on the surface`, `charge is held at sites`, `V_s is read without contact`처럼 쉬운 수업 문장이다. 의미는 이해되지만 F1/F2보다 구어적이다. 각각 `surface charging`, `charge retention at localized sites`, `non-contact surface-potential measurement`처럼 간결한 기술 명사구로 다듬을 수 있다. 위치가 좁으면 더 짧게 줄이고 폰트를 축소하지 않는다. `section`은 `cross-section`이 더 분명하다. `no single decay rate`는 데이터 결과로 보이지 않게 schematic qualification을 유지한다.

### P2-05 — F4 캡션의 모델 확실성이 F1보다 강함

F1(e)는 model-dependent interpretation과 conceptual distribution을 직접 표시한다. F4 caption은 전위 감소가 site escape로 일어나고 inset의 분포가 이 곡선을 produces한다고 먼저 단정한 뒤 schematic이라는 제한을 뒤에서 붙인다. 도식임은 적혀 있으나 인과 모델의 확실성까지 자동으로 낮춰지는 것은 아니다.

권장: `In the schematic trapping model, ...` 또는 그에 상응하는 명시적인 모델 한정을 해당 인과 설명 앞에 둔다. F1의 두 로브와 F4의 연속 분포는 모두 비정량 개념 표현으로 선언되어 있어 그 자체를 오류로 판단하지 않는다. 동일한 측정 DOS인 것처럼 보이지 않도록 범례·캡션의 한정을 유지한다.

## 미감·손맛: 유지할 부분과 선택적 조정

- **F1:** 화학식의 결합선이 가늘고 이중결합이 분리되어 보인다. 동일 길이의 화학 결합은 정확성에 기여하므로 손맛을 이유로 흔들지 않는다. (c)의 서로 다른 방향과 곡률의 사슬, (f)의 일관된 폭을 가진 굽은 필름, 얇은 구분선과 넓은 여백은 잘 살아 있다. 가장 밀도가 높은 (d–f)도 현재 전체 렌더에서는 중대한 문자 겹침이 보이지 않는다.
- **F2:** 네 개의 반복 MIM 사각형은 시편·장치 불변성과 상태 변화의 비교를 위한 것이어서 “AI스럽다”는 결함으로 판정하지 않는다. 다만 굵은 상단 제목, 정렬된 막대 기호와 제작 메모가 함께 있어 F1보다 매뉴얼 도식의 느낌이 강하다. 우선 문구와 제목 위계부터 고치는 것이 적합하다. 임의의 jitter, 텍스처, 굽은 전극을 넣으면 비교 의미가 손상된다.
- **F4:** 시편의 3D 장치와 (c)의 단면, (e)의 평면 그래프를 섞은 것은 목적이 분명하다. 센서 스탠드오프·감지 면적·전하 마커가 작은 크기에서도 읽힌다. 상면·측면의 색 차이는 입체감을 위한 적절한 톤이다. F1/F2의 얕은 베이지에 비해 F4는 노란색이 더 강하지만, 층을 구분하는 기능이 있어 전면 중립화는 권하지 않는다.
- **선택적 미감 조정:** F4(c)의 거의 가로로 흐르는 부드러운 파형들은 F1(c)의 얽힌 사슬과 다른 추상화로 보인다. 명확한 결함으로 단정하지 않지만, 통일 패치 단계에서 필요하다면 방향·span이 다른 소수의 경로로 조정하고 호스트에 붙은 site 의미를 보존한다. 막연히 “손맛을 넣기” 위한 경로 증식은 권하지 않는다.
- **선폭:** 소스 선언보다 PDF의 실제 획을 비교했다. F1의 구조선 약 0.42–0.58 pt와 응답선 약 0.90 pt, F2 약 0.60 pt 구조선과 1.04 pt 응답선, F4 약 0.45 pt 구조선과 0.95 pt 응답선은 대체로 같은 위계다. 화살촉·보조선에는 더 작은 값도 있다. 1 pt 하한을 일괄 적용하면 화학식과 장치가 둔해지므로 권하지 않는다.

## 출판 산출물과 이전 QA의 한계

F1/F2a/F4 독립 PDF는 벡터이며 임베드 텍스트를 추출할 수 있다. 그러나 **F2 최종 조립 PDF의 panel a는 4251×1205 px, 약 600 dpi의 래스터 이미지**다. 해상도 부족이라고 할 수는 없지만, 조립본 안에서 도식 문자·선이 편집 가능한 벡터로 유지되는 것은 아니다. 빌더의 `imshow()`가 원인이다. 도식 수정을 끝낸 뒤 PDF를 벡터로 합성하는 출판 마감 작업을 권한다. 근거: `build_fig2_4panel.py:261`, PDF image object 13.

F4 기존 closeout의 workflow_ready=true는 독립 그림 검증의 상태이며 세 그림 간 일관성의 증거가 아니다. 이번에는 현재 F1의 사각형 변경, 서로 다른 ISPD 풀네임, 충전 프로토콜 서술을 함께 보면서 새 문제를 발견했다. 과거 same-circle rationale을 현재 승인 근거로 반복해서는 안 된다.

이번 read-only status 확인에서 F4 미러는 render/critique FRESH 및 workflow_ready=true였다. F1의 이전 M1_compliance 검증 workspace는 render STALE, critique FRESH, workflow_ready=false로 보고됐다. 원인 문구는 build PDF가 source set보다 오래되었다는 것이며, 이번에는 해당 과거 review workspace를 재컴파일하지 않았다. 이 상태와 별개로 검수한 등록 정본 PDF는 registry 해시와 일치하며, 여기서 그 PDF를 직접 새로 래스터화했다. 따라서 이번 보고서를 F1의 현재 Figure Agent 전체 gate 통과 주장으로 사용해서는 안 된다. `f1_status.json`에 원문 상태를 보존했다.

## 패치 순서와 완료 조건

1. ISPD 풀네임, F2의 제작 메모, 읽기 어려운 아래첨자를 좁은 범위로 수정한다.
2. F1/F4가 동일 실험을 설명하는지 실제 Methods·장치 기록과 대조하고 충전/이송/접지·전위 부호를 확정한다.
3. 그 결정 안에서 trap marker와 색 역할, 제목·설명문 위계를 맞춘다.
4. 단품 재컴파일 후 현재 PDF의 폰트 span과 컬러·흑백 배치를 재검수한다. F2 조립본의 실제 panel-a 자산도 확인한다.
5. 수정본이 선택되면 정본 source/output/caption/registry/deck와 Cowork 소비자를 같은 해시로 동기화한다. F4 전체의 정량 자료 승인과 패널 문자 조립 문제는 별도의 gate로 남긴다.

이번 결과는 report-only cross-figure review다. 새 논문 제출 승인, 소스 패치, 기존 critique의 덮어쓰기, 데이터 검증 완료는 주장하지 않는다.
