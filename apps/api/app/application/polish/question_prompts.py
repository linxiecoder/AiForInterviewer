"""Compact prompt bundle for polish question LLM generation."""

from __future__ import annotations

from typing import Any

from app.application.polish.progress_context import truncate_text


POLISH_QUESTION_GENERATION_TASK_TYPE = "polish_question_generation"
POLISH_QUESTION_GENERATION_PROMPT_VERSION = "polish_question_generation_prompt_v1"
POLISH_QUESTION_GENERATION_SCHEMA_ID = "polish_question_generation_output_v1"
POLISH_QUESTION_GENERATION_SCHEMA_VERSION = 1
POLISH_QUESTION_GENERATION_CONTRACT_IDS = ("P-POLISH-002", "P-SHARED-001", "P-SHARED-003")


def build_polish_question_generation_prompt_bundle(
    *,
    session: Any,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
    deterministic_build: Any,
) -> dict[str, Any]:
    evidence_bundle = build_polish_question_generation_evidence_bundle(
        session=session,
        context=context,
        plan=plan,
        state=state,
        requested_ref=requested_ref,
        deterministic_build=deterministic_build,
    )
    return {
        "task_type": POLISH_QUESTION_GENERATION_TASK_TYPE,
        "prompt_version": POLISH_QUESTION_GENERATION_PROMPT_VERSION,
        "schema_id": POLISH_QUESTION_GENERATION_SCHEMA_ID,
        "schema_version": POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
        "contract_ids": list(POLISH_QUESTION_GENERATION_CONTRACT_IDS),
        "prompt": [
            "基于 compact evidence 生成一题打磨模式面试题。",
            "只返回结构化 JSON，不输出 Markdown。",
            "题目必须绑定 progress_node_ref、输入 evidence_refs 和 selected question_pattern。",
            "evidence_refs must be string[] and contain at least 1 value.",
            "Each evidence_refs value must copy exactly one string from input_evidence_refs.",
            "do not use input_source_refs or input_source_refs[].ref_id as evidence_refs.",
            "Do not return refs outside input_evidence_refs: source refs, progress refs, natural language citations, object refs, or invented refs.",
            'evidence_refs values are not object values, e.g. not object {"ref_id":"..."}; do not return a comma-separated string.',
            "If evidence is uncertain, choose the most relevant ref from input_evidence_refs; do not invent.",
            "progress_node_ref and evidence_refs are different fields; do not mix them.",
            "selected_question_pattern.required_question_elements is a hard semantic validation contract.",
            "question_text must copy/include each required element exactly from selected_question_pattern.required_question_elements.",
            "Do not satisfy required_question_elements only in question_pattern, scenario_constraint_summary, or metadata.",
            "Do not paraphrase required element tokens; put Chinese or English phrases verbatim into question_text.",
            "Missing any required element in question_text triggers semantic validation fallback: missing_pattern_required_elements.",
            "scenario_constraint.business_constraint is a hard semantic validation contract.",
            "For technical / mixed themes, question_text must include the business constraint and marker 业务约束 or 新业务约束.",
            "scenario_constraint_summary cannot replace question_text business constraint expression.",
            "Missing business constraint in question_text triggers semantic validation fallback: missing_business_constraint.",
            "不得输出完整参考答案、隐藏评分规则、raw prompt、completion 或 provider payload。",
            "不得编造未在 compact evidence 中出现的具体组件、系统或实体。",
        ],
        "output_schema": _output_schema(),
        "evidence_bundle": evidence_bundle,
        "redaction_boundary": {
            "raw_prompt_persisted": False,
            "raw_completion_persisted": False,
            "provider_payload_persisted": False,
            "full_resume_or_jd_included": False,
        },
    }


def build_polish_question_generation_evidence_bundle(
    *,
    session: Any,
    context: dict[str, Any],
    plan: dict[str, Any],
    state: dict[str, Any],
    requested_ref: str | None,
    deterministic_build: Any,
) -> dict[str, Any]:
    question_context = deterministic_build.question_context
    evidence_signals = deterministic_build.evidence_signals
    question_pattern = deterministic_build.question_pattern
    scenario = deterministic_build.scenario_constraint
    metadata = deterministic_build.draft.question_metadata

    bundle = {
        "theme_strategy": _theme_strategy_summary(question_context.strategy),
        "question_pattern": {
            "pattern_id": question_pattern.pattern_id,
            "title": question_pattern.title,
            "interview_intent": question_pattern.interview_intent,
            "required_question_elements": list(question_pattern.required_question_elements),
            "expected_answer_dimensions": list(question_pattern.expected_answer_dimensions),
            "quality_rules": list(question_pattern.quality_rules),
        },
        "scenario_constraint": _scenario_summary(scenario),
        "evidence_signal_summary": _evidence_signal_summary(evidence_signals),
        "question_metadata_summary": _question_metadata_summary(metadata),
        "progress_node_summary": _progress_node_summary(question_context.node),
        "selected_evidence_summaries": _selected_evidence_summaries(question_context.evidence_chunks),
        "recent_question_texts": _recent_question_texts(context.get("turns", [])),
        "custom_topic_text_summary": truncate_text(getattr(session, "custom_topic_text_summary", None), max_chars=160),
        "source_availability": question_context.source_availability,
        "low_confidence_flags": _dedupe_strings(
            [
                *getattr(evidence_signals, "low_confidence_flags", ()),
                *metadata.get("low_confidence_flags", []),
            ],
            limit=20,
        ),
        "input_evidence_refs": list(question_context.evidence_refs),
        "input_source_refs": [
            {"source_type": source.source_type, "ref_id": source.ref_id, "availability": source.availability}
            for source in question_context.sources
        ],
        "requested_progress_node_ref": requested_ref,
        "resolved_progress_node_ref": question_context.progress_node_ref,
        "context_digest": question_context.context_digest,
        "source_availability_detail": _source_availability_detail(question_context.sources),
    }
    fixture_marker = _safe_text(context.get("question_llm_fixture"), max_chars=80)
    if fixture_marker:
        bundle["fixture_marker"] = fixture_marker
    return bundle


