"""Progress Tree v2 prompt builders for polish initial generation."""

from __future__ import annotations

from typing import Any

from app.application.polish.progress_context import truncate_text
from app.application.polish.progress_evidence import build_progress_prompt_context


POLISH_PROGRESS_TREE_V2_CONTRACT_IDS = ("P-POLISH-001", "P-SHARED-001", "P-SHARED-003")

POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE = "polish_progress_global_understanding"
POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE = "polish_progress_tree_draft_plan"
POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE = "polish_progress_tree_critic_refiner"
POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE = "polish_progress_tree_evidence_grounding"

POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID = "polish_progress_global_understanding_v2"
POLISH_PROGRESS_TREE_DRAFT_PLAN_SCHEMA_ID = "polish_progress_tree_draft_plan_v2"
POLISH_PROGRESS_TREE_CRITIC_REFINER_SCHEMA_ID = "polish_progress_tree_critic_refiner_v2"
POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID = "polish_progress_tree_grounded_plan_v2"

POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION = "v2"
POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION = "polish_progress_global_understanding_prompt_v2"
POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION = "polish_progress_tree_draft_plan_prompt_v2"
POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION = "polish_progress_tree_critic_refiner_prompt_v2"
POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION = "polish_progress_tree_evidence_grounding_prompt_v2"

_COMMON_JSON_RULES = [
    "只输出合法 JSON，不要 Markdown 包裹。",
    "不得编造简历、项目、技术栈、业务结果或岗位要求。",
    "必须区分 explicit_evidence、reasonable_inference 和 unsupported。",
    "不得输出 provider payload、secret、token、raw completion 或 system prompt。",
    "不得输出精确通过概率。",
    "低证据或资料不足时必须显式标记 low_confidence_flags。",
    "所有候选项或节点的 display_title / exam_point 必须是短考点名词短语。",
    "不得直接复制 selected_evidence_chunks、JD、简历或 evidence 原句作为 display_title / exam_point。",
    "项目背景、业务问题、JD 年限或任职要求只能进入 resume_signal、jd_basis、related_* 或 evidence 字段。",
    "任何可能页面展示的字段不得出现 P7、攻击、拷问、碾压、吊打、火力、红队、必挂、必过、压迫、击穿、杀招。",
]


def build_progress_global_understanding_prompt(context: dict[str, Any]) -> dict[str, Any]:
    """Build the full-context understanding task bundle."""

    prompt_context = {
        "context_metadata": _context_metadata(context),
        "resume_markdown": truncate_text(context.get("resume_snapshot", {}).get("markdown_text"), max_chars=30000),
        "job_payload": _job_payload(context.get("job_snapshot", {})),
        "match_context": _safe_context(context.get("match_context", {})),
        "weakness_context": _safe_context(context.get("weakness_context", {})),
        "asset_context": _safe_context(context.get("asset_context", {})),
        "turns_summary": _turns_summary(context.get("turns", [])),
    }
    return {
        "source_digest": context["content_digest"],
        "task_type": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_TASK_TYPE,
        "prompt_version": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                "你是资深技术面试官、候选人能力建模专家、AI 面试训练产品架构师。",
                "任务：基于完整简历、完整岗位、匹配分析、资产、薄弱项和历史打磨记录，生成候选人画像、岗位能力地图、证据地图、追问方向和打磨策略。",
                "必须识别简历中可深挖的具体技术点，输出 resume_deep_dive_candidates。",
                "必须识别 JD 要求但简历证据弱的具体能力点，输出 jd_gap_learning_candidates。",
                "候选项必须能转成面试考点；不要把项目背景、业务问题、JD 年限或任职要求当作标题候选。",
                "不要直接生成最终进展树。",
                *_COMMON_JSON_RULES,
                "根对象必须包含 schema_id、schema_version、prompt_version、task_type、status、candidate_profile_summary、target_role_competency_map、resume_evidence_map、role_gap_risk_map、interview_strategy、resume_deep_dive_candidates、jd_gap_learning_candidates、recommended_progress_axes、low_confidence_flags。",
            ]
        ),
        "context": prompt_context,
        "output_schema": {
            "schema_id": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_GLOBAL_UNDERSTANDING_PROMPT_VERSION,
            "required_root_fields": [
                "candidate_profile_summary",
                "target_role_competency_map",
                "resume_evidence_map",
                "role_gap_risk_map",
                "interview_strategy",
                "resume_deep_dive_candidates",
                "jd_gap_learning_candidates",
                "recommended_progress_axes",
                "low_confidence_flags",
            ],
        },
    }


