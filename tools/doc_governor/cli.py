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
    from tools.doc_governor.diagnostics import (
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
    from tools.doc_governor.evaluate import build_delta_summary, evaluate_state_file
    from tools.doc_governor.codex_packet import generate_codex_packet
    from tools.doc_governor.task_packet import generate_implementation_packet
    from tools.doc_governor.task_adaptation import (
        build_task_adaptation_plan,
        render_task_adaptation_markdown,
        write_task_adaptation_output,
    )
    from tools.doc_governor.requirement_link_suggestions import (
        build_requirement_link_suggestions,
        render_requirement_link_suggestions_markdown,
        write_requirement_link_suggestions_output,
    )
    from tools.doc_governor.requirement_container_seed import (
        build_requirement_container_seed_plan,
        execute_requirement_container_seed,
        write_requirement_container_seed_output,
    )
    from tools.doc_governor.requirement_seed_apply import (
        build_requirement_seed_apply_plan,
        execute_requirement_seed_apply,
        write_requirement_seed_apply_output,
    )
    from tools.doc_governor.requirement_entity_sync import (
        build_requirement_entity_sync_plan,
        execute_requirement_entity_sync,
        write_requirement_entity_sync_output,
    )
    from tools.doc_governor.task_skeleton_seed import (
        build_task_skeleton_seed_plan,
        execute_task_skeleton_seed,
        write_task_skeleton_seed_output,
    )
    from tools.doc_governor.task_doc_state_sync import (
        build_task_doc_state_sync_plan,
        execute_task_doc_state_sync,
        write_task_doc_state_sync_output,
    )
    from tools.doc_governor.task_implementation_state_sync import (
        build_task_implementation_state_sync_plan,
        execute_task_implementation_state_sync,
        write_task_implementation_state_sync_output,
    )
    from tools.doc_governor.task_remediation import (
        build_task_remediation_plan,
        render_task_remediation_markdown,
        write_task_remediation_output,
    )
    from tools.doc_governor.task_readiness_plan import (
        build_task_readiness_plan,
        render_task_readiness_markdown,
        write_task_readiness_output,
    )
    from tools.doc_governor.task_readiness_preview import (
        build_task_readiness_preview,
        render_task_readiness_preview_markdown,
        write_task_readiness_preview_output,
    )
    from tools.doc_governor.task_patch_preview import (
        build_task_patch_preview,
        render_task_patch_preview_markdown,
        write_task_patch_preview_output,
    )
    from tools.doc_governor.task_apply import (
        execute_task_readiness_fix,
        write_task_readiness_fix_plan_output,
    )
    from tools.doc_governor.task_apply_summary import (
        build_task_apply_summary,
        render_task_apply_summary_markdown,
        write_task_apply_summary_output,
    )
    from tools.doc_governor.task_state_apply import execute_task_state_apply
    from tools.doc_governor.task_state_writeback import (
        build_task_state_writeback_preview,
        render_task_state_writeback_markdown,
        write_task_state_writeback_output,
    )
    from tools.doc_governor.task_readiness_state_sync import (
        build_task_readiness_state_sync_preview,
        execute_task_readiness_state_sync,
        render_task_readiness_state_sync_markdown,
        write_task_readiness_state_sync_output,
    )
    from tools.doc_governor.task_formal_window_sync import (
        build_task_formal_window_sync_preview,
        execute_task_formal_window_sync,
        render_task_formal_window_sync_markdown,
        write_task_formal_window_sync_output,
    )
    from tools.doc_governor.task_state_dependency_map import (
        build_task_state_dependency_map,
        render_task_state_dependency_map_markdown,
        write_task_state_dependency_map_output,
    )
    from tools.doc_governor.task_window_bridge import build_task_window_bridge
    from tools.doc_governor.governance_rounds import (
        build_document_round_plan,
        load_state as load_governance_state,
        update_round_status,
    )
    from tools.doc_governor.history import (
        show_history,
        summarize_history,
    )
    from tools.doc_governor.init_state import init_official_state
    from tools.doc_governor.preflight import preflight_open_window
    from tools.doc_governor.open_window import open_window
    from tools.doc_governor.round_template import generate_round_template
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
    from .evaluate import build_delta_summary, evaluate_state_file
    from .codex_packet import generate_codex_packet
    from .task_packet import generate_implementation_packet
    from .task_adaptation import (
        build_task_adaptation_plan,
        render_task_adaptation_markdown,
        write_task_adaptation_output,
    )
    from .requirement_link_suggestions import (
        build_requirement_link_suggestions,
        render_requirement_link_suggestions_markdown,
        write_requirement_link_suggestions_output,
    )
    from .requirement_container_seed import (
        build_requirement_container_seed_plan,
        execute_requirement_container_seed,
        write_requirement_container_seed_output,
    )
    from .requirement_seed_apply import (
        build_requirement_seed_apply_plan,
        execute_requirement_seed_apply,
        write_requirement_seed_apply_output,
    )
    from .requirement_entity_sync import (
        build_requirement_entity_sync_plan,
        execute_requirement_entity_sync,
        write_requirement_entity_sync_output,
    )
    from .task_skeleton_seed import (
        build_task_skeleton_seed_plan,
        execute_task_skeleton_seed,
        write_task_skeleton_seed_output,
    )
    from .task_doc_state_sync import (
        build_task_doc_state_sync_plan,
        execute_task_doc_state_sync,
        write_task_doc_state_sync_output,
    )
    from .task_implementation_state_sync import (
        build_task_implementation_state_sync_plan,
        execute_task_implementation_state_sync,
        write_task_implementation_state_sync_output,
    )
    from .task_remediation import (
        build_task_remediation_plan,
        render_task_remediation_markdown,
        write_task_remediation_output,
    )
    from .task_readiness_plan import (
        build_task_readiness_plan,
        render_task_readiness_markdown,
        write_task_readiness_output,
    )
    from .task_readiness_preview import (
        build_task_readiness_preview,
        render_task_readiness_preview_markdown,
        write_task_readiness_preview_output,
    )
    from .task_patch_preview import (
        build_task_patch_preview,
        render_task_patch_preview_markdown,
        write_task_patch_preview_output,
    )
    from .task_apply import (
        execute_task_readiness_fix,
        write_task_readiness_fix_plan_output,
    )
    from .task_apply_summary import (
        build_task_apply_summary,
        render_task_apply_summary_markdown,
        write_task_apply_summary_output,
    )
    from .task_state_apply import execute_task_state_apply
    from .task_state_writeback import (
        build_task_state_writeback_preview,
        render_task_state_writeback_markdown,
        write_task_state_writeback_output,
    )
    from .task_readiness_state_sync import (
        build_task_readiness_state_sync_preview,
        execute_task_readiness_state_sync,
        render_task_readiness_state_sync_markdown,
        write_task_readiness_state_sync_output,
    )
    from .task_formal_window_sync import (
        build_task_formal_window_sync_preview,
        execute_task_formal_window_sync,
        render_task_formal_window_sync_markdown,
        write_task_formal_window_sync_output,
    )
    from .task_state_dependency_map import (
        build_task_state_dependency_map,
        render_task_state_dependency_map_markdown,
        write_task_state_dependency_map_output,
    )
    from .task_window_bridge import build_task_window_bridge
    from .governance_rounds import (
        build_document_round_plan,
        load_state as load_governance_state,
        update_round_status,
    )
    from .history import show_history, summarize_history
    from .init_state import init_official_state
    from .preflight import preflight_open_window
    from .open_window import open_window
    from .round_template import generate_round_template
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
        default=OFFICIAL_STATE_PATH,
    )
    evaluate_parser.add_argument("--baseline-evaluate-json")
    evaluate_parser.add_argument("--entity-type")
    evaluate_parser.add_argument("--entity-id")

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

    round_template_parser = subparsers.add_parser("generate-round-template")
    round_template_parser.add_argument("--round-id", required=True)
    round_template_parser.add_argument("--state", default="docs/governance/DOC_STATE.yaml")
    round_template_parser.add_argument("--history", default="docs/governance/transition_history.jsonl")
    round_template_parser.add_argument("--evaluate-json")
    round_template_parser.add_argument("--entity-type")
    round_template_parser.add_argument("--entity-id")
    round_template_parser.add_argument("--limit", type=int)
    round_template_parser.add_argument("--from-plan")
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

    update_round_parser = subparsers.add_parser("update-round-status")
    update_round_parser.add_argument("--round-id", required=True)
    update_round_parser.add_argument("--state", default=OFFICIAL_STATE_PATH)
    update_round_parser.add_argument("--status", required=True)
    update_round_parser.add_argument("--actor", required=True)
    update_round_parser.add_argument("--close-reason")
    update_round_parser.add_argument("--decision-ref", action="append")
    update_round_parser.add_argument("--result-summary")

    packet_parser = subparsers.add_parser("generate-codex-packet")
    packet_parser.add_argument("--round-id", required=True)
    packet_parser.add_argument("--state", default=OFFICIAL_STATE_PATH)

    implementation_packet_parser = subparsers.add_parser("generate-implementation-packet")
    implementation_packet_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    implementation_packet_parser.add_argument("--entity-id", required=True)
    implementation_packet_parser.add_argument("--evaluate-json")
    implementation_packet_parser.add_argument("--output-dir")

    adaptation_parser = subparsers.add_parser("plan-task-adaptation")
    adaptation_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    adaptation_parser.add_argument("--entity-id")
    adaptation_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    adaptation_parser.add_argument("--output")
    adaptation_parser.add_argument("--evaluate-json")

    requirement_link_parser = subparsers.add_parser("suggest-requirement-links")
    requirement_link_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    requirement_link_parser.add_argument("--entity-id")
    requirement_link_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    requirement_link_parser.add_argument("--output")

    requirement_container_seed_parser = subparsers.add_parser("apply-requirement-container-seed")
    requirement_container_seed_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    requirement_container_seed_parser.add_argument("--entity-id", action="append")
    requirement_container_seed_parser.add_argument("--apply", action="store_true")
    requirement_container_seed_parser.add_argument("--confirm-manual", action="store_true")
    requirement_container_seed_parser.add_argument("--output-plan")

    requirement_seed_apply_parser = subparsers.add_parser("apply-requirement-seed")
    requirement_seed_apply_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    requirement_seed_apply_parser.add_argument("--entity-id", action="append", required=True)
    requirement_seed_apply_parser.add_argument("--apply", action="store_true")
    requirement_seed_apply_parser.add_argument("--confirm-manual", action="store_true")
    requirement_seed_apply_parser.add_argument("--output-plan")

    requirement_entity_sync_parser = subparsers.add_parser("apply-requirement-entity-sync")
    requirement_entity_sync_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    requirement_entity_sync_parser.add_argument("--entity-id", action="append")
    requirement_entity_sync_parser.add_argument("--apply", action="store_true")
    requirement_entity_sync_parser.add_argument("--output-plan")

    task_skeleton_seed_parser = subparsers.add_parser("apply-task-skeleton-seed")
    task_skeleton_seed_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    task_skeleton_seed_parser.add_argument("--entity-id", action="append", required=True)
    task_skeleton_seed_parser.add_argument("--apply", action="store_true")
    task_skeleton_seed_parser.add_argument("--output-plan")

    task_doc_state_sync_parser = subparsers.add_parser("apply-task-doc-state-sync")
    task_doc_state_sync_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    task_doc_state_sync_parser.add_argument("--entity-id", action="append", required=True)
    task_doc_state_sync_parser.add_argument("--apply", action="store_true")
    task_doc_state_sync_parser.add_argument("--output-plan")

    task_implementation_state_sync_parser = subparsers.add_parser(
        "apply-task-implementation-state-sync"
    )
    task_implementation_state_sync_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    task_implementation_state_sync_parser.add_argument("--evaluate-json")
    task_implementation_state_sync_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
    )
    task_implementation_state_sync_parser.add_argument("--apply", action="store_true")
    task_implementation_state_sync_parser.add_argument("--output-plan")

    remediation_parser = subparsers.add_parser("plan-task-remediation")
    remediation_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    remediation_parser.add_argument("--entity-id")
    remediation_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    remediation_parser.add_argument("--output")
    remediation_parser.add_argument("--evaluate-json")

    readiness_parser = subparsers.add_parser("plan-task-readiness")
    readiness_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    readiness_parser.add_argument("--entity-id")
    readiness_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    readiness_parser.add_argument("--output")
    readiness_parser.add_argument("--evaluate-json")

    readiness_preview_parser = subparsers.add_parser("preview-task-readiness-fix")
    readiness_preview_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    readiness_preview_parser.add_argument("--entity-id")
    readiness_preview_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    readiness_preview_parser.add_argument("--output")

    patch_preview_parser = subparsers.add_parser("preview-task-patches")
    patch_preview_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    patch_preview_parser.add_argument("--entity-id")
    patch_preview_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    patch_preview_parser.add_argument("--output")

    apply_readiness_parser = subparsers.add_parser("apply-task-readiness-fix")
    apply_readiness_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    apply_readiness_parser.add_argument("--entity-id", required=True)
    apply_readiness_parser.add_argument("--apply", action="store_true")
    apply_readiness_parser.add_argument("--output-plan")

    apply_summary_parser = subparsers.add_parser("summarize-task-apply-result")
    apply_summary_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    apply_summary_parser.add_argument("--entity-id", action="append", required=True)
    apply_summary_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    apply_summary_parser.add_argument("--output")
    apply_summary_parser.add_argument("--before-json")

    state_writeback_preview_parser = subparsers.add_parser("preview-task-state-writeback")
    state_writeback_preview_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    state_writeback_preview_parser.add_argument("--entity-id", action="append")
    state_writeback_preview_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    state_writeback_preview_parser.add_argument("--output")
    state_writeback_preview_parser.add_argument("--evaluate-json")

    dependency_map_parser = subparsers.add_parser("preview-task-state-dependency-map")
    dependency_map_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    dependency_map_parser.add_argument("--entity-id", action="append")
    dependency_map_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
    )
    dependency_map_parser.add_argument("--output")
    dependency_map_parser.add_argument("--evaluate-json")

    state_apply_parser = subparsers.add_parser("apply-task-state-writeback")
    state_apply_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    state_apply_parser.add_argument("--entity-id", action="append", required=True)
    state_apply_parser.add_argument("--apply", action="store_true")
    state_apply_parser.add_argument("--actor")
    state_apply_parser.add_argument("--reason")
    state_apply_parser.add_argument("--evaluate-json")

    readiness_state_sync_preview_parser = subparsers.add_parser("preview-task-readiness-state-sync")
    readiness_state_sync_preview_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    readiness_state_sync_preview_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
    )
    readiness_state_sync_preview_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
    )
    readiness_state_sync_preview_parser.add_argument("--output")
    readiness_state_sync_preview_parser.add_argument("--evaluate-json")

    readiness_state_sync_apply_parser = subparsers.add_parser("apply-task-readiness-state-sync")
    readiness_state_sync_apply_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    readiness_state_sync_apply_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
    )
    readiness_state_sync_apply_parser.add_argument("--apply", action="store_true")
    readiness_state_sync_apply_parser.add_argument("--actor")
    readiness_state_sync_apply_parser.add_argument("--reason")
    readiness_state_sync_apply_parser.add_argument("--evaluate-json")

    formal_window_sync_preview_parser = subparsers.add_parser("preview-task-formal-window-sync")
    formal_window_sync_preview_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    formal_window_sync_preview_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
    )
    formal_window_sync_preview_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
    )
    formal_window_sync_preview_parser.add_argument("--output")
    formal_window_sync_preview_parser.add_argument("--evaluate-json")

    formal_window_sync_apply_parser = subparsers.add_parser("apply-task-formal-window-sync")
    formal_window_sync_apply_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    formal_window_sync_apply_parser.add_argument(
        "--entity-id",
        action="append",
        required=True,
    )
    formal_window_sync_apply_parser.add_argument("--apply", action="store_true")
    formal_window_sync_apply_parser.add_argument("--actor")
    formal_window_sync_apply_parser.add_argument("--reason")
    formal_window_sync_apply_parser.add_argument("--evaluate-json")

    task_window_bridge_parser = subparsers.add_parser("plan-task-window-candidates")
    task_window_bridge_parser.add_argument("--input", default=OFFICIAL_STATE_PATH)
    task_window_bridge_parser.add_argument("--entity-id", action="append")
    task_window_bridge_parser.add_argument(
        "--format", choices=("json", "markdown"), default="json"
    )
    task_window_bridge_parser.add_argument("--output")

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
    if args.command == "generate-round-template":
        return generate_round_template_command(args)
    if args.command == "plan-round":
        return plan_round_command(args)
    if args.command == "apply-round":
        return apply_round_command(args)
    if args.command == "update-round-status":
        return update_round_status_command(args)
    if args.command == "generate-codex-packet":
        return generate_codex_packet_command(args)
    if args.command == "generate-implementation-packet":
        return generate_implementation_packet_command(args)
    if args.command == "plan-task-adaptation":
        return plan_task_adaptation_command(args)
    if args.command == "suggest-requirement-links":
        return suggest_requirement_links_command(args)
    if args.command == "apply-requirement-container-seed":
        return apply_requirement_container_seed_command(args)
    if args.command == "apply-requirement-seed":
        return apply_requirement_seed_command(args)
    if args.command == "apply-requirement-entity-sync":
        return apply_requirement_entity_sync_command(args)
    if args.command == "apply-task-skeleton-seed":
        return apply_task_skeleton_seed_command(args)
    if args.command == "apply-task-doc-state-sync":
        return apply_task_doc_state_sync_command(args)
    if args.command == "apply-task-implementation-state-sync":
        return apply_task_implementation_state_sync_command(args)
    if args.command == "plan-task-remediation":
        return plan_task_remediation_command(args)
    if args.command == "plan-task-readiness":
        return plan_task_readiness_command(args)
    if args.command == "preview-task-readiness-fix":
        return preview_task_readiness_fix_command(args)
    if args.command == "preview-task-patches":
        return preview_task_patches_command(args)
    if args.command == "apply-task-readiness-fix":
        return apply_task_readiness_fix_command(args)
    if args.command == "summarize-task-apply-result":
        return summarize_task_apply_result_command(args)
    if args.command == "preview-task-state-writeback":
        return preview_task_state_writeback_command(args)
    if args.command == "apply-task-state-writeback":
        return apply_task_state_writeback_command(args)
    if args.command == "preview-task-readiness-state-sync":
        return preview_task_readiness_state_sync_command(args)
    if args.command == "apply-task-readiness-state-sync":
        return apply_task_readiness_state_sync_command(args)
    if args.command == "preview-task-formal-window-sync":
        return preview_task_formal_window_sync_command(args)
    if args.command == "apply-task-formal-window-sync":
        return apply_task_formal_window_sync_command(args)
    if args.command == "preview-task-state-dependency-map":
        return preview_task_state_dependency_map_command(args)
    if args.command == "plan-task-window-candidates":
        return plan_task_window_candidates_command(args)

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
    if args.baseline_evaluate_json:
        baseline_path = Path(args.baseline_evaluate_json)
        try:
            baseline_raw = json.loads(baseline_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            diagnostics.append(
                make_diagnostic(
                    code="EVALUATE_BASELINE_FILE_NOT_FOUND",
                    severity="error",
                    entity_type="evaluate",
                    entity_id="GLOBAL",
                    field_path="--baseline-evaluate-json",
                    message=f"baseline evaluate json not found: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=baseline_path.as_posix(),
                            ref="baseline-evaluate-json",
                            value=baseline_path.as_posix(),
                        )
                    ],
                )
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                make_diagnostic(
                    code="EVALUATE_BASELINE_INVALID_JSON",
                    severity="error",
                    entity_type="evaluate",
                    entity_id="GLOBAL",
                    field_path="--baseline-evaluate-json",
                    message=f"baseline evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=baseline_path.as_posix(),
                            ref="baseline-evaluate-json",
                            value=str(exc),
                        )
                    ],
                )
            )
        else:
            baseline_payload = baseline_raw if isinstance(baseline_raw, dict) else {}
            payload["delta_summary"] = build_delta_summary(
                current_payload=payload,
                baseline_payload=baseline_payload,
            )
    filtered_payload, filter_diagnostics = _filter_evaluate_payload(
        payload=payload,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
    )
    diagnostics.extend(filter_diagnostics)
    payload = filtered_payload
    has_error = any(item.severity == "error" for item in diagnostics)
    print(result_to_json(ok=not has_error, diagnostics=diagnostics, **payload))
    return 1 if has_error else 0


