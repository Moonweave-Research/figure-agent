# figure-agent P0–P3 review patch plan v2

2026-06-22 review에서 발견된 항목. 각 항목은 fix + PLAN 갱신 + test가 한 commit.
완료 시 `[ ]` → `[x] (commit <sha7>)`.

---

## P0 — correctness (메타데이터 무결성)

### P0.1 MCP facade SERVER_VERSION이 plugin 버전과 불일치

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

**commit convention**: `fix(mcp): sync SERVER_VERSION with pyproject v0.9.3`

---

## P1 — gate 경고 (게이트 오작동 가능성)

### P1.1 dist/ build artifacts untracked, .gitignore 누락

**evidence**: `git status`에 `?? dist/`와 `?? plugins/figure-agent/dist/` 표시됨.
두 dist/ 디렉토리 모두 `cowork/` ZIP bundle이 들어 있음.
루트 `.gitignore`와 `plugins/figure-agent/.gitignore` 모두 `dist/` 패턴 없음.

**영향**: 낮음. `dist/`는 빌드 산출물이므로 실수로 `git add .` 할 경우 불필요한 파일이 stage됨.

**fix**: 루트 `.gitignore`에 `dist/` 패턴 추가.
`plugins/figure-agent/.gitignore`가 이미 존재하므로 거기에도 추가하거나,
루트 `dist/`는 루트 `.gitignore`에서, plugin `dist/`는 plugin `.gitignore`에서 각각 커버.

**test**: 
```bash
# 수동 확인 — dist/ 디렉토리가 git status에 나타나지 않는지
git status --short | grep dist/ | wc -l  # → 0
```

**commit convention**: `chore(gitignore): add dist/ to prevent accidental staging`

---

## P2 — 데이터 모델 / 구조

### P2.1 scripts/ 디렉토리 flat 구조 → 패키지 계층화

**evidence**: 
- `scripts/` 아래 138개 `.py` 파일이 단일 디렉토리에 flat하게 위치.
- 17개 파일이 `sys.path.insert(0, ...)`로 `scripts/`를 path에 직접 추가하여 import 해결.
- 32개 파일이 동일 디렉토리 내 다른 모듈을 `import` (절대 import, no package prefix).
- `__init__.py` 없음 — Python 3.3+ namespace package으로 동작하지만 구조적 계층 없음.
- 도메인별 그룹이 명확히 존재: `check_*` (7개), `candidate_*` (10개), `quality_*` (7개),
  `fig_loop_*` (12개), `fig_driver*` (4개), `svg_polish_*` (8개).

**fix**: `__init__.py` 추가 + 서브디렉토리 생성 + import 문 일괄 변경. **단, 이 리팩터는
behavior change가 전혀 없어야 하며 하나의 커밋으로 끝나야 함.**

변경 계획:
```
scripts/
  __init__.py
  checks/           ← check_*.py (7개 파일) + __init__.py
  candidates/       ← candidate_*.py (10개) + __init__.py
  quality/          ← quality_*.py (7개) + __init__.py
  loop/             ← fig_loop_*.py (12개) + __init__.py
  driver/           ← fig_driver*.py (4개) + __init__.py
  svg_polish/       ← svg_polish_*.py (8개) + __init__.py
  tests/            ← test_*.py는 이동하지 않음 (tests/ 아래에 그대로)
  (나머지 ~90개 핵심 스크립트는 scripts/에 유지 — runtime_paths, status, compile, export 등)
```

**임계 조건**: 리팩터 후 `import` 경로 변경으로 인한 `ModuleNotFoundError`가 전혀 없어야 함.

**fix 상세**:
1. `scripts/__init__.py` 생성 (optional - namespace package이어도 됨).
2. 각 서브디렉토리에 `__init__.py` 생성.
3. 이동할 파일들을 각 서브디렉토리로 `git mv`.
4. 해당 파일들의 `sys.path.insert(0, ...)` 제거 (더 이상 필요 없음).
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
for subdir in SCRIPTS_DIR.iterdir():
    if subdir.is_dir() and not subdir.name.startswith("_"):
        sys.path.insert(0, str(subdir))