def build_progress_tree_draft_plan_prompt(
    context: dict[str, Any],
    global_understanding: dict[str, Any],
) -> dict[str, Any]:
    """Build the draft progress tree planning task bundle."""

    prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
    prompt_context["global_understanding"] = global_understanding
    return {
        "source_digest": context["content_digest"],
        "task_type": POLISH_PROGRESS_TREE_DRAFT_PLAN_TASK_TYPE,
        "prompt_version": POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_TREE_DRAFT_PLAN_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                "任务：基于 global_understanding、selected_evidence_chunks、岗位匹配分析和当前打磨主题生成“面试菜单”草案。",
                "输出必须优先分为两类：category=resume_deep_dive 且 display_category_title=深度打磨类；category=jd_gap_learning 且 display_category_title=补齐学习类。",
                "每个叶子节点必须是具体考点菜单项，可以直接生成第一题和连续追问方向，不得只是抽象能力类目或技术栈目录。",
                "深度打磨类来自简历项目、技能、工作经历、匹配亮点、面试重点、历史反馈或资产摘要。",
                "补齐学习类来自 JD 要求、岗位职责、匹配缺口、匹配重点或建议问题。",
                "display_title / exam_point 必须把 evidence 原句改写成考点，例如把业务背景改写为架构设计、召回优化、工具调用或服务治理。",
                "depth_goal 使用“深度要求 / 高阶深度目标”的中性表达；follow_up_focus 使用“连续追问方向”的中性表达。",
                *_COMMON_JSON_RULES,
                "每个叶子节点必须尽量包含 progress_node_ref、node_code、category、display_category_title、display_title、exam_point、basis_type、resume_signal、jd_basis、depth_goal、preparation_goal、first_question、follow_up_focus、expected_answer_signals、common_loss_risks、related_job_requirements、related_resume_evidence、related_match_gaps、evidence_chunk_ids、confidence_level、children。",
            ]
        ),
        "context": prompt_context,
        "global_understanding": global_understanding,
        "selected_evidence_chunks": prompt_context["selected_evidence_chunks"],
        "dropped_context_summary": prompt_context["dropped_context_summary"],
        "match_context_summary": prompt_context["match_context_summary"],
        "turns_summary": prompt_context["turns_summary"],
        "output_schema": {
            "schema_id": POLISH_PROGRESS_TREE_DRAFT_PLAN_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_DRAFT_PLAN_PROMPT_VERSION,
            "required_root_fields": [
                "plan_quality_intent",
                "progress_tree_plan",
                "coverage_summary",
                "critic_notes_for_next_task",
                "low_confidence_flags",
            ],
        },
    }


def build_progress_tree_critic_refiner_prompt(
    context: dict[str, Any],
    global_understanding: dict[str, Any],
    draft_plan: dict[str, Any],
) -> dict[str, Any]:
    """Build the critic/refiner task bundle."""

    prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
    prompt_context["global_understanding"] = global_understanding
    prompt_context["draft_progress_tree_plan"] = draft_plan
    return {
        "source_digest": context["content_digest"],
        "task_type": POLISH_PROGRESS_TREE_CRITIC_REFINER_TASK_TYPE,
        "prompt_version": POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_TREE_CRITIC_REFINER_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                "任务：严格审查 draft_progress_tree_plan，识别通用化、弱证据、重复、岗位贴合不足和过度推断，并输出重写后的 refined_progress_tree_plan。",
                "如果 overall_quality_score < 85 必须重写，不要只轻微修饰。",
                "如果 non_generic_score < 80 必须显著增强个性化节点。",
                "如果草案像抽象能力树、只有两个抽象节点、或叶子节点不是具体考点，必须重写成面试菜单。",
                "必须检查具体考点、简历线索或 JD 依据、深度要求、第一题、连续追问方向、常见失分风险、证据绑定、禁用词、错字乱码。",
                "如果 display_title / exam_point 是原文长子串，或以面向、针对、负责、具备、熟悉、5年以上、要求开头，必须重写。",
                "如果 interview_value_score < 80 必须补齐 first_question、follow_up_focus、common_loss_risks。",
                *_COMMON_JSON_RULES,
                "根对象必须包含 quality_review、refinement_strategy、refined_progress_tree_plan、quality_gate、low_confidence_flags。",
            ]
        ),
        "context": prompt_context,
        "global_understanding": global_understanding,
        "draft_progress_tree_plan": draft_plan,
        "selected_evidence_chunks": prompt_context["selected_evidence_chunks"],
        "match_context_summary": prompt_context["match_context_summary"],
        "output_schema": {
            "schema_id": POLISH_PROGRESS_TREE_CRITIC_REFINER_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_CRITIC_REFINER_PROMPT_VERSION,
            "required_root_fields": [
                "quality_review",
                "refinement_strategy",
                "refined_progress_tree_plan",
                "quality_gate",
                "low_confidence_flags",
            ],
        },
    }


