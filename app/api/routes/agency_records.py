from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.agency import AgencyIntake, AgencyUpdateRequest
from app.services.agency_records import (
    save_agency_record,
    list_agency_records,
    get_agency_record,
    record_to_payload,
    update_agency_record,
)
from app.services.audit import append_audit_event

router = APIRouter(prefix="/agency-records", tags=["agency-records"])

@router.post("")
def create_agency_record(payload: AgencyIntake, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    record = save_agency_record(db, current_user.organization_id, payload.data)

    append_audit_event(
        db=db,
        action="agency_record_created",
        detail=f"Created agency record {record.id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=record.agency_name,
    )

    return {"id": record.id, "agency_name": record.agency_name, "organization_id": record.organization_id}

@router.get("")
def get_my_records(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        return []
    records = list_agency_records(db, current_user.organization_id)
    return [
        {
            "id": r.id,
            "agency_name": r.agency_name,
            "state": r.state,
            "city": r.city,
            "updated_at": r.updated_at,
        }
        for r in records
    ]

@router.get("/{agency_record_id}")
def get_one_record(agency_record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    record = get_agency_record(db, current_user.organization_id, agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")
    return record_to_payload(record)

@router.put("/{agency_record_id}")
def update_one_record(agency_record_id: int, payload: AgencyUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    record = get_agency_record(db, current_user.organization_id, agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")
    updated = update_agency_record(db, record, payload.data)

    append_audit_event(
        db=db,
        action="agency_record_updated",
        detail=f"Updated agency record {updated.id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=updated.agency_name,
    )

    return {"id": updated.id, "agency_name": updated.agency_name, "organization_id": updated.organization_id}

@router.delete("/{agency_record_id}")
def delete_one_record(agency_record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")

    record = get_agency_record(db, current_user.organization_id, agency_record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Agency record not found.")

    agency_name = record.agency_name
    db.delete(record)
    db.commit()

    append_audit_event(
        db=db,
        action="agency_record_deleted",
        detail=f"Deleted agency record {agency_record_id}",
        organization_id=current_user.organization_id,
        username=current_user.username,
        agency_name=agency_name,
    )

    return {"status": "deleted", "id": agency_record_id, "agency_name": agency_name}
