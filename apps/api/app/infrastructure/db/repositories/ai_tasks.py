"""SQLAlchemy repository for AI task status and result read paths."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from app.application.polish.feedback_projection import (
    redact_feedback_payload_text,
    response_safe_feedback_payload,
)
from app.infrastructure.db.models.ai_task import AiTask, AiTaskResult
from app.infrastructure.db.models.feedback import Feedback
from app.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyAiTaskRepository(SqlAlchemyRepository):
    def get_status(self, *, owner_id: str, ai_task_id: str) -> dict[str, object] | None:
        with self.session_scope() as db:
            task = db.scalar(
                select(AiTask)
                .where(AiTask.owner_id == owner_id, AiTask.id == ai_task_id)
                .limit(1)
            )
            if task is None:
                return None
            result = db.scalar(
                select(AiTaskResult)
                .where(AiTaskResult.owner_id == owner_id, AiTaskResult.ai_task_id == ai_task_id)
                .order_by(AiTaskResult.created_at.desc(), AiTaskResult.id.desc())
                .limit(1)
            )
            payload = _feedback_payload_for_task(db, owner_id=owner_id, ai_task_id=ai_task_id)
            return _status_projection(task, result=result, payload=payload)

    def get_result(self, *, owner_id: str, ai_task_id: str) -> dict[str, object] | None:
        with self.session_scope() as db:
            task = db.scalar(
                select(AiTask)
                .where(AiTask.owner_id == owner_id, AiTask.id == ai_task_id)
                .limit(1)
            )
            if task is None:
                return None
            result = db.scalar(
                select(AiTaskResult)
                .where(AiTaskResult.owner_id == owner_id, AiTaskResult.ai_task_id == ai_task_id)
                .order_by(AiTaskResult.created_at.desc(), AiTaskResult.id.desc())
                .limit(1)
            )
            payload = _feedback_payload_for_task(db, owner_id=owner_id, ai_task_id=ai_task_id)
            return _result_projection(task, result=result, payload=payload)

    def get_ref(self, ai_task_id: str):
        with self.session_scope() as db:
            task = db.get(AiTask, ai_task_id)
            if task is None:
                return None
            from app.domain.shared.refs import ResourceRef

            return ResourceRef(resource_type="ai_task", resource_id=ai_task_id)


def _status_projection(
    task: AiTask,
    *,
    result: AiTaskResult | None,
    payload: dict[str, Any] | None,
) -> dict[str, object]:
    safe_summary = _safe_summary(result)
    return {
        "ai_task_id": task.id,
        "task_type": task.task_type,
        "status": task.status,
        "contract_ids": _string_list(task.contract_ids),
        "retryable": _is_retryable(task.status, payload, safe_summary=safe_summary),
        "result_ref": _result_ref(task, result=result),
        "user_visible_status": _user_visible_status(task.status, payload, safe_summary=safe_summary),
        "candidate_refs": _projected_candidate_refs(result, payload=payload, safe_summary=safe_summary),
        "suggestion_refs": _projected_suggestion_refs(result, payload=payload, safe_summary=safe_summary),
        "validation_errors": _projected_validation_errors(result, payload=payload, safe_summary=safe_summary),
        "provider_payload": None,
    }


def _result_projection(
    task: AiTask,
    *,
    result: AiTaskResult | None,
    payload: dict[str, Any] | None,
) -> dict[str, object]:
    safe_summary = _safe_summary(result)
    result_payload = _feedback_result_payload(task, payload, safe_summary=safe_summary)
    projection = {
        "ai_task_id": task.id,
        "status": _result_status(task, result=result, result_payload=result_payload),
        "result_ref": _result_ref(task, result=result),
        "candidate_refs": _projected_candidate_refs(result, payload=payload, safe_summary=safe_summary),
        "suggestion_refs": _projected_suggestion_refs(result, payload=payload, safe_summary=safe_summary),
        "validation_result_ref": _validation_result_ref(result),
        "validation_errors": _projected_validation_errors(result, payload=payload, safe_summary=safe_summary),
        "provider_payload": None,
    }
    if result_payload is not None:
        projection["result_payload"] = result_payload
    return projection


def _feedback_payload_for_task(db, *, owner_id: str, ai_task_id: str) -> dict[str, Any] | None:
    feedback = db.scalar(
        select(Feedback)
        .where(Feedback.owner_id == owner_id, Feedback.ai_task_id == ai_task_id)
        .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        .limit(1)
    )
    if feedback is None or not feedback.feedback_summary:
        return None
    try:
        payload = json.loads(feedback.feedback_summary)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _result_ref(task: AiTask, *, result: AiTaskResult | None) -> dict[str, object] | None:
    if result is not None:
        ref_id = result.result_ref_id or result.validation_result_ref_id or result.trace_ref_id
        if ref_id:
            return {
                "trace_ref_id": ref_id,
                "trace_type": "validation_result" if result.validation_result_ref_id else "feedback",
                "created_at": result.created_at,
            }
    trace_refs = task.trace_ref_ids if isinstance(task.trace_ref_ids, list) else []
    first_ref = next((str(item) for item in trace_refs if str(item).strip()), None)
    if first_ref is None:
        return None
    return {"trace_ref_id": first_ref, "trace_type": "ai_task", "created_at": task.created_at}


def _validation_result_ref(result: AiTaskResult | None) -> dict[str, str] | None:
    if result is None or not result.validation_result_ref_id:
        return None
    return {"resource_type": "validation_result", "resource_id": result.validation_result_ref_id}


def _result_status(
    task: AiTask,
    *,
    result: AiTaskResult | None,
    result_payload: dict[str, Any] | None,
) -> str:
    base_status = result.status if result is not None else task.status
    if (
        task.task_type == "polish_feedback_generation"
        and isinstance(result_payload, dict)
        and result_payload.get("status") == "generated"
    ):
        return "succeeded"
    if task.task_type == "polish_feedback_generation" and base_status == "succeeded":
        return "running"
    return base_status


def _candidate_refs(payload: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return []
    refs: list[dict[str, str]] = []
    metadata = payload.get("feedback_metadata")
    if isinstance(metadata, dict):
        candidate_ref = str(metadata.get("candidate_ref") or "").strip()
        if candidate_ref:
            refs.append({"resource_type": "feedback_candidate", "resource_id": candidate_ref})
        asset_refs = metadata.get("asset_update_candidate_refs")
        if isinstance(asset_refs, list):
            for item in asset_refs:
                resource_id = str(item or "").strip()
                if resource_id:
                    refs.append({"resource_type": "asset_update_candidate", "resource_id": resource_id})
    return _dedupe_refs(refs)


def _suggestion_refs(payload: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return []
    refs = payload.get("suggestion_refs")
    if not isinstance(refs, list):
        return []
    return _dedupe_refs(
        [
            {"resource_type": str(item.get("resource_type") or ""), "resource_id": str(item.get("resource_id") or "")}
            for item in refs
            if isinstance(item, dict)
        ]
    )


def _projected_candidate_refs(
    result: AiTaskResult | None,
    *,
    payload: dict[str, Any] | None,
    safe_summary: dict[str, Any],
) -> list[dict[str, str]]:
    return (
        _refs_from_json(getattr(result, "candidate_refs_json", None))
        or _refs_from_json(safe_summary.get("candidate_refs"))
        or _candidate_refs(payload)
    )


def _projected_suggestion_refs(
    result: AiTaskResult | None,
    *,
    payload: dict[str, Any] | None,
    safe_summary: dict[str, Any],
) -> list[dict[str, str]]:
    return (
        _refs_from_json(getattr(result, "suggestion_refs_json", None))
        or _refs_from_json(safe_summary.get("suggestion_refs"))
        or _suggestion_refs(payload)
    )


def _projected_validation_errors(
    result: AiTaskResult | None,
    *,
    payload: dict[str, Any] | None,
    safe_summary: dict[str, Any],
) -> list[str]:
    return (
        _safe_string_list(getattr(result, "validation_errors_json", None))
        or _safe_string_list(safe_summary.get("validation_errors"))
        or _validation_errors(payload)
    )


def _refs_from_json(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "resource_type": _safe_text(item.get("resource_type")),
                "resource_id": _safe_text(item.get("resource_id")),
            }
        )
    return _dedupe_refs(refs)


def _dedupe_refs(refs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, str]] = []
    for ref in refs:
        resource_type = ref["resource_type"].strip()
        resource_id = ref["resource_id"].strip()
        key = (resource_type, resource_id)
        if resource_type and resource_id and key not in seen:
            seen.add(key)
            result.append({"resource_type": resource_type, "resource_id": resource_id})
    return result


def _validation_errors(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("validation_errors"), list):
        return []
    return _safe_string_list(payload["validation_errors"])


def _user_visible_status(
    status: str,
    payload: dict[str, Any] | None,
    *,
    safe_summary: dict[str, Any],
) -> str:
    if isinstance(payload, dict):
        value = payload.get("user_visible_status")
        if isinstance(value, str) and value.strip():
            return _safe_text(value)
    value = safe_summary.get("user_visible_status")
    if isinstance(value, str) and value.strip():
        return _safe_text(value)
    if status == "running":
        return "反馈生成中"
    if status == "queued":
        return "任务已排队"
    if status == "succeeded":
        return "反馈已生成"
    if status == "generation_failed":
        return "反馈生成失败，可重试"
    if status == "timed_out":
        return "任务已超时，可重试"
    if status == "cancelled":
        return "任务已取消"
    return status


def _is_retryable(status: str, payload: dict[str, Any] | None, *, safe_summary: dict[str, Any]) -> bool:
    if isinstance(payload, dict) and isinstance(payload.get("retryable"), bool):
        return bool(payload["retryable"])
    if isinstance(safe_summary.get("retryable"), bool):
        return bool(safe_summary["retryable"])
    return status in {"generation_failed", "timed_out", "source_unavailable"}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_summary(result: AiTaskResult | None) -> dict[str, Any]:
    safe_summary_json = getattr(result, "safe_summary_json", None)
    if result is None or not isinstance(safe_summary_json, dict):
        return {}
    return response_safe_feedback_payload(safe_summary_json)


def _safe_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = _safe_text(item)
        if text:
            result.append(text)
    return result


def _safe_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return redact_feedback_payload_text(text).strip()


def _feedback_result_payload(
    task: AiTask,
    payload: dict[str, Any] | None,
    *,
    safe_summary: dict[str, Any],
) -> dict[str, Any] | None:
    if task.task_type != "polish_feedback_generation":
        return None
    source = payload if isinstance(payload, dict) else safe_summary
    if not _looks_like_generated_feedback_payload(source):
        return None
    return response_safe_feedback_payload(source)


def _looks_like_generated_feedback_payload(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("status") == "generated"
        and isinstance(value.get("feedback_text"), str)
    )