def _filter_evaluate_payload(
    *,
    payload: dict[str, Any],
    entity_type: str | None,
    entity_id: str | None,
) -> tuple[dict[str, Any], list[Any]]:
    diagnostics: list[Any] = []
    normalized_type = _normalize_evaluate_entity_type(entity_type)
    if entity_type and normalized_type is None:
        diagnostics.append(
            make_diagnostic(
                code="EVALUATE_ENTITY_TYPE_INVALID",
                severity="error",
                entity_type="evaluate",
                entity_id="GLOBAL",
                field_path="--entity-type",
                message="entity-type must be requirement, module, task, or subtask",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--entity-type",
                        ref="value",
                        value=entity_type,
                    )
                ],
            )
        )
        return payload, diagnostics

    filtered = dict(payload)
    for key in ("requirements", "modules", "subtasks"):
        value = payload.get(key)
        filtered[key] = value if isinstance(value, dict) else {}

    if normalized_type:
        for key in ("requirements", "modules", "subtasks"):
            if key != normalized_type:
                filtered[key] = {}

    if not entity_id:
        return filtered, diagnostics

    if normalized_type:
        target_map = filtered.get(normalized_type)
        target_map = target_map if isinstance(target_map, dict) else {}
        if entity_id not in target_map:
            diagnostics.append(
                make_diagnostic(
                    code="EVALUATE_ENTITY_NOT_FOUND",
                    severity="error",
                    entity_type="evaluate",
                    entity_id=entity_id,
                    field_path="--entity-id",
                    message="entity-id not found in evaluate payload",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="--entity-id",
                            ref="value",
                            value=entity_id,
                        )
                    ],
                )
            )
            return filtered, diagnostics
        filtered[normalized_type] = {entity_id: target_map[entity_id]}
        return filtered, diagnostics

    matches = {
        key: {entity_id: value[entity_id]}
        for key, value in (
            ("requirements", filtered.get("requirements", {})),
            ("modules", filtered.get("modules", {})),
            ("subtasks", filtered.get("subtasks", {})),
        )
        if isinstance(value, dict) and entity_id in value
    }
    if not matches:
        diagnostics.append(
            make_diagnostic(
                code="EVALUATE_ENTITY_NOT_FOUND",
                severity="error",
                entity_type="evaluate",
                entity_id=entity_id,
                field_path="--entity-id",
                message="entity-id not found in evaluate payload",
                evidence=[
                    make_evidence(
                        type="cli",
                        path="--entity-id",
                        ref="value",
                        value=entity_id,
                    )
                ],
            )
        )
        return filtered, diagnostics
    for key in ("requirements", "modules", "subtasks"):
        filtered[key] = matches.get(key, {})
    return filtered, diagnostics