```
→ 이렇게 하면 모든 기존 import 문을 변경할 필요 없음.

**위험**: scripts/ 내부에서 `sys.path.insert`를 사용하는 17개 파일 중 일부는 `scripts/`를 path에
추가하는 것이 아니라 **자기 자신의 디렉토리** (scripts/)를 추가하여 sibling import를 가능하게 함.
패키지화 후에는 이 17개 파일들의 `sys.path.insert`도 제거 가능.

**test**: `uv run pytest -q -m "not render"` → 기존 테스트와 동일한 pass count 유지.
`bin/fig-agent`를 실제로 호출하는 테스트가 있다면 통과 확인.

### P2.2 MCP facade 단일 파일 분할

**evidence**: `mcp/figure_agent_server.py` 2,133줄:
- 27개 tool handler (`_status`, `_compile`, `_export`, `_render_candidates`, 등)
- 공통 인프라 (`_tool_envelope`, `_error`, `_fixture_lock`, `_run_fig_agent`, 등)
- 리소스 메타데이터 (`_resource_metadata`, `_resource_specs`)
- JSON-RPC 프로토콜 핸들링 (`_call_tool`, `_list_tools`, `initialize` 등)
- TOOLS dict (line 1582-1965, 30개 등록)

**fix**: 모듈 분할. 단, MCP 서버가 **zero runtime dependency** 정책을 유지해야 하므로
표준 라이브러리만 사용.

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
                               _compare_candidate, _render_candidates, _rank_candidates,
                               _candidate_apply_readiness, _apply_candidate, _prepare_human_review
  _handlers_benchmark.py     ← _benchmark_list, _benchmark_run_preview, _benchmark_compare,
                               _benchmark_detectors_preview, _quality_next_experiment
  _handlers_misc.py          ← _propose_patch, _evidence_sync_preview, _closeout_ready, _verify_plan
```

**MAY DO (권장)**: 위 분할 후 `figure_agent_server.py`에는 `initialize`, `_list_tools`, `_call_tool`만 남고
TOOLS dict는 `_handlers_*.py`에서 각자 등록하는 패턴으로 변경.

**MAY DO (선택)**: PIL, yaml 등 흔한 라이브러리까지 zero-dependency 정책을 유지할지 재검토.
현재 doctor에서만 사용되는 `yaml`과 `PIL`을 위해 import guard를 유지하는 건 합리적.

**test**: `tests/test_mcp_facade.py` 1,482줄이 MCP 서버의 전체 표면을 테스트하므로, 리팩터 후
기존 테스트가 모두 통과해야 함. 추가로 각 `_handlers_*.py` 모듈이 독립적으로 import 가능한지 확인.

### P2.3 Untracked real fixtures 정리

**evidence**: 4개 실제 피겨(fig2–fig5)가 `git status`에 `??`로 표시됨.
모두 `.tex`와 빌드된 `.pdf`를 갖추고 있음:
- `fig2_trap_design_space/` — briefing, tex, build/pdf, reference/, previews/, exports/
- `fig3_floating_clip_protocol/` — briefing, tex, build/pdf, reference/, previews/, exports/
- `fig4_trap_energy_diagram/` — briefing, tex, build/pdf, reference/, previews/, exports/
- `fig5_actuation_mechanism/` — briefing, tex, build/pdf, reference/, previews/, exports/

단, `**/build/*`, `**/exports/*`, `**/previews/*`가 `.gitignore`이므로 build/exports/previews
내용물은 추적되지 않음 (의도적). `.tex`, `briefing.md`, `spec.yaml` 등 source 파일만 추적됨.

**fix**: `git add`로 source 파일만 staging:
```bash
git add plugins/figure-agent/examples/fig2_trap_design_space/*.tex
git add plugins/figure-agent/examples/fig2_trap_design_space/briefing.md
git add plugins/figure-agent/examples/fig2_trap_design_space/spec.yaml
git add plugins/figure-agent/examples/fig2_trap_design_space/caption.md
git add plugins/figure-agent/examples/fig2_trap_design_space/design.md
# reference/ 디렉토리는 PNG가 들어있을 수 있으므로 git add -f 필요
git add -f plugins/figure-agent/examples/fig2_trap_design_space/reference/
# 동일 패턴으로 fig3, fig4, fig5 반복
```

