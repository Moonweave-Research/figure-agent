# Authoring Context Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Issue #82 by turning accumulated figure knowledge into a deterministic, read-only authoring context pack that can guide figure #2 before compile and later feed narrow semantic critique questions.

**Architecture:** Keep figure-agent's quality-kernel boundary intact: no generation executor, no prompt loop, no model calls, and no hidden writes. Add one read-only compiler over existing source-of-truth files plus opt-in semantic contracts, then expose it through the public `fig-agent` entrypoint and MCP as a preview tool. Treat fig1-derived rules as N=1 hypotheses until figure #2 validates transfer.

**Tech Stack:** Python 3.12, PyYAML, existing `runtime_paths.py`, existing `bin/fig-agent` command dispatch, existing MCP JSON-RPC facade, pytest, ruff.

---

## Scope Boundary

Issue: https://github.com/Moonweave-Research/figure-agent/issues/82

Spec: `docs/superpowers/specs/2026-06-10-authoring-context-pack-design.md`

This plan implements the first production slice of the direction:

- Slice 1: rule catalog scaffold and contract tests.
- Slice 2: semantic claim/invariant validation for fixtures that opt into authoring context packs.
- Slice 3: read-only `fig-agent context-pack <name>` compiler plus MCP preview.
- Slice 4: narrow-question critique prompt integration.
- Same-slice doc identity update in `docs/quality-kernel-goal.md`.

This plan does not select figure #2. Figure #2 selection is required to validate the north-star metric, not to land the read-only compiler.

## File Map

- Create `docs/authoring-rules-pair001.md`
  Human-reviewed fig1 rule catalog with YAML front matter. The front matter is the machine-readable source of truth; the Markdown body is review context.

- Create `scripts/authoring_rules.py`
  Loads and validates the rule catalog. One responsibility: parse catalog front matter into stable dictionaries.

- Create `scripts/semantic_contracts.py`
  Validates `spec.yaml` opt-in fields: `authoring_context_pack.enabled`, `panels[].semantic_claims`, and `panels[].locked_invariants`.

- Create `scripts/authoring_context_pack.py`
  Builds a deterministic authoring pack payload from fixture spec, briefing, design philosophy, style lock, rule catalog, semantic claims, locked invariants, and paper-specific snippets.

- Modify `bin/fig-agent`
  Add public read-only command `fig-agent context-pack <name> [--json | --format json]`.

- Create `commands/fig_context_pack.md`
  Operator-facing command doc using public `fig-agent` entrypoint only.

- Modify `mcp/figure_agent_server.py`
  Add read-only tool `figure_agent_context_pack` using the shared envelope helper.

- Leave `.mcp.json` unchanged. The new MCP tool is served by the existing server process.

- Modify `scripts/critique_brief.py`
  Append semantic claims as narrow verification questions in the critique brief.

- Modify `docs/quality-kernel-goal.md`
  Replace the stale "does not teach an LLM" boundary with the narrower distinction: no transient prompt orchestration, but durable paper-specific knowledge compilation is in scope.

- Modify tests:
  - `tests/test_authoring_rules.py`
  - `tests/test_semantic_contracts.py`
  - `tests/test_authoring_context_pack.py`
  - `tests/test_mcp_facade.py`
  - `tests/test_command_contract_docs.py`
  - `tests/test_release_contract.py`
  - `tests/test_critique_brief_semantic_claims.py`

---

### Task 1: Rule Catalog Contract

**Files:**
- Create: `docs/authoring-rules-pair001.md`
- Create: `scripts/authoring_rules.py`
- Create: `tests/test_authoring_rules.py`

- [ ] **Step 1: Write the failing catalog tests**

