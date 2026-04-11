from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportGenerateRequest
from app.services.billing import can_generate_report
from app.services.agency_records import get_agency_record, record_to_payload
from app.services.reporting.generator import build_markdown_report, save_markdown_report
from app.services.reporting.pdf_export import markdown_to_simple_pdf
from app.services.report_records import save_report_record, list_reports_for_org, list_reports_for_agency
from app.services.audit import append_audit_event
from app.tasks.report_tasks import generate_report_task

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate")
def generate_report(payload: ReportGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")

    if not can_generate_report(current_user):
        raise HTTPException(status_code=403, detail="Report limit reached. Upgrade plan.")

    record = get_agency_record(db, current_user.organization_id, payload.agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")

    agency_payload = record_to_payload(record)
    markdown = build_markdown_report(agency_payload)
    markdown_path = save_markdown_report(record.agency_name, markdown)
    pdf_path = str(Path(markdown_path).with_suffix(".pdf"))
    markdown_to_simple_pdf(markdown, pdf_path)

    report_record = save_report_record(
        db=db,
        organization_id=current_user.organization_id,
        agency_record_id=record.id,
        report_type="performance_intelligence",
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        summary=f"Generated performance intelligence report for {record.agency_name}",
        created_by=current_user.username,
    )

    append_audit_event(
        db=db,
        action="report_generated",
        detail=f"Generated report {report_record.id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=record.agency_name,
    )

    return {
        "report_id": report_record.id,
        "agency_record_id": record.id,
        "markdown_path": markdown_path,
        "pdf_path": pdf_path,
    }

@router.post("/generate-async")
def generate_report_async(payload: ReportGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")

    if not can_generate_report(current_user):
        raise HTTPException(status_code=403, detail="Report limit reached. Upgrade plan.")

    record = get_agency_record(db, current_user.organization_id, payload.agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")

    task = generate_report_task.delay(current_user.organization_id, record.id, current_user.username)

    append_audit_event(
        db=db,
        action="report_queued",
        detail=f"Queued background report for record {record.id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=record.agency_name,
    )

    return {
        "task_id": task.id,
        "agency_record_id": record.id,
        "status": "queued",
    }

@router.get("/tasks/{task_id}")
def get_report_task_status(task_id: str):
    result = generate_report_task.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }

@router.get("")
def get_reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        return []
    reports = list_reports_for_org(db, current_user.organization_id)
    return [
        {
            "id": r.id,
            "agency_record_id": r.agency_record_id,
            "report_type": r.report_type,
            "markdown_path": r.markdown_path,
            "pdf_path": r.pdf_path,
            "summary": r.summary,
            "created_by": r.created_by,
            "created_at": r.created_at,
        }
        for r in reports
    ]

@router.get("/agency/{agency_record_id}")
def get_reports_for_agency(agency_record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        return []
    reports = list_reports_for_agency(db, current_user.organization_id, agency_record_id)
    return [
        {
            "id": r.id,
            "agency_record_id": r.agency_record_id,
            "report_type": r.report_type,
            "markdown_path": r.markdown_path,
            "pdf_path": r.pdf_path,
            "summary": r.summary,
            "created_by": r.created_by,
            "created_at": r.created_at,
        }
        for r in reports
    ]

@router.get("/{report_id}/download/md")
def download_markdown(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = list_reports_for_org(db, current_user.organization_id)
    report = next((r for r in reports if r.id == report_id), None)
    if not report or not report.markdown_path or not Path(report.markdown_path).exists():
        raise HTTPException(status_code=404, detail="Markdown file not found.")
    return FileResponse(path=report.markdown_path, filename=Path(report.markdown_path).name, media_type="text/markdown")

@router.get("/{report_id}/download/pdf")
def download_pdf(report_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = list_reports_for_org(db, current_user.organization_id)
    report = next((r for r in reports if r.id == report_id), None)
    if not report or not report.pdf_path or not Path(report.pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    return FileResponse(path=report.pdf_path, filename=Path(report.pdf_path).name, media_type="application/pdf")
