"""Job match analyzer backed by the configured LLM transport."""

from __future__ import annotations

import re
from typing import Any

from app.domain.shared.enums import ConfidenceLevel
from app.application.job_match.ports import JobMatchAnalyzerOutput, JobMatchAnalyzerUnavailableError
from app.application.llm.errors import (
    LlmTransportConfigurationError,
    LlmTransportResponseError,
    LlmTransportUnavailableError,
)
from app.application.llm.ports import LlmTransport
from app.application.llm.provider_boundary import ProviderRequestValidationError, build_validated_transport_request
from app.schemas.job_match import JobMatchSourceBundle


JOB_MATCH_CONTRACT_IDS = (
    "P-JOBMATCH-001",
    "P-JOBMATCH-002",
    "P-JOBMATCH-003",
)
JOB_MATCH_PROMPT_VERSION = "P-JOBMATCH-001+P-JOBMATCH-002+P-JOBMATCH-003.v1"
DEFAULT_JOB_MATCH_MODEL_NAME = "llm_job_match_transport"
JOB_REQUIREMENT_SOURCE_WEIGHT = 0.65
JOB_RESPONSIBILITY_SOURCE_WEIGHT = 0.35
DIMENSION_SPECS: dict[str, tuple[int, str]] = {
    "requirement_alignment": (30, "岗位要求匹配"),
    "experience_evidence": (25, "经验证据强度"),
    "skill_coverage": (20, "技能覆盖"),
    "gap_risk": (15, "缺口风险控制"),
    "readiness_actions": (10, "准备行动清晰度"),
}
_JOB_MATCH_PROVIDER_REQUEST_TOP_LEVEL_KEYS = frozenset(
    {
        "source_digest",
        "resume_chunks",
        "job_requirement_chunks",
    }
)


class LlmJobMatchAnalyzer:
    """基于 LLM 传输层的岗位匹配分析器。"""

    def __init__(self, transport: LlmTransport) -> None:
        """初始化分析器，注入 LLM 传输层。"""
        self._transport = transport

    def analyze(self, source_bundle: JobMatchSourceBundle) -> JobMatchAnalyzerOutput:
        """执行岗位匹配分析，返回规范化后的分析结果。"""
        try:
            request = build_validated_transport_request(
                contract_ids=JOB_MATCH_CONTRACT_IDS,
                task_type="job_match_analysis",
                input_refs=_source_input_refs(source_bundle),
                evidence_bundle=_evidence_bundle(source_bundle),
                required_evidence_keys=_JOB_MATCH_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
                allowed_evidence_keys=_JOB_MATCH_PROVIDER_REQUEST_TOP_LEVEL_KEYS,
            )
            result = self._transport.generate(request)
        except ProviderRequestValidationError as exc:
            raise JobMatchAnalyzerUnavailableError("provider_request_validation_failed") from exc
        except (LlmTransportConfigurationError, LlmTransportUnavailableError) as exc:
            raise JobMatchAnalyzerUnavailableError(str(exc)) from exc
        except LlmTransportResponseError as exc:
            raise ValueError(str(exc)) from exc

        payload = result.result.get("job_match_result_payload")
        if not isinstance(payload, dict) and _looks_like_result_payload(result.result):
            payload = result.result
        if not isinstance(payload, dict):
            raise ValueError("LLM transport did not return job_match_result_payload")
        payload = _normalize_job_match_payload(payload, source_bundle)

        prompt_version = result.result.get("prompt_version")
        model_name = result.result.get("model_name")
        return JobMatchAnalyzerOutput(
            payload=payload,
            prompt_version=prompt_version if isinstance(prompt_version, str) else JOB_MATCH_PROMPT_VERSION,
            model_name=model_name if isinstance(model_name, str) else DEFAULT_JOB_MATCH_MODEL_NAME,
        )


def _source_input_refs(source_bundle: JobMatchSourceBundle) -> tuple[str, ...]:
    """从 source_bundle 中提取所有输入引用的排序元组。"""
    refs = {
        *(f"resume_version:{chunk.resume_version_id}" for chunk in source_bundle.resume_chunks),
        *(f"job_version:{chunk.job_version_id}" for chunk in source_bundle.job_requirement_chunks),
    }
    return tuple(sorted(refs))


