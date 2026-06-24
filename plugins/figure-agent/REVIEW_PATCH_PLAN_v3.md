# figure-agent P0–P3 review patch plan v3

2026-06-22 review에서 발견된 항목. 각 항목은 fix + PLAN 갱신 + test가 한 commit.
완료 시 `[ ]` → `[x] (commit <sha7>)`.

---

## P0 — correctness (메타데이터 무결성)

### [x] (commit 20569f7) P0.1 MCP facade SERVER_VERSION이 plugin 버전과 불일치

**evidence**: `mcp/figure_agent_server.py:31` — `SERVER_VERSION = "0.1.0"`인 반면 plugin은 v0.9.3
(`.claude-plugin/plugin.json:4`, `pyproject.toml:3`, `README.md`, `CHANGELOG.md` 모두 0.9.3).

**영향**: 낮음. MCP 클라이언트가 serverInfo.version으로 version negotiation을 하지 않으므로
동작에는 영향 없음. 그러나 향후 MCP 표준이 version 검사를 도입할 경우 혼란 발생 가능.

**fix**: `SERVER_VERSION`을 `pyproject.toml`의 version과 동기화.
MCP facade는 plugin의 한 component이므로 major/minor는 plugin과 동일하게 유지.
단, MCP facade 자체의 bugfix만 있을 경우 patch만 올리는 전략도 가능.
→ 가장 단순한 fix: `SERVER_VERSION = "0.9.3"`으로 변경.

**test**: `tests/test_mcp_facade.py`에 server version assertion 추가.
```python
def test_mcp_server_version_matches_plugin():
    import figure_agent_server
    import tomllib  # Python 3.11+
    import os
    from pathlib import Path
    plugin_root = Path(figure_agent_server.__file__).resolve().parents[1]
    pyproject = tomllib.loads((plugin_root / "pyproject.toml").read_text())
    expected = pyproject["project"]["version"]
    assert figure_agent_server.SERVER_VERSION == expected
```

**참고**: 이 테스트는 `figure_agent_server.SERVER_VERSION`에 접근. P2.2 (MCP 분할) 이후에도
`figure_agent_server`가 `SERVER_VERSION`을 re-export해야 함.

**commit convention**: `fix(mcp): sync SERVER_VERSION with pyproject v0.9.3`

---

## P1 — gate 경고 (게이트 오작동 가능성)

### [x] (commit 20569f7) P1.1 dist/ build artifacts untracked, .gitignore 누락

**evidence**: `git status`에 `?? dist/`와 `?? plugins/figure-agent/dist/` 표시됨.
두 dist/ 디렉토리 모두 `cowork/` ZIP bundle이 들어 있음.
루트 `.gitignore`에 `dist/` 패턴 없음. `plugins/figure-agent/.gitignore`는 존재하지 않음.

**영향**: 낮음. `dist/`는 빌드 산출물이므로 실수로 `git add .` 할 경우 불필요한 파일이 stage됨.

**fix**: 루트 `.gitignore`에 `dist/` 패턴 추가.
(참고: `plugins/figure-agent/.gitignore`는 존재하지 않으므로 루트 `.gitignore`만 수정)

**test**:
```bash
# 수동 확인 — dist/ 디렉토리가 git status에 나타나지 않는지
git status --short | grep dist/ | wc -l  # → 0
```

**commit convention**: `chore(gitignore): add dist/ to prevent accidental staging`

---

## P2 — 데이터 모델 / 구조

### [x] (commit 2c7e351) P2.1 scripts/ 디렉토리 flat 구조 → 패키지 계층화

**evidence**:
- `scripts/` 아래 138개 `.py` 파일이 단일 디렉토리에 flat하게 위치.
- 17개 파일이 `sys.path.insert(0, ...)`로 `scripts/`를 path에 직접 추가하여 import 해결.
- 32개 파일이 동일 디렉토리 내 다른 모듈을 `import` (절대 import, no package prefix).
- `__init__.py` 없음 — Python 3.3+ namespace package으로 동작하지만 구조적 계층 없음.
- 도메인별 그룹이 명확히 존재: `check_*` (9개), `candidate_*` (11개), `quality_*` (9개),
  `fig_loop_*` (15개), `fig_driver_*` (5개 helper; `fig_driver.py`는 root 유지), `svg_polish_*` (6개).

