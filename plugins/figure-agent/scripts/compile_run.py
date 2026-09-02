#!/usr/bin/env python3
"""Issue and verify the receipt that names the compile a build artifact came from."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import uuid
from collections.abc import Mapping
from pathlib import Path

SCHEMA = "figure-agent.compile-run.v1"
RECEIPT_NAME = "compile_run.json"
PASSED = "passed"
FAILED = "failed"
RUN_ID_ENV = "FIGURE_AGENT_COMPILE_RUN_ID"


def receipt_path(build_dir: Path) -> Path:
    return build_dir / RECEIPT_NAME


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def new_run_stamp() -> tuple[str, str]:
    started_at = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    return str(uuid.uuid4()), started_at


def build_receipt(
    *,
    run_id: str,
    started_at: str,
    engine: str,
    strict_requested: bool,
    state: str,
    source_tex: Path,
    render_pdf: Path | None,
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "run_id": run_id,
        "started_at": started_at,
        "engine": engine,
        "strict_requested": strict_requested,
        "state": state,
        "source_tex": source_tex.name,
        "source_tex_sha256": _sha256(source_tex),
        "render_pdf": render_pdf.name if render_pdf is not None else None,
        "render_pdf_sha256": _sha256(render_pdf) if render_pdf is not None else None,
    }


def write_receipt(*, output: Path, payload: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_receipt(path: Path) -> dict[str, object] | None:
    """Return a schema-valid receipt, or None when it is absent or unusable."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return None
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        return None
    if payload.get("state") not in {PASSED, FAILED}:
        return None
    return payload


def verified_receipt(build_dir: Path) -> dict[str, object] | None:
    """Return the receipt only when the render it names is still on disk.

    A receipt is agent-writable like every other build artifact, so it earns
    nothing on its own. What it does buy is that a receipt cannot outlive the
    render it claims to describe: every downstream claim now has to name the
    bytes actually sitting in build/.
    """
    receipt = load_receipt(receipt_path(build_dir))
    if receipt is None or receipt.get("state") != PASSED:
        return None
    render_name = receipt.get("render_pdf")
    if not isinstance(render_name, str) or not render_name:
        return None
    try:
        render_hash = _sha256(build_dir / Path(render_name).name)
    except OSError:
        return None
    if receipt.get("render_pdf_sha256") != render_hash:
        return None
    return receipt


def current_source_sha256(build_dir: Path, receipt: Mapping[str, object]) -> str | None:
    """Hash of the source the receipt names, as it stands now."""
    source_name = receipt.get("source_tex")
    if not isinstance(source_name, str) or not source_name:
        return None
    try:
        return _sha256(build_dir.parent / Path(source_name).name)
    except OSError:
        return None


def _begin(_: argparse.Namespace) -> int:
    run_id, started_at = new_run_stamp()
    print(f"{run_id} {started_at}")
    return 0


def _finish(args: argparse.Namespace) -> int:
    payload = build_receipt(
        run_id=args.run_id,
        started_at=args.started_at,
        engine=args.engine,
        strict_requested=args.strict_requested,
        state=args.state,
        source_tex=args.source_tex.expanduser().resolve(),
        render_pdf=args.render_pdf.expanduser().resolve() if args.render_pdf else None,
    )
    write_receipt(output=args.json_output.expanduser().resolve(), payload=payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("begin").set_defaults(handler=_begin)
    finish = subparsers.add_parser("finish")
    finish.add_argument("--json-output", type=Path, required=True)
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--started-at", required=True)
    finish.add_argument("--engine", required=True)
    finish.add_argument("--state", choices=(PASSED, FAILED), required=True)
    finish.add_argument("--source-tex", type=Path, required=True)
    finish.add_argument("--render-pdf", type=Path)
    finish.add_argument("--strict-requested", action="store_true")
    finish.set_defaults(handler=_finish)
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except OSError as exc:
        parser.error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
