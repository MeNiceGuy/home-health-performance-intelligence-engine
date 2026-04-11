from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.agency_records import get_agency_record, record_to_payload
from app.services.analytics.risk import calculate_risk_summary
from app.services.audit import append_audit_event

router = APIRouter(prefix="/risk", tags=["risk"])

@router.get("/agency/{agency_record_id}")
def agency_risk(agency_record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")

    record = get_agency_record(db, current_user.organization_id, agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")

    payload = record_to_payload(record)
    result = calculate_risk_summary(payload)

    append_audit_event(
        db=db,
        action="risk_viewed",
        detail=f"Viewed risk summary for record {agency_record_id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=record.agency_name,
    )

    return result
