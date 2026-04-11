from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password
from app.schemas.security import PasswordResetRequest, PasswordResetConfirmRequest
from app.services.password_reset import create_reset_token, get_reset_record
from app.services.mailer import send_email
from app.services.audit import append_audit_event

router = APIRouter(prefix="/password", tags=["password"])

@router.post("/reset-request")
def request_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        reset = create_reset_token(db, user)
        send_email(
            to_email=user.email,
            subject="Password reset request",
            body=f"Use this link to reset your password:\n\n{reset['reset_url']}\n\nExpires: {reset['expires_at']}",
        )
        append_audit_event(
            db=db,
            action="password_reset_requested",
            detail=f"Password reset requested for {user.email}",
            organization_id=user.organization_id,
            username=user.username,
        )
    return {"status": "ok"}

@router.post("/reset-confirm")
def confirm_reset(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)):
    record = get_reset_record(db, payload.token)
    if not record or record.used:
        raise HTTPException(status_code=400, detail="Invalid or used token.")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.hashed_password = hash_password(payload.new_password)
    record.used = True
    db.commit()

    append_audit_event(
        db=db,
        action="password_reset_completed",
        detail=f"Password reset completed for {user.email}",
        organization_id=user.organization_id,
        username=user.username,
    )
    return {"status": "password_updated"}
