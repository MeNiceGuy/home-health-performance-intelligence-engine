from pathlib import Path

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal

# Import models so SQLAlchemy metadata knows all referenced tables
from app.models.organization import Organization
from app.models.user import User
from app.models.agency_record import AgencyRecord
from app.models.report_record import ReportRecord

from app.services.agency_records import record_to_payload
from app.services.reporting.generator import build_markdown_report, save_markdown_report
from app.services.reporting.pdf_export import markdown_to_simple_pdf
from app.services.report_records import save_report_record

@celery_app.task(name="generate_report_task")
def generate_report_task(organization_id: int, agency_record_id: int, username: str | None = None):
    db = SessionLocal()
    try:
        record = (
            db.query(AgencyRecord)
            .filter(
                AgencyRecord.id == agency_record_id,
                AgencyRecord.organization_id == organization_id
            )
            .first()
        )
        if not record:
            return {"status": "error", "detail": "Agency record not found"}

        payload = record_to_payload(record)
        markdown = build_markdown_report(payload)
        markdown_path = save_markdown_report(record.agency_name, markdown)
        pdf_path = str(Path(markdown_path).with_suffix(".pdf"))
        markdown_to_simple_pdf(markdown, pdf_path)

        report_record = save_report_record(
            db=db,
            organization_id=organization_id,
            agency_record_id=record.id,
            report_type="performance_intelligence",
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            summary=f"Generated background report for {record.agency_name}",
            created_by=username,
        )

        return {
            "status": "ok",
            "report_id": report_record.id,
            "markdown_path": markdown_path,
            "pdf_path": pdf_path,
        }
    finally:
        db.close()
