from __future__ import annotations

import argparse
import contextlib
import io
import json
import uuid
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from diagnostics import (
        diagnostic_to_dict,
        make_diagnostic,
        make_evidence,
        result_to_json,
    )
    from tools.doc_governor.bootstrap import (  # type: ignore[no-redef]
        build_bootstrap_state,
        ensure_writable_bootstrap_targets,
        resolve_output_paths,
        write_bootstrap_outputs,
    )
    from tools.doc_governor.confirm import confirm_transition
    from tools.doc_governor.evaluate import evaluate_state_file
    from tools.doc_governor.history import (
        show_history,
        summarize_history,
    )
    from tools.doc_governor.init_state import init_official_state
    from tools.doc_governor.preflight import preflight_open_window
    from tools.doc_governor.open_window import open_window
    from tools.doc_governor.window_plan import plan_open_window, sort_round_entities
    from tools.doc_governor.repo_scan import scan_repo
    from tools.doc_governor.render import (
        build_render_diagnostics,
        render_from_payload,
        RENDER_OUTPUT_DIR_NAME,
    )
    from tools.doc_governor.schema import (
        BOOTSTRAP_STATE_PATH,
        OFFICIAL_STATE_PATH,
    )
    from tools.doc_governor.validate import validate_state_file
else:
    from .diagnostics import (
        diagnostic_to_dict,
        make_diagnostic,
        make_evidence,
        result_to_json,
    )
    from .bootstrap import (
        build_bootstrap_state,
        ensure_writable_bootstrap_targets,
        resolve_output_paths,
        write_bootstrap_outputs,
    )
    from .confirm import confirm_transition
    from .evaluate import evaluate_state_file
    from .history import show_history, summarize_history
    from .init_state import init_official_state
    from .preflight import preflight_open_window
    from .open_window import open_window
    from .window_plan import plan_open_window, sort_round_entities
    from .repo_scan import scan_repo
    from .render import (
        build_render_diagnostics,
        render_from_payload,
        RENDER_OUTPUT_DIR_NAME,
    )
    from .schema import BOOTSTRAP_STATE_PATH, OFFICIAL_STATE_PATH
    from .validate import validate_state_file

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="doc-governor")
    subparsers = parser.add_subparsers(dest="command")

    bootstrap_parser = subparsers.add_parser("bootstrap-state")
    bootstrap_parser.add_argument("--repo-root", default=".")
    bootstrap_parser.add_argument("--output")
    bootstrap_parser.add_argument("--report")
    bootstrap_parser.add_argument("--overwrite", action="store_true")

    validate_parser = subparsers.add_parser("validate-state")
    validate_parser.add_argument(
        "--input",
        default="docs/governance/DOC_STATE.bootstrap.yaml",
    )

    evaluate_parser = subparsers.add_parser("evaluate-state")
    evaluate_parser.add_argument(
        "--input",
        default=BOOTSTRAP_STATE_PATH,
    )

    render_parser = subparsers.add_parser("render-report")
    render_parser.add_argument("--evaluate-json")
    render_parser.add_argument("--state")
    render_parser.add_argument(
        "--report-path",
        default=str(Path("docs/governance") / RENDER_OUTPUT_DIR_NAME),
    )
    render_parser.add_argument("--agenda-limit", type=int, default=10)

    confirm_parser = subparsers.add_parser("confirm-transition")
    confirm_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    confirm_parser.add_argument("--entity-type")
    confirm_parser.add_argument("--entity-id")
    confirm_parser.add_argument("--proposed-changes")
    confirm_parser.add_argument("--mode")
    confirm_parser.add_argument("--evidence-ref", action="append")
    confirm_parser.add_argument("--actor")
    confirm_parser.add_argument("--reason")
    confirm_parser.add_argument("--round-id")

    init_state_parser = subparsers.add_parser("init-official-state")
    init_state_parser.add_argument(
        "--bootstrap-input",
        default=BOOTSTRAP_STATE_PATH,
    )
    init_state_parser.add_argument("--dry-run", action="store_true")
    init_state_parser.add_argument("--actor")
    init_state_parser.add_argument("--reason")
    init_state_parser.add_argument("--force-overwrite", action="store_true")

    show_history_parser = subparsers.add_parser("show-history")
    show_history_parser.add_argument(
        "--history",
        default="docs/governance/transition_history.jsonl",
    )
    show_history_parser.add_argument("--entity-type")
    show_history_parser.add_argument("--entity-id")
    show_history_parser.add_argument("--actor")
    show_history_parser.add_argument("--result")
    show_history_parser.add_argument("--limit", default=50, type=int)
    show_history_parser.add_argument("--since")
    show_history_parser.add_argument("--until")

    summarize_history_parser = subparsers.add_parser("summarize-history")
    summarize_history_parser.add_argument(
        "--history",
        default="docs/governance/transition_history.jsonl",
    )
    summarize_history_parser.add_argument("--entity-type")
    summarize_history_parser.add_argument("--entity-id")
    summarize_history_parser.add_argument("--actor")
    summarize_history_parser.add_argument("--result")
    summarize_history_parser.add_argument("--limit", default=20, type=int)
    summarize_history_parser.add_argument("--since")
    summarize_history_parser.add_argument("--until")
    summarize_history_parser.add_argument("--top-rejected", default=10, type=int)

    preflight_parser = subparsers.add_parser("preflight-open-window")
    preflight_parser.add_argument("--state", default="docs/governance/DOC_STATE.yaml")
    preflight_parser.add_argument("--evaluate-json")
    preflight_parser.add_argument("--history", default="docs/governance/transition_history.jsonl")
    preflight_parser.add_argument("--entity-type")
    preflight_parser.add_argument("--entity-id")

    open_parser = subparsers.add_parser("open-window")
    open_parser.add_argument("--state", default="docs/governance/DOC_STATE.yaml")
    open_parser.add_argument("--history", default="docs/governance/transition_history.jsonl")
    open_parser.add_argument("--entity-type")
    open_parser.add_argument("--entity-id")
    open_parser.add_argument("--mode")
    open_parser.add_argument("--actor")
    open_parser.add_argument("--reason")

    plan_parser = subparsers.add_parser("plan-open-window")
    plan_parser.add_argument("--state", default="docs/governance/DOC_STATE.yaml")
    plan_parser.add_argument("--history", default="docs/governance/transition_history.jsonl")
    plan_parser.add_argument("--evaluate-json")
    plan_parser.add_argument("--entity-type")
    plan_parser.add_argument("--entity-id")
    plan_parser.add_argument("--limit", type=int)

    plan_round_parser = subparsers.add_parser("plan-round")
    plan_round_parser.add_argument("--state", default="docs/governance/DOC_STATE.yaml")
    plan_round_parser.add_argument("--history", default="docs/governance/transition_history.jsonl")
    plan_round_parser.add_argument("--evaluate-json")
    plan_round_parser.add_argument("--entity-type")
    plan_round_parser.add_argument("--entity-id")
    plan_round_parser.add_argument("--limit", type=int)
    plan_round_parser.add_argument("--round-id")

    apply_round_parser = subparsers.add_parser("apply-round")
    apply_round_parser.add_argument("--round-id", required=True)
    apply_round_parser.add_argument("--plan-json")
    apply_round_parser.add_argument("--from-plan")
    apply_round_parser.add_argument("--state", default=OFFICIAL_STATE_PATH)
    apply_round_parser.add_argument("--actor", default="doc-governor-round")
    apply_round_parser.add_argument("--reason", default="apply-round")

    args = parser.parse_args(argv)
    if args.command == "bootstrap-state":
        return bootstrap_state(args)
    if args.command == "validate-state":
        return validate_state(args)
    if args.command == "evaluate-state":
        return evaluate_state_command(args)
    if args.command == "render-report":
        return render_report_command(args)
    if args.command == "confirm-transition":
        return confirm_transition(args)
    if args.command == "init-official-state":
        return init_official_state_command(args)
    if args.command == "show-history":
        return show_history_command(args)
    if args.command == "summarize-history":
        return summarize_history_command(args)
    if args.command == "preflight-open-window":
        return preflight_open_window_command(args)
    if args.command == "open-window":
        return open_window(args)
    if args.command == "plan-open-window":
        return plan_open_window_command(args)
    if args.command == "plan-round":
        return plan_round_command(args)
    if args.command == "apply-round":
        return apply_round_command(args)

    parser.print_help()
    return 1