def _normalize_evaluate_entity_type(entity_type: str | None) -> str | None:
    if entity_type is None:
        return None
    normalized = str(entity_type).strip().lower()
    if normalized == "":
        return None
    if normalized == "task":
        return "subtasks"
    if normalized == "subtask":
        return "subtasks"
    if normalized == "module":
        return "modules"
    if normalized == "requirement":
        return "requirements"
    return None


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
    requirements = input_payload.get("requirements")
    modules = input_payload.get("modules")
    subtasks = input_payload.get("subtasks")
    documents = input_payload.get("documents")
    oqs = input_payload.get("oqs")
    governance_rounds = input_payload.get("governance_rounds")
    delta_summary = input_payload.get("delta_summary")

    if not isinstance(summary, dict):
        input_incomplete = True
    if not isinstance(modules, dict):
        input_incomplete = True
    if not isinstance(subtasks, dict):
        input_incomplete = True
    if "documents" in input_payload and not isinstance(documents, dict):
        input_incomplete = True
    if not isinstance(oqs, dict):
        input_incomplete = True

    payload = {
        "summary": summary if isinstance(summary, dict) else {},
        "requirements": requirements if isinstance(requirements, dict) else {},
        "modules": modules if isinstance(modules, dict) else {},
        "subtasks": subtasks if isinstance(subtasks, dict) else {},
        "documents": documents if isinstance(documents, dict) else {},
        "oqs": oqs if isinstance(oqs, dict) else {},
        "governance_rounds": governance_rounds if isinstance(governance_rounds, list) else [],
        "delta_summary": delta_summary if isinstance(delta_summary, dict) else {},
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


def _load_round_evaluate_payload(*, state: str, evaluate_json: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    if evaluate_json:
        payload_path = Path(evaluate_json)
        try:
            raw_payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                {
                    "code": "ROUND_EVALUATE_JSON_INVALID",
                    "severity": "error",
                    "field_path": "--evaluate-json",
                    "message": f"evaluate json parse failed: {exc}",
                }
            )
            return diagnostics, {}
        return diagnostics, raw_payload if isinstance(raw_payload, dict) else {}

    eval_diags, payload = evaluate_state_file(Path(state))
    diagnostics.extend(diagnostic_to_dict(item) for item in eval_diags)
    return diagnostics, payload if isinstance(payload, dict) else {}


def generate_round_template_command(args: argparse.Namespace) -> int:
    plan_payload: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = []
    if args.from_plan:
        plan_payload = json.loads(Path(args.from_plan).read_text(encoding="utf-8"))
    elif args.entity_type == "document":
        state = load_governance_state(args.state)
        eval_diagnostics, evaluate_payload = _load_round_evaluate_payload(
            state=args.state,
            evaluate_json=args.evaluate_json,
        )
        diagnostics.extend(eval_diagnostics)
        if any(item.get("severity") == "error" for item in diagnostics):
            print(json.dumps({"ok": False, "diagnostics": diagnostics}, ensure_ascii=False, indent=2))
            return 1
        plan_payload = build_document_round_plan(
            round_id=args.round_id,
            evaluate_payload=evaluate_payload,
            state=state,
            entity_id=args.entity_id,
        )
    payload = generate_round_template(
        round_id=args.round_id,
        state=args.state,
        history=args.history,
        evaluate_json=args.evaluate_json,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        limit=args.limit,
        plan_payload=plan_payload,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if not payload.get("ok", False) else 0


def plan_round_command(args: argparse.Namespace) -> int:
    if args.entity_type == "document":
        state = load_governance_state(args.state)
        diagnostics, evaluate_payload = _load_round_evaluate_payload(
            state=args.state,
            evaluate_json=args.evaluate_json,
        )
        if any(item.get("severity") == "error" for item in diagnostics):
            print(json.dumps({"ok": False, "diagnostics": diagnostics}, ensure_ascii=False, indent=2))
            return 1
        round_id = args.round_id or f"round-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
        payload = build_document_round_plan(
            round_id=round_id,
            evaluate_payload=evaluate_payload,
            state=state,
            entity_id=args.entity_id,
        )
        payload["diagnostics"] = diagnostics
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if not payload.get("ok", False) else 0

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


def update_round_status_command(args: argparse.Namespace) -> int:
    try:
        round_entry = update_round_status(
            state_path=args.state,
            round_id=args.round_id,
            status=args.status,
            actor=args.actor,
            close_reason=args.close_reason,
            decision_refs=list(args.decision_ref or []),
            result_summary=args.result_summary,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "diagnostics": [{"code": "ROUND_STATUS_UPDATE_FAILED", "severity": "error", "message": str(exc)}]}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "round": round_entry}, ensure_ascii=False, indent=2))
    return 0