**주의**: `fig3_trapping_concept`(tracked)와 `fig3_floating_clip_protocol`(untracked)은
별개의 fixture. 혼동하지 않도록 확인.

**test**: `git status --short | grep 'fig[2-5]_'` → 출력 없음.
각 fixture에 대해 `git ls-files -- 'plugins/figure-agent/examples/fig*'`로 추적 확인.

### P2.4 pyproject.toml packages / py-modules 빈 설정

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

### P3.1 Stale milestone 문서 정리

**evidence**: `docs/milestones/` 아래 68개 파일 — 대부분 2026-05-17 ~ 2026-06-08 사이의
dogfood evidence / milestone closeout 보고서. 현재 v0.9.3 상태에서는 대부분 historical.

**fix**: 최근 N개(예: 최근 10개) milestone만 `docs/milestones/`에 보관하고, 나머지는
`docs/milestones/archive/`나 `docs/historical/milestones/`로 이동.

보관 기준:
- v0.9.3 현재 유효한 참조 문서 (release gate, operator playbook 등) → 유지
- 특정 issue의 dogfood evidence (Issue 70, 71, 77-88 등) → 이미 main에 반영됨 → archive
- 단순 날짜별 실험 결과 → archive

**MUST DO 목록 (유지)**:
- `docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md`
- `docs/milestones-archive/2026-05-30-v0-9-operator-playbook.md`
- `docs/milestones-archive/2026-05-30-v0-9-final-review-and-merge-readiness.md`
- `docs/milestones-archive/2026-05-30-v0-9-package-and-version-metadata.md`
- `docs/milestones/2026-05-30-queue-operator-playbook.md`
- `docs/milestones-archive/2026-06-03-operator-completion-explanation-dogfood.md`

**MAY DO (archive)**:
나머지 ~62개 파일 → `docs/historical/milestones/`로 이동.
README나 관련 문서에서 참조하는 링크가 있다면 수정 필요.

**test**: README와 docs/*.md에서 `milestones/` 참조를 깨지 않았는지 확인.

### P3.2 fig_new.md 한국어/영어 혼용 정리

**evidence**: `commands/fig_new.md`에서 질문 1-7이 모두 한국어로 되어 있으나
명령어 설명과 인터뷰 안내는 영어로 되어 있음. 사용자가 한국어 사용자이므로
의도적일 가능성이 높음.

**fix**: 현재 상태 유지 권장. 사용자 기반이 한국어 사용자이므로 briefing interview의
한국어 질문은 사용자 경험에 긍정적. 단, 일관성을 위해 다음 결정 필요:
- 옵션 A: "Naver/KaKao/korean 사용자 대상이므로 한국어 질문 유지, 영어 인프라 문서 유지" → 현상 유지
- 옵션 B: 모든 명령어 문서를 한국어로 통일 → 문서 16개 전체 번역 필요 (대작업)
- 옵션 C: 모든 문서를 영어로 통일 → briefing 질문은 한국어로 유지하는 것이 UX에 좋음

**권장**: 현재 상태 유지 (옵션 A). 문서 상단에 한국어 지원 명시 추가.

### P3.3 CHANGELOG.md v0.1.x 이전 항목 정리

**evidence**: `CHANGELOG.md` 895줄 중 v0.1.x 이전 항목 (0.1.0 ~ 0.1.14, 0.2.0)이
약 200줄. v0.1.x의 frozen orchestration (prompt_gen, redact, fig_prompt 등)에 대한
상세 기록으로 현재 아키텍처와 무관.

**fix**: v0.2.0 이전 항목을 `CHANGELOG.md` 하단 `## Pre-v0.2` 접이식 섹션으로 이동하거나
별도 `CHANGELOG_LEGACY.md`로 분리. 현재 활성 개발(v0.5+) 관련 기록만 `CHANGELOG.md`에 유지.

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

통과 시 `<promise>REVIEW_PATCH_V2_CLOSED</promise>`.