def _evidence_bundle(source_bundle: JobMatchSourceBundle) -> dict[str, Any]:
    """将 source_bundle 转为 LLM 传输层所需的 evidence_bundle 字典。"""
    return {
        "source_digest": source_bundle.source_digest,
        "resume_chunks": [
            chunk.model_dump(mode="json") for chunk in source_bundle.resume_chunks
        ],
        "job_requirement_chunks": [
            chunk.model_dump(mode="json")
            for chunk in source_bundle.job_requirement_chunks
        ],
    }


def _looks_like_result_payload(value: dict[str, Any]) -> bool:
    """判断字典是否包含岗位匹配结果的关键字段。"""
    return any(key in value for key in ("overall_score", "dimension_scores", "summary"))


def _normalize_job_match_payload(
    raw_payload: dict[str, Any],
    source_bundle: JobMatchSourceBundle,
) -> dict[str, Any]:
    """
    把常见的 LLM 宽松输出整理为项目内部严格契约，再交给领域校验层兜底。
    包括：置信度、匹配/缺失要求、维度评分、简历证据、风险标记等字段的归一化。
    """

    payload = dict(raw_payload)
    confidence = _normalize_confidence(payload.get("confidence"), default="medium")
    matched_requirements = _normalize_matched_requirements(
        payload.get("matched_requirements"),
        source_bundle,
        confidence,
    )
    missing_requirements = _normalize_missing_requirements(
        payload.get("missing_requirements"),
        source_bundle,
    )
    missing_requirements = _fill_uncovered_missing_requirements(
        missing_requirements,
        matched_requirements,
        source_bundle,
    )
    payload_for_dimensions = {
        **payload,
        "missing_requirements": missing_requirements,
    }
    dimension_scores = _normalize_dimension_scores(
        payload_for_dimensions,
        source_bundle,
        confidence,
    )
    dimension_scores = _calibrate_dimension_scores_for_gap_coverage(
        dimension_scores,
        missing_requirements,
        source_bundle,
    )
    overall_score = sum(item["score"] for item in dimension_scores)
    summary = _chinese_text_or(
        payload.get("summary"),
        f"基于大模型对当前绑定简历与岗位信息的分析，匹配分为 {overall_score} / 100。",
    )

    payload["overall_score"] = overall_score
    payload["overall_level"] = _overall_level(overall_score, confidence)
    payload["confidence"] = confidence
    payload["summary"] = summary
    payload["dimension_scores"] = dimension_scores
    payload["matched_requirements"] = matched_requirements
    payload["missing_requirements"] = missing_requirements
    payload["resume_evidence"] = _normalize_resume_evidence(
        payload.get("resume_evidence"),
        source_bundle,
        confidence,
    )
    payload["risk_flags"] = _normalize_risk_flags(
        payload.get("risk_flags"),
        source_bundle,
    )
    payload["interview_focus"] = _chinese_string_list(payload.get("interview_focus")) or [
        "围绕匹配度最高的证据追问候选人的真实参与深度。"
    ]
    payload["suggested_questions"] = _chinese_string_list(payload.get("suggested_questions")) or [
        "请结合岗位要求说明这段经历中最能证明匹配度的具体产出。"
    ]
    payload["markdown_report"] = _chinese_text_or(
        payload.get("markdown_report"),
        f"# 岗位匹配分析\n\n{summary}",
    )
    return payload