def _output_schema() -> dict[str, Any]:
    return {
        "schema_id": POLISH_QUESTION_GENERATION_SCHEMA_ID,
        "schema_version": POLISH_QUESTION_GENERATION_SCHEMA_VERSION,
        "required": [
            "schema_id",
            "schema_version",
            "status",
            "question_text",
            "question_pattern",
            "interview_intent",
            "scenario_constraint_summary",
            "expected_answer_dimensions",
            "evidence_refs",
            "source_availability",
            "confidence_level",
            "low_confidence_flags",
            "quality_hints",
            "requires_repair",
            "redaction_boundary",
        ],
        "forbidden": [
            "reference_answer",
            "raw_prompt",
            "raw_completion",
            "completion",
            "provider_payload",
            "hidden_rubric",
        ],
        "field_contracts": {
            "question_text": {
                "type": "string",
                "role": "semantic validation target",
                "required_elements": "must include all selected pattern required elements from selected_question_pattern.required_question_elements",
                "required_element_copy_rule": "copy/include each required element exactly; question_pattern or metadata do not satisfy this contract",
                "business_constraint": "for technical / mixed themes, must include scenario_constraint.business_constraint and marker 业务约束 or 新业务约束",
                "semantic_validation_failures": [
                    "missing_pattern_required_elements",
                    "missing_business_constraint",
                ],
            },
            "question_pattern": {
                "role": "selected pattern identifier or title summary only",
                "contract": "question_pattern does not satisfy required_question_elements; question_text must include all required tokens",
            },
            "scenario_constraint_summary": {
                "role": "summary only",
                "contract": "scenario_constraint_summary cannot replace question_text business constraint marker or expression",
            },
            "evidence_refs": {
                "type": "array<string>",
                "min_items": 1,
                "allowed_values": "copy exactly from input_evidence_refs strings",
                "forbidden_values": [
                    "source refs",
                    "progress refs",
                    "object refs",
                    "invented refs",
                    "natural language citations",
                    "comma-separated string",
                ],
            },
        },
    }


def _theme_strategy_summary(strategy: Any) -> dict[str, Any]:
    return {
        "theme": getattr(strategy, "theme", None),
        "label": getattr(strategy, "label", None),
        "explicit_weight": getattr(strategy, "explicit_weight", None),
        "implicit_weight": getattr(strategy, "implicit_weight", None),
        "question_intent": truncate_text(getattr(strategy, "question_intent", None), max_chars=200),
        "question_types": _safe_string_list(getattr(strategy, "question_types", ()), limit=12),
    }


def _scenario_summary(scenario: Any) -> dict[str, Any]:
    return {
        "business_constraint": truncate_text(getattr(scenario, "business_constraint", None), max_chars=220),
        "failure_mode": truncate_text(getattr(scenario, "failure_mode", None), max_chars=220),
        "scale_or_performance_constraint": truncate_text(
            getattr(scenario, "scale_or_performance_constraint", None), max_chars=220
        ),
        "consistency_constraint": truncate_text(getattr(scenario, "consistency_constraint", None), max_chars=220),
        "cost_constraint": truncate_text(getattr(scenario, "cost_constraint", None), max_chars=180),
        "observability_constraint": truncate_text(getattr(scenario, "observability_constraint", None), max_chars=180),
        "system_components": _safe_string_list(getattr(scenario, "system_components", ()), limit=12),
        "technical_entities": _safe_string_list(getattr(scenario, "technical_entities", ()), limit=12),
        "metrics": _safe_string_list(getattr(scenario, "metrics", ()), limit=12),
        "confidence_level": getattr(scenario, "confidence_level", None),
        "low_confidence_flags": _safe_string_list(getattr(scenario, "low_confidence_flags", ()), limit=20),
        "evidence_refs": _safe_string_list(getattr(scenario, "evidence_refs", ()), limit=20),
    }


