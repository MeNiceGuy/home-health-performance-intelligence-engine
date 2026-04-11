from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class ReportRecord(Base):
    __tablename__ = "report_records"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    agency_record_id = Column(Integer, ForeignKey("agency_records.id"), nullable=False, index=True)

    report_type = Column(String, nullable=False, default="performance_intelligence")
    markdown_path = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