def bootstrap_state(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    output_path, report_path = resolve_output_paths(
        repo_root=repo_root,
        output=args.output,
        report=args.report,
    )

    diagnostics = ensure_writable_bootstrap_targets(
        repo_root=repo_root,
        output_path=output_path,
        report_path=report_path,
        overwrite=args.overwrite,
    )
    if diagnostics:
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                output_path=output_path.as_posix(),
                report_path=report_path.as_posix(),
            )
        )
        return 1

    try:
        import yaml
    except ImportError as exc:
        diagnostics = [
            _make_yaml_bootstrap_diagnostic(
                code="BOOTSTRAP_PYYAML_UNAVAILABLE",
                message="PyYAML is required for bootstrap operations.",
                path=repo_root.as_posix(),
                ref="import yaml",
                value=str(exc),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                output_path=output_path.as_posix(),
                report_path=report_path.as_posix(),
            )
        )
        return 1

    scan_result = scan_repo(repo_root)
    state, diagnostics = build_bootstrap_state(scan_result)

    if any(item.severity == "error" for item in diagnostics):
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                output_path=output_path.as_posix(),
                report_path=report_path.as_posix(),
                scan_counts=scan_result["counts"],
            )
        )
        return 1

    try:
        write_bootstrap_outputs(
            state=state,
            diagnostics=diagnostics,
            scan_result=scan_result,
            output_path=output_path,
            report_path=report_path,
            yaml_module=yaml,
            overwrite=args.overwrite,
        )
    except OSError as exc:
        diagnostics = diagnostics + [
            _make_yaml_bootstrap_diagnostic(
                code="BOOTSTRAP_WRITE_FAILED",
                message="Failed to write bootstrap outputs.",
                path=output_path.as_posix(),
                ref="write",
                value=str(exc),
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=diagnostics,
                output_path=output_path.as_posix(),
                report_path=report_path.as_posix(),
                scan_counts=scan_result["counts"],
            )
        )
        return 1

    print(
        result_to_json(
            ok=True,
            diagnostics=diagnostics,
            output_path=output_path.as_posix(),
            report_path=report_path.as_posix(),
            scan_counts=scan_result["counts"],
        )
    )
    return 0


