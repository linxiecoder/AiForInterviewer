"""Prompt builders for polish progress tree LLM tasks."""

from __future__ import annotations

from typing import Any

from app.application.polish.progress_evidence import build_progress_prompt_context


POLISH_PROGRESS_TREE_PLAN_CONTRACT_IDS = ("P-POLISH-001", "P-SHARED-001", "P-SHARED-003")
POLISH_PROGRESS_TREE_STATE_CONTRACT_IDS = ("P-POLISH-001", "P-SHARED-001", "P-SHARED-003")
POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION = "polish_progress_tree_plan_prompt_v1"
POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION = "polish_progress_tree_state_prompt_v1"
POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID = "llm_progress_tree_plan_v1"
POLISH_PROGRESS_TREE_STATE_SCHEMA_ID = "llm_progress_tree_state_v1"
POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION = "v1"
POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION = "v1"

INITIAL_PROGRESS_TREE_PROMPT_CONTRACT = (
    "你必须基于岗位版本内容和简历版本内容经过 deterministic evidence chunking 后得到的 "
    "selected_evidence_chunks 生成进展树。岗位名、简历名只能作为展示信息和 metadata，不能作为"
    "主要语义依据。不要编造 selected_evidence_chunks 中不存在的项目、技术栈、业务经验或岗位要求。"
    "每个能力节点的 evidence 必须尽量引用 evidence_chunk_ids。"
    "若 evidence 不足以支撑生成进展树，返回 insufficient_context。进展树节点必须反映"
    "该候选人针对该岗位的真实面试准备路径，而不是通用技术分类。"
)

PROGRESS_TREE_STATE_REFRESH_PROMPT_CONTRACT = (
    "你必须基于 existing plan、existing state、selected_evidence_chunks 和 turns 刷新状态。"
    "不得删除或重命名 existing plan.nodes，不得重建主树，不得因为最近一题临时漂移到无关能力。"
    "状态更新必须引用相关 evidence_chunk_ids、related_question_indexes、related_answer_indexes "
    "和 missing_points。current_priority 必须选择对当前岗位最关键且候选人尚未掌握的节点。"
)


def build_initial_progress_tree_prompt(context: dict[str, Any]) -> dict[str, Any]:
    prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
    return {
        "source_digest": context["content_digest"],
        "task_type": "polish_progress_tree_plan",
        "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                INITIAL_PROGRESS_TREE_PROMPT_CONTRACT,
                "只输出合法 JSON，不要 Markdown 包裹。",
                "如果岗位或简历内容不足，返回 status=insufficient_context，不要编造节点。",
                "prompt 输入只包含 context_metadata、selected_evidence_chunks、dropped_context_summary、match_context_summary 和 turns_summary。",
                (
                    "根对象必须包含 schema_id、schema_version、prompt_version、progress_tree_plan "
                    "和 progress_tree_state。"
                ),
                (
                    f"schema_id 固定为 {POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID}，schema_version 固定为 "
                    f"{POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION}。"
                ),
            ]
        ),
        "context": prompt_context,
        "selected_evidence_chunks": prompt_context["selected_evidence_chunks"],
        "dropped_context_summary": prompt_context["dropped_context_summary"],
        "match_context_summary": prompt_context["match_context_summary"],
        "turns_summary": prompt_context["turns_summary"],
        "output_schema": {
            "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
            "required_root_fields": [
                "schema_id",
                "schema_version",
                "prompt_version",
                "progress_tree_plan",
                "progress_tree_state",
            ],
            "progress_tree_plan": {
                "schema_id": POLISH_PROGRESS_TREE_PLAN_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_PLAN_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready | insufficient_context | failed",
                "context_digest": "string",
                "nodes": [
                    {
                        "progress_node_ref": "stable string",
                        "title": "一级方向标题",
                        "expected_capability": "该节点期望验证的能力",
                        "related_job_requirements": ["来自 selected_evidence_chunks 的岗位职责或要求摘要"],
                        "related_resume_evidence": ["来自 selected_evidence_chunks 的经历或技能证据摘要"],
                        "missing_points": ["来自 selected_evidence_chunks、match_context_summary 或反馈的缺口"],
                        "evidence_chunk_ids": ["来自 selected_evidence_chunks 的 chunk_id"],
                        "children": ["同结构二级节点，可为空数组"],
                    }
                ],
            },
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_PLAN_PROMPT_VERSION,
                "status": "ready",
                "node_states": [
                    {
                        "progress_node_ref": "必须来自 plan.nodes",
                        "status": "completed | in_progress | pending",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": None,
                    }
                ],
                "current_priority": {
                    "progress_node_ref": "必须来自 plan.nodes",
                    "title": "string",
                    "expected_capability": "string",
                },
                "progress": {"progress_percent": 0},
            },
        },
    }


def build_progress_tree_state_refresh_prompt(
    *,
    context: dict[str, Any],
    existing_plan: dict[str, Any],
    existing_state: dict[str, Any],
) -> dict[str, Any]:
    prompt_context = build_progress_prompt_context(
        context,
        purpose="state_refresh",
        existing_plan=existing_plan,
        existing_state=existing_state,
    )
    return {
        "source_digest": context["content_digest"],
        "task_type": "polish_progress_tree_state",
        "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                PROGRESS_TREE_STATE_REFRESH_PROMPT_CONTRACT,
                "只输出合法 JSON，不要 Markdown 包裹。",
                "不得修改、删除或重排 existing_progress_tree_plan.nodes。",
                "必须基于 selected_evidence_chunks 和 turns_summary 刷新状态，并尽量写回 evidence_chunk_ids。",
                "状态更新必须同时参考当前回答表现、feedback 缺口、岗位要求和简历经历。",
                (
                    "根对象必须包含 schema_id、schema_version、prompt_version 和 "
                    "progress_tree_state。"
                ),
                (
                    f"schema_id 固定为 {POLISH_PROGRESS_TREE_STATE_SCHEMA_ID}，schema_version 固定为 "
                    f"{POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION}。"
                ),
            ]
        ),
        "context": prompt_context,
        "selected_evidence_chunks": prompt_context["selected_evidence_chunks"],
        "dropped_context_summary": prompt_context["dropped_context_summary"],
        "match_context_summary": prompt_context["match_context_summary"],
        "turns_summary": prompt_context["turns_summary"],
        "existing_progress_tree_plan": existing_plan,
        "existing_progress_tree_state": existing_state,
        "output_schema": {
            "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
            "required_root_fields": [
                "schema_id",
                "schema_version",
                "prompt_version",
                "progress_tree_state",
            ],
            "progress_tree_state": {
                "schema_id": POLISH_PROGRESS_TREE_STATE_SCHEMA_ID,
                "schema_version": POLISH_PROGRESS_TREE_STATE_SCHEMA_VERSION,
                "prompt_version": POLISH_PROGRESS_TREE_STATE_PROMPT_VERSION,
                "status": "ready | refresh_failed",
                "node_states": [
                    {
                        "progress_node_ref": "必须来自 existing_progress_tree_plan.nodes",
                        "status": "completed | in_progress | pending",
                        "completed_questions_count": 0,
                        "latest_feedback_summary": "string | null",
                    }
                ],
                "current_priority": {
                    "progress_node_ref": "必须来自 existing_progress_tree_plan.nodes",
                    "title": "string",
                    "expected_capability": "string",
                },
                "progress": {"progress_percent": 0},
            }
        },
    }
