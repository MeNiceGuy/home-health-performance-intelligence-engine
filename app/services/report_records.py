from sqlalchemy.orm import Session
from app.models.report_record import ReportRecord

def save_report_record(
    db: Session,
    organization_id: int,
    agency_record_id: int,
    report_type: str,
    markdown_path: str | None,
    pdf_path: str | None,
    summary: str | None,
    created_by: str | None,
) -> ReportRecord:
    record = ReportRecord(
        organization_id=organization_id,
        agency_record_id=agency_record_id,
        report_type=report_type,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        summary=summary,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def list_reports_for_org(db: Session, organization_id: int) -> list[ReportRecord]:
    return (
        db.query(ReportRecord)
        .filter(ReportRecord.organization_id == organization_id)
        .order_by(ReportRecord.created_at.desc())
        .all()
    )

def list_reports_for_agency(db: Session, organization_id: int, agency_record_id: int) -> list[ReportRecord]:
    return (
        db.query(ReportRecord)
        .filter(
            ReportRecord.organization_id == organization_id,
            ReportRecord.agency_record_id == agency_record_id
        )
        .order_by(ReportRecord.created_at.desc())
        .all()
    )
