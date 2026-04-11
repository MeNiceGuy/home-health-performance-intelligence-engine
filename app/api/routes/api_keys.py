from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.security import ApiKeyCreateRequest, ApiKeyToggleRequest
from app.services.api_keys import generate_api_key
from app.services.api_key_records import create_api_key_record, list_api_keys, get_api_key_by_id
from app.services.audit import append_audit_event

router = APIRouter(prefix="/keys", tags=["api-keys"])

@router.post("")
def create_key(
    payload: ApiKeyCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    full_key, prefix, key_hash = generate_api_key()
    record = create_api_key_record(db, current_user.organization_id, payload.name, prefix, key_hash, current_user.username)
    append_audit_event(
        db=db,
        action="api_key_created",
        detail=f"API key created: {payload.name}",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {
        "id": record.id,
        "name": record.name,
        "key_prefix": record.key_prefix,
        "api_key": full_key
    }

@router.get("")
def list_keys(
    current_user: User = Depends(require_role("admin", "analyst")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        return []
    keys = list_api_keys(db, current_user.organization_id)
    return [
        {
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "active": k.active,
            "created_by": k.created_by,
            "created_at": k.created_at,
        }
        for k in keys
    ]

@router.patch("/{key_id}")
def toggle_key(
    key_id: int,
    payload: ApiKeyToggleRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    record = get_api_key_by_id(db, current_user.organization_id, key_id)
    if not record:
        raise HTTPException(status_code=404, detail="API key not found.")
    record.active = payload.active
    db.commit()
    db.refresh(record)
    append_audit_event(
        db=db,
        action="api_key_toggled",
        detail=f"API key {record.name} active={record.active}",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {"id": record.id, "active": record.active}