Add `tests/test_authoring_rules.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import authoring_rules  # noqa: E402


def test_pair001_rule_catalog_requires_source_anchored_rules() -> None:
    catalog = authoring_rules.load_rule_catalog(
        PLUGIN_ROOT / "docs" / "authoring-rules-pair001.md"
    )

    assert catalog["schema"] == "figure-agent.authoring-rules.v1"
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert catalog["promotion_state"] == "n1_hypotheses"
    assert len(catalog["rules"]) >= 8
    for rule in catalog["rules"]:
        assert rule["id"].startswith("pair001.")
        assert rule["category"] in {
            "physics_semantics",
            "label_binding",
            "instrument_standard",
            "panel_layout",
            "style_lock",
        }
        assert rule["source"]["kind"] in {
            "iteration_comment",
            "critique_adjudication",
            "hand_patch_commit",
        }
        assert rule["source"]["locator"]
        assert rule["source"]["quote"]
        assert rule["transfer_policy"] in {"use_as_question", "use_as_constraint"}


def test_rule_catalog_rejects_unanchored_generic_guidance(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_text(
        "---\n"
        "schema: figure-agent.authoring-rules.v1\n"
        "fixture: fig1_overview_v2_pair_001_vault\n"
        "promotion_state: n1_hypotheses\n"
        "rules:\n"
        "  - id: pair001.bad\n"
        "    category: panel_layout\n"
        "    rule: Make the figure beautiful.\n"
        "    source:\n"
        "      kind: iteration_comment\n"
        "      locator: ''\n"
        "      quote: ''\n"
        "    transfer_policy: use_as_constraint\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(authoring_rules.AuthoringRuleError, match="source_anchor_missing"):
        authoring_rules.load_rule_catalog(path)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
uv run pytest -q tests/test_authoring_rules.py
```

Expected: FAIL with `ModuleNotFoundError: No module named 'authoring_rules'`.

- [ ] **Step 3: Add the rule loader**

Create `scripts/authoring_rules.py`:

```python
"""Load source-anchored authoring rule catalogs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.authoring-rules.v1"
VALID_CATEGORIES = {
    "physics_semantics",
    "label_binding",
    "instrument_standard",
    "panel_layout",
    "style_lock",
}
VALID_SOURCE_KINDS = {
    "iteration_comment",
    "critique_adjudication",
    "hand_patch_commit",
}
VALID_TRANSFER_POLICIES = {"use_as_question", "use_as_constraint"}
_FRONT_MATTER_RE = re.compile(r"\\A---\\n(.*?)\\n---\\n?", re.DOTALL)


class AuthoringRuleError(ValueError):
    """Raised when an authoring rule catalog is malformed."""


def _front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(text)
    if match is None:
        raise AuthoringRuleError("front_matter_missing")
    payload = yaml.safe_load(match.group(1)) or {}
    if not isinstance(payload, dict):
        raise AuthoringRuleError("front_matter_invalid")
    return payload


def _require_text(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthoringRuleError(code)
    return value.strip()


def _validate_rule(rule: object) -> dict[str, Any]:
    if not isinstance(rule, dict):
        raise AuthoringRuleError("rule_invalid")
    rule_id = _require_text(rule.get("id"), "rule_id_missing")
    if not rule_id.startswith("pair001."):
        raise AuthoringRuleError("rule_id_invalid")
    category = _require_text(rule.get("category"), "rule_category_missing")
    if category not in VALID_CATEGORIES:
        raise AuthoringRuleError("rule_category_invalid")
    _require_text(rule.get("rule"), "rule_text_missing")
    source = rule.get("source")
    if not isinstance(source, dict):
        raise AuthoringRuleError("source_missing")
    kind = _require_text(source.get("kind"), "source_kind_missing")
    if kind not in VALID_SOURCE_KINDS:
        raise AuthoringRuleError("source_kind_invalid")
    _require_text(source.get("locator"), "source_anchor_missing")
    _require_text(source.get("quote"), "source_anchor_missing")
    transfer_policy = _require_text(rule.get("transfer_policy"), "transfer_policy_missing")
    if transfer_policy not in VALID_TRANSFER_POLICIES:
        raise AuthoringRuleError("transfer_policy_invalid")
    return rule


def load_rule_catalog(path: Path) -> dict[str, Any]:
    payload = _front_matter(path)
    if payload.get("schema") != SCHEMA:
        raise AuthoringRuleError("schema_invalid")
    _require_text(payload.get("fixture"), "fixture_missing")
    if payload.get("promotion_state") != "n1_hypotheses":
        raise AuthoringRuleError("promotion_state_invalid")
    rules = payload.get("rules")
    if not isinstance(rules, list) or not rules:
        raise AuthoringRuleError("rules_missing")
    payload["rules"] = [_validate_rule(rule) for rule in rules]
    return payload
```

- [ ] **Step 4: Add the initial catalog**

Create `docs/authoring-rules-pair001.md` with YAML front matter. Include at least 8 rules. Every rule must cite a source locator and a short quote from fig1 source comments, `critique_adjudication.yaml`, or commit `0a6e308`.

Required first rule:

