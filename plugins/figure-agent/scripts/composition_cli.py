from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import candidate_contracts
import composition_acceptance
import composition_apply
import composition_contracts
import composition_families
import composition_generalization
import composition_post_apply_verify
import composition_rank
import composition_render
import composition_review
import composition_review_synthesis
import composition_visual_clash_triage
import fixture_identity
import runtime_paths


def _validate_name(parser: argparse.ArgumentParser, name: str) -> str:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        parser.error(str(exc))
    return name


def _json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _write_output(
    paths: runtime_paths.RuntimePaths,
    name: str,
    value: str | None,
    payload: dict[str, Any],
) -> None:
    if value is None:
        return
    output = candidate_contracts.fixture_local_output_path(
        paths.workspace_root,
        name,
        value,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_fixture_json(paths: runtime_paths.RuntimePaths, name: str, value: str) -> dict[str, Any]:
    path = candidate_contracts.fixture_local_output_path(paths.workspace_root, name, value)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("expected JSON object")
    return payload


def _capture(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-capture")
    parser.add_argument("name")
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--proposal-json", dest="proposal", required=False)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_contracts.capture_composition_candidates(
            name,
            proposal_json_path=Path(args.proposal),
            workspace_root=paths.workspace_root,
        )
        _write_output(paths, name, args.output, payload)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        candidate_contracts.CandidateContractError,
    ) as exc:
        print(f"fig-agent compose-capture: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    if payload.get("status") == "rejected":
        print(f"fig-agent compose-capture: {payload.get('diagnostics')}", file=sys.stderr)
        return 1
    return 0


def _generate_families(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-generate-families")
    parser.add_argument("name")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_families.generate_structural_family_candidates(
            name,
            workspace_root=paths.workspace_root,
        )
        _write_output(paths, name, args.output, payload)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-generate-families: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0 if payload.get("status") == "proposed_unranked" else 1


def _generalization_report(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-generalization-report")
    parser.add_argument("name")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_generalization.write_generalization_report(
            name,
            output_path=args.output,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-generalization-report: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def _render(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-render")
    parser.add_argument("name")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--candidate-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        candidate_set = _load_fixture_json(paths, name, args.candidate_set)
        payload = composition_render.prepare_composition_render(
            name,
            candidate_set=candidate_set,
            workspace_root=paths.workspace_root,
            candidate_set_path=Path(args.candidate_set),
            candidate_id=args.candidate_id,
        )
    except (
        RuntimeError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        composition_render.CompositionRenderError,
    ) as exc:
        print(f"fig-agent compose-render: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    if payload.get("status") != "prepared":
        print(f"fig-agent compose-render: {payload.get('diagnostics')}", file=sys.stderr)
        return 1
    return 0


def _rank(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-rank")
    parser.add_argument("name")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_rank.rank_composition_candidates(
            name,
            candidate_set=_load_fixture_json(paths, name, args.candidate_set),
            workspace_root=paths.workspace_root,
        )
        _write_output(paths, name, args.output, payload)
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-rank: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    if payload.get("status") != "ranked":
        print(f"fig-agent compose-rank: {payload.get('diagnostics')}", file=sys.stderr)
        return 1
    return 0


def _review(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-review")
    parser.add_argument("name")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_review.build_composition_review_packet(
            name,
            candidate_set=_load_fixture_json(paths, name, args.candidate_set),
            candidate_id=args.candidate_id,
            workspace_root=paths.workspace_root,
            candidate_set_path=Path(args.candidate_set),
            write_visual_metrics=True,
        )
        _write_output(paths, name, args.output, payload)
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-review: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def _review_synthesis(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-review-synthesis")
    parser.add_argument("name")
    parser.add_argument("--review-packet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_review_synthesis.write_review_synthesis(
            name,
            review_packet_path=args.review_packet,
            output_path=args.output,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-review-synthesis: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def _apply_ready(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-apply-ready")
    parser.add_argument("name")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_acceptance.build_composition_apply_readiness(
            name,
            args.candidate_id,
            candidate_set=_load_fixture_json(paths, name, args.candidate_set),
            candidate_set_path=Path(args.candidate_set),
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-apply-ready: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    if payload.get("status") != "ready_for_local_acceptance":
        print(f"fig-agent compose-apply-ready: {payload.get('blocking_reasons')}", file=sys.stderr)
        return 1
    return 0


def _accept(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-accept")
    parser.add_argument("name")
    parser.add_argument("positional_candidate_id", nargs="?")
    parser.add_argument("--candidate-id")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--decision", default="accept")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--rationale", required=True)
    parser.add_argument("--permission", action="append", default=[])
    parser.add_argument("--permissions-granted", nargs="+", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    candidate_id = args.candidate_id or args.positional_candidate_id
    if candidate_id is None:
        parser.error("candidate id is required")
    permissions = [*args.permission, *args.permissions_granted]
    try:
        payload = composition_acceptance.write_composition_acceptance(
            name,
            candidate_id,
            candidate_set=_load_fixture_json(paths, name, args.candidate_set),
            candidate_set_path=Path(args.candidate_set),
            decision=args.decision,
            reviewer=args.reviewer,
            rationale=args.rationale,
            permissions_granted=permissions,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-accept: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def _apply(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-apply")
    parser.add_argument("name")
    parser.add_argument("--candidate-set", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--acceptance")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    acceptance_path = args.acceptance or (
        f"build/candidates/{args.candidate_id}/composition_acceptance.json"
    )
    try:
        candidate_set = _load_fixture_json(paths, name, args.candidate_set)
        acceptance = _load_fixture_json(paths, name, acceptance_path)
        payload = composition_apply.apply_composition_acceptance(
            name,
            args.candidate_id,
            candidate_set=candidate_set,
            candidate_set_path=Path(args.candidate_set),
            acceptance=acceptance,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-apply: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    if payload.get("status") != "applied_unverified":
        print(f"fig-agent compose-apply: {payload.get('diagnostics')}", file=sys.stderr)
        return 1
    return 0


def _post_apply_verify(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-post-apply-verify")
    parser.add_argument("name")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--apply-result", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_post_apply_verify.write_post_apply_visual_receipt(
            name,
            candidate_id=args.candidate_id,
            apply_result_path=args.apply_result,
            output_path=args.output,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-post-apply-verify: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def _visual_clash_triage(paths: runtime_paths.RuntimePaths, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent compose-visual-clash-triage")
    parser.add_argument("name")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    name = _validate_name(parser, args.name)
    try:
        payload = composition_visual_clash_triage.write_visual_clash_triage(
            name,
            receipt_path=args.receipt,
            output_path=args.output,
            workspace_root=paths.workspace_root,
        )
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"fig-agent compose-visual-clash-triage: {exc}", file=sys.stderr)
        return 1
    _json(payload)
    return 0


def dispatch(command: str, argv: list[str], *, paths: runtime_paths.RuntimePaths) -> int:
    handlers = {
        "compose-capture": _capture,
        "compose-generate-families": _generate_families,
        "compose-generalization-report": _generalization_report,
        "compose-render": _render,
        "compose-rank": _rank,
        "compose-review": _review,
        "compose-review-synthesis": _review_synthesis,
        "compose-apply-ready": _apply_ready,
        "compose-accept": _accept,
        "compose-apply": _apply,
        "compose-post-apply-verify": _post_apply_verify,
        "compose-visual-clash-triage": _visual_clash_triage,
    }
    handler = handlers.get(command)
    if handler is None:
        return 2
    return handler(paths, argv)