def _normalize_dimension_scores(
    payload: dict[str, Any],
    source_bundle: JobMatchSourceBundle,
    default_confidence: str,
) -> list[dict[str, Any]]:
    """归一化维度评分列表：从 LLM 宽松格式转为严格格式，确保每个维度都有值。"""
    raw_scores = payload.get("dimension_scores")
    score_by_key: dict[str, Any] = {}
    if isinstance(raw_scores, dict):
        score_by_key = raw_scores
    elif isinstance(raw_scores, list):
        for item in raw_scores:
            if isinstance(item, dict) and isinstance(item.get("key"), str):
                score_by_key[item["key"]] = item

    target_scores = _target_dimension_scores(payload, score_by_key)
    fallback_evidence = _source_refs([source_bundle.resume_chunks[0].chunk_id], source_bundle)
    missing_reasons = _string_list(payload.get("missing_requirements"))

    normalized: list[dict[str, Any]] = []
    for key, (max_score, label) in DIMENSION_SPECS.items():
        raw_item = score_by_key.get(key)
        raw_dict = raw_item if isinstance(raw_item, dict) else {}
        score = _bounded_int(
            raw_dict.get("score") if raw_dict else raw_item,
            default=target_scores[key],
            lower=0,
            upper=max_score,
        )
        gaps = _string_list(raw_dict.get("gaps"))
        if key == "gap_risk":
            for reason in missing_reasons:
                if reason not in gaps:
                    gaps.append(reason)
        supporting_evidence = _source_refs(
            raw_dict.get("supporting_evidence"),
            source_bundle,
            default_refs=fallback_evidence,
        )
        normalized.append(
            {
                "key": key,
                "score": score,
                "max_score": max_score,
                "rationale": _chinese_text_or(
                    raw_dict.get("rationale"),
                    f"大模型围绕“{label}”维度给出了该项评分。",
                ),
                "supporting_evidence": supporting_evidence,
                "gaps": gaps,
                "confidence": _normalize_confidence(
                    raw_dict.get("confidence"),
                    default=default_confidence,
                ),
            }
        )
    return normalized


def _calibrate_dimension_scores_for_gap_coverage(
    dimension_scores: list[dict[str, Any]],
    missing_requirements: list[dict[str, Any]],
    source_bundle: JobMatchSourceBundle,
) -> list[dict[str, Any]]:
    """根据未覆盖的岗位要求对维度评分进行扣减校准。"""
    missing_chunk_ids = {
        item["requirement_chunk_id"]
        for item in missing_requirements
        if isinstance(item.get("requirement_chunk_id"), str)
    }
    source_weights = _job_source_weights(source_bundle)
    total_source_weight = sum(source_weights.values())
    if total_source_weight <= 0:
        return dimension_scores
    missing_weight = sum(source_weights.get(chunk_id, 0) for chunk_id in missing_chunk_ids)
    missing_ratio = min(1.0, missing_weight / total_source_weight)
    if missing_ratio <= 0:
        return dimension_scores

    calibrated: list[dict[str, Any]] = []
    for score in dimension_scores:
        item = dict(score)
        key = item.get("key")
        max_score = _bounded_int(item.get("max_score"), default=0, lower=0, upper=100)
        cap: int | None = None
        if key == "requirement_alignment":
            cap = max(8, round(max_score * (1 - 0.5 * missing_ratio)))
        elif key == "gap_risk":
            cap = max(3, round(max_score * (1 - 0.8 * missing_ratio)))
        elif key == "readiness_actions":
            cap = max(4, round(max_score * (1 - 0.5 * missing_ratio)))
        if cap is not None and item["score"] > cap:
            item["score"] = cap
        calibrated.append(item)
    return calibrated


def _job_source_weights(source_bundle: JobMatchSourceBundle) -> dict[str, float]:
    """
    为岗位来源分配评分权重：岗位要求偏硬门槛（65%），职责偏场景佐证（35%）。
    无明确类型时均分权重。
    """

    requirement_chunks = []
    responsibility_chunks = []
    note_chunks = []
    for chunk in source_bundle.job_requirement_chunks:
        requirement_type = chunk.requirement_type.strip().lower()
        if requirement_type == "requirement":
            requirement_chunks.append(chunk)
        elif requirement_type == "responsibility":
            responsibility_chunks.append(chunk)
        else:
            note_chunks.append(chunk)

    weights: dict[str, float] = {}
    if requirement_chunks and responsibility_chunks:
        requirement_weight = JOB_REQUIREMENT_SOURCE_WEIGHT
        responsibility_weight = JOB_RESPONSIBILITY_SOURCE_WEIGHT
    elif requirement_chunks:
        requirement_weight = 1.0
        responsibility_weight = 0.0
    elif responsibility_chunks:
        requirement_weight = 0.0
        responsibility_weight = 1.0
    else:
        note_weight = 1.0 / max(1, len(note_chunks))
        return {chunk.chunk_id: note_weight for chunk in note_chunks}

    if requirement_chunks:
        per_requirement_weight = requirement_weight / len(requirement_chunks)
        weights.update(
            {chunk.chunk_id: per_requirement_weight for chunk in requirement_chunks}
        )
    if responsibility_chunks:
        per_responsibility_weight = responsibility_weight / len(responsibility_chunks)
        weights.update(
            {chunk.chunk_id: per_responsibility_weight for chunk in responsibility_chunks}
        )
    weights.update({chunk.chunk_id: 0.0 for chunk in note_chunks})
    return weights