```yaml
---
schema: figure-agent.authoring-rules.v1
fixture: fig1_overview_v2_pair_001_vault
promotion_state: n1_hypotheses
rules:
  - id: pair001.panel_f_coulomb_deflection
    category: physics_semantics
    rule: "Cantilever-like polymer elements under Coulomb repulsion must visibly deflect away from the biased electrode; a nearly straight beam with a horizontal tip is semantically wrong."
    source:
      kind: hand_patch_commit
      locator: "0a6e308 Deflect Panel F cantilever under Coulomb repulsion"
      quote: "Deflect Panel F cantilever under Coulomb repulsion"
    transfer_policy: use_as_question
---
```

Use `rg -n "%|FIX|iteration|Panel|cantilever|bezel|label|mobility|deep|shallow" examples/fig1_overview_v2_pair_001_vault` to find the remaining source anchors.

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest -q tests/test_authoring_rules.py
uv run ruff check scripts/authoring_rules.py tests/test_authoring_rules.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/authoring-rules-pair001.md scripts/authoring_rules.py tests/test_authoring_rules.py
git commit -m "Add source-anchored authoring rule catalog"
```

---

### Task 2: Semantic Contract Validation

**Files:**
- Create: `scripts/semantic_contracts.py`
- Create: `tests/test_semantic_contracts.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_semantic_contracts.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import semantic_contracts  # noqa: E402


def _fixture(root: Path, body: str) -> Path:
    fixture = root / "examples" / "semantic_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(body.strip() + "\n", encoding="utf-8")
    return fixture


def test_semantic_contract_accepts_opt_in_panel_claims(tmp_path: Path) -> None:
    fixture = _fixture(
        tmp_path,
        """
name: semantic_demo
authoring_context_pack:
  enabled: true
panels:
  - id: F
    caption: mechanical actuation
    semantic_claims:
      - id: f_deflection_direction
        question: Does the cantilever visibly deflect away from the electrode?
        must_show: Cantilever arc bends left under Coulomb repulsion.
      - id: f_air_gap
        question: Is an air gap visible between polymer and electrode?
        must_show: Polymer tip remains separated from electrode.
      - id: f_charge_sites
        question: Are charge markers located on the polymer body?
        must_show: Charge sites sit along the bent polymer.
    locked_invariants:
      - id: f_no_straight_beam
        statement: Beam must not be nearly straight under Coulomb repulsion.
""",
    )

    payload = semantic_contracts.validate_fixture(fixture)

    assert payload["schema"] == "figure-agent.semantic-contracts.v1"
    assert payload["state"] == "ok"
    assert payload["claim_count"] == 3
    assert payload["invariant_count"] == 1


def test_semantic_contract_requires_three_claims_when_opted_in(tmp_path: Path) -> None:
    fixture = _fixture(
        tmp_path,
        """
name: semantic_demo
authoring_context_pack:
  enabled: true
panels:
  - id: F
    semantic_claims:
      - id: f_only_one
        question: Is one claim present?
        must_show: One claim.
    locked_invariants: []
""",
    )

    payload = semantic_contracts.validate_fixture(fixture)

    assert payload["state"] == "failed"
    assert payload["diagnostics"][0]["code"] == "semantic_claim_count_out_of_range"
```

- [ ] **Step 2: Run tests and verify failure**

```bash
uv run pytest -q tests/test_semantic_contracts.py
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement validator**

Create `scripts/semantic_contracts.py`:

