from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import critique_brief  # noqa: E402


def test_critique_brief_renders_semantic_claims_as_narrow_questions() -> None:
    section = critique_brief._semantic_claim_questions_section(
        {
            "authoring_context_pack": {"enabled": True},
            "panels": [
                {
                    "id": "C",
                    "semantic_claims": [
                        {"id": "trap-depth", "claim": "Deep traps are harder to escape."}
                    ],
                }
            ],
        }
    )

    assert "## Narrow semantic claim checks" in section
    assert "Do not broaden this into open-ended physics judgment." in section
    assert "[C:trap-depth] Does the rendered panel visually support this claim" in section