**fix**: `__init__.py` 추가 + 서브디렉토리 생성 + import 문 일괄 변경. **단, 이 리팩터는
behavior change가 전혀 없어야 하며 하나의 커밋으로 끝나야 함.**

변경 계획:
```
scripts/
  __init__.py
  checks/           ← check_*.py (9개) + __init__.py
  candidates/       ← candidate_*.py (11개) + __init__.py
  quality/          ← quality_*.py (9개) + __init__.py
  loop/             ← fig_loop_*.py (15개) + __init__.py
  driver/           ← fig_driver_*.py (5개 helper; fig_driver.py는 root에 유지) + __init__.py
  svg_polish/       ← svg_polish_*.py (6개) + __init__.py
  tests/            ← test_*.py는 이동하지 않음 (tests/ 아래에 그대로)
  (나머지 ~82개 핵심 스크립트는 scripts/에 유지 — runtime_paths, status, compile, export 등)
```

**임계 조건**: 리팩터 후 `import` 경로 변경으로 인한 `ModuleNotFoundError`가 전혀 없어야 함.

**fix 상세**:
1. `scripts/__init__.py` 생성 (optional - namespace package이어도 됨).
2. 각 서브디렉토리에 `__init__.py` 생성.
3. 이동할 파일들을 각 서브디렉토리로 `git mv`.
4. 해당 파일들의 `sys.path.insert(0, ...)` 제거 — 단, `if __name__ == '__main__'` 블록이 있는
   파일(~10개)은 직접 실행 시 필요하므로 유지 (idempotent하므로 유지해도 무해).
5. 다른 파일들의 import 문 업데이트: `import check_collisions` → `from scripts.checks import check_collisions` 또는
   `from scripts.checks.check_collisions import ...`.
   단, `bin/fig-agent`와 `mcp/figure_agent_server.py`는 `sys.path.insert(0, str(SCRIPTS_DIR))`를
   사용하므로 이쪽 경로도 업데이트.

**실행 전 MUST DO**:
- `bin/fig-agent`가 `sys.path.insert(0, str(SCRIPTS_DIR))`로 scripts/를 path에 추가.
- `mcp/figure_agent_server.py`도 `sys.path.insert(0, str(SCRIPTS_DIR))`로 scripts/를 path에 추가.
- 두 entry point에서 서브디렉토리 import가 동작하려면 `from scripts.checks import check_collisions` 형태로
  변경하거나, 서브디렉토리를 별도로 path에 추가해야 함.
- **권장 전략**: 기존 import 패턴 유지 — `import check_collisions`가 동작하려면 각 서브디렉토리가
  path에 직접 노출되어야 함. 대신 entry point 두 곳에서 각 서브디렉토리를 `sys.path`에 추가:
```python
SCRIPTS_DIR = CODE_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
EXCLUDED_SUBDIRS = {"__pycache__", "examples"}
for subdir in SCRIPTS_DIR.iterdir():
    if subdir.is_dir() and not subdir.name.startswith("_") and subdir.name not in EXCLUDED_SUBDIRS:
        sys.path.insert(0, str(subdir))
```
→ `examples/`와 `__pycache__`는 sys.path에서 제외. `iterdir()` 순서는 filesystem-dependent이므로
   같은 이름의 파일이 서로 다른 서브디렉토리에 있지 않도록 주의.
→ 이렇게 하면 모든 기존 import 문을 변경할 필요 없음.

**sys.path.insert 제거 주의사항**:
- scripts/ 내부에서 `sys.path.insert`를 사용하는 17개 파일 중
  **16개** 파일에 `if __name__ == '__main__'` 블록이 있어 직접 실행(`python scripts/foo.py`) 가능.
