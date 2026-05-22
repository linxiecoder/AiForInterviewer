"""Deterministic candidate extraction for polish feedback payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import re
from typing import Any


class CandidateType(str, Enum):
    WEAKNESS = "weakness_candidate"
    ASSET = "asset_candidate"
    TRAINING_SUGGESTION = "training_suggestion_candidate"
    ORAL_SCRIPT = "oral_script_candidate"
    POLISHED_ANSWER = "polished_answer_candidate"


class CandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    MERGED = "merged"
    ARCHIVED = "archived"


class CandidateSourceType(str, Enum):
    STRUCTURED_FEEDBACK = "structured_feedback"
    RETRY_DELTA = "retry_delta"
    LEGACY_FEEDBACK = "legacy_feedback"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class PolishCandidate:
    candidate_id: str
    candidate_type: CandidateType
    owner_id: str
    source_type: CandidateSourceType
    source_refs: tuple[dict[str, Any], ...]
    evidence_refs: tuple[dict[str, Any], ...]
    trace_refs: tuple[dict[str, Any], ...]
    session_id: str
    question_id: str
    answer_id: str
    feedback_id: str
    title: str
    summary: str
    evidence_excerpt: str
    reason: str
    confidence_level: str
    merge_key: str
    created_at: datetime
    updated_at: datetime
    feedback_id_ref: str | None = None
    merge_target_candidate_id: str | None = None
    target_formal_ref: dict[str, Any] | None = None
    status: CandidateStatus = CandidateStatus.CANDIDATE
    user_confirmation_required: bool = True
    candidate_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateExtractionInput:
    owner_id: str
    session_id: str
    question_id: str
    answer_id: str
    feedback_id: str
    score_result_id: str | None
    feedback_payload: dict[str, Any]
    question_metadata: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


FORBIDDEN_CANDIDATE_KEYS = frozenset(
    {
        "prompt",
        "raw_prompt",
        "system_prompt",
        "completion",
        "raw_completion",
        "provider_payload",
        "raw_provider_payload",
        "provider_response",
        "raw_provider_response",
        "hidden_rubric",
        "full_evidence_text",
        "full_resume_markdown",
        "resume_markdown",
        "full_jd",
        "job_description",
        "token",
        "api_key",
        "cookie",
        "secret",
    }
)
_MAX_TEXT_LENGTH = 220
_LOW_SCORE_THRESHOLD = 60
_HIGH_SCORE_THRESHOLD = 80
_MAX_WEAKNESS_CANDIDATES = 5
_MAX_ASSET_CANDIDATES = 8
_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"raw\s+prompt", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"raw\s+completion", re.IGNORECASE),
    re.compile(r"provider\s+payload", re.IGNORECASE),
    re.compile(r"hidden\s+rubric", re.IGNORECASE),
    re.compile(r"full\s+evidence\s+text", re.IGNORECASE),
    re.compile(r"full\s+resume\s+markdown", re.IGNORECASE),
    re.compile(r"full\s+jd", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"(?:token|secret)\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_-]{6,}"),
)


def extract_feedback_candidates(extraction_input: CandidateExtractionInput) -> dict[str, Any]:
    payload = normalize_candidate_payload(extraction_input.feedback_payload)
    if not isinstance(payload, dict):
        payload = {}

    if not _has_structured_candidate_material(payload):
        payload["weakness_candidates"] = []
        payload["asset_candidates"] = []
        payload["training_suggestion_candidates"] = []
        payload["oral_script_candidates"] = []
        payload["polished_answer_candidates"] = []
        payload["candidate_refs"] = _safe_candidate_refs(payload.get("candidate_refs"))
        return payload

    weakness_candidates = extract_weakness_candidates(extraction_input)
    asset_like_candidates = extract_asset_candidates(extraction_input)
    training_candidates = extract_training_suggestion_candidates(extraction_input)

    asset_candidates = [
        candidate for candidate in asset_like_candidates if candidate.candidate_type == CandidateType.ASSET
    ]
    oral_script_candidates = [
        candidate for candidate in asset_like_candidates if candidate.candidate_type == CandidateType.ORAL_SCRIPT
    ]
    polished_answer_candidates = [
        candidate for candidate in asset_like_candidates if candidate.candidate_type == CandidateType.POLISHED_ANSWER
    ]

    payload["weakness_candidates"] = [safe_candidate_dict(candidate) for candidate in weakness_candidates]
    payload["asset_candidates"] = [safe_candidate_dict(candidate) for candidate in asset_candidates]
    payload["training_suggestion_candidates"] = [safe_candidate_dict(candidate) for candidate in training_candidates]
    payload["oral_script_candidates"] = [safe_candidate_dict(candidate) for candidate in oral_script_candidates]
    payload["polished_answer_candidates"] = [
        safe_candidate_dict(candidate) for candidate in polished_answer_candidates
    ]
    payload["candidate_refs"] = _candidate_refs(
        [
            *weakness_candidates,
            *asset_candidates,
            *training_candidates,
            *oral_script_candidates,
            *polished_answer_candidates,
        ]
    )
    return payload


def extract_weakness_candidates(extraction_input: CandidateExtractionInput) -> list[PolishCandidate]:
    payload = extraction_input.feedback_payload
    loss_points = _dict_items(payload.get("loss_points"))
    loss_by_id = {str(point.get("loss_point_id")): point for point in loss_points if point.get("loss_point_id")}
    candidates: list[PolishCandidate] = []
    seen_merge_keys: set[str] = set()

    for loss_ref in _string_items(payload.get("repeated_loss_points")):
        point = loss_by_id.get(loss_ref)
        title = _candidate_title(point, fallback=loss_ref)
        confidence_level = "high" if point else "medium"
        source_refs = _base_source_refs(extraction_input) + _loss_source_refs(point, loss_ref)
        evidence_refs = _loss_evidence_refs(point, loss_ref)
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.WEAKNESS,
            source_type=CandidateSourceType.RETRY_DELTA,
            source_refs=source_refs,
            evidence_refs=evidence_refs,
            title=title,
            summary=f"同一缺口在本 session 内重复出现：{title}",
            evidence_excerpt=_loss_excerpt(point, loss_ref),
            reason="repeated_loss_points 表明该问题尚未收敛，需要用户确认是否沉淀为薄弱项。",
            confidence_level=confidence_level,
            dimension_id=_dimension_id(point),
            source_category="repeated_loss_point",
            candidate_payload={
                "source_loss_point_id": _loss_point_id(point, loss_ref),
                "formal_write_intent": False,
            },
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    for point in loss_points:
        if str(point.get("loss_point_id")) in set(_string_items(payload.get("repeated_loss_points"))):
            continue
        if not _is_critical_loss_point(point):
            continue
        title = _candidate_title(point, fallback="关键失分点")
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.WEAKNESS,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input) + _loss_source_refs(point, None),
            evidence_refs=_loss_evidence_refs(point, None),
            title=title,
            summary=f"关键失分点提示需要补齐：{title}",
            evidence_excerpt=_loss_excerpt(point, ""),
            reason="critical loss_points 可生成待确认 weakness candidate，但本阶段不写正式 Weakness。",
            confidence_level="medium",
            dimension_id=_dimension_id(point),
            source_category="critical_loss_point",
            candidate_payload={
                "source_loss_point_id": _loss_point_id(point, ""),
                "formal_write_intent": False,
            },
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    for dimension in _dict_items(payload.get("scoring_dimensions")):
        if int(dimension.get("score_value") or 100) > _LOW_SCORE_THRESHOLD:
            continue
        dimension_id = str(dimension.get("dimension_id") or "low_score_dimension")
        title = _title_for_dimension(dimension_id)
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.WEAKNESS,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input)
            + (_resource_ref("score_dimension", dimension_id),),
            evidence_refs=(_resource_ref("score_dimension", dimension_id),),
            title=title,
            summary=f"{dimension_id} 维度分数偏低，需要用户确认是否作为候选薄弱项。",
            evidence_excerpt=f"{dimension_id}: {dimension.get('score_value')}",
            reason="低分维度只能生成 candidate，不直接写正式 Weakness。",
            confidence_level="medium",
            dimension_id=dimension_id,
            source_category="low_scoring_dimension",
            candidate_payload={"score_value": dimension.get("score_value"), "formal_write_intent": False},
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    for gap in [*_string_items(payload.get("technical_gaps")), *_string_items(payload.get("communication_gaps"))]:
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.WEAKNESS,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input),
            evidence_refs=(_resource_ref("feedback_gap", _stable_hash(gap)),),
            title=_short_text(gap, 80),
            summary=f"反馈中仍有未闭合缺口：{_short_text(gap, 100)}",
            evidence_excerpt=_short_text(gap),
            reason="technical_gaps / communication_gaps 只作为候选来源，需要用户确认。",
            confidence_level="low",
            dimension_id=None,
            source_category="feedback_gap",
            candidate_payload={"formal_write_intent": False},
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    return candidates[:_MAX_WEAKNESS_CANDIDATES]


def extract_asset_candidates(extraction_input: CandidateExtractionInput) -> list[PolishCandidate]:
    payload = extraction_input.feedback_payload
    score_value = _score_value(payload)
    if score_value is not None and score_value < _LOW_SCORE_THRESHOLD:
        return []

    candidates: list[PolishCandidate] = []
    seen_merge_keys: set[str] = set()
    for point in _dict_items(payload.get("positive_evidence_points")):
        point_id = str(point.get("point_id") or _stable_hash(str(point)))
        title = _short_text(point.get("title") or "候选亮点", 80)
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.ASSET,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input) + (_resource_ref("positive_evidence_point", point_id),),
            evidence_refs=(_resource_ref("positive_evidence_point", point_id),),
            title=title,
            summary=f"回答中出现可复用亮点：{title}",
            evidence_excerpt=_short_text(point.get("evidence_excerpt") or point.get("reason") or title),
            reason="positive_evidence_points 可生成 asset candidate，但不自动写正式 Asset。",
            confidence_level=_confidence(point.get("confidence_level"), default="medium"),
            dimension_id=str(point.get("dimension_id") or ""),
            source_category="positive_evidence_point",
            candidate_payload={
                "source_positive_evidence_point_id": point_id,
                "fact_source": "user_fact",
                "model_suggested": False,
                "formal_write_intent": False,
            },
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    for dimension in _dict_items(payload.get("scoring_dimensions")):
        if int(dimension.get("score_value") or 0) < _HIGH_SCORE_THRESHOLD:
            continue
        dimension_id = str(dimension.get("dimension_id") or "high_score_dimension")
        title = f"{_title_for_dimension(dimension_id)}表现较好"
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.ASSET,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input)
            + (_resource_ref("score_dimension", dimension_id),),
            evidence_refs=(_resource_ref("score_dimension", dimension_id),),
            title=title,
            summary=f"{dimension_id} 维度达到较高分，可作为候选素材等待确认。",
            evidence_excerpt=f"{dimension_id}: {dimension.get('score_value')}",
            reason="高分维度只生成 asset candidate，避免未经确认写正式资产。",
            confidence_level="medium",
            dimension_id=dimension_id,
            source_category="high_scoring_dimension",
            candidate_payload={"fact_source": "score_signal", "model_suggested": False},
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    for strength in _string_items(_dict_value(payload.get("answer_diagnosis"), "strengths")):
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.ASSET,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input),
            evidence_refs=(_resource_ref("answer_diagnosis_strength", _stable_hash(strength)),),
            title=_short_text(strength, 80),
            summary=f"answer_diagnosis 中识别到候选亮点：{_short_text(strength, 100)}",
            evidence_excerpt=_short_text(strength),
            reason="answer_diagnosis strength 只作为候选素材，需用户确认。",
            confidence_level="low",
            dimension_id=None,
            source_category="answer_diagnosis_strength",
            candidate_payload={"fact_source": "user_fact", "model_suggested": False},
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    oral_script = _short_text(payload.get("oral_script"))
    if oral_script:
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.ORAL_SCRIPT,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input)
            + (_resource_ref("oral_script", f"{extraction_input.feedback_id}:oral_script"),),
            evidence_refs=(_resource_ref("oral_script", f"{extraction_input.feedback_id}:oral_script"),),
            title="口语化表达候选",
            summary="模型建议的口语化表达模板，需用户确认后才能沉淀。",
            evidence_excerpt=oral_script,
            reason="oral_script 属于 model_suggested_phrasing，不能直接归档为正式 Asset。",
            confidence_level="medium",
            dimension_id=None,
            source_category="oral_script",
            candidate_payload={
                "model_suggested": True,
                "fact_source": "model_suggested_phrasing",
                "formal_write_intent": False,
            },
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    polished_answer = _short_text(payload.get("p7_reference_answer"))
    if polished_answer:
        candidate = _build_candidate(
            extraction_input,
            candidate_type=CandidateType.POLISHED_ANSWER,
            source_type=CandidateSourceType.STRUCTURED_FEEDBACK,
            source_refs=_base_source_refs(extraction_input)
            + (_resource_ref("p7_reference_answer", f"{extraction_input.feedback_id}:p7_reference_answer"),),
            evidence_refs=(
                _resource_ref("p7_reference_answer", f"{extraction_input.feedback_id}:p7_reference_answer"),
            ),
            title="高阶参考回答候选",
            summary="模型建议的高阶回答表达，需用户确认后才能进入资产或训练材料。",
            evidence_excerpt=polished_answer,
            reason="p7_reference_answer 是 model_suggested_phrasing，本阶段只作为 polished answer candidate。",
            confidence_level="medium",
            dimension_id=None,
            source_category="p7_reference_answer",
            candidate_payload={
                "model_suggested": True,
                "fact_source": "model_suggested_phrasing",
                "formal_write_intent": False,
            },
        )
        _append_unique_candidate(candidates, candidate, seen_merge_keys)

    return candidates[:_MAX_ASSET_CANDIDATES]


def extract_training_suggestion_candidates(extraction_input: CandidateExtractionInput) -> list[PolishCandidate]:
    payload = extraction_input.feedback_payload
    mastery_status = str(payload.get("mastery_status") or "")
    remaining_gaps = _string_items(payload.get("remaining_gaps"))
    repeated_loss_points = _string_items(payload.get("repeated_loss_points"))
    next_retry_focus = _dict_items(payload.get("next_retry_focus"))
    loss_points = _dict_items(payload.get("loss_points"))
    should_continue_same_question = bool(payload.get("should_continue_same_question"))
    should_generate_next_question = bool(payload.get("should_generate_next_question"))
    if not any(
        [
            mastery_status,
            remaining_gaps,
            repeated_loss_points,
            next_retry_focus,
            loss_points,
            should_continue_same_question,
            should_generate_next_question,
        ]
    ):
        return []

    if mastery_status in {"stuck", "regressed"} or (should_continue_same_question and loss_points):
        title = "同题重答训练建议"
        summary = "当前 mastery_status 表明同题尚未收敛，建议围绕重复缺口重答。"
        confidence_level = "high" if repeated_loss_points else "medium"
        source_type = CandidateSourceType.RETRY_DELTA
    elif mastery_status == "mastered":
        title = "进入下一题训练建议"
        summary = "当前题目已基本掌握，可候选推荐生成下一题继续训练。"
        confidence_level = "medium"
        source_type = CandidateSourceType.STRUCTURED_FEEDBACK
    else:
        title = "剩余缺口专项练习建议"
        summary = "当前回答仍有 remaining_gaps / next_retry_focus，可候选生成专项练习。"
        confidence_level = "medium" if remaining_gaps or next_retry_focus else "low"
        source_type = CandidateSourceType.RETRY_DELTA

    direct_loss_point_ids = [
        str(point["loss_point_id"])
        for point in loss_points
        if point.get("loss_point_id")
    ]
    loss_refs = tuple(
        _resource_ref("loss_point", value)
        for value in [*remaining_gaps, *repeated_loss_points, *direct_loss_point_ids]
        if _looks_like_ref_id(value)
    )
    focus_refs = tuple(
        _resource_ref("next_retry_focus", str(item.get("focus_id") or _stable_hash(str(item))))
        for item in next_retry_focus
    )
    candidate = _build_candidate(
        extraction_input,
        candidate_type=CandidateType.TRAINING_SUGGESTION,
        source_type=source_type,
        source_refs=_base_source_refs(extraction_input) + loss_refs + focus_refs,
        evidence_refs=loss_refs + focus_refs or (_resource_ref("mastery_status", mastery_status or "unknown"),),
        title=title,
        summary=summary,
        evidence_excerpt=_short_text(
            "; ".join(
                [
                    *remaining_gaps,
                    *[str(item.get("title") or item.get("reason") or item.get("focus_id") or "next_retry_focus") for item in next_retry_focus],
                    *[str(point.get("title") or point.get("loss_point_id")) for point in loss_points],
                ]
            )
        ),
        reason="训练建议候选来自 retry delta / mastery_status，本阶段不写正式 TrainingRecommendation。",
        confidence_level=confidence_level,
        dimension_id=None,
        source_category=mastery_status or "training_suggestion",
        candidate_payload={
            "mastery_status": mastery_status or None,
            "should_continue_same_question": should_continue_same_question,
            "should_generate_next_question": should_generate_next_question,
            "question_pattern": _question_pattern(extraction_input),
            "expected_answer_dimensions": _expected_answer_dimensions(extraction_input),
            "formal_write_intent": False,
        },
    )
    return [candidate]


def build_candidate_merge_key(
    *,
    owner_id: str,
    candidate_type: CandidateType | str,
    normalized_title: str,
    question_pattern: str | None,
    dimension_id: str | None,
    source_type: CandidateSourceType | str,
) -> str:
    candidate_type_value = _enum_value(candidate_type)
    source_type_value = _enum_value(source_type)
    owner_hash = _stable_hash(owner_id, size=12)
    title = _normalize_merge_component(normalized_title)
    pattern = _normalize_merge_component(question_pattern or "unknown_pattern")
    dimension = _normalize_merge_component(dimension_id or "unknown_dimension")
    return f"{candidate_type_value}:{owner_hash}:{title}:{pattern}:{dimension}:{source_type_value}"


_REDACTED_SENSITIVE_DETAIL = "redacted_sensitive_detail"
_FORBIDDEN_CANDIDATE_KEY_OVERRIDES = frozenset({"full_resume"})
_FORBIDDEN_CANDIDATE_VALUE_MARKERS = (
    "raw_prompt",
    "system_prompt",
    "raw_completion",
    "completion",
    "provider_payload",
    "raw_provider_payload",
    "provider_response",
    "raw_provider_response",
    "hidden_rubric",
    "full_evidence_text",
    "full_resume",
    "full_resume_markdown",
    "full_jd",
    "full_jd_text",
)
_FORBIDDEN_CANDIDATE_ASSIGNMENT_PATTERNS = (
    re.compile(r"api[_-]?key\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"token\s*=\s*[^\s,;，；]+", re.IGNORECASE),
    re.compile(r"secret\s*=\s*[^\s,;，；]+", re.IGNORECASE),
)


def _is_forbidden_candidate_key(key: str) -> bool:
    normalized = key.strip().lower()
    return (
        normalized in FORBIDDEN_CANDIDATE_KEYS
        or normalized in _FORBIDDEN_CANDIDATE_KEY_OVERRIDES
        or "prompt" in normalized
    )


def _normalized_sensitive_marker_text(value: str) -> str:
    return re.sub(r"[\s-]+", "_", value.lower())


def _has_forbidden_candidate_value(value: str) -> bool:
    normalized = _normalized_sensitive_marker_text(value)
    if any(marker in normalized for marker in _FORBIDDEN_CANDIDATE_VALUE_MARKERS):
        return True
    if any(pattern.search(value) for pattern in _FORBIDDEN_VALUE_PATTERNS):
        return True
    return any(pattern.search(value) for pattern in _FORBIDDEN_CANDIDATE_ASSIGNMENT_PATTERNS)

def normalize_candidate_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): normalize_candidate_payload(item)
            for key, item in value.items()
            if not _is_forbidden_candidate_key(str(key))
        }
    if isinstance(value, list):
        return [normalize_candidate_payload(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_candidate_payload(item) for item in value]
    if isinstance(value, str):
        return _redact_forbidden_text(value)
    return value


def safe_candidate_dict(candidate: PolishCandidate) -> dict[str, Any]:
    raw = asdict(candidate)
    raw["candidate_type"] = candidate.candidate_type.value
    raw["source_type"] = candidate.source_type.value
    raw["status"] = candidate.status.value
    raw["created_at"] = _isoformat(candidate.created_at)
    raw["updated_at"] = _isoformat(candidate.updated_at)
    raw["feedback_id"] = candidate.feedback_id
    raw.pop("feedback_id_ref", None)
    return normalize_candidate_payload(raw)


def _build_candidate(
    extraction_input: CandidateExtractionInput,
    *,
    candidate_type: CandidateType,
    source_type: CandidateSourceType,
    source_refs: tuple[dict[str, Any], ...],
    evidence_refs: tuple[dict[str, Any], ...],
    title: str,
    summary: str,
    evidence_excerpt: str,
    reason: str,
    confidence_level: str,
    dimension_id: str | None,
    source_category: str,
    candidate_payload: dict[str, Any] | None = None,
) -> PolishCandidate:
    created_at = extraction_input.created_at or datetime.utcnow()
    updated_at = extraction_input.updated_at or created_at
    safe_title = _short_text(title, 100) or "候选对象"
    question_pattern = _question_pattern(extraction_input)
    merge_key = build_candidate_merge_key(
        owner_id=extraction_input.owner_id,
        candidate_type=candidate_type,
        normalized_title=safe_title,
        question_pattern=question_pattern,
        dimension_id=dimension_id or source_category,
        source_type=source_type,
    )
    candidate_id = _candidate_id(
        extraction_input=extraction_input,
        candidate_type=candidate_type,
        merge_key=merge_key,
        evidence_refs=evidence_refs,
    )
    return PolishCandidate(
        candidate_id=candidate_id,
        candidate_type=candidate_type,
        owner_id=extraction_input.owner_id,
        source_type=source_type,
        source_refs=_unique_refs(source_refs),
        evidence_refs=_unique_refs(evidence_refs),
        trace_refs=_trace_refs(extraction_input),
        session_id=extraction_input.session_id,
        question_id=extraction_input.question_id,
        answer_id=extraction_input.answer_id,
        feedback_id=extraction_input.feedback_id,
        title=safe_title,
        summary=_short_text(summary),
        evidence_excerpt=_short_text(evidence_excerpt),
        reason=_short_text(reason),
        confidence_level=_confidence(confidence_level),
        merge_key=merge_key,
        created_at=created_at,
        updated_at=updated_at,
        candidate_payload=normalize_candidate_payload(candidate_payload or {}),
    )


def _has_structured_candidate_material(payload: dict[str, Any]) -> bool:
    if str(payload.get("status") or "") == "pending":
        return False
    structured_fields = (
        "loss_points",
        "repeated_loss_points",
        "remaining_gaps",
        "technical_gaps",
        "communication_gaps",
        "positive_evidence_points",
        "oral_script",
        "p7_reference_answer",
        "next_retry_focus",
        "scoring_dimensions",
        "answer_diagnosis",
    )
    return any(bool(payload.get(field_name)) for field_name in structured_fields)


def _base_source_refs(extraction_input: CandidateExtractionInput) -> tuple[dict[str, Any], ...]:
    refs = [
        _resource_ref("polish_session", extraction_input.session_id),
        _resource_ref("question", extraction_input.question_id),
        _resource_ref("answer", extraction_input.answer_id),
        _resource_ref("feedback", extraction_input.feedback_id),
    ]
    score_result_id = _score_result_id(extraction_input)
    if score_result_id:
        refs.append(_resource_ref("score_result", score_result_id))
    question_pattern = _question_pattern(extraction_input)
    if question_pattern:
        refs.append(_resource_ref("question_pattern", question_pattern))
    if extraction_input.question_metadata:
        refs.append(_resource_ref("question_metadata", f"{extraction_input.question_id}:metadata"))
    return _unique_refs(tuple(refs))


def _trace_refs(extraction_input: CandidateExtractionInput) -> tuple[dict[str, Any], ...]:
    created_at = extraction_input.created_at
    refs = [
        _trace_ref("question", extraction_input.question_id, created_at),
        _trace_ref("answer", extraction_input.answer_id, created_at),
        _trace_ref("feedback", extraction_input.feedback_id, created_at),
    ]
    score_result_id = _score_result_id(extraction_input)
    if score_result_id:
        refs.append(_trace_ref("score_result", score_result_id, created_at))
    return tuple(refs)


def _candidate_refs(candidates: list[PolishCandidate]) -> list[dict[str, str]]:
    return [
        {"resource_type": candidate.candidate_type.value, "resource_id": candidate.candidate_id}
        for candidate in candidates
    ]


def _safe_candidate_refs(value: Any) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in _dict_items(value):
        resource_type = str(item.get("resource_type") or "")
        resource_id = str(item.get("resource_id") or "")
        if resource_type.endswith("_candidate") and resource_id:
            refs.append({"resource_type": resource_type, "resource_id": resource_id})
    return refs


def _append_unique_candidate(
    candidates: list[PolishCandidate],
    candidate: PolishCandidate,
    seen_merge_keys: set[str],
) -> None:
    if candidate.merge_key in seen_merge_keys:
        return
    seen_merge_keys.add(candidate.merge_key)
    candidates.append(candidate)


def _loss_source_refs(point: dict[str, Any] | None, fallback: str | None) -> tuple[dict[str, Any], ...]:
    loss_point_id = _loss_point_id(point, fallback or "")
    refs = [_resource_ref("loss_point", loss_point_id)] if loss_point_id else []
    dimension_id = _dimension_id(point)
    if dimension_id:
        refs.append(_resource_ref("score_dimension", dimension_id))
    return tuple(refs)


def _loss_evidence_refs(point: dict[str, Any] | None, fallback: str | None) -> tuple[dict[str, Any], ...]:
    loss_point_id = _loss_point_id(point, fallback or "")
    if loss_point_id:
        return (_resource_ref("loss_point", loss_point_id),)
    return (_resource_ref("feedback_gap", _stable_hash(str(fallback or "loss_point"))),)


def _loss_excerpt(point: dict[str, Any] | None, fallback: str) -> str:
    if not point:
        return _short_text(fallback)
    return _short_text(point.get("answer_excerpt") or point.get("reason") or point.get("title") or fallback)


def _loss_point_id(point: dict[str, Any] | None, fallback: str) -> str:
    if point and point.get("loss_point_id"):
        return str(point["loss_point_id"])
    return str(fallback or "")


def _candidate_title(point: dict[str, Any] | None, *, fallback: str) -> str:
    if point and point.get("title"):
        return _short_text(point["title"], 80)
    return _short_text(fallback, 80)


def _dimension_id(point: dict[str, Any] | None) -> str | None:
    if point and point.get("dimension_id"):
        return str(point["dimension_id"])
    return None


def _is_critical_loss_point(point: dict[str, Any]) -> bool:
    if bool(point.get("critical")):
        return True
    try:
        return int(point.get("deducted_points") or 0) >= 10
    except (TypeError, ValueError):
        return False


def _score_value(payload: dict[str, Any]) -> int | None:
    score_result = payload.get("score_result")
    if not isinstance(score_result, dict) or "score_value" not in score_result:
        return None
    try:
        return int(score_result["score_value"])
    except (TypeError, ValueError):
        return None


def _score_result_id(extraction_input: CandidateExtractionInput) -> str | None:
    if extraction_input.score_result_id:
        return extraction_input.score_result_id
    score_result = extraction_input.feedback_payload.get("score_result")
    if isinstance(score_result, dict) and score_result.get("score_result_id"):
        return str(score_result["score_result_id"])
    score_result_ref = extraction_input.feedback_payload.get("score_result_ref")
    if isinstance(score_result_ref, dict) and score_result_ref.get("resource_id"):
        return str(score_result_ref["resource_id"])
    return None


def _question_pattern(extraction_input: CandidateExtractionInput) -> str | None:
    metadata = extraction_input.question_metadata or {}
    if metadata.get("question_pattern"):
        return str(metadata["question_pattern"])
    payload_metadata = extraction_input.feedback_payload.get("feedback_metadata")
    if isinstance(payload_metadata, dict) and payload_metadata.get("question_pattern"):
        return str(payload_metadata["question_pattern"])
    if extraction_input.feedback_payload.get("question_pattern"):
        return str(extraction_input.feedback_payload["question_pattern"])
    return None


def _expected_answer_dimensions(extraction_input: CandidateExtractionInput) -> list[str]:
    metadata = extraction_input.question_metadata or {}
    raw_dimensions = metadata.get("expected_answer_dimensions")
    if not isinstance(raw_dimensions, list):
        raw_dimensions = extraction_input.feedback_payload.get("expected_answer_dimensions")
    if not isinstance(raw_dimensions, list):
        return []
    return [str(item) for item in raw_dimensions if str(item).strip()]


def _resource_ref(resource_type: str, resource_id: str) -> dict[str, Any]:
    return {"resource_type": resource_type, "resource_id": str(resource_id)}


def _trace_ref(resource_type: str, resource_id: str, created_at: datetime | None) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "resource_type": resource_type,
        "resource_id": str(resource_id),
        "trace_type": resource_type,
        "trace_ref_id": str(resource_id),
        "redaction_boundary": "none",
    }
    if created_at is not None:
        ref["created_at"] = _isoformat(created_at)
    return ref


def _unique_refs(refs: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for ref in refs:
        resource_type = str(ref.get("resource_type") or ref.get("trace_type") or "")
        resource_id = str(ref.get("resource_id") or ref.get("trace_ref_id") or "")
        if not resource_type or not resource_id:
            continue
        key = (resource_type, resource_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(ref))
    return tuple(unique)


def _dict_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_short_text(item, 120) for item in value if _short_text(item, 120)]


def _dict_value(value: Any, key: str) -> Any:
    if not isinstance(value, dict):
        return None
    return value.get(key)


def _looks_like_ref_id(value: str) -> bool:
    return bool(value) and len(value) <= 120 and not any(ch in value for ch in " ，。；,;")


def _title_for_dimension(dimension_id: str) -> str:
    mapping = {
        "technical_depth": "技术深度表达不足",
        "answer_structure": "项目表达结构不清晰",
        "communication_structure": "项目表达结构不清晰",
        "business_impact": "业务结果表达能力",
    }
    return mapping.get(dimension_id, f"{dimension_id} 维度待提升")


def _confidence(value: Any, *, default: str = "medium") -> str:
    normalized = str(value or default).lower()
    if normalized in {"low", "medium", "high"}:
        return normalized
    return default


def _short_text(value: Any, limit: int = _MAX_TEXT_LENGTH) -> str:
    text = re.sub(r"\s+", " ", _redact_forbidden_text(str(value or ""))).strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1]}…"


def _redact_forbidden_text(value: str) -> str:
    if _has_forbidden_candidate_value(value):
        return _REDACTED_SENSITIVE_DETAIL
    return value


def _candidate_id(
    *,
    extraction_input: CandidateExtractionInput,
    candidate_type: CandidateType,
    merge_key: str,
    evidence_refs: tuple[dict[str, Any], ...],
) -> str:
    evidence_key = "|".join(
        f"{ref.get('resource_type')}:{ref.get('resource_id')}" for ref in evidence_refs
    )
    return f"cand_{_stable_hash('|'.join([candidate_type.value, merge_key, evidence_key]), 24)}"


def _stable_hash(value: str, size: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]


def _normalize_merge_component(value: str) -> str:
    text = _short_text(value, 120).lower()
    text = re.sub(r"[\s/|:]+", "-", text)
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff_.-]+", "", text)
    return text.strip("-") or "unknown"


def _enum_value(value: CandidateType | CandidateSourceType | str) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _isoformat(value: datetime) -> str:
    return value.isoformat()
