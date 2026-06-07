from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator, model_validator


POLISH_FEEDBACK_FINAL_SCHEMA_ID = "polish_feedback_generated_v1"
POLISH_FEEDBACK_FINAL_SCHEMA_VERSION = "1.0"
POLISH_FEEDBACK_AGENT_PROMPT_VERSION = "polish_feedback_agent_prompt.v1"
POLISH_FEEDBACK_TASK_TYPE = "polish_feedback_generation"
POLISH_FEEDBACK_CANDIDATE_MODE = "candidate_compact"
POLISH_FEEDBACK_CANDIDATE_TASK = "polish_feedback_candidate_v1"
POLISH_FEEDBACK_FINAL_CONTRACT_IDS = (
    "P-POLISH-003",
    "P-POLISH-004",
    "P-POLISH-005",
)
POLISH_FEEDBACK_FUTURE_CONTRACT_HINTS = ("P-POLISH-009",)

SAME_QUESTION_EFFECT_TRENDS = ("unchanged", "improved", "regressed", "mixed", "first_attempt")
_SAME_QUESTION_EFFECT_ALIASES = {"not_applicable": "unchanged"}


def _clean_text(value: object, *, max_chars: int = 240) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) > max_chars:
        return text[:max_chars].rstrip()
    return text


def _generated_reference_section_id(index: int, seen_section_ids: set[str]) -> str:
    candidate = f"section_{index}"
    suffix = index
    while candidate in seen_section_ids:
        suffix += 1
        candidate = f"section_{suffix}"
    return candidate


class _PayloadModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ScoreReasoningItem(_PayloadModel):
    dimension: str
    rationale: str