def validate_state(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    diagnostics = validate_state_file(input_path)
    has_error = any(item.severity == "error" for item in diagnostics)
    print(result_to_json(ok=not has_error, diagnostics=diagnostics))
    return 1 if has_error else 0


def evaluate_state_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))
    if not isinstance(payload, dict):
        payload = {}
    has_error = any(item.severity == "error" for item in diagnostics)
    print(result_to_json(ok=not has_error, diagnostics=diagnostics, **payload))
    return 1 if has_error else 0


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_report_diagnostics(
    diagnostics: list[Any],
) -> tuple[list[dict[str, Any]], bool]:
    converted: list[dict[str, Any]] = []
    render_input_invalid = False
    for item in diagnostics:
        if isinstance(item, dict):
            converted.append(item)
            if str(item.get("severity", "")).lower() == "error":
                render_input_invalid = True
            continue
        converted_item = diagnostic_to_dict(item)
        converted.append(converted_item)
        if converted_item.get("severity") == "error":
            render_input_invalid = True
    return converted, render_input_invalid


def _is_render_report_path_forbidden(report_path: Path) -> bool:
    governance_root = Path("docs/governance").resolve()
    resolved = report_path.resolve()
    if resolved == (governance_root / "DOC_STATE.yaml").resolve():
        return True
    if resolved == (governance_root / "DOC_STATE.bootstrap.yaml").resolve():
        return True
    try:
        resolved.relative_to(governance_root)
        return False
    except ValueError:
        return True