```python
"""Validate authoring-time semantic claims and locked invariants."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.semantic-contracts.v1"


def _diagnostic(code: str, panel: str | None = None, detail: str | None = None) -> dict[str, str]:
    payload = {"code": code}
    if panel is not None:
        payload["panel"] = panel
    if detail is not None:
        payload["detail"] = detail
    return payload


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _claims_valid(claims: object, panel_id: str) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if not isinstance(claims, list) or not 3 <= len(claims) <= 5:
        diagnostics.append(_diagnostic("semantic_claim_count_out_of_range", panel_id))
        return diagnostics
    seen: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            diagnostics.append(_diagnostic("semantic_claim_invalid", panel_id))
            continue
        claim_id = claim.get("id")
        if not _is_text(claim_id):
            diagnostics.append(_diagnostic("semantic_claim_id_missing", panel_id))
        elif str(claim_id) in seen:
            diagnostics.append(_diagnostic("semantic_claim_id_duplicate", panel_id, str(claim_id)))
        else:
            seen.add(str(claim_id))
        if not _is_text(claim.get("question")):
            diagnostics.append(_diagnostic("semantic_claim_question_missing", panel_id))
        if not _is_text(claim.get("must_show")):
            diagnostics.append(_diagnostic("semantic_claim_must_show_missing", panel_id))
    return diagnostics


def _invariants_valid(invariants: object, panel_id: str) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    if not isinstance(invariants, list):
        return [_diagnostic("locked_invariants_invalid", panel_id)]
    for invariant in invariants:
        if not isinstance(invariant, dict):
            diagnostics.append(_diagnostic("locked_invariant_invalid", panel_id))
            continue
        if not _is_text(invariant.get("id")):
            diagnostics.append(_diagnostic("locked_invariant_id_missing", panel_id))
        if not _is_text(invariant.get("statement")):
            diagnostics.append(_diagnostic("locked_invariant_statement_missing", panel_id))
    return diagnostics


def validate_fixture(example_dir: Path) -> dict[str, Any]:
    spec_path = example_dir / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    if not isinstance(spec, dict):
        spec = {}
    enabled = bool((spec.get("authoring_context_pack") or {}).get("enabled"))
    diagnostics: list[dict[str, str]] = []
    claim_count = 0
    invariant_count = 0
    if enabled:
        panels = spec.get("panels")
        if not isinstance(panels, list) or not panels:
            diagnostics.append(_diagnostic("panels_missing"))
        else:
            for index, panel in enumerate(panels):
                if not isinstance(panel, dict):
                    diagnostics.append(_diagnostic("panel_invalid", f"panel_{index + 1}"))
                    continue
                panel_id = str(panel.get("id") or f"panel_{index + 1}")
                claims = panel.get("semantic_claims")
                invariants = panel.get("locked_invariants", [])
                if isinstance(claims, list):
                    claim_count += len(claims)
                if isinstance(invariants, list):
                    invariant_count += len(invariants)
                diagnostics.extend(_claims_valid(claims, panel_id))
                diagnostics.extend(_invariants_valid(invariants, panel_id))
    return {
        "schema": SCHEMA,
        "fixture": example_dir.name,
        "enabled": enabled,
        "state": "failed" if diagnostics else "ok",
        "claim_count": claim_count,
        "invariant_count": invariant_count,
        "diagnostics": diagnostics,
    }
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest -q tests/test_semantic_contracts.py
uv run ruff check scripts/semantic_contracts.py tests/test_semantic_contracts.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/semantic_contracts.py tests/test_semantic_contracts.py
git commit -m "Validate authoring semantic contracts"
```

---

### Task 3: Read-Only Context Pack Compiler

**Files:**
- Create: `scripts/authoring_context_pack.py`
- Create: `tests/test_authoring_context_pack.py`
- Modify: `bin/fig-agent`
- Create: `commands/fig_context_pack.md`

- [ ] **Step 1: Write failing compiler and CLI tests**

Create `tests/test_authoring_context_pack.py` with:

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import authoring_context_pack  # noqa: E402


def _fixture(workspace: Path) -> Path:
    fixture = workspace / "examples" / "context_demo"
    fixture.mkdir(parents=True)
    (fixture / "briefing.md").write_text("# Brief\n\nDraw Panel F.\n", encoding="utf-8")
    (fixture / "context_demo.tex").write_text("% source\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: context_demo
authoring_context_pack:
  enabled: true
panels:
  - id: F
    caption: mechanical actuation
    semantic_claims:
      - id: f_deflection_direction
        question: Does the cantilever visibly deflect away from the electrode?
        must_show: Cantilever arc bends left under Coulomb repulsion.
      - id: f_air_gap
        question: Is an air gap visible?
        must_show: Polymer remains separated from electrode.
      - id: f_charge_sites
        question: Are charge markers on the polymer?
        must_show: Charge markers sit on the bent polymer body.
    locked_invariants:
      - id: f_no_straight_beam
        statement: Beam must not be nearly straight.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return fixture


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_context_pack_compiler_is_deterministic_and_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = _tree(workspace)

    first = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )
    second = authoring_context_pack.build_context_pack(
        "context_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert first == second
    assert first["schema"] == "figure-agent.authoring-context-pack.v1"
    assert first["fixture"] == "context_demo"
    assert first["semantic_contract"]["state"] == "ok"
    assert first["rules"]["promotion_state"] == "n1_hypotheses"
    assert "Cantilever arc bends left" in first["pack_markdown"]
    assert _tree(workspace) == before


def test_fig_agent_context_pack_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--json",
        ],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.authoring-context-pack.v1"
    assert payload["manifest"]["read_only"] is True
```

- [ ] **Step 2: Run tests and verify failure**

```bash
uv run pytest -q tests/test_authoring_context_pack.py
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement compiler**

Create `scripts/authoring_context_pack.py`:

