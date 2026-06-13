from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from app.application.llm.agent_io import (
    DEFAULT_AGENT_SAFETY_POLICY,
    AgentEvidenceItem,
    AgentFocusTarget,
    AgentPromptBundle,
    AgentSafetyPolicy,
)
from app.application.polish.feedback_models import FeedbackCandidatePayload
from app.application.polish.feedback_schema import (
    POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
    POLISH_FEEDBACK_FINAL_CONTRACT_IDS,
    POLISH_FEEDBACK_FINAL_SCHEMA_ID,
    POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
    POLISH_FEEDBACK_CANDIDATE_MODE,
    POLISH_FEEDBACK_CANDIDATE_TASK,
    POLISH_FEEDBACK_TASK_TYPE,
)
from app.application.polish.transcript_signal_parser import (
    POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID,
    TranscriptSignalParser,
    build_fallback_structured_answer,
    structured_answer_to_evaluation_text,
)

_FEEDBACK_FORBIDDEN_OUTPUT_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "token",
    "secret",
    "cookie",
)
_FEEDBACK_FORBIDDEN_METADATA_KEYS = (
    "raw_prompt",
    "system_prompt",
    "developer_prompt",
    "completion",
    "raw_completion",
    "provider_payload",
    "raw_provider_payload",
    "full_resume",
    "full_jd",
    "full_answer",
    "full_asset_body",
    "token",
    "secret",
    "cookie",
)
_UNSAFE_CONTEXT_KEYS = frozenset(
    {
        "raw_prompt",
        "system_prompt",
        "developer_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "full_resume",
        "full_jd",
        "full_answer",
        "full_asset_body",
        "api_key",
        "token",
        "secret",
        "cookie",
    }
)
_CURRENT_ANSWER_TEXT_MAX_CHARS = 1200
_CURRENT_ANSWER_TEXT_POLICY = "structured_answer_signal_primary_input"
_SOURCE_REF_KEYS = ("resource_type", "resource_id", "ref_type", "ref_id", "source_ref", "source_type")
_EVIDENCE_ITEMS_LIMIT = 5
_PROVIDER_EVIDENCE_ITEMS_LIMIT = 5
_PROVIDER_PROMPT_CHAR_LIMIT = 12000
_PROVIDER_PROMPT_TARGET_CHARS = 8000
_QUESTION_SOURCE_LIMIT = 2
_JOB_REQUIREMENTS_LIMIT = 2
_RESUME_PROJECTS_LIMIT = 2
_SESSION_RECENT_TURNS_LIMIT = 3
_SAME_QUESTION_ANSWERS_LIMIT = 1
_RELATED_CONTEXT_ITEMS_LIMIT = 5
_PROJECT_ASSET_SUMMARIES_LIMIT = 5


def build_feedback_prompt_asset(context: object) -> dict[str, Any]:
    """Build the compact runtime prompt asset for feedback candidate output."""

    safety_policy = _feedback_safety_policy()
    validation_rules = _validation_rules()
    output_schema = _feedback_candidate_output_schema()
    evidence_refs = _string_list(_get_list(context, "evidence_refs"))
    progress_node_ref = _get_text(context, "progress_node_ref", max_chars=200)
    related_terms = _related_terms(context, evidence_refs=(*evidence_refs, progress_node_ref))
    canonical_project_assets = _compact_canonical_project_assets(_get_dict(context, "canonical_project_assets"))
    structured_answer = _structured_answer_for(context)
    input_data = {
        "current_question": {
            "question_id": _get_text(context, "question_id"),
            "question_text": _get_text(context, "question_text", max_chars=600),
            "polish_theme": _get_text(context, "polish_theme", max_chars=500),
            "progress_node_ref": progress_node_ref,
            "question_metadata": _compact_question_metadata(_get_dict(context, "question_metadata")),
            "question_sources": _compact_question_sources(
                _get_list(context, "question_sources"),
                evidence_refs=(*evidence_refs, progress_node_ref),
            ),
            "evidence_refs": evidence_refs,
        },
        "current_answer": {
            "answer_id": _get_text(context, "answer_id"),
            "structured_answer": structured_answer,
            "answer_text_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_schema_id": POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID,
            "answer_text_max_chars": _CURRENT_ANSWER_TEXT_MAX_CHARS,
            "answer_text_is_bounded": True,
            "full_answer_forbidden": True,
            "answer_round": _get(context, "answer_round"),
        },
        "same_question_answers": _compact_same_question_answers(_get_list(context, "same_question_answers")),
        "same_project_turns": _compact_recent_turns(_get_list(context, "same_project_turns")),
        "session_recent_turns": _compact_recent_turns(_get_list(context, "session_recent_turns")),
        "project_asset_summaries": _compact_project_asset_summaries(_get_list(context, "project_asset_summaries")),
        "canonical_project_assets": canonical_project_assets,
        "context_snapshots": {
            "job_snapshot": _compact_job_snapshot(_get_dict(context, "job_snapshot")),
            "resume_snapshot": _compact_resume_snapshot(_get_dict(context, "resume_snapshot"), related_terms=related_terms),
            "progress_node_snapshot": _compact_progress_node_snapshot(_get_dict(context, "progress_node_snapshot")),
        },
    }
    input_data["evidence_items"] = [item.to_prompt_dict() for item in _evidence_items(context)]
    input_data["focus_target"] = _focus_target(context).to_prompt_dict()

    prompt_asset = AgentPromptBundle(
        task_type=POLISH_FEEDBACK_TASK_TYPE,
        prompt_version=POLISH_FEEDBACK_AGENT_PROMPT_VERSION,
        schema_id=POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        schema_version=POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        prompt="\n".join(
            [
                "Generate structured polish feedback for the current answer.",
                *safety_policy.to_prompt_rules(),
                *validation_rules,
            ]
        ),
        input_data=input_data,
        output_schema=output_schema,
        system_role="You review interview polish answers and return validated feedback JSON.",
        developer_constraints=tuple((*safety_policy.to_prompt_rules(), *validation_rules)),
        user_task="Evaluate the current answer using only the provided evidence and context snapshots.",
        input_contract={
            "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
            "required_context_refs": ["session_id", "question_id", "answer_id"],
            "raw_model_io_storage": False,
            "answer_text_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_schema_id": POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID,
            "answer_text_max_chars": _CURRENT_ANSWER_TEXT_MAX_CHARS,
            "answer_text_is_bounded": True,
            "full_answer_forbidden": True,
        },
        extra_fields={
            "asset_id": "prompt_asset.polish.feedback.generated.phase3",
            "evidence_retrieval_hints": {
                "prefer": ["current_answer", "project_asset_summaries", "progress_node_snapshot"],
                "avoid": ["full_resume", "full_jd", "provider_payload"],
            },
            "evidence_selection_policy": {
                "evidence_items_field": "input_data.evidence_items",
                "must_ground_major_loss_points": True,
            },
            "citation_rules": [
                "Use evidence_refs only for refs present in input_data.evidence_items.",
                "Do not cite raw resume, raw job description, or provider payload.",
            ],
            "refusal_and_low_confidence_policy": {
                "safety_policy": safety_policy.to_prompt_dict(),
                "safety_rules": safety_policy.to_prompt_rules(),
                "validation_rules": validation_rules,
            },
            "conflict_check": {
                "project_asset_conflict": "clarify instead of choosing for the user",
                "same_session_similarity": "mark repeated, covered, or conflicting with evidence",
            },
        },
    ).to_prompt_asset_dict()
    prompt_asset["feedback_mode"] = POLISH_FEEDBACK_CANDIDATE_MODE
    prompt_asset["provider_prompt"] = _provider_compact_prompt(
        input_data,
        prompt=prompt_asset["prompt"] if isinstance(prompt_asset.get("prompt"), str) else "",
        output_schema=deepcopy(prompt_asset["output_schema"]),
        prompt_version=_get_clean_text(prompt_asset.get("prompt_version"), max_chars=120),
    )
    return prompt_asset


