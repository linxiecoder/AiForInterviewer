"""SQLAlchemy repository for report retrieval."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.reports.entities import ReportDetail, ReportSectionDetail
from app.application.reports.ports import ReportRepository
from app.domain.shared.refs import ResourceRef
from app.infrastructure.db.models.report import InterviewReport as InterviewReportModel
from app.infrastructure.db.models.report import ReportSection as ReportSectionModel
from app.infrastructure.db.repositories.base import SqlAlchemyRepository
from app.infrastructure.db.session import get_session_factory


class SqlAlchemyReportRepository(SqlAlchemyRepository, ReportRepository):
    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        *,
        session: Session | None = None,
    ) -> None:
        super().__init__(session_factory, session=session)

    def get_ref(self, report_id: str) -> ResourceRef | None:
        with self.session_scope() as session:
            found = session.get(InterviewReportModel, report_id)
        if found is None or found.status == "deleted":
            return None
        return ResourceRef(resource_type="report", resource_id=report_id)

    def get_report(self, *, owner_id: str, report_id: str) -> ReportDetail | None:
        with self.session_scope() as session:
            report = session.scalar(
                select(InterviewReportModel).where(
                    InterviewReportModel.owner_id == owner_id,
                    InterviewReportModel.id == report_id,
                    InterviewReportModel.status != "deleted",
                )
            )
            if report is None:
                return None
            sections = session.scalars(
                select(ReportSectionModel)
                .where(
                    ReportSectionModel.owner_id == owner_id,
                    ReportSectionModel.report_id == report_id,
                    ReportSectionModel.status != "deleted",
                )
                .order_by(ReportSectionModel.created_at.asc(), ReportSectionModel.id.asc())
            ).all()
            return _to_report_detail(report, sections)

    @classmethod
    def clear_state(cls) -> None:
        session_factory = get_session_factory()
        with session_factory() as session:
            session.execute(delete(ReportSectionModel))
            session.execute(delete(InterviewReportModel))
            session.commit()


def _to_report_detail(
    report: InterviewReportModel,
    sections: list[ReportSectionModel],
) -> ReportDetail:
    return ReportDetail(
        report_id=report.id,
        owner_id=report.owner_id,
        session_id=report.session_id,
        report_type=report.report_type,
        report_status=report.status,
        score_ref=report.score_result_id,
        generated_at=report.generated_at,
        sections=tuple(_to_section_detail(section) for section in sections),
    )


def _to_section_detail(section: ReportSectionModel) -> ReportSectionDetail:
    return ReportSectionDetail(
        section_key=section.section_key,
        section_summary=section.section_summary,
        score_ref=section.score_result_id,
    )
