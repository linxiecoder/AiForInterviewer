"""Report HTTP adapters."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db_session_factory, require_authenticated_actor
from app.api.envelope import success_envelope
from app.api.errors import raise_api_error
from app.application.reports.entities import ReportDetail
from app.application.reports.queries import GetReportQuery
from app.application.reports.use_cases import ReportUseCases
from app.domain.auth.entities import CurrentActor
from app.domain.shared.enums import SourceAvailability
from app.domain.shared.errors import DomainError
from app.infrastructure.db.repositories.reports import SqlAlchemyReportRepository
from app.schemas.refs import ResourceRef, SourceAvailabilitySchema
from app.schemas.reports import ReportDetailResponse, ReportSectionResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    actor: CurrentActor = Depends(require_authenticated_actor),
    session_factory: sessionmaker[Session] = Depends(get_db_session_factory),
) -> Any:
    result = _use_cases(session_factory).get_report(
        GetReportQuery(owner_id=actor.owner_id, report_id=report_id)
    )
    if not result.is_success:
        _raise_result_error(result.error)
    return success_envelope(resource_type="report_detail", data=_to_report_detail(result.value))


def _use_cases(session_factory: sessionmaker[Session]) -> ReportUseCases:
    return ReportUseCases(repository=SqlAlchemyReportRepository(session_factory))


def _to_report_detail(report: ReportDetail | None) -> dict:
    if report is None:
        raise_api_error(
            status_code=500,
            code="internal_error",
            message="Report result is not available.",
        )

    return ReportDetailResponse(
        report_id=report.report_id,
        report_type=report.report_type,
        session_ref=report.session_id,
        report_status=report.report_status,
        sections=[
            ReportSectionResponse(
                section_key=section.section_key,
                section_summary=section.section_summary,
                score_ref=section.score_ref,
            )
            for section in report.sections
        ],
        score_ref=report.score_ref,
        copy_content_available=report.copy_content_available,
        source_availability=_source_availability(report),
        generated_at=report.generated_at,
    ).model_dump(mode="json")


def _source_availability(report: ReportDetail) -> SourceAvailabilitySchema:
    if report.session_id:
        return SourceAvailabilitySchema(
            source_ref=ResourceRef(resource_type="polish_session", resource_id=report.session_id),
            status=SourceAvailability.SOURCE_AVAILABLE,
            can_read_for_generation=True,
            display_summary="Polish session snapshot available.",
        )
    return SourceAvailabilitySchema(
        source_ref=ResourceRef(resource_type="report", resource_id=report.report_id),
        status=SourceAvailability.SOURCE_UNAVAILABLE,
        can_read_for_generation=False,
        display_summary="Report source session is unavailable.",
    )


def _raise_result_error(error: DomainError | None) -> None:
    if error is None:
        raise_api_error(status_code=500, code="internal_error", message="Unknown report error.")
    raise_api_error(status_code=_error_status(error.code), code=error.code, message=error.message)


def _error_status(code: str) -> int:
    if code == "not_found_or_inaccessible":
        return 404
    if code == "validation_failed":
        return 422
    if code.endswith("_conflict"):
        return 409
    return 400