```python
"""Compile read-only authoring context packs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import authoring_rules
import runtime_paths
import semantic_contracts
import yaml

SCHEMA = "figure-agent.authoring-context-pack.v1"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _load_spec(example_dir: Path) -> dict[str, Any]:
    payload = yaml.safe_load((example_dir / "spec.yaml").read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _semantic_markdown(spec: dict[str, Any]) -> str:
    lines = ["## Semantic Claims"]
    panels = spec.get("panels") if isinstance(spec.get("panels"), list) else []
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        panel_id = str(panel.get("id") or "panel")
        lines.append(f"### Panel {panel_id}")
        for claim in panel.get("semantic_claims") or []:
            if isinstance(claim, dict):
                lines.append(f"- {claim.get('id')}: {claim.get('must_show')}")
                lines.append(f"  Question: {claim.get('question')}")
        for invariant in panel.get("locked_invariants") or []:
            if isinstance(invariant, dict):
                lines.append(f"- Locked invariant {invariant.get('id')}: {invariant.get('statement')}")
    return "\n".join(lines).strip() + "\n"


def _rules_markdown(catalog: dict[str, Any]) -> str:
    lines = ["## Fig1-Derived Correction Rules"]
    for rule in catalog["rules"]:
        lines.append(f"- {rule['id']}: {rule['rule']}")
        lines.append(f"  Source: {rule['source']['kind']} {rule['source']['locator']}")
    return "\n".join(lines).strip() + "\n"


def _style_lock_summary(style_text: str) -> dict[str, Any]:
    tokens = []
    for line in style_text.splitlines():
        if "\\definecolor" in line:
            tokens.append(line.strip())
    return {"color_token_lines": tokens[:24]}


def build_context_pack(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    spec = _load_spec(example_dir)
    semantic_contract = semantic_contracts.validate_fixture(example_dir)
    catalog_path = paths.plugin_root / "docs" / "authoring-rules-pair001.md"
    catalog = authoring_rules.load_rule_catalog(catalog_path)
    philosophy = _read(paths.plugin_root / "docs" / "figure-design-philosophy.md")
    style_text = _read(paths.styles_dir / "polymer-paper-preamble.sty")
    briefing = _read(example_dir / "briefing.md")
    pack_markdown = "\n\n".join(
        [
            f"# Authoring Context Pack: {name}",
            "## Briefing",
            briefing.strip(),
            "## Design Philosophy Excerpt",
            philosophy.split("## 5. Anti-pattern checklist", 1)[0].strip(),
            _rules_markdown(catalog).strip(),
            _semantic_markdown(spec).strip(),
        ]
    ).strip() + "\n"
    return {
        "schema": SCHEMA,
        "fixture": name,
        "manifest": {
            "read_only": True,
            "pack_sha256": _sha256_text(pack_markdown),
            "source_files": [
                "docs/figure-design-philosophy.md",
                "docs/authoring-rules-pair001.md",
                f"examples/{name}/spec.yaml",
                f"examples/{name}/briefing.md",
                "styles/polymer-paper-preamble.sty",
            ],
        },
        "semantic_contract": semantic_contract,
        "rules": {
            "fixture": catalog["fixture"],
            "promotion_state": catalog["promotion_state"],
            "count": len(catalog["rules"]),
        },
        "style_lock": _style_lock_summary(style_text),
        "pack_markdown": pack_markdown,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args(argv)
    payload = build_context_pack(args.name)
    if args.json or args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload["pack_markdown"], end="")
    return 0 if payload["semantic_contract"]["state"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Add `fig-agent context-pack` dispatch**

In `bin/fig-agent`, add:

```python
def _context_pack(argv: list[str]) -> int:
    import authoring_context_pack

    return authoring_context_pack.main(argv)
```

Then in `main()`:

```python
    if command == "context-pack":
        return _context_pack(rest)
```

- [ ] **Step 5: Add operator command doc**

Create `commands/fig_context_pack.md`:

```markdown
---
description: Compile a read-only authoring context pack for one figure.
argument-hint: <name> [--json | --format json]
---

Run:

```bash
fig-agent context-pack "$1" --json
```

Cowork fallback:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" context-pack "$1" --json
```

The command is read-only. It compiles fixture-local semantic claims, locked
invariants, the fig1-derived correction-rule catalog, Style Lock tokens, and
paper design guidance into an authoring artifact. It does not generate or edit
TikZ.
```

- [ ] **Step 6: Run tests**

```bash
uv run pytest -q tests/test_authoring_context_pack.py tests/test_command_contract_docs.py
uv run ruff check scripts/authoring_context_pack.py bin/fig-agent tests/test_authoring_context_pack.py
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/authoring_context_pack.py bin/fig-agent commands/fig_context_pack.md tests/test_authoring_context_pack.py
git commit -m "Add read-only authoring context pack CLI"
```