def generate_codex_packet_command(args: argparse.Namespace) -> int:
    try:
        payload = generate_codex_packet(
            state_path=args.state,
            round_id=args.round_id,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "diagnostics": [{"code": "CODEX_PACKET_GENERATION_FAILED", "severity": "error", "message": str(exc)}]}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def generate_implementation_packet_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        evaluate_path = Path(args.evaluate_json)
        try:
            raw_payload = json.loads(evaluate_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            diagnostics.append(
                make_diagnostic(
                    code="IMPLEMENTATION_PACKET_EVALUATE_JSON_NOT_FOUND",
                    severity="error",
                    entity_type="subtask",
                    entity_id=args.entity_id,
                    field_path="--evaluate-json",
                    message=f"evaluate json not found: {evaluate_path}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=evaluate_path.as_posix(),
                            ref="exists",
                            value=False,
                        )
                    ],
                )
            )
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        except json.JSONDecodeError as exc:
            diagnostics.append(
                make_diagnostic(
                    code="IMPLEMENTATION_PACKET_EVALUATE_JSON_INVALID",
                    severity="error",
                    entity_type="subtask",
                    entity_id=args.entity_id,
                    field_path="--evaluate-json",
                    message=f"evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=evaluate_path.as_posix(),
                            ref="json.parse",
                            value=str(exc),
                        )
                    ],
                )
            )
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    filtered_payload, filter_diagnostics = _filter_evaluate_payload(
        payload=payload if isinstance(payload, dict) else {},
        entity_type="task",
        entity_id=args.entity_id,
    )
    diagnostics.extend(filter_diagnostics)
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    derived = (
        _as_dict(filtered_payload.get("subtasks"))
        .get(args.entity_id, {})
        .get("derived", {})
    )
    derived = derived if isinstance(derived, dict) else {}
    if not bool(derived.get("implementation_ready")):
        blocker_refs = derived.get("blocker_refs")
        blocker_refs = blocker_refs if isinstance(blocker_refs, list) else []
        implementation_blockers = derived.get("implementation_blockers")
        implementation_blockers = (
            implementation_blockers if isinstance(implementation_blockers, list) else []
        )
        refusal = [
            make_diagnostic(
                code="IMPLEMENTATION_PACKET_BLOCKED",
                severity="error",
                entity_type="subtask",
                entity_id=args.entity_id,
                field_path=f"subtasks.{args.entity_id}.derived.implementation_ready",
                message="task is not implementation_ready; packet generation refused",
                evidence=[
                    make_evidence(
                        type="evaluate",
                        path=args.input,
                        ref="blocker_refs",
                        value=blocker_refs,
                    )
                ],
            )
        ]
        print(
            result_to_json(
                ok=False,
                diagnostics=refusal,
                blocker_refs=blocker_refs,
                implementation_blockers=implementation_blockers,
            )
        )
        return 1

    try:
        result = generate_implementation_packet(
            state_path=args.input,
            entity_id=args.entity_id,
            evaluate_payload=filtered_payload,
            output_dir=args.output_dir,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="IMPLEMENTATION_PACKET_GENERATION_FAILED",
                        severity="error",
                        entity_type="subtask",
                        entity_id=args.entity_id,
                        field_path="generate-implementation-packet",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="generate-implementation-packet",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def plan_task_adaptation_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        evaluate_path = Path(args.evaluate_json)
        try:
            raw_payload = json.loads(evaluate_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            diagnostics.append(
                make_diagnostic(
                    code="TASK_ADAPTATION_EVALUATE_JSON_NOT_FOUND",
                    severity="error",
                    entity_type="adaptation",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="--evaluate-json",
                    message=f"evaluate json not found: {evaluate_path}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=evaluate_path.as_posix(),
                            ref="exists",
                            value=False,
                        )
                    ],
                )
            )
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        except json.JSONDecodeError as exc:
            diagnostics.append(
                make_diagnostic(
                    code="TASK_ADAPTATION_EVALUATE_JSON_INVALID",
                    severity="error",
                    entity_type="adaptation",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="--evaluate-json",
                    message=f"evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="file_scan",
                            path=evaluate_path.as_posix(),
                            ref="json.parse",
                            value=str(exc),
                        )
                    ],
                )
            )
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        plan = build_task_adaptation_plan(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_ADAPTATION_PLAN_FAILED",
                        severity="error",
                        entity_type="adaptation",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="plan-task-adaptation",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="plan-task-adaptation",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **plan}
    if args.output:
        write_task_adaptation_output(
            plan=output_payload,
            output_path=args.output,
            output_format=args.format,
        )

    if args.format == "markdown":
        print(render_task_adaptation_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def suggest_requirement_links_command(args: argparse.Namespace) -> int:
    try:
        payload = build_requirement_link_suggestions(
            state_path=args.input,
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="REQUIREMENT_LINK_SUGGESTION_FAILED",
                        severity="error",
                        entity_type="requirement_link",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="suggest-requirement-links",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="suggest-requirement-links",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [], **payload}
    if args.output:
        write_requirement_link_suggestions_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_requirement_link_suggestions_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_requirement_container_seed_command(args: argparse.Namespace) -> int:
    diagnostics = validate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_requirement_container_seed(
            state_path=args.input,
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
            allow_manual_confirmation=bool(args.confirm_manual),
        )
    except ValueError as exc:
        dry_run_plan = build_requirement_container_seed_plan(
            state_path=args.input,
            entity_ids=args.entity_id,
            allow_manual_confirmation=bool(args.confirm_manual),
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="REQUIREMENT_CONTAINER_SEED_APPLY_REJECTED",
                        severity="error",
                        entity_type="requirement_container_seed",
                        entity_id=",".join(args.entity_id or []),
                        field_path="apply-requirement-container-seed",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-requirement-container-seed",
                                ref="entity_id",
                                value=args.entity_id or [],
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_requirement_container_seed_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_requirement_container_seed_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_requirement_seed_command(args: argparse.Namespace) -> int:
    diagnostics = validate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_requirement_seed_apply(
            state_path=args.input,
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
            allow_manual_confirmation=bool(args.confirm_manual),
        )
    except ValueError as exc:
        dry_run_plan = build_requirement_seed_apply_plan(
            state_path=args.input,
            entity_ids=args.entity_id,
            allow_manual_confirmation=bool(args.confirm_manual),
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="REQUIREMENT_SEED_APPLY_REJECTED",
                        severity="error",
                        entity_type="requirement_seed_apply",
                        entity_id=",".join(args.entity_id),
                        field_path="apply-requirement-seed",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-requirement-seed",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_requirement_seed_apply_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_requirement_seed_apply_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_requirement_entity_sync_command(args: argparse.Namespace) -> int:
    diagnostics = validate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_requirement_entity_sync(
            state_path=args.input,
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
        )
    except ValueError as exc:
        dry_run_plan = build_requirement_entity_sync_plan(
            state_path=args.input,
            entity_ids=args.entity_id,
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="REQUIREMENT_ENTITY_SYNC_APPLY_REJECTED",
                        severity="error",
                        entity_type="requirement_entity_sync",
                        entity_id=",".join(args.entity_id or []),
                        field_path="apply-requirement-entity-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-requirement-entity-sync",
                                ref="entity_id",
                                value=args.entity_id or [],
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_requirement_entity_sync_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_requirement_entity_sync_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_skeleton_seed_command(args: argparse.Namespace) -> int:
    diagnostics = validate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_skeleton_seed(
            state_path=args.input,
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
        )
    except ValueError as exc:
        dry_run_plan = build_task_skeleton_seed_plan(
            state_path=args.input,
            entity_ids=args.entity_id,
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_SKELETON_SEED_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_skeleton_seed",
                        entity_id=",".join(args.entity_id or []),
                        field_path="apply-task-skeleton-seed",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-skeleton-seed",
                                ref="entity_id",
                                value=args.entity_id or [],
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_task_skeleton_seed_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_task_skeleton_seed_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_doc_state_sync_command(args: argparse.Namespace) -> int:
    diagnostics = validate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_doc_state_sync(
            state_path=args.input,
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
        )
    except ValueError as exc:
        dry_run_plan = build_task_doc_state_sync_plan(
            state_path=args.input,
            entity_ids=args.entity_id,
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_DOC_STATE_SYNC_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_doc_state_sync",
                        entity_id=",".join(args.entity_id or []),
                        field_path="apply-task-doc-state-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-doc-state-sync",
                                ref="entity_id",
                                value=args.entity_id or [],
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_task_doc_state_sync_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_task_doc_state_sync_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_implementation_state_sync_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if getattr(args, "evaluate_json", None):
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_IMPLEMENTATION_STATE_SYNC_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_implementation_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-implementation-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_IMPLEMENTATION_STATE_SYNC_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_implementation_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-implementation-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
            )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_implementation_state_sync(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
        )
    except ValueError as exc:
        try:
            dry_run_plan = build_task_implementation_state_sync_plan(
                state_path=args.input,
                evaluate_payload=payload if isinstance(payload, dict) else {},
                entity_ids=args.entity_id,
            )
        except ValueError:
            dry_run_plan = None
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_IMPLEMENTATION_STATE_SYNC_REJECTED",
                        severity="error",
                        entity_type="task_implementation_state_sync",
                        entity_id="GLOBAL",
                        field_path="apply-task-implementation-state-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-implementation-state-sync",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan and dry_run_plan is not None:
            write_task_implementation_state_sync_output(
                payload=dry_run_plan,
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {
        "ok": True,
        "diagnostics": [diagnostic_to_dict(item) for item in diagnostics],
        **result,
    }
    if args.output_plan:
        write_task_implementation_state_sync_output(
            payload=output_payload,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def plan_task_remediation_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            diagnostics = [
                make_diagnostic(
                    code="TASK_REMEDIATION_EVALUATE_JSON_NOT_FOUND",
                    severity="error",
                    entity_type="remediation",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="plan-task-remediation",
                    message=f"evaluate json not found: {args.evaluate_json}",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="plan-task-remediation",
                            ref="evaluate_json",
                            value=args.evaluate_json,
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        except json.JSONDecodeError as exc:
            diagnostics = [
                make_diagnostic(
                    code="TASK_REMEDIATION_EVALUATE_JSON_INVALID",
                    severity="error",
                    entity_type="remediation",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="plan-task-remediation",
                    message=f"evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="plan-task-remediation",
                            ref="evaluate_json",
                            value=args.evaluate_json,
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        plan = build_task_remediation_plan(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_REMEDIATION_PLAN_FAILED",
                        severity="error",
                        entity_type="remediation",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="plan-task-remediation",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="plan-task-remediation",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **plan}
    if args.output:
        write_task_remediation_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_remediation_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def plan_task_readiness_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            diagnostics = [
                make_diagnostic(
                    code="TASK_READINESS_EVALUATE_JSON_NOT_FOUND",
                    severity="error",
                    entity_type="readiness",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="plan-task-readiness",
                    message=f"evaluate json not found: {args.evaluate_json}",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="plan-task-readiness",
                            ref="evaluate_json",
                            value=args.evaluate_json,
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        except json.JSONDecodeError as exc:
            diagnostics = [
                make_diagnostic(
                    code="TASK_READINESS_EVALUATE_JSON_INVALID",
                    severity="error",
                    entity_type="readiness",
                    entity_id=args.entity_id or "GLOBAL",
                    field_path="plan-task-readiness",
                    message=f"evaluate json parse failed: {exc}",
                    evidence=[
                        make_evidence(
                            type="cli",
                            path="plan-task-readiness",
                            ref="evaluate_json",
                            value=args.evaluate_json,
                        )
                    ],
                )
            ]
            print(result_to_json(ok=False, diagnostics=diagnostics))
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        plan = build_task_readiness_plan(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_READINESS_PLAN_FAILED",
                        severity="error",
                        entity_type="readiness",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="plan-task-readiness",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="plan-task-readiness",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **plan}
    if args.output:
        write_task_readiness_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_readiness_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_readiness_fix_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_readiness_preview(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_READINESS_PREVIEW_FAILED",
                        severity="error",
                        entity_type="readiness_preview",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="preview-task-readiness-fix",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-readiness-fix",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **preview}
    if args.output:
        write_task_readiness_preview_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_readiness_preview_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_patches_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_patch_preview(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_PATCH_PREVIEW_FAILED",
                        severity="error",
                        entity_type="task_patch_preview",
                        entity_id=args.entity_id or "GLOBAL",
                        field_path="preview-task-patches",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-patches",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **preview}
    if args.output:
        write_task_patch_preview_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_patch_preview_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_readiness_fix_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_readiness_fix(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
            apply_changes=bool(args.apply),
        )
    except ValueError as exc:
        dry_run_plan = execute_task_readiness_fix(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_id=args.entity_id,
            apply_changes=False,
        )
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_READINESS_FIX_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_apply",
                        entity_id=args.entity_id,
                        field_path="apply-task-readiness-fix",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-readiness-fix",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
            "plan": dry_run_plan,
        }
        if args.output_plan:
            write_task_readiness_fix_plan_output(
                payload=output_payload["plan"],
                output_path=args.output_plan,
            )
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    if args.output_plan:
        write_task_readiness_fix_plan_output(
            payload=result,
            output_path=args.output_plan,
        )
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def summarize_task_apply_result_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    before_payload: dict[str, Any] | None = None
    if args.before_json:
        try:
            raw_before = json.loads(Path(args.before_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_APPLY_SUMMARY_BEFORE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_apply_summary",
                            entity_id="GLOBAL",
                            field_path="--before-json",
                            message=f"before json not found: {args.before_json}",
                            evidence=[make_evidence(type="cli", path="summarize-task-apply-result", ref="before_json", value=args.before_json)],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_APPLY_SUMMARY_BEFORE_JSON_INVALID",
                            severity="error",
                            entity_type="task_apply_summary",
                            entity_id="GLOBAL",
                            field_path="--before-json",
                            message=f"before json parse failed: {exc}",
                            evidence=[make_evidence(type="cli", path="summarize-task-apply-result", ref="before_json", value=args.before_json)],
                        )
                    ],
                )
            )
            return 1
        before_payload = raw_before if isinstance(raw_before, dict) else None

    try:
        summary = build_task_apply_summary(
            state_path=args.input,
            after_evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
            before_payload=before_payload,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_APPLY_SUMMARY_FAILED",
                        severity="error",
                        entity_type="task_apply_summary",
                        entity_id="GLOBAL",
                        field_path="summarize-task-apply-result",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="summarize-task-apply-result",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **summary}
    if args.output:
        write_task_apply_summary_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_apply_summary_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_state_writeback_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_WRITEBACK_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_state_writeback",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-state-writeback",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_WRITEBACK_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_state_writeback",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-state-writeback",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_state_writeback_preview(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_STATE_WRITEBACK_PREVIEW_FAILED",
                        severity="error",
                        entity_type="task_state_writeback",
                        entity_id="GLOBAL",
                        field_path="preview-task-state-writeback",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-state-writeback",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **preview}
    if args.output:
        write_task_state_writeback_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_state_writeback_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_state_writeback_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_APPLY_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_state_apply",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-state-writeback",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_APPLY_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_state_apply",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-state-writeback",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_state_apply(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
            actor=args.actor,
            reason=args.reason,
        )
    except ValueError as exc:
        try:
            dry_run_plan = execute_task_state_apply(
                state_path=args.input,
                evaluate_payload=payload if isinstance(payload, dict) else {},
                entity_ids=args.entity_id,
                apply_changes=False,
                actor=None,
                reason=None,
            )
        except ValueError:
            dry_run_plan = None
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_STATE_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_state_apply",
                        entity_id="GLOBAL",
                        field_path="apply-task-state-writeback",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-state-writeback",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
        }
        if dry_run_plan is not None:
            output_payload["plan"] = dry_run_plan
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_readiness_state_sync_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_READINESS_STATE_SYNC_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_readiness_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-readiness-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_READINESS_STATE_SYNC_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_readiness_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-readiness-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_readiness_state_sync_preview(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_READINESS_STATE_SYNC_PREVIEW_FAILED",
                        severity="error",
                        entity_type="task_readiness_state_sync",
                        entity_id="GLOBAL",
                        field_path="preview-task-readiness-state-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-readiness-state-sync",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **preview}
    if args.output:
        write_task_readiness_state_sync_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_readiness_state_sync_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_readiness_state_sync_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_READINESS_STATE_SYNC_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_readiness_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-readiness-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_READINESS_STATE_SYNC_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_readiness_state_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-readiness-state-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_readiness_state_sync(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
            actor=args.actor,
            reason=args.reason,
        )
    except ValueError as exc:
        try:
            dry_run_plan = execute_task_readiness_state_sync(
                state_path=args.input,
                evaluate_payload=payload if isinstance(payload, dict) else {},
                entity_ids=args.entity_id,
                apply_changes=False,
                actor=None,
                reason=None,
            )
        except ValueError:
            dry_run_plan = None
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_READINESS_STATE_SYNC_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_readiness_state_sync",
                        entity_id="GLOBAL",
                        field_path="apply-task-readiness-state-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-readiness-state-sync",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
        }
        if dry_run_plan is not None:
            output_payload["plan"] = dry_run_plan
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_formal_window_sync_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_FORMAL_WINDOW_SYNC_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_formal_window_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-formal-window-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_FORMAL_WINDOW_SYNC_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_formal_window_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-formal-window-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_formal_window_sync_preview(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_FORMAL_WINDOW_SYNC_PREVIEW_FAILED",
                        severity="error",
                        entity_type="task_formal_window_sync",
                        entity_id="GLOBAL",
                        field_path="preview-task-formal-window-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-formal-window-sync",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **preview}
    if args.output:
        write_task_formal_window_sync_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_formal_window_sync_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def apply_task_formal_window_sync_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_FORMAL_WINDOW_SYNC_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_formal_window_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-formal-window-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_FORMAL_WINDOW_SYNC_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_formal_window_sync",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="apply-task-formal-window-sync",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        result = execute_task_formal_window_sync(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
            apply_changes=bool(args.apply),
            actor=args.actor,
            reason=args.reason,
        )
    except ValueError as exc:
        try:
            dry_run_plan = execute_task_formal_window_sync(
                state_path=args.input,
                evaluate_payload=payload if isinstance(payload, dict) else {},
                entity_ids=args.entity_id,
                apply_changes=False,
                actor=None,
                reason=None,
            )
        except ValueError:
            dry_run_plan = None
        output_payload = {
            "ok": False,
            "diagnostics": [
                diagnostic_to_dict(
                    make_diagnostic(
                        code="TASK_FORMAL_WINDOW_SYNC_APPLY_REJECTED",
                        severity="error",
                        entity_type="task_formal_window_sync",
                        entity_id="GLOBAL",
                        field_path="apply-task-formal-window-sync",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="apply-task-formal-window-sync",
                                ref="entity_id",
                                value=args.entity_id,
                            )
                        ],
                    )
                )
            ],
        }
        if dry_run_plan is not None:
            output_payload["plan"] = dry_run_plan
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        return 1

    output_payload = {"ok": True, "diagnostics": [diagnostic_to_dict(item) for item in diagnostics], **result}
    print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def preview_task_state_dependency_map_command(args: argparse.Namespace) -> int:
    diagnostics: list[Any] = []
    if args.evaluate_json:
        try:
            raw_payload = json.loads(Path(args.evaluate_json).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_DEPENDENCY_MAP_EVALUATE_JSON_NOT_FOUND",
                            severity="error",
                            entity_type="task_state_dependency_map",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json not found: {args.evaluate_json}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-state-dependency-map",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        except json.JSONDecodeError as exc:
            print(
                result_to_json(
                    ok=False,
                    diagnostics=[
                        make_diagnostic(
                            code="TASK_STATE_DEPENDENCY_MAP_EVALUATE_JSON_INVALID",
                            severity="error",
                            entity_type="task_state_dependency_map",
                            entity_id="GLOBAL",
                            field_path="--evaluate-json",
                            message=f"evaluate json parse failed: {exc}",
                            evidence=[
                                make_evidence(
                                    type="cli",
                                    path="preview-task-state-dependency-map",
                                    ref="evaluate_json",
                                    value=args.evaluate_json,
                                )
                            ],
                        )
                    ],
                )
            )
            return 1
        payload = raw_payload if isinstance(raw_payload, dict) else {}
    else:
        diagnostics, payload = evaluate_state_file(Path(args.input))

    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        preview = build_task_state_dependency_map(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_STATE_DEPENDENCY_MAP_PREVIEW_FAILED",
                        severity="error",
                        entity_type="task_state_dependency_map",
                        entity_id="GLOBAL",
                        field_path="preview-task-state-dependency-map",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="preview-task-state-dependency-map",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {
        "ok": True,
        "diagnostics": [diagnostic_to_dict(item) for item in diagnostics],
        **preview,
    }
    if args.output:
        write_task_state_dependency_map_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_state_dependency_map_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def plan_task_window_candidates_command(args: argparse.Namespace) -> int:
    diagnostics, payload = evaluate_state_file(Path(args.input))
    if any(getattr(item, "severity", None) == "error" for item in diagnostics):
        print(result_to_json(ok=False, diagnostics=diagnostics))
        return 1

    try:
        bridge = build_task_window_bridge(
            state_path=args.input,
            evaluate_payload=payload if isinstance(payload, dict) else {},
            entity_ids=args.entity_id,
        )
    except ValueError as exc:
        print(
            result_to_json(
                ok=False,
                diagnostics=[
                    make_diagnostic(
                        code="TASK_WINDOW_BRIDGE_PLAN_FAILED",
                        severity="error",
                        entity_type="task_window_bridge",
                        entity_id="GLOBAL",
                        field_path="plan-task-window-candidates",
                        message=str(exc),
                        evidence=[
                            make_evidence(
                                type="cli",
                                path="plan-task-window-candidates",
                                ref="entity_id",
                                value=args.entity_id or "ALL",
                            )
                        ],
                    )
                ],
            )
        )
        return 1

    output_payload = {
        "ok": True,
        "diagnostics": [diagnostic_to_dict(item) for item in diagnostics],
        **bridge,
    }
    if args.output:
        write_task_window_bridge_output(
            payload=output_payload,
            output_path=args.output,
            output_format=args.format,
        )
    if args.format == "markdown":
        print(render_task_window_bridge_markdown(output_payload), end="")
    else:
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
    return 0


def render_task_window_bridge_markdown(payload: dict[str, Any]) -> str:
    summary = _as_dict(payload.get("summary"))
    confidence = _as_dict(payload.get("confidence"))
    candidate_tasks = _as_list_of_dicts(payload.get("candidate_tasks_after_state_activation"))
    blocked_tasks = _as_list_of_dicts(payload.get("blocked_before_open_window"))
    next_actions = _as_list_of_dicts(payload.get("recommended_next_step"))
    notes = _as_string_list(payload.get("reasoning_notes"))

    lines = [
        "# 任务开窗候选规划",
        "",
        "## 摘要",
        "",
        f"- 选中 task 数：{summary.get('selected_task_count', 0)}",
        (
            "- state 激活后候选数："
            f"{summary.get('candidate_tasks_after_state_activation_count', 0)}"
        ),
        f"- 开窗前阻断数：{summary.get('blocked_before_open_window_count', 0)}",
        (
            "- 置信度："
            f"{confidence.get('level', 'unknown')} ({confidence.get('score', 'n/a')})"
        ),
        "",
        "## 候选任务",
        "",
    ]
    if candidate_tasks:
        for item in candidate_tasks:
            lines.append(
                "- "
                + _format_task_bridge_item(
                    task_id=str(item.get("task_id", "")).strip(),
                    module_id=str(item.get("module_id", "")).strip(),
                    reason=str(item.get("reason", "")).strip(),
                )
            )
    else:
        lines.append("- 无")

    lines.extend(["", "## 阻断任务", ""])
    if blocked_tasks:
        for item in blocked_tasks:
            lines.append(
                "- "
                + _format_task_bridge_item(
                    task_id=str(item.get("task_id", "")).strip(),
                    module_id=str(item.get("module_id", "")).strip(),
                    reason=str(item.get("reason", "")).strip(),
                )
            )
    else:
        lines.append("- 无")

    lines.extend(["", "## 下一步建议", ""])
    if next_actions:
        for item in next_actions:
            title = str(item.get("title", "")).strip() or "未命名动作"
            reason = str(item.get("reason", "")).strip()
            task_id = str(item.get("task_id", "")).strip()
            module_id = str(item.get("module_id", "")).strip()
            scope = str(item.get("scope", "")).strip() or "task"
            owner = task_id or module_id or "GLOBAL"
            detail = f"{title}：{reason}" if reason else title
            lines.append(f"- [{scope}] {owner} {detail}")
    else:
        lines.append("- 无")

    if notes:
        lines.extend(["", "## 说明", ""])
        lines.extend(f"- {note}" for note in notes)

    return "\n".join(lines) + "\n"


def write_task_window_bridge_output(
    *,
    payload: dict[str, Any],
    output_path: str | Path,
    output_format: str,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if output_format == "markdown":
        content = render_task_window_bridge_markdown(payload)
    else:
        content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    target.write_text(content, encoding="utf-8")


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            output.append(text)
    return output


def _format_task_bridge_item(*, task_id: str, module_id: str, reason: str) -> str:
    owner = task_id or "UNKNOWN"
    if module_id:
        owner = f"{owner} ({module_id})"
    return f"{owner}：{reason}" if reason else owner


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
        reason = args.reason
        if "Decision:" not in reason:
            reason = f"{reason} Decision: batch apply"
        namespace = argparse.Namespace(
            input=args.state,
            entity_type=action["entity_type"],
            entity_id=action["entity_id"],
            proposed_changes=json.dumps(action.get("proposed_changes", {}), ensure_ascii=False),
            mode=action["action"],
            evidence_ref=list(action.get("evidence_refs", [])),
            actor=args.actor,
            reason=reason,
            round_id=args.round_id,
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