def _target_dimension_scores(
    payload: dict[str, Any],
    score_by_key: dict[str, Any],
) -> dict[str, int]:
    """从 payload 和逐维度评分中提取目标维度分数；LLM 未给出时按 overall_score 等比分配。"""
    direct_scores: dict[str, int] = {}
    for key, (max_score, _label) in DIMENSION_SPECS.items():
        raw_item = score_by_key.get(key)
        raw_score = raw_item.get("score") if isinstance(raw_item, dict) else raw_item
        parsed = _optional_int(raw_score)
        if parsed is not None:
            direct_scores[key] = max(0, min(max_score, parsed))

    if direct_scores:
        return {
            key: direct_scores.get(key, max_score // 2)
            for key, (max_score, _label) in DIMENSION_SPECS.items()
        }

    overall_score = _bounded_int(payload.get("overall_score"), default=60, lower=0, upper=100)
    remaining = overall_score
    targets: dict[str, int] = {}
    specs = list(DIMENSION_SPECS.items())
    for index, (key, (max_score, _label)) in enumerate(specs):
        if index == len(specs) - 1:
            targets[key] = max(0, min(max_score, remaining))
            continue
        weighted = round(overall_score * max_score / 100)
        score = max(0, min(max_score, weighted, remaining))
        targets[key] = score
        remaining -= score
    return targets


def _normalize_matched_requirements(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
    default_confidence: str,
) -> list[dict[str, Any]]:
    """归一化已匹配的岗位要求列表：为每项绑定 requirement_chunk_id 和 resume_evidence_chunk_ids。"""
    items = _list_items(raw_value)
    matches: list[dict[str, Any]] = []
    fallback_resume_refs = _resume_chunk_ids(source_bundle)[:1]
    for item in items:
        if isinstance(item, dict):
            text = _text_or(
                item.get("requirement") or item.get("text") or item.get("rationale"),
                "",
            )
            requirement_chunk_id = _known_job_chunk_id(
                item.get("requirement_chunk_id"),
                source_bundle,
            ) or _best_job_chunk_id(text, source_bundle)
            resume_chunk_ids = _resume_chunk_ids_from_value(
                item.get("resume_evidence_chunk_ids")
                or item.get("resume_evidence")
                or item.get("supporting_evidence"),
                source_bundle,
                default_refs=fallback_resume_refs,
            )
            rationale = _text_or(item.get("rationale"), text or "大模型认为该岗位要求已有简历证据支撑。")
            confidence = _normalize_confidence(item.get("confidence"), default=default_confidence)
        else:
            text = str(item).strip()
            requirement_chunk_id = _best_job_chunk_id(text, source_bundle)
            resume_chunk_ids = fallback_resume_refs
            rationale = text or "大模型认为该岗位要求已有简历证据支撑。"
            confidence = default_confidence
        if requirement_chunk_id:
            matches.append(
                {
                    "requirement_chunk_id": requirement_chunk_id,
                    "resume_evidence_chunk_ids": resume_chunk_ids,
                    "rationale": rationale,
                    "confidence": confidence,
                }
            )
    return matches


def _normalize_missing_requirements(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
) -> list[dict[str, Any]]:
    """归一化未覆盖的岗位要求列表：为每项绑定 requirement_chunk_id 和原因。"""
    missing: list[dict[str, Any]] = []
    for item in _list_items(raw_value):
        if isinstance(item, dict):
            reason = _text_or(item.get("reason") or item.get("text"), "大模型识别到该要求证据不足。")
            requirement_chunk_id = _known_job_chunk_id(
                item.get("requirement_chunk_id"),
                source_bundle,
            ) or _best_job_chunk_id(reason, source_bundle)
            confidence = _normalize_confidence(item.get("confidence"), default="medium")
            # evidence_insufficient 在领域契约中表示“证据不足到无法分析整体结果”，
            # 大模型常把普通岗位缺口误标为 true；只在无法绑定任何岗位要求时保留该语义。
            evidence_insufficient = requirement_chunk_id is None
        else:
            reason = str(item).strip() or "大模型识别到该要求证据不足。"
            requirement_chunk_id = _best_job_chunk_id(reason, source_bundle)
            confidence = "medium"
            evidence_insufficient = requirement_chunk_id is None
        if requirement_chunk_id is None:
            continue
        missing.append(
            {
                "requirement_chunk_id": requirement_chunk_id,
                "reason": reason,
                "confidence": confidence,
                "evidence_insufficient": evidence_insufficient or requirement_chunk_id is None,
            }
        )
    return missing


def _fill_uncovered_missing_requirements(
    missing_requirements: list[dict[str, Any]],
    matched_requirements: list[dict[str, Any]],
    source_bundle: JobMatchSourceBundle,
) -> list[dict[str, Any]]:
    """补充 LLM 未覆盖的岗位要求项（确保输出的 missing_requirements 与 source_bundle 一一对应）。"""
    covered_job_chunk_ids = {
        item["requirement_chunk_id"]
        for item in matched_requirements
        if isinstance(item.get("requirement_chunk_id"), str)
    } | {
        item["requirement_chunk_id"]
        for item in missing_requirements
        if isinstance(item.get("requirement_chunk_id"), str)
    }
    completed = list(missing_requirements)
    for chunk in source_bundle.job_requirement_chunks:
        if chunk.chunk_id in covered_job_chunk_ids:
            continue
        completed.append(
            {
                "requirement_chunk_id": chunk.chunk_id,
                "reason": f"模型结果未明确覆盖该岗位项，建议面试核验：{_short_text(chunk.text)}",
                "confidence": "medium",
                "evidence_insufficient": False,
            }
        )
    return completed


def _normalize_resume_evidence(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
    default_confidence: str,
) -> list[dict[str, Any]]:
    """归一化简历证据列表：将 LLM 输出的各种格式统一为 chunk_id + summary + confidence。"""
    evidence: list[dict[str, Any]] = []
    if isinstance(raw_value, dict):
        iterable: list[Any] = [
            {"summary": str(summary), "chunk_ids": chunk_ids}
            for summary, chunk_ids in raw_value.items()
        ]
    else:
        iterable = _list_items(raw_value)

    for item in iterable:
        if isinstance(item, dict):
            summary = _text_or(item.get("summary") or item.get("text"), "大模型引用的简历证据。")
            chunk_ids = _resume_chunk_ids_from_value(
                item.get("chunk_id") or item.get("chunk_ids"),
                source_bundle,
                default_refs=[],
            )
            confidence = _normalize_confidence(item.get("confidence"), default=default_confidence)
        else:
            summary = str(item).strip() or "大模型引用的简历证据。"
            chunk_ids = [_best_resume_chunk_id(summary, source_bundle) or source_bundle.resume_chunks[0].chunk_id]
            confidence = default_confidence
        for chunk_id in chunk_ids:
            evidence.append(
                {
                    "chunk_id": chunk_id,
                    "summary": summary,
                    "confidence": confidence,
                }
            )
    if evidence:
        return evidence
    return [
        {
            "chunk_id": source_bundle.resume_chunks[0].chunk_id,
            "summary": "大模型引用的主要简历证据。",
            "confidence": default_confidence,
        }
    ]


def _normalize_risk_flags(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
) -> list[dict[str, Any]]:
    """归一化风险标记列表：统一为 risk_type + description + severity + supporting_evidence。"""
    risks: list[dict[str, Any]] = []
    for item in _list_items(raw_value):
        if isinstance(item, dict):
            description = _text_or(item.get("description") or item.get("text"), "大模型识别到潜在风险。")
            risk_type = _text_or(item.get("risk_type"), "gap_risk")
            severity = _severity(item.get("severity"))
            supporting_evidence = _source_refs(item.get("supporting_evidence"), source_bundle)
        else:
            description = str(item).strip() or "大模型识别到潜在风险。"
            risk_type = "gap_risk"
            severity = "medium"
            supporting_evidence = _source_refs([description], source_bundle)
        risks.append(
            {
                "risk_type": risk_type,
                "description": description,
                "severity": severity,
                "supporting_evidence": supporting_evidence,
            }
        )
    return risks


def _source_refs(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
    *,
    default_refs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """从 LLM 输出中提取 source 引用列表，绑定到已知 chunk_id；未知 ID 自动匹配最佳块。"""
    known_ids = _known_chunk_ids(source_bundle)
    refs: list[dict[str, Any]] = []
    for item in _list_items(raw_value):
        chunk_id: str | None
        quote = None
        if isinstance(item, dict):
            quote = item.get("quote") if isinstance(item.get("quote"), str) else None
            chunk_id = item.get("chunk_id") if isinstance(item.get("chunk_id"), str) else None
            if chunk_id not in known_ids:
                chunk_id = _best_chunk_id(str(item), source_bundle)
        else:
            chunk_id = str(item).strip()
            if chunk_id not in known_ids:
                chunk_id = _best_chunk_id(chunk_id, source_bundle)
        if chunk_id and chunk_id in known_ids:
            ref = {"chunk_id": chunk_id}
            if quote:
                ref["quote"] = quote
            refs.append(ref)
    return refs or list(default_refs or [])


def _resume_chunk_ids_from_value(
    raw_value: Any,
    source_bundle: JobMatchSourceBundle,
    *,
    default_refs: list[str],
) -> list[str]:
    """从 LLM 输出值中提取简历 chunk ID 列表，只返回属于简历的 ID。"""
    resume_ids = set(_resume_chunk_ids(source_bundle))
    chunk_ids: list[str] = []
    for ref in _source_refs(raw_value, source_bundle):
        chunk_id = ref["chunk_id"]
        if chunk_id in resume_ids and chunk_id not in chunk_ids:
            chunk_ids.append(chunk_id)
    return chunk_ids or list(default_refs)


def _known_chunk_ids(source_bundle: JobMatchSourceBundle) -> set[str]:
    """返回 source_bundle 中所有已知的 chunk ID 集合（简历+岗位）。"""
    return {
        *(chunk.chunk_id for chunk in source_bundle.resume_chunks),
        *(chunk.chunk_id for chunk in source_bundle.job_requirement_chunks),
    }


def _resume_chunk_ids(source_bundle: JobMatchSourceBundle) -> list[str]:
    """返回 source_bundle 中所有简历 chunk ID 列表。"""
    return [chunk.chunk_id for chunk in source_bundle.resume_chunks]


def _known_job_chunk_id(value: Any, source_bundle: JobMatchSourceBundle) -> str | None:
    """验证 value 是否为已知的岗位 chunk ID；是则返回，否则返回 None。"""
    if not isinstance(value, str):
        return None
    job_ids = {chunk.chunk_id for chunk in source_bundle.job_requirement_chunks}
    return value if value in job_ids else None


def _best_chunk_id(text: str, source_bundle: JobMatchSourceBundle) -> str | None:
    """在简历和岗位中分别尝试匹配最佳 chunk ID。"""
    return _best_resume_chunk_id(text, source_bundle) or _best_job_chunk_id(text, source_bundle)


def _best_resume_chunk_id(text: str, source_bundle: JobMatchSourceBundle) -> str | None:
    """在简历 chunks 中查找与 text 最佳匹配的 chunk ID。"""
    return _best_source_chunk_id(
        text,
        [(chunk.chunk_id, chunk.text) for chunk in source_bundle.resume_chunks],
    )


def _best_job_chunk_id(text: str, source_bundle: JobMatchSourceBundle) -> str | None:
    """在岗位 chunks 中查找与 text 最佳匹配的 chunk ID。"""
    return _best_source_chunk_id(
        text,
        [(chunk.chunk_id, chunk.text) for chunk in source_bundle.job_requirement_chunks],
    )


def _best_source_chunk_id(text: str, candidates: list[tuple[str, str]]) -> str | None:
    """通过子串匹配和 token 交集评分，从候选列表中找出与 text 最匹配的 chunk ID。"""
    stripped = text.strip()
    if not candidates:
        return None
    for chunk_id, chunk_text in candidates:
        if stripped and (stripped in chunk_text or chunk_text in stripped):
            return chunk_id
    tokens = _tokens(stripped)
    if not tokens:
        return None
    best_id = candidates[0][0]
    best_score = -1
    for chunk_id, chunk_text in candidates:
        score = len(tokens & _tokens(chunk_text))
        if score > best_score:
            best_id = chunk_id
            best_score = score
    return best_id if best_score > 0 else None


def _tokens(text: str) -> set[str]:
    """将文本拆分为 token 集合（含英文词块和中文二元组），用于文本匹配。"""
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9]{2,}", lowered))
    cjk_tokens: set[str] = set()
    for segment in re.findall(r"[\u4e00-\u9fff]+", lowered):
        if len(segment) == 1:
            cjk_tokens.add(segment)
        else:
            cjk_tokens.update(segment[index : index + 2] for index in range(len(segment) - 1))
    return ascii_tokens | cjk_tokens


def _list_items(value: Any) -> list[Any]:
    """将任意值规范化为列表：None→[]，列表/元组/集合→列表，其他→[value]。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _string_list(value: Any) -> list[str]:
    """从任意值中提取所有非空字符串文本（支持从字典的 text/summary/reason 字段提取）。"""
    strings: list[str] = []
    for item in _list_items(value):
        if isinstance(item, dict):
            text = item.get("text") or item.get("summary") or item.get("reason") or item.get("description")
            if isinstance(text, str) and text.strip():
                strings.append(text.strip())
            continue
        text = str(item).strip()
        if text:
            strings.append(text)
    return strings


def _text_or(value: Any, default: str) -> str:
    """如果 value 是非空字符串则返回，否则返回 default。"""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _short_text(value: str, *, limit: int = 80) -> str:
    """截断长文本到指定长度，超出时追加 ...。"""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def _chinese_text_or(value: Any, default: str) -> str:
    """如果 value 是含中文的字符串则返回，否则返回 default。"""
    text = _text_or(value, "")
    return text if _has_cjk(text) else default


def _chinese_string_list(value: Any) -> list[str]:
    """从 string_list 中筛选出含中文的字符串列表。"""
    return [text for text in _string_list(value) if _has_cjk(text)]


def _has_cjk(value: str) -> bool:
    """检测字符串是否包含中文字符（CJK 统一表意文字）。"""
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _normalize_confidence(value: Any, *, default: str) -> str:
    """归一化置信度字符串：支持中英文别名，统一为 high / medium / low / insufficient。"""
    if isinstance(value, ConfidenceLevel):
        return value.value
    if isinstance(value, str):
        normalized = value.strip().lower()
        aliases = {
            "高": "high",
            "高置信": "high",
            "high": "high",
            "中": "medium",
            "中等": "medium",
            "medium": "medium",
            "moderate": "medium",
            "低": "low",
            "low": "low",
            "不足": "insufficient",
            "证据不足": "insufficient",
            "insufficient": "insufficient",
        }
        if normalized in aliases:
            return aliases[normalized]
    return default if default in {"high", "medium", "low", "insufficient"} else "medium"


def _overall_level(score: int, confidence: str) -> str:
    """根据总分和置信度计算总体匹配等级。"""
    if confidence == "insufficient":
        return "insufficient_evidence"
    if score >= 80:
        return "strong_match"
    if score >= 60:
        return "medium_match"
    return "weak_match"


def _severity(value: Any) -> str:
    """归一化严重等级：支持中英文，统一为 low / medium / high。"""
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"low", "medium", "high"}:
            return normalized
        if normalized in {"低", "轻微"}:
            return "low"
        if normalized in {"高", "严重"}:
            return "high"
    return "medium"


def _optional_int(value: Any) -> int | None:
    """尝试从任意值中提取整数（支持字符串中的首数字）。"""
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match is None:
            return None
        return int(match.group(0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bounded_int(value: Any, *, default: int, lower: int, upper: int) -> int:
    """将任意值解析为整数并限制在 [lower, upper] 范围内。"""
    parsed = _optional_int(value)
    if parsed is None:
        parsed = default
    return max(lower, min(upper, parsed))