---

### Task 4: MCP Preview Tool

**Files:**
- Modify: `mcp/figure_agent_server.py`
- Modify: `tests/test_mcp_facade.py`
- Modify: `docs/mcp-facade-design.md`

- [ ] **Step 1: Add failing MCP tests**

In `tests/test_mcp_facade.py`, add:

```python
def test_mcp_context_pack_is_read_only_tool(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace, name="context_demo")
    (fixture / "spec.yaml").write_text(
        """
name: context_demo
authoring_context_pack:
  enabled: true
panels:
  - id: F
    semantic_claims:
      - id: f_deflection_direction
        question: Does the cantilever deflect away from the electrode?
        must_show: Cantilever deflects away from the electrode.
      - id: f_air_gap
        question: Is the air gap visible?
        must_show: Air gap remains visible.
      - id: f_charge_sites
        question: Are charge markers on the polymer?
        must_show: Charge markers sit on polymer.
    locked_invariants:
      - id: f_no_straight_beam
        statement: Beam is not straight under repulsion.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    before = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))

    result = _run_mcp_server(
        [
            _mcp_request("initialize", request_id=1),
            _mcp_request(
                "tools/call",
                {"name": "figure_agent_context_pack", "arguments": {"name": "context_demo"}},
                request_id=2,
            ),
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[1])
    assert payload["success"] is True
    assert payload["context_pack"]["manifest"]["read_only"] is True
    after = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))
    assert after == before
```

- [ ] **Step 2: Run test and verify failure**

```bash
uv run pytest -q tests/test_mcp_facade.py::test_mcp_context_pack_is_read_only_tool
```

Expected: FAIL because `figure_agent_context_pack` is not listed.

- [ ] **Step 3: Add MCP handler**

In `mcp/figure_agent_server.py`, add a handler that calls the public entrypoint through `_run_fig_agent_enveloped`:

```python
def _context_pack(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.context-pack.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=["context-pack", name, "--json"],
        workspace_root=workspace_root,
        timeout_seconds=60,
        timeout_message="fig-agent context-pack timed out",
        name=name,
    )
    if isinstance(result, dict):
        return result
    payload, invalid = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent context-pack returned invalid JSON",
        required=True,
    )
    if invalid is not None:
        return invalid
    success = result.returncode == 0
    return _tool_envelope(
        schema,
        success=success,
        started=started,
        name=name,
        context_pack=payload,
        stderr=_bounded(result.stderr),
        error=None if success else _error("context_pack_failed", "fig-agent context-pack failed"),
    )
```

Add to `TOOLS`:

```python
"figure_agent_context_pack": {
    "description": "Compile a read-only authoring context pack for one fixture.",
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["name"],
        "properties": {"name": {"type": "string"}},
    },
    "handler": _context_pack,
},
```

- [ ] **Step 4: Update MCP design doc**

In `docs/mcp-facade-design.md`, add `figure_agent_context_pack` under read-only tools and state that it must not write under `examples/`.

- [ ] **Step 5: Run tests**

```bash
uv run pytest -q tests/test_mcp_facade.py::test_mcp_context_pack_is_read_only_tool tests/test_mcp_facade.py::test_mcp_startup_and_list_tools_are_side_effect_free
uv run ruff check mcp/figure_agent_server.py tests/test_mcp_facade.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add mcp/figure_agent_server.py docs/mcp-facade-design.md tests/test_mcp_facade.py
git commit -m "Expose authoring context pack over MCP"
```

---

### Task 5: Narrow Semantic Critique Questions

**Files:**
- Modify: `scripts/critique_brief.py`
- Create or modify: `tests/test_critique_brief_semantic_claims.py`
- Modify: `commands/fig_critique.md`

- [ ] **Step 1: Write failing critique brief test**

Create `tests/test_critique_brief_semantic_claims.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import critique_brief  # noqa: E402


def test_semantic_claims_render_as_narrow_questions(tmp_path: Path) -> None:
    example = tmp_path / "examples" / "claim_demo"
    example.mkdir(parents=True)
    spec = {
        "panels": [
            {
                "id": "F",
                "semantic_claims": [
                    {
                        "id": "f_deflection_direction",
                        "question": "Does the cantilever visibly deflect away from the electrode?",
                        "must_show": "Cantilever bends away from the electrode.",
                    }
                ],
                "locked_invariants": [
                    {
                        "id": "f_no_straight_beam",
                        "statement": "Beam must not be nearly straight.",
                    }
                ],
            }
        ]
    }

    text = critique_brief._semantic_claim_questions(spec)

    assert "Panel F" in text
    assert "f_deflection_direction" in text
    assert "Does the cantilever visibly deflect away from the electrode?" in text
    assert "Beam must not be nearly straight." in text
```

