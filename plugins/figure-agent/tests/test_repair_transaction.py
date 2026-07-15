from __future__ import annotations

import json
from pathlib import Path

import pytest
import repair_transaction


def _lock_record(owner: str) -> str:
    return json.dumps(
        {"schema": "figure-agent.recoverable-lock.v1", "owner": owner},
        sort_keys=True,
        separators=(",", ":"),
    )


def test_recoverable_lock_reclaims_crashed_owner_record(tmp_path: Path) -> None:
    lock = tmp_path / ".materialization.lock"
    lock.write_text(_lock_record("authoring_repair_rollback"), encoding="utf-8")

    with repair_transaction.recoverable_exclusive_lock(
        lock, owner="authoring_repair_rollback"
    ):
        assert lock.is_file()

    assert not lock.exists()


def test_recoverable_lock_refuses_live_holder(tmp_path: Path) -> None:
    lock = tmp_path / ".materialization.lock"

    with repair_transaction.recoverable_exclusive_lock(
        lock, owner="authoring_repair_rollback"
    ):
        with pytest.raises(
            repair_transaction.RepairTransactionError,
            match="transaction lock exists",
        ):
            with repair_transaction.recoverable_exclusive_lock(
                lock, owner="authoring_repair_rollback"
            ):
                raise AssertionError("unreachable")
        assert lock.is_file()


def test_recoverable_lock_refuses_unknown_stale_record(tmp_path: Path) -> None:
    lock = tmp_path / ".materialization.lock"
    lock.write_text("authoring_repair_finalize\n", encoding="utf-8")

    with pytest.raises(
        repair_transaction.RepairTransactionError,
        match="transaction lock exists",
    ):
        with repair_transaction.recoverable_exclusive_lock(
            lock, owner="authoring_repair_rollback"
        ):
            raise AssertionError("unreachable")

    assert lock.read_text(encoding="utf-8") == "authoring_repair_finalize\n"
