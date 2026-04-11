import secrets
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.invite import Invite
from app.models.org_settings import OrgSettings
from app.models.subscription import Subscription

def create_org_user(db: Session, organization_id: int, username: str, email: str | None, password: str, role: str) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        organization_id=organization_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_invite(db: Session, organization_id: int, email: str, role: str, created_by: str | None) -> Invite:
    invite = Invite(
        organization_id=organization_id,
        email=email,
        role=role,
        token=secrets.token_urlsafe(32),
        accepted=False,
        created_by=created_by,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite

def get_invite_by_token(db: Session, token: str) -> Invite | None:
    return db.query(Invite).filter(Invite.token == token).first()

def accept_invite(db: Session, invite: Invite, username: str, password: str) -> User:
    user = User(
        username=username,
        email=invite.email,
        hashed_password=hash_password(password),
        role=invite.role,
        is_active=True,
        organization_id=invite.organization_id,
    )
    invite.accepted = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_or_create_org_settings(db: Session, organization_id: int) -> OrgSettings:
    settings = db.query(OrgSettings).filter(OrgSettings.organization_id == organization_id).first()
    if not settings:
        settings = OrgSettings(organization_id=organization_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_org_settings(db: Session, organization_id: int, data: dict) -> OrgSettings:
    settings = get_or_create_org_settings(db, organization_id)
    for key, value in data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings

def get_or_create_subscription(db: Session, organization_id: int) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.organization_id == organization_id).first()
    if not sub:
        sub = Subscription(organization_id=organization_id, plan_name="free", status="inactive")
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

def update_subscription_from_stripe(
    db: Session,
    organization_id: int,
    stripe_customer_id: str | None,
    stripe_subscription_id: str | None,
    plan_name: str,
    status: str,
    current_period_end: str | None,
) -> Subscription:
    sub = get_or_create_subscription(db, organization_id)
    sub.stripe_customer_id = stripe_customer_id
    sub.stripe_subscription_id = stripe_subscription_id
    sub.plan_name = plan_name
    sub.status = status
    sub.current_period_end = current_period_end
    db.commit()
    db.refresh(sub)
    return sub