class LossPoint(_PayloadModel):
    loss_point_id: str
    severity: str | None = None
    deduction: float | None = None
    reason: str
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_aliases(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if not payload.get("loss_point_id"):
            alias = payload.get("id") or payload.get("loss_id")
            if alias:
                payload["loss_point_id"] = alias
        if not payload.get("reason") and payload.get("description"):
            payload["reason"] = payload.get("description")
        return payload


class ReferenceAnswerSection(_PayloadModel):
    section_id: str = ""
    title: str = ""
    content: str = ""
    addresses_loss_point_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_section_id_alias(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if not payload.get("section_id") and payload.get("id"):
            payload["section_id"] = payload.get("id")
        if not _clean_text(payload.get("section_id"), max_chars=120):
            payload["section_id"] = "section_1"
        if not _clean_text(payload.get("title"), max_chars=240):
            payload["title"] = "参考回答 1"
        if not isinstance(payload.get("addresses_loss_point_ids"), list):
            payload["addresses_loss_point_ids"] = []
        return payload


class ReferenceAnswer(_PayloadModel):
    sections: list[ReferenceAnswerSection]
    _validation_warnings: list[str] = PrivateAttr(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_top_level_addresses(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        refs = payload.get("addresses_loss_point_ids")
        sections = payload.get("sections")
        warnings: list[str] = []
        if isinstance(refs, list):
            if isinstance(sections, list) and len(sections) == 1 and isinstance(sections[0], dict):
                section = dict(sections[0])
                if not section.get("addresses_loss_point_ids"):
                    section["addresses_loss_point_ids"] = refs
                    sections = [section]
                    payload["sections"] = sections
                    warnings.append("reference_answer_top_level_addresses_loss_point_ids_normalized")
            else:
                warnings.append("reference_answer_top_level_addresses_loss_point_ids_unassigned")
        if warnings:
            payload["__validation_warnings"] = warnings
        sections = payload.get("sections")
        if isinstance(sections, list):
            normalized_sections: list[object] = []
            seen_section_ids: set[str] = set()
            for index, item in enumerate(sections, start=1):
                if not isinstance(item, dict):
                    normalized_sections.append(item)
                    continue
                section = dict(item)
                section_id = _clean_text(section.get("section_id") or section.get("id"), max_chars=120)
                if not section_id:
                    section_id = _generated_reference_section_id(index, seen_section_ids)
                section["section_id"] = section_id
                seen_section_ids.add(section_id)
                if not _clean_text(section.get("title"), max_chars=240):
                    section["title"] = f"参考回答 {index}"
                if not isinstance(section.get("addresses_loss_point_ids"), list):
                    section["addresses_loss_point_ids"] = []
                normalized_sections.append(section)
            payload["sections"] = normalized_sections
        return payload

    @model_validator(mode="after")
    def _store_warnings(self) -> "ReferenceAnswer":
        source = self.model_extra or {}
        raw_warnings = source.get("__validation_warnings")
        if isinstance(raw_warnings, list):
            self._validation_warnings = [str(item) for item in raw_warnings if item]
        return self

    @property
    def validation_warnings(self) -> list[str]:
        return list(self._validation_warnings)


class SameQuestionEffect(_PayloadModel):
    trend: Literal["unchanged", "improved", "regressed", "mixed", "first_attempt"] | None = None
    improved_points: list[str] = Field(default_factory=list)
    repeated_loss_point_ids: list[str] = Field(default_factory=list)
    regressed_points: list[str] = Field(default_factory=list)
    next_retry_focus: list[str] = Field(default_factory=list)
    score_delta: float | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_enum_string(cls, value: object) -> object:
        if isinstance(value, str):
            trend = _SAME_QUESTION_EFFECT_ALIASES.get(value, value)
            if trend in SAME_QUESTION_EFFECT_TRENDS:
                return {
                    "trend": trend,
                    "improved_points": [],
                    "repeated_loss_point_ids": [],
                    "regressed_points": [],
                    "next_retry_focus": [],
                    "score_delta": None,
                }
        return value

    @field_validator("improved_points", "repeated_loss_point_ids", "regressed_points", "next_retry_focus", mode="before")
    @classmethod
    def _list_or_empty(cls, value: object) -> object:
        return value if isinstance(value, list) else []


class ProjectAssetUpdateCandidate(_PayloadModel):
    candidate_type: str = "project_asset_update_candidate"
    candidate_ref: str | None = None
    user_confirmation_required: bool = True
    target_asset_ref: dict[str, Any] | None = None
    summary: str | None = None
    suggested_patch: dict[str, Any] | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class FeedbackInputPayload(_PayloadModel):
    owner_id: str
    actor_id: str
    session_id: str
    question_id: str
    answer_id: str


class FeedbackCandidatePayload(_PayloadModel):
    feedback_text: str
    answer_summary: str
    score_reasoning: list[ScoreReasoningItem] = Field(default_factory=list)
    loss_points: list[LossPoint] = Field(default_factory=list)
    reference_answer: ReferenceAnswer
    same_question_effect: SameQuestionEffect | None = None
    project_asset_update_candidates: list[ProjectAssetUpdateCandidate] = Field(default_factory=list)
    low_confidence_flags: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    _validation_warnings: list[str] = PrivateAttr(default_factory=list)

    @field_validator("score_reasoning", mode="before")
    @classmethod
    def _score_reasoning_or_empty(cls, value: object) -> object:
        return value if isinstance(value, list) else []

    @field_validator("project_asset_update_candidates", mode="before")
    @classmethod
    def _candidate_list_or_empty(cls, value: object) -> object:
        if value in (None, []):
            return []
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @field_validator("same_question_effect", mode="before")
    @classmethod
    def _effect_or_none(cls, value: object) -> object:
        if value in (None, "", {}):
            return None
        if isinstance(value, str):
            trend = _SAME_QUESTION_EFFECT_ALIASES.get(value, value)
            if trend not in SAME_QUESTION_EFFECT_TRENDS:
                return None
        return value

    @model_validator(mode="after")
    def _collect_validation_warnings(self) -> "FeedbackCandidatePayload":
        warnings: list[str] = []
        if not self.score_reasoning:
            warnings.append("score_reasoning_missing")
        warnings.extend(self.reference_answer.validation_warnings)
        self._validation_warnings = list(dict.fromkeys(warnings))
        return self

    @property
    def validation_warnings(self) -> list[str]:
        return list(self._validation_warnings)


class FeedbackFinalPayload(_PayloadModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_id: str
    schema_version: str
    status: Literal["generated", "partial", "low_confidence", "validation_failed"]
    contract_ids: list[str]
    feedback_id: str
    feedback_text: str
    answer_summary: str
    score_result: dict[str, Any]
    loss_points: list[dict[str, Any]]
    reference_answer: ReferenceAnswer
    asset_consistency_check: dict[str, Any]
    answer_coverage: dict[str, Any]
    answer_change_analysis: dict[str, Any]
    feedback_cards: list[dict[str, Any]]
    next_recommended_actions: list[str]
    low_confidence_flags: list[str] = Field(default_factory=list)
    trace_refs: list[Any] = Field(default_factory=list)
    feedback_metadata: dict[str, Any] = Field(default_factory=dict)

    PROVIDER_METADATA_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "model_name",
            "prompt_version",
            "provider_status",
            "provider_model",
            "provider_validation_status",
            "llm_called",
            "request_id",
            "trace_id",
            "raw_io_ref",
        }
    )
