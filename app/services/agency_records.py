import json
from sqlalchemy.orm import Session
from app.models.agency_record import AgencyRecord

JSON_FIELDS = {
    "pain_points": "pain_points_json",
    "cms_context": "cms_context_json",
    "scorecard": "scorecard_json",
    "compliance_findings": "compliance_findings_json",
    "trend_summary": "trend_summary_json",
    "alerts": "alerts_json",
    "monthly_series": "monthly_series_json",
}

SCALAR_FIELDS = [
    "agency_name","state","city","ownership_type","avg_monthly_patients","clinicians_total",
    "star_rating","readmission_rate","patient_satisfaction","oasis_timeliness","soc_delay_days",
    "visit_completion_rate","documentation_lag_hours","turnover_rate","open_positions",
    "visits_per_clinician_week","ehr_vendor","evv_present","scheduling_software",
    "telehealth_present","automation_present","monthly_revenue_range","cost_pressure_level",
    "improvement_budget","leadership_readiness","change_resistance","training_infrastructure",
    "notes"
]

def save_agency_record(db: Session, organization_id: int, data: dict) -> AgencyRecord:
    record = AgencyRecord(organization_id=organization_id)
    for field in SCALAR_FIELDS:
        if field in data:
            setattr(record, field, data.get(field))
    for source_key, model_field in JSON_FIELDS.items():
        setattr(record, model_field, json.dumps(data.get(source_key, {} if source_key != "pain_points" else [])))
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def update_agency_record(db: Session, record: AgencyRecord, data: dict) -> AgencyRecord:
    for field in SCALAR_FIELDS:
        if field in data:
            setattr(record, field, data.get(field))
    for source_key, model_field in JSON_FIELDS.items():
        if source_key in data:
            setattr(record, model_field, json.dumps(data.get(source_key, {} if source_key != "pain_points" else [])))
    db.commit()
    db.refresh(record)
    return record

def list_agency_records(db: Session, organization_id: int) -> list[AgencyRecord]:
    return (
        db.query(AgencyRecord)
        .filter(AgencyRecord.organization_id == organization_id)
        .order_by(AgencyRecord.updated_at.desc())
        .all()
    )

def get_agency_record(db: Session, organization_id: int, agency_record_id: int) -> AgencyRecord | None:
    return (
        db.query(AgencyRecord)
        .filter(
            AgencyRecord.id == agency_record_id,
            AgencyRecord.organization_id == organization_id
        )
        .first()
    )

def record_to_payload(record: AgencyRecord) -> dict:
    payload = {field: getattr(record, field) for field in SCALAR_FIELDS}
    payload["id"] = record.id
    payload["organization_id"] = record.organization_id
    payload["pain_points"] = json.loads(record.pain_points_json or "[]")
    payload["cms_context"] = json.loads(record.cms_context_json or "{}")
    payload["scorecard"] = json.loads(record.scorecard_json or "{}")
    payload["compliance_findings"] = json.loads(record.compliance_findings_json or "[]")
    payload["trend_summary"] = json.loads(record.trend_summary_json or "{}")
    payload["alerts"] = json.loads(record.alerts_json or "[]")
    payload["monthly_series"] = json.loads(record.monthly_series_json or "[]")
    return payload