- 직접 실행 시 entry point의 sys.path 설정이 적용되지 않으므로 이 `sys.path.insert` 유지 필요.
- **권장**: entry point를 통해서만 실행되는 파일에서만 제거하고, 직접 실행 가능한 파일은 유지.
- **참고**: 17개 중 오직 **2개 파일만** (`check_golden_artifacts.py`, `check_layout_drift.py`)이
  서브디렉토리로 이동하는 그룹에 속함. 나머지 15개는 `scripts/` root에 유지되므로
  `sys.path.insert` 경로가 stale될 위험이 낮음. 단, 이동된 2개 파일의
  `os.path.dirname(__file__)` 기반 `sys.path.insert`는 이동 후 경로가 변경되므로
  `scripts/` 절대 경로로 업데이트 필요.

**test**: `uv run pytest -q -m "not render"` → 기존 테스트와 동일한 pass count 유지.
`bin/fig-agent`를 실제로 호출하는 테스트가 있다면 통과 확인.

**실행 순서**: P2.2 (MCP 분할) 이후에 실행. P2.2가 `mcp/figure_agent_server.py`를 재구성하므로
P2.2 완료 후 P2.1의 sys.path 변경사항을 새로운 구조에 적용.

### [x] (commit 32e3822) P2.2 MCP facade 단일 파일 분할

**evidence**: `mcp/figure_agent_server.py` 2,133줄:
- 27개 tool handler (`_status`, `_compile`, `_export`, `_render_candidates`, 등)
- 공통 인프라 (`_tool_envelope`, `_error`, `_fixture_lock`, `_run_fig_agent`, 등)
- 리소스 메타데이터 (`_resource_metadata`, `_resource_specs`)
- JSON-RPC 프로토콜 핸들링 (`_call_tool`, `_list_tools`, `initialize` 등)
- TOOLS dict (line 1582-1965, 28개 등록)

**fix**: 모듈 분할. 단, MCP 서버가 **zero runtime dependency** 정책을 유지해야 하므로
표준 라이브러리만 사용. (현재 doctor 함수들에서 PILLOW/yaml을 `__import__`로 동적 로드하는
패턴은 유지 — zero-dependency는 pip 설치 가능한 패키지에 한함; first-party인 `scripts/`
모듈 import는 제약 없음.)

변경 계획:
```
mcp/
  __init__.py
  figure_agent_server.py     ← JSON-RPC loop + entry point (약 200줄로 축소)
  _protocol.py               ← JSON-RPC envelope, tool result, error helpers (기존 ~100줄)
  _runtime.py                ← _plugin_root, _workspace_root, _fixture_lock, _run_fig_agent (~200줄)
  _validation.py             ← _is_safe_fixture_name, _is_safe_panel_id, _validated_workspace_and_name (~100줄)
  _resources.py              ← _resource_specs, _resource_metadata, _status_artifacts (~200줄)
  _handlers_status.py        ← _status, _next, _quality_map, _context_pack, _memory_summary
  _handlers_compile.py       ← _compile, _export, _loop_checkpoint
  _handlers_candidates.py    ← _analyze_figure, _propose_improvements, _analyze_panel,
                               _propose_panel_improvements, _compare_candidate,
                               _render_candidates, _rank_candidates,
                               _candidate_apply_readiness, _apply_candidate, _prepare_human_review
  _handlers_benchmark.py     ← _benchmark_list, _benchmark_run_preview, _benchmark_compare,
                               _benchmark_detectors_preview, _quality_next_experiment
  _handlers_misc.py          ← _doctor, _propose_patch, _evidence_sync_preview,
                               _closeout_ready, _verify_plan
```

**TOOLS 등록 결정** (MAY DO 아님 — 반드시 결정):
- **옵션 A (권장)**: `figure_agent_server.py`가 모든 TOOLS dict를 유지. 각 handler는
  `_handlers_*.py`에 정의되고 `figure_agent_server.py`에서 import + TOOLS에 등록.
  → `figure_agent_server.py`가 ~350줄 (200줄 entry + 150줄 TOOLS dict)로 늘어나지만
     테스트 변경 불필요.
- **옵션 B**: 각 `_handlers_*.py`에서 자체 등록. 패턴은 registry decorator 또는
  import-time 수집 필요. → `figure_agent_server.py`는 200줄 유지되나
  `_handlers_*.py` import 시 side effect 발생.
  `tests/test_mcp_facade.py`의 `TOOLS` 접근 경로 변경 필요.

