from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from illustration_grammar import (  # noqa: E402
    IllustrationGrammarError,
    load_illustration_grammar,
)

GRAMMAR_PATH = (
    PLUGIN_ROOT / "styles" / "illustration-grammar" / "sulfur_trap_domain.v1.yaml"
)


def test_loads_sulfur_trap_domain_with_closed_visual_contract() -> None:
    grammar = load_illustration_grammar(GRAMMAR_PATH)

    assert grammar["schema"] == "figure-agent.illustration-grammar.v1"
    assert grammar["motif_family"] == "sulfur_trap_domain"
    assert set(grammar["semantic_slots"]) == {
        "chain.backbones",
        "sulfur.regions",
        "sulfur.sites",
        "trap.levels",
        "trapped.carriers",
    }
    assert grammar["layer_order"] == [
        "sulfur.regions",
        "chain.backbones",
        "sulfur.sites",
        "trap.levels",
        "trapped.carriers",
    ]
    assert grammar["relations"] == [
        ["sulfur.sites", "attached_to", "chain.backbones"],
        ["sulfur.sites", "located_in", "sulfur.regions"],
        ["trap.levels", "co_located_with", "sulfur.regions"],
        ["trapped.carriers", "sits_on", "trap.levels"],
    ]


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (("schema", "figure-agent.illustration-grammar.v2"), "schema_unsupported"),
        (("motif_family", ""), "motif_family_invalid"),
        (("layer_order", ["chain.backbones"]), "layer_order_incomplete"),
    ],
)
def test_grammar_fails_closed(
    tmp_path: Path,
    mutation: tuple[str, object],
    error: str,
) -> None:
    payload = yaml.safe_load(GRAMMAR_PATH.read_text(encoding="utf-8"))
    payload[mutation[0]] = mutation[1]
    candidate = tmp_path / "grammar.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(IllustrationGrammarError, match=error):
        load_illustration_grammar(candidate)


@pytest.mark.parametrize("forbidden", ["aesthetic_levers", "route", "filters", "fonts"])
def test_rejects_review_routing_and_freeform_render_fields(
    tmp_path: Path,
    forbidden: str,
) -> None:
    payload = yaml.safe_load(GRAMMAR_PATH.read_text(encoding="utf-8"))
    payload[forbidden] = ["invented"]
    candidate = tmp_path / "grammar.yaml"
    candidate.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(IllustrationGrammarError, match="field_forbidden"):
        load_illustration_grammar(candidate)