def _feedback_safety_policy() -> AgentSafetyPolicy:
    return AgentSafetyPolicy(
        json_only=DEFAULT_AGENT_SAFETY_POLICY.json_only,
        forbid_markdown_wrapper=DEFAULT_AGENT_SAFETY_POLICY.forbid_markdown_wrapper,
        untrusted_input_boundary=DEFAULT_AGENT_SAFETY_POLICY.untrusted_input_boundary,
        forbidden_output_markers=_unique(
            (*DEFAULT_AGENT_SAFETY_POLICY.forbidden_output_markers, *_FEEDBACK_FORBIDDEN_OUTPUT_MARKERS)
        ),
        forbidden_metadata_keys=_unique(
            (*DEFAULT_AGENT_SAFETY_POLICY.forbidden_metadata_keys, *_FEEDBACK_FORBIDDEN_METADATA_KEYS)
        ),
        no_fabrication_rules=_unique(
            (
                *DEFAULT_AGENT_SAFETY_POLICY.no_fabrication_rules,
                "不得编造项目经历、技术栈、指标、职责边界。",
                "项目资产和当前回答冲突时必须澄清，不得替用户取舍。",
            )
        ),
        sensitive_data_rules=_unique(
            (
                *DEFAULT_AGENT_SAFETY_POLICY.sensitive_data_rules,
                "不得输出 raw prompt、system prompt、developer prompt、completion、provider payload、full resume、full JD、token、secret 或 cookie。",
            )
        ),
        low_confidence_rules=_unique(
            (
                *DEFAULT_AGENT_SAFETY_POLICY.low_confidence_rules,
                "证据不足、项目同名疑似误合并、技术判断缺证据时必须标记 low confidence。",
            )
        ),
    )


def _validation_rules() -> tuple[str, ...]:
    return (
        "feedback_id is produced by the service and must not be output by the model.",
        "score_reasoning is recommended but may be omitted when evidence is insufficient; service-side scoring remains authoritative.",
        "Final fields such as score_result, asset_consistency_check, answer_coverage, answer_change_analysis, feedback_cards, and next_recommended_actions are produced by the service.",
        "Do not output raw prompt, provider payload, full resume, full JD, token, secret, or cookie.",
        "Do not invent user experience or project facts.",
        "Every major loss point must be covered by a reference answer section.",
        "If canonical_project_assets conflict with the answer, mark conflict in optional asset checks without writing formal assets.",
        "Any project_asset_update_candidates must be candidates with user_confirmation_required=true.",
        "Keep project asset and session similarity checks lightweight in service synthesis when evidence is insufficient.",
    )


def _feedback_candidate_output_schema() -> dict[str, Any]:
    schema = _compact_json_schema(FeedbackCandidatePayload.model_json_schema())
    schema["schema_id"] = POLISH_FEEDBACK_FINAL_SCHEMA_ID
    schema["schema_version"] = POLISH_FEEDBACK_FINAL_SCHEMA_VERSION
    schema["required_status"] = "generated_or_partial_or_low_confidence"
    schema["fields"] = list(FeedbackCandidatePayload.model_fields)
    return schema