def _evidence_signal_summary(signals: Any) -> dict[str, Any]:
    metrics = []
    for metric in getattr(signals, "metrics", ())[:8]:
        metrics.append(
            {
                "metric_type": truncate_text(getattr(metric, "metric_type", None), max_chars=80),
                "display": truncate_text(getattr(metric, "display", None), max_chars=120),
                "evidence_ref": truncate_text(getattr(metric, "evidence_ref", None), max_chars=120),
            }
        )
    return {
        "technical_components": _safe_string_list(getattr(signals, "technical_components", ()), limit=12),
        "architecture_components": _safe_string_list(getattr(signals, "architecture_components", ()), limit=12),
        "middleware_components": _safe_string_list(getattr(signals, "middleware_components", ()), limit=12),
        "data_stores": _safe_string_list(getattr(signals, "data_stores", ()), limit=12),
        "message_queues": _safe_string_list(getattr(signals, "message_queues", ()), limit=12),
        "metrics": metrics,
        "failure_signals": _safe_string_list(getattr(signals, "failure_signals", ()), limit=12),
        "consistency_signals": _safe_string_list(getattr(signals, "consistency_signals", ()), limit=12),
        "cost_signals": _safe_string_list(getattr(signals, "cost_signals", ()), limit=12),
        "observability_signals": _safe_string_list(getattr(signals, "observability_signals", ()), limit=12),
        "evidence_refs": _safe_string_list(getattr(signals, "evidence_refs", ()), limit=20),
        "source_availability": getattr(signals, "source_availability", None),
        "confidence_level": getattr(signals, "confidence_level", None),
        "low_confidence_flags": _safe_string_list(getattr(signals, "low_confidence_flags", ()), limit=20),
        "signal_version": getattr(signals, "signal_version", None),
    }


def _question_metadata_summary(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_pattern": _safe_text(metadata.get("question_pattern"), max_chars=120),
        "scenario_constraint_summary": _safe_text(metadata.get("scenario_constraint_summary"), max_chars=300),
        "expected_answer_dimensions": _safe_string_list(metadata.get("expected_answer_dimensions"), limit=8),
        "quality_score": metadata.get("quality_score"),
        "quality_warnings": _safe_string_list(metadata.get("quality_warnings"), limit=12),
        "confidence_level": _safe_text(metadata.get("confidence_level"), max_chars=40),
        "low_confidence_flags": _safe_string_list(metadata.get("low_confidence_flags"), limit=20),
        "evidence_signal_refs": _safe_string_list(metadata.get("evidence_signal_refs"), limit=20),
        "anti_repeat_refs": _safe_string_list(metadata.get("anti_repeat_refs"), limit=10),
        "source_availability": _safe_text(metadata.get("source_availability"), max_chars=40),
    }


def _progress_node_summary(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "progress_node_ref": _safe_text(node.get("progress_node_ref"), max_chars=120),
        "title": _safe_text(node.get("title") or node.get("display_title"), max_chars=160),
        "expected_capability": _safe_text(node.get("expected_capability"), max_chars=260),
        "related_job_requirements": _safe_string_list(node.get("related_job_requirements"), limit=6),
        "related_resume_evidence": _safe_string_list(node.get("related_resume_evidence"), limit=6),
        "missing_points": _safe_string_list(node.get("missing_points"), limit=6),
    }


def _selected_evidence_summaries(chunks: tuple[Any, ...]) -> list[dict[str, Any]]:
    result = []
    for chunk in chunks[:8]:
        result.append(
            {
                "chunk_id": _safe_text(getattr(chunk, "chunk_id", None), max_chars=120),
                "source_type": _safe_text(getattr(chunk, "source_type", None), max_chars=80),
                "title": _safe_text(getattr(chunk, "title", None), max_chars=160),
                "text_summary": _safe_text(getattr(chunk, "text", None), max_chars=260),
                "keywords": _safe_string_list(getattr(chunk, "keywords", ()), limit=8),
                "reason": _safe_text(getattr(chunk, "reason", None), max_chars=120),
            }
        )
    return result


def _recent_question_texts(turns: object) -> list[str]:
    if not isinstance(turns, list):
        return []
    result = []
    for turn in turns[-5:]:
        if isinstance(turn, dict):
            text = _safe_text(turn.get("question_text"), max_chars=260)
            if text:
                result.append(text)
    return result


def _source_availability_detail(sources: tuple[Any, ...]) -> list[dict[str, Any]]:
    return [
        {
            "index": getattr(source, "index", None),
            "source_type": getattr(source, "source_type", None),
            "availability": getattr(source, "availability", None),
            "ref_id": getattr(source, "ref_id", None),
        }
        for source in sources
    ]


def _safe_string_list(value: object, *, limit: int = 20, max_chars: int = 180) -> list[str]:
    if isinstance(value, str):
        raw_items: list[object] = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = []
    return _dedupe_strings((_safe_text(item, max_chars=max_chars) for item in raw_items), limit=limit)


def _safe_text(value: object, *, max_chars: int) -> str | None:
    text = truncate_text(value, max_chars=max_chars)
    return text or None


def _dedupe_strings(values: Any, *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(str(value))
        if len(result) >= limit:
            break
    return result
