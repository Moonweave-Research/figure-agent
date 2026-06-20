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
# Rule ids are namespaced "<namespace>.<local_id>". The namespace was historically
# hard-coded to "pair001", which locked conventions to one pilot fixture; any
# lowercase namespace is now allowed so a project-scope catalog can carry
# cross-figure conventions (e.g. "polymer_paper_project.cantilever-vertical-clip").
VALID_RULE_ID_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z0-9_.-]+$")
_FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


class AuthoringRuleError(ValueError):
    """Raised when an authoring rule catalog is malformed."""


def _front_matter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AuthoringRuleError("catalog_missing")
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
    if not VALID_RULE_ID_PATTERN.match(rule_id):
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