def _compact_json_schema(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: _compact_json_schema(nested, parent_key=key)
            for key, nested in value.items()
            if not (key == "title" and parent_key != "properties")
        }
    if isinstance(value, list):
        return [_compact_json_schema(item, parent_key=parent_key) for item in value]
    return value


def _required_json_schema(output_schema: dict[str, Any]) -> dict[str, Any]:
    properties = output_schema.get("properties")
    field_names = tuple(properties) if isinstance(properties, dict) else tuple(FeedbackCandidatePayload.model_fields)
    required_fields = [
        field_name
        for field_name in (
            "feedback_text",
            "answer_summary",
            "loss_points",
            "reference_answer.sections",
            "low_confidence_flags",
            "evidence_refs",
        )
        if field_name.split(".", maxsplit=1)[0] in field_names
    ]
    required_roots = {field_name.split(".", maxsplit=1)[0] for field_name in required_fields}
    optional_fields = [field_name for field_name in field_names if field_name not in required_roots]
    return {
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "default_empty_fields": [
            field_name
            for field_name in (
                "score_reasoning",
                "same_question_effect",
                "project_asset_update_candidates",
                "low_confidence_flags",
                "evidence_refs",
            )
            if field_name in field_names
        ],
        "not_applicable_fields": [],
    }


def _provider_compact_prompt(
    input_data: dict[str, Any],
    *,
    prompt: str,
    output_schema: dict[str, Any],
    prompt_version: str,
) -> dict[str, Any]:
    current_question = _safe_dict(input_data.get("current_question"))
    current_answer = _safe_dict(input_data.get("current_answer"))
    question_sources = _limit_question_sources(_safe_list(current_question.get("question_sources")))
    same_question_answers = _limit_same_question_answers(_safe_list(input_data.get("same_question_answers")))
    context_snapshots = _safe_dict(input_data.get("context_snapshots"))
    progress_node = _safe_dict(context_snapshots.get("progress_node_snapshot"))
    job_snapshot = _safe_dict(context_snapshots.get("job_snapshot"))
    resume_snapshot = _safe_dict(context_snapshots.get("resume_snapshot"))
    evidence_items = _provider_evidence_items(_safe_list(input_data.get("evidence_items")))
    canonical_project_assets = _safe_dict(input_data.get("canonical_project_assets"))
    provider_prompt: dict[str, Any] = {
        "task": POLISH_FEEDBACK_CANDIDATE_TASK,
        "task_type": POLISH_FEEDBACK_TASK_TYPE,
        "feedback_mode": POLISH_FEEDBACK_CANDIDATE_MODE,
        "schema_id": POLISH_FEEDBACK_FINAL_SCHEMA_ID,
        "schema_version": POLISH_FEEDBACK_FINAL_SCHEMA_VERSION,
        "prompt_version": prompt_version,
        "prompt": prompt,
        "output_schema": output_schema,
        "contract_ids": list(POLISH_FEEDBACK_FINAL_CONTRACT_IDS),
        "input_contract": {
            "raw_model_io_storage": False,
            "context_mode": "quick_compact",
            "answer_text_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "answer_text_max_chars": _CURRENT_ANSWER_TEXT_MAX_CHARS,
            "answer_text_is_bounded": True,
            "full_answer_forbidden": True,
        },
        "required_json_schema": _required_json_schema(output_schema),
        "current_question": {
            "question_id": _get_clean_text(current_question.get("question_id"), max_chars=120),
            "question_text": _get_clean_text(current_question.get("question_text"), max_chars=600),
            "polish_theme": _get_clean_text(current_question.get("polish_theme"), max_chars=200),
            "progress_node_ref": _get_clean_text(current_question.get("progress_node_ref"), max_chars=120),
            "question_sources": question_sources,
            "evidence_refs": _string_list(current_question.get("evidence_refs"), max_chars=120)[:5],
            "expected_answer_dimensions": _string_list(
                _safe_dict(current_question.get("question_metadata")).get("expected_answer_dimensions"),
                max_chars=160,
            )[:5],
        },
        "current_answer": {
            "answer_id": _get_clean_text(current_answer.get("answer_id"), max_chars=120),
            "structured_answer": _compact_structured_answer(current_answer.get("structured_answer")),
            "answer_text_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_policy": _CURRENT_ANSWER_TEXT_POLICY,
            "structured_answer_schema_id": POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID,
            "answer_text_max_chars": _CURRENT_ANSWER_TEXT_MAX_CHARS,
            "answer_text_is_bounded": True,
            "full_answer_forbidden": True,
            "answer_round": current_answer.get("answer_round"),
        },
        "scoring_rules": {
            "scale": "0-100",
            "score_reasoning": "Each entry includes dimension and rationale.",
            "major_loss_points": "must be mapped by reference_answer.sections.addresses_loss_point_ids",
        },
        "evidence": evidence_items,
        "canonical_project_assets": canonical_project_assets,
        "same_question_answers": same_question_answers,
        "progress_node_snapshot": {
            "node_ref": _get_clean_text(progress_node.get("node_ref"), max_chars=120),
            "title": _get_clean_text(progress_node.get("title"), max_chars=200),
            "expected_capability": _get_clean_text(progress_node.get("expected_capability"), max_chars=200),
            "missing_points": _string_list(progress_node.get("missing_points"), max_chars=120)[:3],
            "related_job_requirements": _string_list(progress_node.get("related_job_requirements"), max_chars=120)[:2],
            "related_resume_evidence": _string_list(progress_node.get("related_resume_evidence"), max_chars=120)[:2],
        },
        "job_requirements": _string_list(job_snapshot.get("requirements"), max_chars=160)[:_JOB_REQUIREMENTS_LIMIT],
        "resume_projects": _string_list(resume_snapshot.get("projects"), max_chars=240)[:_RESUME_PROJECTS_LIMIT],
        "output_requirements": [
            "Return JSON only.",
            "Use only output_schema candidate fields.",
            "Required: feedback_text, answer_summary, loss_points, reference_answer, low_confidence_flags, evidence_refs.",
            "reference_answer.sections[].title recommended; service generates if omitted.",
            "reference_answer.sections[].content required for display.",
            "score_reasoning is recommended; if uncertain, omit it.",
            "Optional candidate fields: same_question_effect, project_asset_update_candidates.",
            "Aliases accepted: loss_points[].id/loss_id, reference_answer.sections[].id.",
            "same_question_effect may be an object or unchanged/improved/regressed/mixed/first_attempt.",
            "Do not include final/metadata fields: feedback_id, schema_id, schema_version, model_name, prompt_version, score_result.",
            "Do not include raw prompt, provider payload, full resume, full JD, token, secret, or cookie.",
        ],
        "feedback_metadata": {
            "feedback_mode": POLISH_FEEDBACK_CANDIDATE_MODE,
            "context_compaction_applied": True,
            "omitted_context_summary": [
                "same project history",
                "session recent turn history",
                "project asset summaries",
                "raw resume body",
                "raw job description",
                "work history details",
                "resume markdown body",
            ],
            "prompt_char_count": 0,
            "evidence_item_count": len(evidence_items),
        },
    }
    _trim_provider_prompt(provider_prompt)
    provider_prompt["feedback_metadata"]["evidence_item_count"] = len(provider_prompt["evidence"])
    provider_prompt["feedback_metadata"]["prompt_char_count"] = _prompt_char_count(provider_prompt)
    return provider_prompt