**테스트 호환성**:
`tests/test_mcp_facade.py` (1,482줄, 43개 테스트)가 다음에 접근:
- `figure_agent_server.SERVER_VERSION`
- `figure_agent_server.PROTOCOL_VERSION`
- `figure_agent_server.TOOLS`
- `figure_agent_server._apply_candidate(...)` (private 함수!)
- `figure_agent_server._next(...)` 등

위 심볼들은 옵션 A/B 모두에서 `figure_agent_server`로 re-export되어야 함.

**실행 순서**: **P2.2를 먼저 실행**. 그 후 P2.1 (scripts 패키지화)에서 변경된
sys.path 설정을 새 `figure_agent_server.py` 구조에 적용.

**참고 — P2.2↔P2.1 의존성 완화**: `figure_agent_server.py`는 tool handler에서 scripts/ 모듈을
Python import가 아닌 **subprocess**로 호출 (`sys.executable, str(SCRIPTS_DIR / script_name)`).
`sys.path`는 `import runtime_paths` 하나만을 위해 사용됨. 따라서:
- P2.2의 `_runtime.py`에서 `import runtime_paths`만 유지되면 `sys.path` 설정은 single-point 변경
- P2.1의 서브디렉토리 sys.path 추가 전략이 `_runtime.py`에서만 동작하면 충분
- 즉, P2.2→P2.1 순서는 권장사항이지만 **강제 의존성은 아님**

**test**: `tests/test_mcp_facade.py` 1,482줄이 MCP 서버의 전체 표면을 테스트하므로, 리팩터 후
기존 테스트가 모두 통과해야 함. 추가로 각 `_handlers_*.py` 모듈이 독립적으로 import 가능한지 확인.

### [x] (commits 515096b, 279902d, 921bfa7, f1c9f14, e11e1b0) P2.3 Untracked real fixtures 정리

**evidence**: 4개 실제 피겨(fig2–fig5)가 `git status`에 `??`로 표시됨.
모두 `.tex`와 빌드된 `.pdf`를 갖추고 있음:
- `fig2_trap_design_space/` — briefing, tex, caption.md, design.md, build/pdf, reference/, previews/, exports/
- `fig3_floating_clip_protocol/` — briefing, tex, caption.md, build/pdf, reference/, previews/, exports/
- `fig4_trap_energy_diagram/` — briefing, tex, caption.md, design.md, build/pdf, reference/, previews/, exports/
- `fig5_actuation_mechanism/` — briefing, tex, build/pdf, reference/, previews/, exports/

단, `**/build/*`, `**/exports/*`, `**/previews/*`가 `.gitignore`이므로 build/exports/previews
내용물은 추적되지 않음 (의도적). `.tex`, `briefing.md`, `spec.yaml` 등 source 파일만 추적됨.

**fix**: `git add`로 source 파일만 staging. **fixture별로 파일 구성이 다르므로 개별 명시**:

```bash
# fig2: briefing + tex + spec + caption + design
git add plugins/figure-agent/examples/fig2_trap_design_space/briefing.md
git add plugins/figure-agent/examples/fig2_trap_design_space/fig2_trap_design_space.tex
git add plugins/figure-agent/examples/fig2_trap_design_space/spec.yaml
git add plugins/figure-agent/examples/fig2_trap_design_space/caption.md
git add plugins/figure-agent/examples/fig2_trap_design_space/design.md

# fig3: briefing + tex + spec + caption (design.md 없음)
git add plugins/figure-agent/examples/fig3_floating_clip_protocol/briefing.md
git add plugins/figure-agent/examples/fig3_floating_clip_protocol/fig3_floating_clip_protocol.tex
git add plugins/figure-agent/examples/fig3_floating_clip_protocol/spec.yaml
git add plugins/figure-agent/examples/fig3_floating_clip_protocol/caption.md

# fig4: briefing + tex + spec + caption + design
git add plugins/figure-agent/examples/fig4_trap_energy_diagram/briefing.md
git add plugins/figure-agent/examples/fig4_trap_energy_diagram/fig4_trap_energy_diagram.tex
git add plugins/figure-agent/examples/fig4_trap_energy_diagram/spec.yaml
git add plugins/figure-agent/examples/fig4_trap_energy_diagram/caption.md
git add plugins/figure-agent/examples/fig4_trap_energy_diagram/design.md

# fig5: briefing + tex + spec (caption.md, design.md 없음)
git add plugins/figure-agent/examples/fig5_actuation_mechanism/briefing.md
git add plugins/figure-agent/examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex
git add plugins/figure-agent/examples/fig5_actuation_mechanism/spec.yaml
```

