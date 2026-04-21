from __future__ import annotations

import argparse
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.doc_governor.bootstrap import (  # type: ignore[no-redef]
        build_bootstrap_state,
        ensure_writable_bootstrap_targets,
        resolve_output_paths,
        write_bootstrap_outputs,
    )
    from tools.doc_governor.diagnostics import make_diagnostic, make_evidence, result_to_json
    from tools.doc_governor.repo_scan import scan_repo
    from tools.doc_governor.validate import validate_state_file  # type: ignore[no-redef]
else:
    from .bootstrap import (
        build_bootstrap_state,
        ensure_writable_bootstrap_targets,
        resolve_output_paths,
        write_bootstrap_outputs,
    )
    from .diagnostics import make_diagnostic, make_evidence, result_to_json
    from .repo_scan import scan_repo
    from .validate import validate_state_file


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

    args = parser.parse_args(argv)
    if args.command == "bootstrap-state":
        return bootstrap_state(args)
    if args.command == "validate-state":
        return validate_state(args)

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
            make_diagnostic(
                code="BOOTSTRAP_PYYAML_UNAVAILABLE",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="python.dependencies.yaml",
                message="PyYAML is required for bootstrap operations.",
                evidence=[
                    make_evidence(
                        type="derived_check",
                        path=repo_root.as_posix(),
                        ref="import yaml",
                        value=str(exc),
                    )
                ],
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
            make_diagnostic(
                code="BOOTSTRAP_WRITE_FAILED",
                severity="error",
                entity_type="system",
                entity_id="GLOBAL",
                field_path="bootstrap.outputs",
                message="Failed to write bootstrap outputs.",
                evidence=[
                    make_evidence(
                        type="file_scan",
                        path=output_path.as_posix(),
                        ref="write",
                        value=str(exc),
                    )
                ],
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


if __name__ == "__main__":
    sys.exit(main())
