from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_schema_vocab as vocab  # noqa: E402
from critique_contract import CritiqueContractError  # noqa: E402
from critique_schema_validator import validate_critique_schema  # noqa: E402


def test_validate_critique_schema_warns_for_v1_legacy() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        validate_critique_schema({"schema": vocab.CRITIQUE_SCHEMA_V1})

    assert len(captured) == 1
    assert captured[0].category is DeprecationWarning
    assert vocab.CRITIQUE_SCHEMA_V1 in str(captured[0].message)


def test_validate_critique_schema_rejects_future_unsupported_schema() -> None:
    with pytest.raises(CritiqueContractError, match="unsupported critique schema"):
        validate_critique_schema({"schema": "figure-agent.critique.v99"})