참고: `reference/` 디렉토리는 현재 모든 fixture에서 `.gitkeep`만 존재.
향후 PNG가 추가되면 `git add -f` 필요 (`.gitignore`에 `reference/` 패턴이 없으므로
일반 `git add`로도 가능하지만, PNG가 `*.png` pattern에 걸릴 경우 `-f` 필요).

**주의**: `fig3_trapping_concept`(tracked)와 `fig3_floating_clip_protocol`(untracked)은
별개의 fixture. 혼동하지 않도록 확인.

**test**: `git status --short | grep 'fig[2-5]_'` → 출력 없음.
각 fixture에 대해 `git ls-files -- 'plugins/figure-agent/examples/fig*'`로 추적 확인.

### [x] (commit 20569f7) P2.4 pyproject.toml packages / py-modules 빈 설정

**evidence**: `pyproject.toml:28-30`
```toml
[tool.setuptools]
packages = []
py-modules = []
```

**영향**: 낮음. 이 프로젝트는 `pip install` 방식으로 배포되지 않고 Claude plugin으로
설치됨. `packages = []`는 의도적 — 프로젝트가 Python 패키지가 아님을 선언.

**fix**: 문서화-only. `pyproject.toml` 주석 추가로 의도 명시:
```toml
[tool.setuptools]
packages = []
py-modules = []
# Intentional: figure-agent is not pip-installable.
# It is distributed as a Claude Code plugin via claude plugin install.
```

**commit convention**: `chore(pyproject): document intentional empty packages config`

---

## P3 — 문서 / polish

### [x] (commit 19e832f) P3.1 Stale milestone 문서 정리

**evidence**: `docs/milestones/` 아래 **77개 파일** — 대부분 2026-05-17 ~ 2026-06-08 사이의
dogfood evidence / milestone closeout 보고서. 현재 v0.9.3 상태에서는 대부분 historical.

**fix**: 최근 N개(예: 최근 10개) milestone만 `docs/milestones/`에 보관하고, 나머지는
`docs/milestones/archive/`나 `docs/historical/milestones/`로 이동.

보관 기준:
- v0.9.3 현재 유효한 참조 문서 (release gate, operator playbook 등) → 유지
- 특정 issue의 dogfood evidence (Issue 70, 71, 77-88 등) → 이미 main에 반영됨 → archive
- 단순 날짜별 실험 결과 → archive

**MUST DO 목록 (유지)**:
- `docs/milestones-archive/2026-05-17-quality-state-hardening.md` — README.md:213에서 직접 참조
- `docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md`
- `docs/milestones-archive/2026-05-30-v0-9-operator-playbook.md`
- `docs/milestones-archive/2026-05-30-v0-9-final-review-and-merge-readiness.md`
- `docs/milestones-archive/2026-05-30-v0-9-package-and-version-metadata.md`
- `docs/milestones/2026-05-30-queue-runner-operator-playbook.md`
- `docs/milestones-archive/2026-06-03-operator-completion-explanation-dogfood.md`

**MAY DO (archive)**:
나머지 ~70개 파일 → `docs/historical/milestones/`로 이동.

**주의 — cross-reference**: milestone 파일들 간 내부 링크가 다수 존재함
(e.g., `2026-05-21-plugin-development-closeout-status.md`는 최소 3개 다른 파일에서 참조).
아카이브 전에 `grep -r 'milestones/' docs/`로 내부 참조를 모두 확인하고,
참조된 파일이 아카이브 대상이면 링크를 `docs/historical/milestones/`로 업데이트 필요.

