from pydantic import BaseModel

class ReportGenerateRequest(BaseModel):
    agency_record_id: int

class ReportRecordOut(BaseModel):
    id: int
    organization_id: int
    agency_record_id: int
    report_type: str
    markdown_path: str | None = None
    pdf_path: str | None = None
    summary: str | None = None

    class Config:
        from_attributes = True
