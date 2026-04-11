from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.admin_service import get_invite_by_token, accept_invite
from app.services.audit import append_audit_event

router = APIRouter(prefix="/invites", tags=["invites"])

class InviteAcceptRequest(BaseModel):
    token: str
    username: str
    password: str

@router.post("/accept")
def invite_accept(payload: InviteAcceptRequest, db: Session = Depends(get_db)):
    invite = get_invite_by_token(db, payload.token)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if invite.accepted:
        raise HTTPException(status_code=400, detail="Invite already accepted.")

    user = accept_invite(db, invite, payload.username, payload.password)
    append_audit_event(
        db=db,
        action="invite_accepted",
        detail=f"Invite accepted by {user.username}",
        organization_id=user.organization_id,
        username=user.username,
    )
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "organization_id": user.organization_id,
    }