**특수 확인 — README.md 링크**:
```bash
# README.md와 docs/*.md에서 milestones/ 참조 확인
grep -rn 'milestones/' README.md docs/ --include='*.md' | grep -v 'docs/historical/'
# README.md:213 — 2026-05-17-quality-state-hardening.md 참조 (위 MUST DO에 포함됨)
```

**test**: README와 docs/*.md에서 `milestones/` 참조를 깨지 않았는지 확인.
모든 아카이브 대상 파일의 내부 링크 업데이트 완료 확인.

### [x] (commit 20569f7) P3.2 fig_new.md 한국어/영어 혼용 정리

**evidence**: `commands/fig_new.md`에서 질문 1-7이 모두 한국어로 되어 있으나
명령어 설명과 인터뷰 안내는 영어로 되어 있음. 사용자가 한국어 사용자이므로
의도적일 가능성이 높음.

**fix**: 현재 상태 유지 권장. 사용자 기반이 한국어 사용자이므로 briefing interview의
한국어 질문은 사용자 경험에 긍정적. 단, 일관성을 위해 다음 결정 필요:
- 옵션 A: "Naver/KaKao/korean 사용자 대상이므로 한국어 질문 유지, 영어 인프라 문서 유지" → 현상 유지
- 옵션 B: 모든 명령어 문서를 한국어로 통일 → 문서 16개 전체 번역 필요 (대작업)
- 옵션 C: 모든 문서를 영어로 통일 → briefing 질문은 한국어로 유지하는 것이 UX에 좋음

**권장**: 현재 상태 유지 (옵션 A). 문서 상단에 한국어 지원 명시 추가.

### [x] (commit 20569f7) P3.3 CHANGELOG.md v0.1.x 이전 항목 정리

**evidence**: `CHANGELOG.md` 895줄 중 v0.2.0 이전 항목이 약 399줄.
v0.1.x의 frozen orchestration (prompt_gen, redact, fig_prompt 등)에 대한
상세 기록으로 현재 아키텍처와 무관.

**fix**: v0.2.0 이전 항목을 `CHANGELOG.md` 하단 `## Pre-v0.2` 접이식 섹션으로 이동하거나
별도 `CHANGELOG_LEGACY.md`로 분리. 현재 활성 개발(v0.5+) 관련 기록만 `CHANGELOG.md`에 유지.

**참고**: 실제 분량은 ~399줄 (v0.2.0 ~ v0.1.0 전체). ~200줄이 아니라 약 2배이므로
`CHANGELOG_LEGACY.md` 분리 방식이 더 적합할 수 있음.

**commit convention**: `docs(changelog): archive pre-v0.2 entries to CHANGELOG_LEGACY.md`

---

## 게이트

모든 P0/P1/P2/P3 항목 처리 후:

```bash
uv run pytest -q -m "not render"          # 빠른 테스트
uv run ruff check .                        # lint
git status --short                         # 의도한 파일만 변경되었는지 확인
git diff --stat                            # 변경 범위 확인
```

통과 시 `<promise>REVIEW_PATCH_V3_CLOSED</promise>`.

---

## 실행 순서 요약

| 순서 | 항목 | 이유 |
|------|------|------|
| 1 | **P2.2** — MCP facade 분할 | `mcp/figure_agent_server.py` 재구성 — 이후 P2.1이 이 파일의 sys.path를 설정 |
| 2 | **P2.1** — scripts/ 패키지화 | P2.2의 새 구조에서 sys.path 추가 + 파일 이동 |
| 3 | **P0.1** — version sync | 독립적 단순 변경. P2.2 후에도 `SERVER_VERSION` re-export만 유지되면 OK |
| 4 | **P1.1** — dist/ .gitignore | 독립적 단순 변경 |
| 5 | **P2.3** — untracked fixtures | 독립적 단순 변경 |
| 6 | **P2.4** — pyproject 주석 | 독립적 단순 변경 |
| 7 | **P3.1** — milestone 정리 | 문서 작업. P2 완료 후에 해도 무방 |
| 8 | **P3.2** — fig_new.md 결정 | 문서 작업 |
| 9 | **P3.3** — CHANGELOG 정리 | 문서 작업 |