def render_report_command(args: argparse.Namespace) -> int:
    report_path = Path(args.report_path)
    if _is_render_report_path_forbidden(report_path):
        diagnostics = build_render_diagnostics(
            report_path,
            code="RENDER_REPORT_PATH_FORBIDDEN",
            message="report path must be under docs/governance and not official/bootstrap state files.",
            severity="error",
        )
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    input_payload: dict[str, Any] = {}
    report_input_diagnostics: list[dict[str, Any]] = []
    render_input_invalid = False
    input_incomplete = False

    if args.evaluate_json:
        payload_path = Path(args.evaluate_json)
        try:
            raw_payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            diagnostics = [
                make_diagnostic(
                    code="RENDER_INPUT_FILE_NOT_FOUND",
                    severity="error",
                    entity_type="render",
                    entity_id="GLOBAL",
                    field_path="--evaluate-json",
                    message=f"evaluate json not found: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=payload_path.as_posix(),
                            ref="evaluate-json",
                            value=payload_path.as_posix(),
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        except Exception as exc:
            diagnostics = [
                make_diagnostic(
                    code="RENDER_INPUT_INVALID_JSON",
                    severity="error",
                    entity_type="render",
                    entity_id="GLOBAL",
                    field_path="--evaluate-json",
                    message=f"evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=payload_path.as_posix(),
                            ref="evaluate-json",
                            value=str(exc),
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1

        if isinstance(raw_payload, dict):
            input_payload = raw_payload
            report_input_diagnostics, render_input_invalid = _normalize_report_diagnostics(
                raw_payload.get("diagnostics", [])
            )
        else:
            input_payload = {}
    elif args.state:
        diagnostics, state_payload = evaluate_state_file(Path(args.state))
        input_payload = state_payload if isinstance(state_payload, dict) else {}
        report_input_diagnostics, render_input_invalid = _normalize_report_diagnostics(diagnostics)
    else:
        diagnostics = [
            make_diagnostic(
                code="RENDER_INPUT_REQUIRED",
                severity="error",
                entity_type="render",
                entity_id="GLOBAL",
                field_path="render",
                message="render-report requires --evaluate-json or --state",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="render-report",
                        ref="input",
                        value="none",
                    )
                ],
            )
        ]
        report_input_diagnostics = [diagnostic_to_dict(item) for item in diagnostics]
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    summary = input_payload.get("summary")
    modules = input_payload.get("modules")
    subtasks = input_payload.get("subtasks")
    oqs = input_payload.get("oqs")

    if not isinstance(summary, dict):
        input_incomplete = True
    if not isinstance(modules, dict):
        input_incomplete = True
    if not isinstance(subtasks, dict):
        input_incomplete = True
    if not isinstance(oqs, dict):
        input_incomplete = True

    payload = {
        "summary": summary if isinstance(summary, dict) else {},
        "modules": modules if isinstance(modules, dict) else {},
        "subtasks": subtasks if isinstance(subtasks, dict) else {},
        "oqs": oqs if isinstance(oqs, dict) else {},
        "diagnostics": report_input_diagnostics,
    }
    report_text = render_from_payload(
        payload,
        render_input_invalid=render_input_invalid,
        input_incomplete=input_incomplete,
        agenda_limit=args.agenda_limit,
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_text, encoding="utf-8")

    output_payload = {
        "ok": True,
        **payload,
    }
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def show_history_command(args: argparse.Namespace) -> int:
    payload = show_history(
        history=args.history,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        actor=args.actor,
        result=args.result,
        limit=int(args.limit),
        since=_parse_iso_datetime(args.since),
        until=_parse_iso_datetime(args.until),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def summarize_history_command(args: argparse.Namespace) -> int:
    payload = summarize_history(
        history=args.history,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        actor=args.actor,
        result=args.result,
        limit=int(args.limit),
        since=_parse_iso_datetime(args.since),
        until=_parse_iso_datetime(args.until),
        top_rejected=int(args.top_rejected),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def init_official_state_command(args: argparse.Namespace) -> int:
    code, diagnostics = init_official_state(
        bootstrap_input=args.bootstrap_input,
        dry_run=args.dry_run,
        actor=args.actor,
        reason=args.reason,
        force_overwrite=args.force_overwrite,
    )
    print(
        result_to_json(
            ok=code == 0,
            diagnostics=diagnostics,
            dry_run=args.dry_run,
        )
    )
    return code


def preflight_open_window_command(args: argparse.Namespace) -> int:
    payload = preflight_open_window(
        state=args.state,
        evaluate_json=args.evaluate_json,
        history=args.history,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if not payload.get("ok", False) else 0


def plan_open_window_command(args: argparse.Namespace) -> int:
    payload = plan_open_window(
        state=args.state,
        history=args.history,
        evaluate_json=args.evaluate_json,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        limit=args.limit,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if not payload.get("ok", False) else 0


def plan_round_command(args: argparse.Namespace) -> int:
    preflight_payload = preflight_open_window(
        state=args.state,
        evaluate_json=args.evaluate_json,
        history=args.history,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
    )
    window_plan_payload = plan_open_window(
        state=args.state,
        history=args.history,
        evaluate_json=args.evaluate_json,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        limit=args.limit,
    )

    round_id = args.round_id or f"round-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    must_review = [
        _decorate_round_entity(item, recommended_action="defer")
        for item in sort_round_entities(
            list(window_plan_payload.get("near_open_but_blocked", [])),
        )
    ]
    can_approve_now = [
        _decorate_round_entity(item, recommended_action="approve")
        for item in sort_round_entities(
            list(window_plan_payload.get("eligible_to_apply", [])),
        )
    ]
    blocked_hard = [
        _decorate_round_entity(item, recommended_action="reject")
        for item in sort_round_entities(
            list(window_plan_payload.get("hard_blocked", [])),
        )
    ]
    if args.limit is not None:
        must_review = must_review[: args.limit]
        can_approve_now = can_approve_now[: args.limit]
        blocked_hard = blocked_hard[: args.limit]

    payload = {
        "ok": bool(preflight_payload.get("ok", False)) and bool(window_plan_payload.get("ok", False)),
        "round_id": round_id,
        "state_path": window_plan_payload.get("state_path"),
        "history_path": window_plan_payload.get("history_path"),
        "evaluation_source": window_plan_payload.get("evaluation_source"),
        "scope": window_plan_payload.get("scope", {}),
        "queues": {
            "must_review": must_review,
            "can_approve_now": can_approve_now,
            "blocked_hard": blocked_hard,
        },
        "summary": {
            "must_review_count": len(must_review),
            "can_approve_now_count": len(can_approve_now),
            "blocked_hard_count": len(blocked_hard),
            "entities_scanned": window_plan_payload.get("summary", {}).get("entities_scanned", 0),
        },
        "parse_errors": window_plan_payload.get("parse_errors", []),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if not payload["ok"] else 0


def apply_round_command(args: argparse.Namespace) -> int:
    if bool(args.plan_json) == bool(args.from_plan):
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="APPLY_ROUND_PLAN_INPUT_INVALID",
                        severity="error",
                        entity_type="system",
                        entity_id="GLOBAL",
                        field_path="apply-round",
                        message="provide exactly one of --plan-json or --from-plan",
                        evidence=[],
                    )
                ],
            )
        )
        return 1

    raw_plan = args.plan_json
    if args.from_plan:
        raw_plan = Path(args.from_plan).read_text(encoding="utf-8")
    try:
        plan_payload = json.loads(raw_plan or "{}")
    except json.JSONDecodeError as exc:
        print(result_to_json(ok=False, diagnostics=[make_diagnostic(
            code="APPLY_ROUND_PLAN_PARSE_ERROR",
            severity="error",
            entity_type="system",
            entity_id="GLOBAL",
            field_path="plan",
            message=f"plan json parse failed: {exc}",
            evidence=[],
        )]))
        return 1

    if str(plan_payload.get("round_id")) != str(args.round_id):
        print(result_to_json(ok=False, diagnostics=[make_diagnostic(
            code="APPLY_ROUND_ID_MISMATCH",
            severity="error",
            entity_type="system",
            entity_id="GLOBAL",
            field_path="--round-id",
            message="provided --round-id does not match plan round_id",
            evidence=[],
        )]))
        return 1

    actions = _collect_round_actions(plan_payload)
    results: list[dict[str, Any]] = []
    failed = 0
    skipped = 0
    applied = 0
    for action in actions:
        if action["action"] == "defer":
            skipped += 1
            results.append({**action, "ok": True, "skipped": True})
            continue
        namespace = argparse.Namespace(
            input=args.state,
            entity_type=action["entity_type"],
            entity_id=action["entity_id"],
            proposed_changes=json.dumps(action.get("proposed_changes", {}), ensure_ascii=False),
            mode=action["action"],
            evidence_ref=list(action.get("evidence_refs", [])),
            actor=args.actor,
            reason=args.reason,
        )
        with io.StringIO() as buffer:
            with contextlib.redirect_stdout(buffer):
                code = confirm_transition(namespace)
            confirm_output = buffer.getvalue().strip()
        confirm_payload = {}
        if confirm_output:
            try:
                confirm_payload = json.loads(confirm_output)
            except json.JSONDecodeError:
                confirm_payload = {"raw_output": confirm_output}
        if code == 0:
            applied += 1
        else:
            failed += 1
        results.append({**action, "ok": code == 0, "confirm": confirm_payload})

    ok = failed == 0
    print(
        json.dumps(
            {
                "ok": ok,
                "round_id": args.round_id,
                "state_path": str(Path(args.state).resolve()),
                "summary": {
                    "total": len(actions),
                    "applied": applied,
                    "skipped": skipped,
                    "failed": failed,
                },
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ok else 1


def _decorate_round_entity(item: dict[str, Any], *, recommended_action: str) -> dict[str, Any]:
    payload = dict(item)
    payload["recommended_action"] = recommended_action
    payload["proposed_changes"] = payload.get("proposed_changes", {})
    payload["evidence_refs"] = payload.get("evidence_refs", [])
    return payload


def _collect_round_actions(plan_payload: dict[str, Any]) -> list[dict[str, Any]]:
    queues = plan_payload.get("queues", {})
    if not isinstance(queues, dict):
        return []
    output: list[dict[str, Any]] = []
    for queue_name in ("can_approve_now", "blocked_hard", "must_review"):
        raw_items = queues.get(queue_name, [])
        if not isinstance(raw_items, list):
            continue
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            action = str(item.get("recommended_action", "")).strip().lower()
            if action not in {"approve", "reject", "defer"}:
                continue
            output.append(
                {
                    "queue": queue_name,
                    "entity_type": item.get("entity_type"),
                    "entity_id": item.get("entity_id"),
                    "action": action,
                    "proposed_changes": item.get("proposed_changes", {}),
                    "evidence_refs": item.get("evidence_refs", []),
                }
            )
    return output


def _make_yaml_bootstrap_diagnostic(
    *,
    code: str,
    message: str,
    path: str,
    ref: str,
    value: Any,
) -> Any:
    return make_diagnostic(
        code=code,
        severity="error",
        entity_type="system",
        entity_id="GLOBAL",
        field_path="bootstrap",
        message=message,
        evidence=[
            make_evidence(
                type="dependency",
                path=path,
                ref=ref,
                value=value,
            )
        ],
    )


if __name__ == "__main__":
    sys.exit(main())