def _provider_evidence_items(values: list[Any]) -> list[dict[str, object]]:
    priority = {
        "current_answer": 100,
        "current_answer_structured": 100,
        "canonical_project_asset": 95,
        "progress_node_summary": 90,
        "question_source": 80,
        "project_asset_summary": 78,
        "resume_project_evidence": 70,
        "same_question_history": 60,
        "job_requirement": 50,
    }
    items: list[dict[str, object]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        reason = _get_clean_text(value.get("reason"), max_chars=80)
        if reason not in priority:
            continue
        items.append(
            {
                "ref": _get_clean_text(value.get("ref"), max_chars=120),
                "source_type": _get_clean_text(value.get("source_type"), max_chars=80),
                "title": _get_clean_text(value.get("title"), max_chars=120),
                "excerpt": _get_clean_text(
                    value.get("excerpt"),
                    max_chars=(
                        _CURRENT_ANSWER_TEXT_MAX_CHARS
                        if reason in {"current_answer", "current_answer_structured"}
                        else 300
                    ),
                ),
                "reason": reason,
                "priority": priority[reason],
            }
        )
    deduped: dict[str, dict[str, object]] = {}
    for item in sorted(items, key=lambda candidate: int(candidate["priority"]), reverse=True):
        ref = str(item.get("ref") or "")
        if ref and ref not in deduped:
            deduped[ref] = item
    return list(deduped.values())[:_PROVIDER_EVIDENCE_ITEMS_LIMIT]


def _limit_question_sources(values: list[Any]) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    for index, source in enumerate(values[:_QUESTION_SOURCE_LIMIT], start=1):
        if not isinstance(source, dict):
            continue
        sources.append(
            {
                "ref": _get_clean_text(source.get("ref"), max_chars=120) or f"question_source_{index}",
                "source_type": _get_clean_text(source.get("source_type"), max_chars=80),
                "title": _get_clean_text(source.get("title"), max_chars=120),
                "summary": _get_clean_text(source.get("summary"), max_chars=300),
            }
        )
    return sources


def _limit_same_question_answers(values: list[Any]) -> list[dict[str, object]]:
    answers: list[dict[str, object]] = []
    for index, answer in enumerate(values[:_SAME_QUESTION_ANSWERS_LIMIT], start=1):
        if not isinstance(answer, dict):
            continue
        answers.append(
            {
                "answer_id": _get_clean_text(answer.get("answer_id"), max_chars=120) or f"same_question_answer_{index}",
                "answer_round": _get_clean_text(answer.get("answer_round"), max_chars=20),
                "answer_summary": _get_clean_text(answer.get("answer_summary"), max_chars=240),
                "feedback_summary": _get_clean_text(answer.get("feedback_summary"), max_chars=240),
                "loss_point_ids": _string_list(answer.get("loss_point_ids"), max_chars=120)[:5],
            }
        )
    return answers


def _trim_provider_prompt(provider_prompt: dict[str, Any]) -> None:
    while _prompt_char_count(provider_prompt) > _PROVIDER_PROMPT_TARGET_CHARS and len(provider_prompt["evidence"]) > 1:
        provider_prompt["evidence"].pop()
    if _prompt_char_count(provider_prompt) <= _PROVIDER_PROMPT_CHAR_LIMIT:
        return
    provider_prompt["same_question_answers"] = []
    provider_prompt["resume_projects"] = provider_prompt.get("resume_projects", [])[:1]
    provider_prompt["job_requirements"] = provider_prompt.get("job_requirements", [])[:1]
    while _prompt_char_count(provider_prompt) > _PROVIDER_PROMPT_CHAR_LIMIT and len(provider_prompt["evidence"]) > 1:
        provider_prompt["evidence"].pop()


def _prompt_char_count(provider_prompt: dict[str, Any]) -> int:
    return len(json.dumps(provider_prompt, ensure_ascii=False, sort_keys=True))


def _structured_answer_for(context: object) -> dict[str, Any]:
    existing = _get_dict(context, "structured_answer")
    if existing:
        return _compact_structured_answer(existing)
    answer_text = _get_text(context, "answer_text", max_chars=12000)
    try:
        return _compact_structured_answer(TranscriptSignalParser().parse(answer_text).to_dict())
    except Exception:
        return _compact_structured_answer(build_fallback_structured_answer(answer_text).to_dict())


def _compact_structured_answer(value: object) -> dict[str, Any]:
    source = value if isinstance(value, dict) else build_fallback_structured_answer("").to_dict()
    return {
        "schema_id": _get_clean_text(source.get("schema_id"), max_chars=80) or POLISH_TRANSCRIPT_SIGNALS_SCHEMA_ID,
        "parse_status": _get_clean_text(source.get("parse_status"), max_chars=40) or "fallback",
        "claims": _compact_structured_items(
            source.get("claims"),
            keys=("claim_id", "text", "evidence_ref"),
            limit=8,
            max_chars=300,
        ),
        "topics": _string_list(source.get("topics"), max_chars=80)[:12],
        "sentiment": _get_clean_text(source.get("sentiment"), max_chars=40) or None,
        "confidence_indicators": _compact_structured_items(
            source.get("confidence_indicators"),
            keys=("indicator_id", "text", "kind", "evidence_ref"),
            limit=6,
            max_chars=160,
        ),
        "experience_signals": _compact_structured_items(
            source.get("experience_signals"),
            keys=("signal_id", "signal_type", "text", "evidence_ref"),
            limit=6,
            max_chars=240,
        ),
    }


def _compact_structured_items(
    value: object,
    *,
    keys: tuple[str, ...],
    limit: int,
    max_chars: int,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for item in _safe_list(value)[:limit]:
        if not isinstance(item, dict):
            continue
        compact = {key: text for key in keys if (text := _get_clean_text(item.get(key), max_chars=max_chars))}
        if compact:
            items.append(compact)
    return items


def _evidence_items(context: object) -> list[AgentEvidenceItem]:
    items: list[AgentEvidenceItem] = []
    question_text = _get_text(context, "question_text", max_chars=600)
    structured_answer = _structured_answer_for(context)
    answer_signal_text = _get_clean_text(
        structured_answer_to_evaluation_text(structured_answer),
        max_chars=_CURRENT_ANSWER_TEXT_MAX_CHARS,
    )
    question_id = _get_text(context, "question_id") or "current_question"
    answer_id = _get_text(context, "answer_id") or "current_answer"
    evidence_refs = _string_list(_get_list(context, "evidence_refs"))
    progress_node_ref = _get_text(context, "progress_node_ref", max_chars=200)

    for index, source in enumerate(
        _matching_question_sources(_get_list(context, "question_sources"), evidence_refs=(*evidence_refs, progress_node_ref)),
        start=1,
    ):
        if not isinstance(source, dict):
            continue
        ref = _first_text(source.get("ref"), source.get("ref_id"), source.get("source_ref"), f"question_source_{index}")
        source_type = _first_text(source.get("source_type"), "question_source")
        title = _first_text(source.get("title"), source.get("source_type"), "Question source")
        excerpt = _first_text_limited(source.get("excerpt"), source.get("summary"), question_text, max_chars=300)
        items.append(
            AgentEvidenceItem(
                ref=ref,
                source_type=source_type,
                title=title,
                excerpt=excerpt,
                source_ref=_source_ref(source),
                availability=_first_text(source.get("availability")) or None,
                priority=90 - index,
                reason="question_source",
            )
        )

    if answer_signal_text:
        items.append(
            AgentEvidenceItem(
                ref=answer_id,
                source_type="answer_excerpt",
                title="Current answer",
                excerpt=answer_signal_text,
                source_ref={"resource_type": "answer", "resource_id": answer_id},
                priority=100,
                reason="current_answer_structured",
            )
        )

    for index, answer in enumerate(_get_list(context, "same_question_answers"), start=1):
        if not isinstance(answer, dict):
            continue
        ref = _first_text(answer.get("answer_id"), answer.get("ref"), f"same_question_answer_{index}")
        excerpt = _first_text(answer.get("answer_summary"), answer.get("summary"))
        if excerpt:
            items.append(
                AgentEvidenceItem(
                    ref=ref,
                    source_type="same_question_previous_answer",
                    title=f"Previous answer {index}",
                    excerpt=excerpt,
                    source_ref={"resource_type": "answer", "resource_id": ref},
                    priority=70 - index,
                    reason="same_question_history",
                )
            )

    for index, turn in enumerate(_get_list(context, "same_project_turns"), start=1):
        if not isinstance(turn, dict):
            continue
        ref = _first_text(turn.get("answer_id"), turn.get("question_id"), turn.get("ref"), f"same_project_turn_{index}")
        excerpt = _first_text(turn.get("feedback_summary"), turn.get("answer_summary"), turn.get("summary"))
        if excerpt:
            items.append(
                AgentEvidenceItem(
                    ref=ref,
                    source_type="same_project_previous_turn",
                    title=f"Same project turn {index}",
                    excerpt=excerpt,
                    source_ref=_source_ref(turn),
                    priority=60 - index,
                    reason="same_project_history",
                )
            )

    for index, asset in enumerate(_canonical_project_asset_items(_get_dict(context, "canonical_project_assets")), start=1):
        ref = _first_text(asset.get("asset_id"), asset.get("asset_ref"), asset.get("ref"), f"canonical_asset_{index}")
        excerpt = _first_text(asset.get("summary"), asset.get("content_excerpt"), asset.get("title"))
        if excerpt:
            items.append(
                AgentEvidenceItem(
                    ref=ref,
                    source_type="canonical_project_asset",
                    title=_first_text(asset.get("title"), "Canonical project asset"),
                    excerpt=excerpt,
                    source_ref={"resource_type": "asset", "resource_id": ref},
                    priority=95 - index,
                    reason="canonical_project_asset",
                )
            )

    for index, asset in enumerate(_get_list(context, "project_asset_summaries"), start=1):
        if not isinstance(asset, dict):
            continue
        ref = _first_text(asset.get("asset_id"), asset.get("asset_ref"), asset.get("ref"), f"project_asset_{index}")
        excerpt = _first_text(asset.get("summary"), asset.get("excerpt"), asset.get("title"))
        if excerpt:
            items.append(
                AgentEvidenceItem(
                    ref=ref,
                    source_type="project_asset_summary",
                    title=_first_text(asset.get("title"), "Project asset"),
                    excerpt=excerpt,
                    source_ref={"resource_type": "asset", "resource_id": ref},
                    priority=80 - index,
                    reason="project_asset_summary",
                )
            )

    job_snapshot = _get_dict(context, "job_snapshot")
    requirements = job_snapshot.get("requirements") if isinstance(job_snapshot, dict) else None
    if isinstance(requirements, list):
        for index, requirement in enumerate(requirements[:_JOB_REQUIREMENTS_LIMIT], start=1):
            excerpt = _get_clean_text(requirement, max_chars=160)
            if excerpt:
                items.append(
                    AgentEvidenceItem(
                        ref=f"job_requirement_{index}",
                        source_type="job_requirement",
                        title="Job requirement",
                        excerpt=excerpt,
                        source_ref={"resource_type": "job", "resource_id": _first_text(job_snapshot.get("job_id"), "job")},
                        priority=50 - index,
                        reason="job_requirement",
                    )
                )

    resume_snapshot = _get_dict(context, "resume_snapshot")
    projects = resume_snapshot.get("projects") if isinstance(resume_snapshot, dict) else None
    if isinstance(projects, list):
        for index, project in enumerate(
            _related_resume_projects(projects, related_terms=_related_terms(context, evidence_refs=(*evidence_refs, progress_node_ref))),
            start=1,
        ):
            excerpt = _get_clean_text(project, max_chars=300)
            if excerpt:
                items.append(
                    AgentEvidenceItem(
                        ref=f"resume_project_{index}",
                        source_type="resume_project_evidence",
                        title="Resume project evidence",
                        excerpt=excerpt,
                        source_ref={
                            "resource_type": "resume",
                            "resource_id": _first_text(resume_snapshot.get("resume_id"), "resume"),
                        },
                        priority=40 - index,
                        reason="resume_project_evidence",
                    )
                )

    progress_node = _get_dict(context, "progress_node_snapshot")
    progress_excerpt = _first_text(progress_node.get("expected_capability"), progress_node.get("title"))
    if progress_excerpt:
        progress_ref = _first_text(progress_node.get("node_ref"), progress_node.get("progress_node_ref"), _get_text(context, "progress_node_ref"), "progress_node")
        items.append(
            AgentEvidenceItem(
                ref=progress_ref,
                source_type="progress_node_summary",
                title=_first_text(progress_node.get("title"), "Progress node"),
                excerpt=progress_excerpt,
                source_ref={"resource_type": "progress_node", "resource_id": progress_ref},
                priority=75,
                reason="progress_node_summary",
            )
        )

    return _dedupe_and_limit_evidence_items(items)


def _dedupe_and_limit_evidence_items(items: list[AgentEvidenceItem]) -> list[AgentEvidenceItem]:
    deduped: dict[str, AgentEvidenceItem] = {}
    for item in sorted(items, key=lambda candidate: candidate.priority, reverse=True):
        if item.ref not in deduped:
            deduped[item.ref] = item
    return list(deduped.values())[:_EVIDENCE_ITEMS_LIMIT]


def _compact_question_sources(values: list[Any], *, evidence_refs: tuple[str, ...] = ()) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    for index, source in enumerate(_matching_question_sources(values, evidence_refs=evidence_refs), start=1):
        if not isinstance(source, dict):
            continue
        ref = _first_text(source.get("ref"), source.get("ref_id"), source.get("source_ref"), f"question_source_{index}")
        sources.append(
            {
                "ref": ref,
                "source_type": _first_text(source.get("source_type"), "question_source"),
                "title": _first_text(source.get("title"), source.get("source_type"), "Question source"),
                "summary": _first_text_limited(source.get("summary"), source.get("excerpt"), max_chars=300),
            }
        )
    return sources


def _matching_question_sources(values: list[Any], *, evidence_refs: tuple[str, ...] = ()) -> list[Any]:
    refs = {ref for ref in evidence_refs if ref}
    if not refs:
        return values[:_QUESTION_SOURCE_LIMIT]
    matched: list[Any] = []
    for source in values:
        if not isinstance(source, dict):
            continue
        source_refs = {
            _first_text(source.get("ref")),
            _first_text(source.get("ref_id")),
            _first_text(source.get("source_ref")),
        }
        if refs & {ref for ref in source_refs if ref}:
            matched.append(source)
        if len(matched) >= _QUESTION_SOURCE_LIMIT:
            break
    return matched


def _compact_same_question_answers(values: list[Any]) -> list[dict[str, object]]:
    answers: list[dict[str, object]] = []
    for index, answer in enumerate(values[:_SAME_QUESTION_ANSWERS_LIMIT], start=1):
        if not isinstance(answer, dict):
            continue
        answers.append(
            {
                "answer_id": _first_text(answer.get("answer_id"), answer.get("ref"), f"same_question_answer_{index}"),
                "answer_round": _get_clean_text(answer.get("answer_round"), max_chars=20),
                "answer_summary": _first_text_limited(answer.get("answer_summary"), answer.get("summary"), max_chars=240),
                "feedback_summary": _first_text_limited(answer.get("feedback_summary"), max_chars=240),
                "loss_point_ids": _string_list(answer.get("loss_point_ids"), max_chars=120)[:5],
                "covered_points": _string_list(answer.get("covered_points"), max_chars=120)[:5],
                "missing_points": _string_list(answer.get("missing_points"), max_chars=120)[:5],
            }
        )
    return answers


def _compact_recent_turns(values: list[Any]) -> list[dict[str, object]]:
    turns: list[dict[str, object]] = []
    for index, turn in enumerate(values[-_SESSION_RECENT_TURNS_LIMIT:], start=1):
        if not isinstance(turn, dict):
            continue
        turns.append(
            {
                "question_id": _first_text(turn.get("question_id"), turn.get("ref"), f"recent_turn_{index}"),
                "answer_id": _first_text(turn.get("answer_id")),
                "answer_round": _get_clean_text(turn.get("answer_round"), max_chars=20),
                "progress_node_ref": _first_text(turn.get("progress_node_ref")),
                "question_summary": _first_text_limited(turn.get("question_summary"), turn.get("question_text"), max_chars=500),
                "answer_summary": _first_text_limited(turn.get("answer_summary"), max_chars=700),
                "feedback_summary": _first_text_limited(turn.get("feedback_summary"), max_chars=700),
            }
        )
    return turns


def _compact_question_metadata(value: dict[str, Any]) -> dict[str, object]:
    return {
        "expected_answer_dimensions": _string_list(value.get("expected_answer_dimensions"), max_chars=160)[:5],
        "focus_dimension": _first_text_limited(value.get("focus_dimension"), max_chars=160),
        "focus_key": _first_text_limited(value.get("focus_key"), max_chars=160),
        "source_availability": _first_text_limited(value.get("source_availability"), max_chars=80),
    }


def _compact_canonical_project_assets(value: dict[str, Any]) -> dict[str, object]:
    items = _canonical_project_asset_items(value)
    return {
        "available": bool(value.get("available")) and bool(items),
        "selection_policy": _first_text(value.get("selection_policy"), "rule_based_keyword_overlap_v1"),
        "items": items,
    }


def _canonical_project_asset_items(value: dict[str, Any]) -> list[dict[str, object]]:
    raw_items = value.get("items") if isinstance(value.get("items"), list) else []
    items: list[dict[str, object]] = []
    for index, item in enumerate(raw_items[:_PROJECT_ASSET_SUMMARIES_LIMIT], start=1):
        if not isinstance(item, dict):
            continue
        if _first_text(item.get("status")) != "asset_confirmed":
            continue
        items.append(
            {
                "asset_id": _first_text(item.get("asset_id"), f"canonical_asset_{index}"),
                "status": _first_text(item.get("status")),
                "asset_type": _first_text(item.get("asset_type")),
                "title": _first_text(item.get("title"), "Canonical project asset"),
                "summary": _first_text_limited(item.get("summary"), max_chars=700),
                "content_excerpt": _first_text_limited(item.get("content_excerpt"), max_chars=360),
                "source_refs": _safe_ref_list(item.get("source_refs")),
                "evidence_refs": _safe_ref_list(item.get("evidence_refs")),
                "current_version_id": _first_text(item.get("current_version_id")),
                "priority": item.get("priority") if isinstance(item.get("priority"), int) else None,
                "relevance_reason": _first_text_limited(item.get("relevance_reason"), max_chars=160),
            }
        )
    return items


def _compact_project_asset_summaries(values: list[Any]) -> list[dict[str, object]]:
    assets: list[dict[str, object]] = []
    for index, asset in enumerate(values[:_PROJECT_ASSET_SUMMARIES_LIMIT], start=1):
        if not isinstance(asset, dict):
            continue
        assets.append(
            {
                "asset_id": _first_text(asset.get("asset_id"), asset.get("asset_ref"), asset.get("ref"), f"asset_{index}"),
                "title": _first_text(asset.get("title"), "Project asset"),
                "summary": _first_text_limited(asset.get("summary"), asset.get("excerpt"), max_chars=900),
            }
        )
    return assets


def _compact_job_snapshot(value: dict[str, Any]) -> dict[str, object]:
    if not value:
        return {}
    return {
        "job_id": _first_text(value.get("job_id")),
        "job_version_id": _first_text(value.get("job_version_id")),
        "title": _first_text_limited(value.get("title"), max_chars=200),
        "company": _first_text_limited(value.get("company"), max_chars=200),
        "requirements": _string_list(value.get("requirements"), max_chars=160)[:_JOB_REQUIREMENTS_LIMIT],
        "responsibilities": _string_list(value.get("responsibilities"), max_chars=160)[:_JOB_REQUIREMENTS_LIMIT],
        "content_digest": _first_text_limited(value.get("content_digest"), max_chars=200),
    }


def _compact_resume_snapshot(value: dict[str, Any], *, related_terms: tuple[str, ...] = ()) -> dict[str, object]:
    if not value:
        return {}
    return {
        "resume_id": _first_text(value.get("resume_id")),
        "resume_version_id": _first_text(value.get("resume_version_id")),
        "title": _first_text_limited(value.get("title"), max_chars=200),
        "summary": _first_text_limited(value.get("summary"), max_chars=300),
        "projects": _related_resume_projects(_string_list(value.get("projects"), max_chars=300), related_terms=related_terms),
        "content_digest": _first_text_limited(value.get("content_digest"), max_chars=200),
    }


def _compact_progress_node_snapshot(value: dict[str, Any]) -> dict[str, object]:
    if not value:
        return {}
    return {
        "node_ref": _first_text(value.get("node_ref"), value.get("progress_node_ref")),
        "progress_node_ref": _first_text(value.get("progress_node_ref"), value.get("node_ref")),
        "title": _first_text_limited(value.get("title"), max_chars=200),
        "question_title": _first_text_limited(value.get("question_title"), value.get("current_question_title"), max_chars=200),
        "expected_capability": _first_text_limited(value.get("expected_capability"), value.get("description"), max_chars=200),
        "missing_points": _string_list(value.get("missing_points"), max_chars=120)[:3],
        "related_job_requirements": _string_list(value.get("related_job_requirements"), max_chars=120)[:2],
        "related_resume_evidence": _string_list(value.get("related_resume_evidence"), max_chars=120)[:2],
    }


def _focus_target(context: object) -> AgentFocusTarget:
    progress_node = _get_dict(context, "progress_node_snapshot")
    answer_id = _get_text(context, "answer_id") or "current_answer"
    question_id = _get_text(context, "question_id") or "current_question"
    expected_capability = _first_text(
        progress_node.get("expected_capability"),
        progress_node.get("description"),
        _get_text(context, "polish_theme"),
        "Generate actionable polish feedback.",
    )
    return AgentFocusTarget(
        ref=answer_id,
        title=_first_text(progress_node.get("question_title"), progress_node.get("current_question_title"), question_id),
        expected_capability=expected_capability,
        missing_points=tuple(_string_list(progress_node.get("missing_points"))),
        metadata={
            "session_id": _get_text(context, "session_id"),
            "question_id": question_id,
            "progress_node_ref": _first_text(_get_text(context, "progress_node_ref"), progress_node.get("node_ref")),
            "answer_round": _get_clean_text(_get(context, "answer_round"), max_chars=20),
            "polish_theme": _get_text(context, "polish_theme", max_chars=200),
        },
    )


def _related_terms(context: object, *, evidence_refs: tuple[str, ...] = ()) -> tuple[str, ...]:
    progress_node = _get_dict(context, "progress_node_snapshot")
    question_sources = _get_list(context, "question_sources")
    terms = [
        _get_text(context, "polish_theme", max_chars=120),
        _get_text(context, "progress_node_ref", max_chars=120),
        _first_text(progress_node.get("title"), progress_node.get("question_title")),
        _first_text(progress_node.get("expected_capability")),
    ]
    for source in _matching_question_sources(question_sources, evidence_refs=evidence_refs):
        if not isinstance(source, dict):
            continue
        terms.append(_first_text(source.get("title"), source.get("summary"), source.get("excerpt")))
    return tuple(dict.fromkeys(term for term in (_get_clean_text(value, max_chars=120) for value in terms) if term))


def _related_resume_projects(projects: list[Any], *, related_terms: tuple[str, ...] = ()) -> list[str]:
    project_texts = _string_list(projects, max_chars=300)
    if not project_texts:
        return []
    normalized_terms = [term.casefold() for term in related_terms if len(term) >= 3]
    matched = [
        project
        for project in project_texts
        if any(term in project.casefold() or project.casefold() in term for term in normalized_terms)
    ]
    if matched:
        return matched[:_RESUME_PROJECTS_LIMIT]
    if normalized_terms:
        return []
    return project_texts[:1]


def _safe_ref_list(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value[:5]:
        if not isinstance(item, dict):
            continue
        cleaned = {
            str(key): text
            for key, raw_value in item.items()
            if (text := _get_clean_text(raw_value, max_chars=120))
        }
        if cleaned:
            refs.append(cleaned)
    return refs


def _safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _get(context: object, field_name: str) -> object:
    if isinstance(context, dict):
        return context.get(field_name)
    return getattr(context, field_name, None)


def _get_text(context: object, field_name: str, *, max_chars: int = 240) -> str:
    value = _get(context, field_name)
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _get_dict(context: object, field_name: str) -> dict[str, Any]:
    value = _get(context, field_name)
    if not isinstance(value, dict):
        return {}
    return deepcopy(value)


def _get_list(context: object, field_name: str) -> list[Any]:
    value = _get(context, field_name)
    if not isinstance(value, (list, tuple)):
        return []
    return deepcopy(list(value))


def _source_ref(value: dict[str, Any]) -> dict[str, Any]:
    ref: dict[str, Any] = {}
    for key in _SOURCE_REF_KEYS:
        text = _get_clean_text(value.get(key), max_chars=200)
        if text:
            ref[key] = text
    return ref


def _string_list(value: object, *, max_chars: int = 240) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [text for item in value if (text := _get_clean_text(item, max_chars=max_chars))]


def _first_text(*values: object) -> str:
    for value in values:
        text = _get_clean_text(value)
        if text:
            return text
    return ""


def _first_text_limited(*values: object, max_chars: int) -> str:
    return _get_clean_text(_first_text(*values), max_chars=max_chars)


def _get_clean_text(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _safe_value(value: object) -> object:
    if isinstance(value, dict):
        safe: dict[str, object] = {}
        for key, nested in value.items():
            if not isinstance(key, str) or key.lower() in _UNSAFE_CONTEXT_KEYS:
                continue
            safe[key] = _safe_value(nested)
        return safe
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    return deepcopy(value)


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))
