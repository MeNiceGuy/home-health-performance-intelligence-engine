from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.services.audit import list_audit_events

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
def get_audit_events(
    current_user: User = Depends(require_role("admin", "analyst")),
    db: Session = Depends(get_db)
):
    events = list_audit_events(db, current_user.organization_id, limit=100)
    return [
        {
            "id": e.id,
            "action": e.action,
            "detail": e.detail,
            "agency_name": e.agency_name,
            "username": e.username,
            "ip_address": e.ip_address,
            "created_at": e.created_at,
        }
        for e in events
    ]
