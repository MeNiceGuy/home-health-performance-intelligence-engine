from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import AdminCreateUserRequest, InviteCreateRequest, OrgSettingsUpdateRequest
from app.services.admin_service import (
    create_org_user,
    create_invite,
    get_or_create_org_settings,
    update_org_settings,
    get_or_create_subscription,
)
from app.services.audit import append_audit_event

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/users")
def admin_create_user(
    payload: AdminCreateUserRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    user = create_org_user(
        db=db,
        organization_id=current_user.organization_id,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    append_audit_event(
        db=db,
        action="admin_user_created",
        detail=f"Created user {user.username}",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "organization_id": user.organization_id,
    }

@router.post("/invites")
def admin_create_invite(
    payload: InviteCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    invite = create_invite(
        db=db,
        organization_id=current_user.organization_id,
        email=payload.email,
        role=payload.role,
        created_by=current_user.username,
    )
    append_audit_event(
        db=db,
        action="invite_created",
        detail=f"Invite created for {invite.email}",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {
        "id": invite.id,
        "email": invite.email,
        "role": invite.role,
        "token": invite.token,
        "accepted": invite.accepted,
    }

@router.get("/settings")
def admin_get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    settings = get_or_create_org_settings(db, current_user.organization_id)
    return {
        "display_name": settings.display_name,
        "logo_url": settings.logo_url,
        "primary_color": settings.primary_color,
        "report_footer": settings.report_footer,
        "timezone": settings.timezone,
    }

@router.put("/settings")
def admin_update_settings(
    payload: OrgSettingsUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    settings = update_org_settings(db, current_user.organization_id, payload.model_dump(exclude_none=True))
    append_audit_event(
        db=db,
        action="org_settings_updated",
        detail="Organization settings updated",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {
        "display_name": settings.display_name,
        "logo_url": settings.logo_url,
        "primary_color": settings.primary_color,
        "report_footer": settings.report_footer,
        "timezone": settings.timezone,
    }

@router.get("/subscription")
def admin_get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    sub = get_or_create_subscription(db, current_user.organization_id)
    return {
        "plan_name": sub.plan_name,
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "stripe_customer_id": sub.stripe_customer_id,
        "stripe_subscription_id": sub.stripe_subscription_id,
    }
