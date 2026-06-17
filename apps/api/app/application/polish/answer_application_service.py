"""Focused application service for Polish answer operations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Protocol

from app.application.common.result import ApplicationResult
from app.application.polish.commands import CreatePolishAnswerCommand
from app.application.polish.entities import PolishAnswer
from app.domain.shared.errors import DomainError


ANSWER_STATUS_SAVED = "saved"
ANSWER_TEXT_MIN_LENGTH = 2
ANSWER_TEXT_MAX_LENGTH = 8000
ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH = 128


@dataclass(frozen=True)
class AnswerSubmissionBoundary:
    answer_text: str
    idempotency_key: str | None
    request_body_hash: str


class AnswerSubmissionBoundaryBuilder:
    def prepare(self, command: CreatePolishAnswerCommand) -> ApplicationResult[AnswerSubmissionBoundary]:
        answer_text = command.answer_text.strip()
        text_error = self._validate_answer_text(answer_text)
        if text_error is not None:
            return ApplicationResult(error=text_error)

        raw_idempotency_key = getattr(command, "idempotency_key", None)
        idempotency_key_error = self._validate_answer_idempotency_key(raw_idempotency_key)
        if idempotency_key_error is not None:
            return ApplicationResult(error=idempotency_key_error)
        return ApplicationResult(
            value=AnswerSubmissionBoundary(
                answer_text=answer_text,
                idempotency_key=self._normalize_answer_idempotency_key(raw_idempotency_key),
                request_body_hash=_answer_request_body_hash(command=command, answer_text=answer_text),
            )
        )

    def build_answer(
        self,
        *,
        command: CreatePolishAnswerCommand,
        answer_id: str,
        answer_round: int,
        answer_text: str,
        timestamp: datetime,
    ) -> PolishAnswer:
        return PolishAnswer(
            answer_id=answer_id,
            owner_id=command.owner_id,
            actor_id=command.actor_id,
            session_id=command.session_id,
            question_id=command.question_id,
            answer_round=answer_round,
            answer_text=answer_text,
            status=ANSWER_STATUS_SAVED,
            created_at=timestamp,
            updated_at=timestamp,
            idempotency_key=self._normalize_answer_idempotency_key(getattr(command, "idempotency_key", None)),
            request_body_hash=_answer_request_body_hash(command=command, answer_text=answer_text),
        )

    @staticmethod
    def _validate_answer_text(answer_text: str) -> DomainError | None:
        if not answer_text:
            return DomainError(
                code="validation_failed",
                message="Answer text cannot be empty",
                details={
                    "field": "answer_text",
                    "min_length": ANSWER_TEXT_MIN_LENGTH,
                    "max_length": ANSWER_TEXT_MAX_LENGTH,
                },
            )
        if len(answer_text) < ANSWER_TEXT_MIN_LENGTH:
            return DomainError(
                code="validation_failed",
                message="Answer text is too short",
                details={
                    "field": "answer_text",
                    "min_length": ANSWER_TEXT_MIN_LENGTH,
                    "actual_length": len(answer_text),
                },
            )
        if len(answer_text) > ANSWER_TEXT_MAX_LENGTH:
            return DomainError(
                code="validation_failed",
                message="Answer text is too long",
                details={
                    "field": "answer_text",
                    "max_length": ANSWER_TEXT_MAX_LENGTH,
                    "actual_length": len(answer_text),
                },
            )
        return None

    def _validate_answer_idempotency_key(self, raw_key: object) -> DomainError | None:
        key = self._normalize_answer_idempotency_key(raw_key)
        if key is None:
            return None
        if len(key) > ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH:
            return DomainError(
                code="validation_failed",
                message="Idempotency key is too long",
                details={
                    "field": "idempotency_key",
                    "max_length": ANSWER_IDEMPOTENCY_KEY_MAX_LENGTH,
                    "actual_length": len(key),
                },
            )
        return None

    @staticmethod
    def _normalize_answer_idempotency_key(raw_key: object) -> str | None:
        if raw_key is None:
            return None
        key = str(raw_key).strip()
        return key or None


def _answer_request_body_hash(*, command: CreatePolishAnswerCommand, answer_text: str) -> str:
    base_ref = command.base_question_version_ref
    payload = {
        "question_id": command.question_id,
        "answer_text": answer_text,
        "base_question_version_ref": None
        if base_ref is None
        else {
            "resource_type": base_ref.resource_type,
            "resource_id": base_ref.resource_id,
            "version_id": base_ref.version_id,
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


class _AnswerOperations(Protocol):
    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]: ...


class PolishAnswerApplicationService:
    def __init__(self, operations: _AnswerOperations) -> None:
        self._operations = operations

    def bind(self, operations: _AnswerOperations) -> None:
        self._operations = operations

    def create_answer(self, command: CreatePolishAnswerCommand) -> ApplicationResult[PolishAnswer]:
        return self._operations.create_answer(command)
