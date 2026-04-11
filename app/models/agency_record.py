from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class AgencyRecord(Base):
    __tablename__ = "agency_records"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    agency_name = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    city = Column(String, nullable=True, index=True)
    ownership_type = Column(String, nullable=True)

    avg_monthly_patients = Column(Float, nullable=True)
    clinicians_total = Column(Float, nullable=True)
    star_rating = Column(Float, nullable=True)
    readmission_rate = Column(Float, nullable=True)
    patient_satisfaction = Column(Float, nullable=True)
    oasis_timeliness = Column(Float, nullable=True)
    soc_delay_days = Column(Float, nullable=True)
    visit_completion_rate = Column(Float, nullable=True)
    documentation_lag_hours = Column(Float, nullable=True)
    turnover_rate = Column(Float, nullable=True)
    open_positions = Column(Float, nullable=True)
    visits_per_clinician_week = Column(Float, nullable=True)

    ehr_vendor = Column(String, nullable=True)
    evv_present = Column(Boolean, default=False)
    scheduling_software = Column(String, nullable=True)
    telehealth_present = Column(Boolean, default=False)
    automation_present = Column(Boolean, default=False)

    monthly_revenue_range = Column(String, nullable=True)
    cost_pressure_level = Column(String, nullable=True)
    improvement_budget = Column(String, nullable=True)
    leadership_readiness = Column(String, nullable=True)
    change_resistance = Column(String, nullable=True)
    training_infrastructure = Column(String, nullable=True)

    pain_points_json = Column(Text, nullable=True)
    cms_context_json = Column(Text, nullable=True)
    scorecard_json = Column(Text, nullable=True)
    compliance_findings_json = Column(Text, nullable=True)
    trend_summary_json = Column(Text, nullable=True)
    alerts_json = Column(Text, nullable=True)
    monthly_series_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