- [ ] **Step 2: Run test and verify failure**

```bash
uv run pytest -q tests/test_critique_brief_semantic_claims.py
```

Expected: FAIL because `_semantic_claim_questions` is missing.

- [ ] **Step 3: Add semantic question renderer**

In `scripts/critique_brief.py`, add:

```python
def _semantic_claim_questions(spec: dict) -> str:
    panels = spec.get("panels") if isinstance(spec.get("panels"), list) else []
    blocks: list[str] = []
    for index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            continue
        panel_id = _panel_id(panel, index)
        lines: list[str] = []
        for claim in panel.get("semantic_claims") or []:
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("id")
            question = claim.get("question")
            must_show = claim.get("must_show")
            if isinstance(claim_id, str) and isinstance(question, str):
                lines.append(f"- `{claim_id}`: {question}")
                if isinstance(must_show, str) and must_show.strip():
                    lines.append(f"  Must show: {must_show.strip()}")
        for invariant in panel.get("locked_invariants") or []:
            if not isinstance(invariant, dict):
                continue
            invariant_id = invariant.get("id")
            statement = invariant.get("statement")
            if isinstance(invariant_id, str) and isinstance(statement, str):
                lines.append(f"- Locked invariant `{invariant_id}`: {statement.strip()}")
        if lines:
            blocks.append(f"### Panel {panel_id}\n" + "\n".join(lines))
    if not blocks:
        return "No semantic claims declared."
    return "\n\n".join(blocks)
```

Then include the result in the generated brief near author intent, under heading:

```markdown
## Semantic Claim Verification Questions
```

- [ ] **Step 4: Update critique command doc**

In `commands/fig_critique.md`, add one sentence: if `spec.yaml panels[].semantic_claims` exists, the brief asks narrow per-claim verification questions and does not ask the host to invent physics constraints.

- [ ] **Step 5: Run tests**

```bash
uv run pytest -q tests/test_critique_brief_semantic_claims.py tests/test_command_contract_docs.py
uv run ruff check scripts/critique_brief.py tests/test_critique_brief_semantic_claims.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/critique_brief.py commands/fig_critique.md tests/test_critique_brief_semantic_claims.py
git commit -m "Add semantic claim questions to critique briefs"
```

---

### Task 6: Product Direction Docs and Contracts

**Files:**
- Modify: `docs/quality-kernel-goal.md`
- Modify: `skills/figure-agent/SKILL.md`
- Modify: `README.md`
- Modify: `tests/test_release_contract.py`
- Modify: `tests/test_command_contract_docs.py`

- [ ] **Step 1: Add failing direction contract tests**

In `tests/test_release_contract.py`, add:

```python
def test_docs_define_authoring_context_pack_as_quality_kernel_extension() -> None:
    quality_goal = (REPO_ROOT / "docs" / "quality-kernel-goal.md").read_text()
    readme = (REPO_ROOT / "README.md").read_text()
    skill = (REPO_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text()

    required = [
        "durable paper-specific knowledge compilation",
        "authoring context pack",
        "no transient prompt orchestration",
    ]
    for text in (quality_goal, readme, skill):
        for phrase in required:
            assert phrase in text
```

In `tests/test_command_contract_docs.py`, extend command docs coverage so `fig_context_pack.md` is checked for `fig-agent` entrypoint and JSON spelling.

- [ ] **Step 2: Run tests and verify failure**

```bash
uv run pytest -q tests/test_release_contract.py::test_docs_define_authoring_context_pack_as_quality_kernel_extension tests/test_command_contract_docs.py
```

Expected: FAIL until docs are updated.

- [ ] **Step 3: Update docs**

In `docs/quality-kernel-goal.md`, replace the bullet:

```markdown
- Teaching an LLM how to create every figure.
```

with:

```markdown
- Transient prompt orchestration that tries to control today's model behavior.
- Generic teaching of an LLM how to create every figure.
```

Add under "The plugin owns":

```markdown
- Durable paper-specific knowledge compilation for authoring context packs:
  Style Lock, figure-specific semantic claims, locked invariants, and
  source-anchored correction rules can guide a human or LLM before compile,
  while the same contracts remain auditable after compile.
```

