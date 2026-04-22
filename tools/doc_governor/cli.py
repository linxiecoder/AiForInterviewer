from __future__ import annotations

import argparse
import json
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

    confirm_parser = subparsers.add_parser("confirm-transition")
    confirm_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    confirm_parser.add_argument("--entity-type")
    confirm_parser.add_argument("--entity-id")
    confirm_parser.add_argument("--proposed-changes")
    confirm_parser.add_argument("--mode")
    confirm_parser.add_argument("--evidence-ref", action="append")
    confirm_parser.add_argument("--actor")
    confirm_parser.add_argument("--reason")

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