def build_progress_tree_grounding_prompt(
    context: dict[str, Any],
    global_understanding: dict[str, Any],
    refined_plan: dict[str, Any],
) -> dict[str, Any]:
    """Build the evidence grounding task bundle."""

    prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
    prompt_context["global_understanding"] = global_understanding
    prompt_context["refined_progress_tree_plan"] = refined_plan
    resume = context.get("resume_snapshot", {})
    job = context.get("job_snapshot", {})
    return {
        "source_digest": context["content_digest"],
        "task_type": POLISH_PROGRESS_TREE_GROUNDING_TASK_TYPE,
        "prompt_version": POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION,
        "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
        "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
        "prompt": "\n".join(
            [
                "任务：对 refined_progress_tree_plan 进行证据锚定、置信度分类、unsupported claim detection 和 final normalization。",
                "必须保留面试菜单结构，不得把节点改回抽象能力树。",
                "grounding 只负责绑定 evidence、设置 confidence、设置 grounding_status、修正 evidence_chunk_ids。",
                "不得因为证据不足而伪造 evidence_chunk_ids。",
                "不得在 grounding 阶段把 evidence 原句填回 display_title / exam_point；发现原句式标题必须改写或标记 low_confidence_flags。",
                "grounding_status 只能使用 strongly_grounded、partially_grounded、weakly_grounded、ungrounded。",
                "current_priority 不应默认选择第一个节点，应优先选择岗位关键、证据不稳、能产生高价值追问的节点。",
                *_COMMON_JSON_RULES,
                "根对象必须包含 progress_tree_plan、grounding_summary、initial_progress_tree_state、low_confidence_flags。",
            ]
        ),
        "context": prompt_context,
        "global_understanding": global_understanding,
        "refined_progress_tree_plan": refined_plan,
        "selected_evidence_chunks": prompt_context["selected_evidence_chunks"],
        "resume_version_ref": {
            "resume_id": resume.get("resume_id"),
            "resume_version_id": resume.get("resume_version_id"),
        },
        "job_version_ref": {
            "job_id": job.get("job_id"),
            "job_version_id": job.get("job_version_id"),
        },
        "match_context_summary": prompt_context["match_context_summary"],
        "output_schema": {
            "schema_id": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_ID,
            "schema_version": POLISH_PROGRESS_TREE_GROUNDED_SCHEMA_VERSION,
            "prompt_version": POLISH_PROGRESS_TREE_GROUNDED_PROMPT_VERSION,
            "required_root_fields": [
                "progress_tree_plan",
                "grounding_summary",
                "initial_progress_tree_state",
                "low_confidence_flags",
            ],
        },
    }


def _context_metadata(context: dict[str, Any]) -> dict[str, Any]:
    prompt_context = build_progress_prompt_context(context, purpose="initial_plan")
    return prompt_context["context_metadata"]


def _job_payload(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": truncate_text(job.get("title"), max_chars=240),
        "company": truncate_text(job.get("company"), max_chars=240),
        "department": truncate_text(job.get("department"), max_chars=240),
        "responsibilities": _truncated_list(job.get("responsibilities"), max_chars=12000),
        "requirements": _truncated_list(job.get("requirements"), max_chars=12000),
        "other_notes": truncate_text(job.get("other_notes"), max_chars=12000),
    }


def _safe_context(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return value


def _turns_summary(turns: object) -> list[dict[str, Any]]:
    if not isinstance(turns, list):
        return []
    result: list[dict[str, Any]] = []
    for turn in turns[-8:]:
        if not isinstance(turn, dict):
            continue
        result.append(
            {
                "turn_index": turn.get("turn_index"),
                "question_text": truncate_text(turn.get("question_text"), max_chars=800),
                "answer_text": truncate_text(turn.get("answer_text"), max_chars=1200),
                "feedback_text": truncate_text(turn.get("feedback_text"), max_chars=1200),
            }
        )
    return result


def _truncated_list(value: object, *, max_chars: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = truncate_text(item, max_chars=max_chars)
        if text:
            result.append(text)
    return result