In `README.md` and `skills/figure-agent/SKILL.md`, add a short "Authoring context pack" paragraph using the same phrases from the test.

- [ ] **Step 4: Run tests**

```bash
uv run pytest -q tests/test_release_contract.py::test_docs_define_authoring_context_pack_as_quality_kernel_extension tests/test_command_contract_docs.py
uv run ruff check tests/test_release_contract.py tests/test_command_contract_docs.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/quality-kernel-goal.md README.md skills/figure-agent/SKILL.md tests/test_release_contract.py tests/test_command_contract_docs.py
git commit -m "Document authoring context pack product boundary"
```

---

### Task 7: Packaging and Full Verification

**Files:**
- Inspect: `scripts/package_cowork_plugin.py`
- Inspect: `tests/test_package_cowork_plugin.py`
- Modify: `scripts/package_cowork_plugin.py` when Step 1 proves a required runtime file is missing from the ZIP.
- Modify: `tests/test_package_cowork_plugin.py` when Step 1 proves a required runtime file is missing from the ZIP.

- [ ] **Step 1: Run package audit before changing packaging**

```bash
outdir=$(mktemp -d /tmp/figure-agent-context-pack.XXXXXX)
python3 scripts/package_cowork_plugin.py --output "$outdir"
tmpdir=$(mktemp -d /tmp/figure-agent-context-pack-audit.XXXXXX)
unzip -q "$outdir/figure-agent-cowork-0.9.3.zip" -d "$tmpdir"
python3 scripts/plugin_package_audit.py "$tmpdir" --max-mib 50
unzip -l "$outdir/figure-agent-cowork-0.9.3.zip" | rg 'authoring_context_pack.py|authoring_rules.py|semantic_contracts.py|authoring-rules-pair001.md|fig_context_pack.md'
```

Expected: audit PASS; `unzip -l` should show all new runtime/docs files. If `unzip -l` misses any of these, update the package builder include list.

- [ ] **Step 2: Add package test if needed**

If files are missing, add assertions to `tests/test_package_cowork_plugin.py`:

```python
assert "scripts/authoring_context_pack.py" in names
assert "scripts/authoring_rules.py" in names
assert "scripts/semantic_contracts.py" in names
assert "docs/authoring-rules-pair001.md" in names
assert "commands/fig_context_pack.md" in names
```

- [ ] **Step 3: Run full local fast CI**

```bash
uv run pytest -q -m "not render"
uv run ruff check .
git diff --check
```

Expected: PASS.

- [ ] **Step 4: Run focused runtime smoke**

From `plugins/figure-agent`:

```bash
bin/fig-agent context-pack fig1_overview_v2_pair_001_vault --json
```

Expected: JSON schema `figure-agent.authoring-context-pack.v1`. If fig1 has not opted into semantic contracts, the command may return nonzero with a semantic contract diagnostic; use this as evidence to decide whether fig1 should opt in now or only figure #2 should opt in.

- [ ] **Step 5: Commit packaging changes if any**

```bash
git add scripts/package_cowork_plugin.py tests/test_package_cowork_plugin.py
git commit -m "Package authoring context pack runtime files"
```

Skip this commit if Step 1 proves packaging already includes the files.

- [ ] **Step 6: Push branch and update PR/issue**

```bash
git push
gh pr comment 81 --body "Implements Issue #82 authoring context pack plan through read-only CLI/MCP surfaces, semantic claim validation, and narrow critique questions. Verification: uv run pytest -q -m 'not render'; uv run ruff check .; package audit."
gh issue comment 82 --body "Implementation pushed to PR #81. The first landing slice is read-only and does not select figure #2; figure #2 remains the validation blocker for iterations-to-golden."
```

---

## Self-Review

Spec coverage:

- Correction-rule distillation: Task 1.
- Semantic contracts: Task 2.
- Context-pack compiler: Task 3.
- MCP preview: Task 4.
- Narrow-question critique: Task 5.
- `quality-kernel-goal.md` revision: Task 6.
- Packaging: Task 7.
- Figure #2 validation: explicitly left as blocker for metric validation, not implementation.

Risk controls:

- No generation executor is added.
- No new third-party dependency is added.
- All new runtime surfaces are read-only.
- Rules require source anchors to prevent generic guidance and snippet lock-in.
- Semantic claim lint is opt-in to avoid breaking existing fixtures.
- Package audit remains required before PR completion.

Known dependency:

- The plan can land the read-only machinery without figure #2. It cannot validate the north-star `iterations-to-golden` metric until figure #2 is selected and authored with the pack.
